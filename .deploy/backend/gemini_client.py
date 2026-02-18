"""
Gemini Client - Using Google's NEW genai SDK for both LLM and Image generation.
Model: gemini-2.5-flash-image supports both text and image output.
"""

import os
import base64
import re
import uuid
from aws_clients import get_s3_client as _get_pooled_s3_client
import concurrent.futures
from typing import Optional, Dict, Any, List

# NEW SDK - google-genai (not google-generativeai)
from google import genai
from dotenv import load_dotenv

# Structured logging
from aws_lambda_powertools import Logger

# Load environment variables
load_dotenv()

logger = Logger(service="medibot")

# Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Model IDs
LLM_MODEL_ID = os.getenv("GEMINI_LLM_MODEL", "gemini-2.5-pro")
IMAGE_MODEL_ID = "gemini-2.5-flash-image"  # Supports native image generation

# S3 bucket for storing generated images
IMAGES_BUCKET = os.getenv("IMAGES_BUCKET", "")

# Initialize Gemini client
client = None
if GOOGLE_API_KEY:
    client = genai.Client(api_key=GOOGLE_API_KEY)

# S3 client — delegated to centralized aws_clients for connection pooling
def get_s3_client():
    """Get shared S3 client with connection pooling."""
    return _get_pooled_s3_client()


def upload_image_to_s3(image_bytes: bytes, step_number: str, query_hash: str) -> tuple[Optional[str], Optional[str]]:
    """Upload image bytes to S3 and return (presigned_url, s3_key)."""
    if not IMAGES_BUCKET:
        logger.warning("IMAGES_BUCKET not configured")
        return None, None

    try:
        image_key = f"steps/{query_hash}/step_{step_number}_{uuid.uuid4().hex[:8]}.png"

        s3 = get_s3_client()
        s3.put_object(
            Bucket=IMAGES_BUCKET,
            Key=image_key,
            ContentType='image/png',
            Body=image_bytes
        )

        # Generate URL valid for 7 days (max practical for S3)
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': IMAGES_BUCKET, 'Key': image_key},
            ExpiresIn=604800  # 7 days
        )
        logger.info("Uploaded image to S3", key=image_key)
        return presigned_url, image_key

    except Exception as e:
        logger.error("Error uploading to S3", error=str(e))
        return None, None


def clean_llm_response(response: str, keep_thinking: bool = False) -> str:
    """Clean the LLM response by optionally removing thinking tags."""
    if not response:
        return response

    if not keep_thinking:
        # Remove thinking tags if user doesn't want to see them
        cleaned = re.sub(r'<thinking>.*?</thinking>', '', response, flags=re.DOTALL)
    else:
        # Format thinking sections nicely for display
        cleaned = re.sub(r'<thinking>', '\n\n---\n**🧠 My Thinking Process:**\n', response)
        cleaned = re.sub(r'</thinking>', '\n\n---\n\n', cleaned)

    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()


# ============================================
# Optimized System Prompt (Token-Efficient)
# ============================================
_SYSTEM_PROMPT = """You are MediBot, a medical assistance AI providing step-by-step guidance.

Rules:
- Number steps explicitly (Step 1 to Step N). Each step is self-contained.
- Keep each step to 2-3 concise sentences. Avoid filler.
- Each step maps to one image (don't reference images in text).
- Structure each step internally: action, method, what to avoid, expected outcome.
- NEVER diagnose or prescribe. Recommend professional care when risk is high.
- Use warm, simple, reassuring language.

Format:
**Understanding Your Situation**
1-2 sentence overview.

**Step 1: [Action Title]**
Instruction with materials, timing, technique.

(Continue for all necessary steps)

**⚠️ Warnings**
Safety-critical information.

**When to Seek Professional Help**
Urgent conditions.

Greetings: If user says "Hi"/"Hello" or is vague, respond warmly, summarize capabilities, and ask for their medical concern. Do NOT generate steps for a random condition."""

_THINKING_ADDENDUM = """

Thinking Mode: Show reasoning in <thinking>...</thinking> tags before your response."""


def _build_prompt(prompt: str, context: str, thinking_mode: bool) -> str:
    """Build the full prompt from system prompt, context, and user query."""
    sys = _SYSTEM_PROMPT + (_THINKING_ADDENDUM if thinking_mode else "")
    full = f"Context: {context}\n\n{prompt}" if context else prompt
    return f"{sys}\n\nUser: {full}"


def invoke_llm(
    prompt: str,
    context: str = "",
    max_tokens: int = 1536,
    temperature: float = 0.7,
    thinking_mode: bool = False,
    model_override: Optional[str] = None
) -> Optional[str]:
    """
    Invoke Gemini for medical research and treatment instructions.

    Args:
        prompt: User's query
        context: Additional context
        max_tokens: Maximum tokens in response
        temperature: Creativity level (0-1)
        thinking_mode: If True, show the model's reasoning process
        model_override: Optional model ID to override the default
    """

    if not client:
        logger.error("Gemini client not initialized - missing API key")
        return None

    model = model_override or LLM_MODEL_ID

    try:
        from google.genai import types

        combined_prompt = _build_prompt(prompt, context, thinking_mode)

        logger.info("Calling Gemini LLM", model=model, thinking_mode=thinking_mode)

        response = client.models.generate_content(
            model=model,
            contents=combined_prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            ),
        )

        # Extract text from response
        response_text = None
        if response.text:
            response_text = response.text
        elif response.parts:
            for part in response.parts:
                if hasattr(part, 'text') and part.text:
                    response_text = part.text
                    break

        if response_text:
            return clean_llm_response(response_text, keep_thinking=thinking_mode)

        return None

    except Exception as e:
        logger.error("Error invoking Gemini LLM", error=str(e))
        import traceback
        print(traceback.format_exc())
        return None


def invoke_llm_streaming(
    prompt: str,
    context: str = "",
    max_tokens: int = 1536,
    temperature: float = 0.7,
    thinking_mode: bool = False,
    model_override: Optional[str] = None
):
    """
    Stream Gemini response token-by-token for SSE.

    Yields text chunks as they arrive from the model.
    Falls back silently if streaming is not available.
    """
    if not client:
        logger.error("Gemini client not initialized - missing API key")
        return

    model = model_override or LLM_MODEL_ID

    try:
        from google.genai import types

        combined_prompt = _build_prompt(prompt, context, thinking_mode)

        logger.info("Streaming Gemini LLM", model=model)

        response_stream = client.models.generate_content_stream(
            model=model,
            contents=combined_prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            ),
        )

        for chunk in response_stream:
            if chunk.text:
                yield chunk.text
            elif hasattr(chunk, 'parts') and chunk.parts:
                for part in chunk.parts:
                    if hasattr(part, 'text') and part.text:
                        yield part.text

    except Exception as e:
        logger.error("Error in streaming Gemini LLM", error=str(e))
        import traceback
        print(traceback.format_exc())


def invoke_llm_with_files(
    prompt: str,
    files: List[Dict[str, Any]],
    context: str = "",
    thinking_mode: bool = False
) -> Optional[str]:
    """
    Invoke Gemini with file attachments (PDFs, images).

    Args:
        prompt: User's query
        files: List of dicts with 'data' (bytes), 'mime_type', 'filename'
        context: Additional context
        thinking_mode: If True, show model reasoning
    """

    if not client:
        print("Gemini client not initialized - missing API key")
        return None

    try:
        from google.genai import types

        # Build system prompt for file analysis
        system_prompt = """You are MediBot, an expert medical assistant. You are analyzing medical documents and images provided by the user.

## Your Approach:
1. **Analyze the attached files** thoroughly - look for key medical information
2. **Extract important data**: conditions, medications, test results, diagnoses
3. **Summarize clearly** in simple language the user can understand
4. **Provide context** about what the values mean
5. **Suggest follow-up questions** they should ask their doctor

## Guidelines:
- Be thorough but concise
- Highlight any abnormal values or concerns
- Explain medical terms in simple language
- Always recommend consulting a healthcare professional for medical decisions
"""

        if thinking_mode:
            system_prompt += "\n\nShow your thinking process in <thinking>...</thinking> tags before your response."

        # Build content parts
        content_parts = []

        # Add text prompt
        full_prompt = f"Context: {context}\n\n{prompt}" if context else prompt
        content_parts.append(f"{system_prompt}\n\nUser: {full_prompt}")

        # Add file parts
        for f in files:
            try:
                file_part = types.Part.from_bytes(
                    data=f["data"],
                    mime_type=f["mime_type"]
                )
                content_parts.append(file_part)
                print(f"Added file: {f.get('filename', 'unknown')} ({f['mime_type']})")
            except Exception as e:
                print(f"Failed to add file {f.get('filename')}: {e}")

        print(f"Calling Gemini with {len(files)} files (model={LLM_MODEL_ID})")

        response = client.models.generate_content(
            model=LLM_MODEL_ID,
            contents=content_parts,
        )

        # Extract text from response
        response_text = None
        if response.text:
            response_text = response.text
        elif response.parts:
            for part in response.parts:
                if hasattr(part, 'text') and part.text:
                    response_text = part.text
                    break

        if response_text:
            return clean_llm_response(response_text, keep_thinking=thinking_mode)

        return None

    except Exception as e:
        print(f"Error invoking Gemini with files: {e}")
        import traceback
        print(traceback.format_exc())
        return None


def generate_image(prompt: str, width: int = 512, height: int = 512) -> Optional[bytes]:
    """
    Generate an image using Gemini's native image generation.
    Uses gemini-2.5-flash-image model which supports image output.
    Returns raw image bytes.
    """
    if not client:
        print("Gemini client not initialized - missing API key")
        return None

    try:
        enhanced_prompt = (
            "Create a clear, professional medical illustration: "
            f"{prompt}. Style: educational diagram, clean white background, "
            f"anatomically accurate. Preferred size: {width}x{height}."
        )

        print(f"Generating image with Gemini: {IMAGE_MODEL_ID}")

        response = client.models.generate_content(
            model=IMAGE_MODEL_ID,
            contents=enhanced_prompt,
        )

        # Try candidates structure first (new SDK format)
        if hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts'):
                        for part in candidate.content.parts:
                            if hasattr(part, 'inline_data') and part.inline_data:
                                if hasattr(part.inline_data, 'data'):
                                    print("Image generated successfully!")
                                    return part.inline_data.data

        # Fall back to direct parts attribute (old SDK format)
        if hasattr(response, 'parts') and response.parts:
            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data is not None:
                    if hasattr(part.inline_data, 'data'):
                        print("Image generated successfully!")
                        return part.inline_data.data

        print("No image found in Gemini response")
        if hasattr(response, 'text') and response.text:
            print(f"Response text: {response.text[:200]}...")
        return None

    except Exception as e:
        print(f"Error generating image with Gemini: {e}")
        import traceback
        print(traceback.format_exc())
        return None


def extract_treatment_steps(llm_response: str) -> List[Dict[str, str]]:
    """Parse the LLM response to extract individual treatment steps."""
    steps = []

    step_pattern = r'\*?\*?Step\s*(\d+)[:\s]*\*?\*?\s*\[?([^\]\n]+)\]?\*?\*?'
    matches = list(re.finditer(step_pattern, llm_response, re.IGNORECASE))

    for i, match in enumerate(matches):
        step_num = match.group(1)
        title = match.group(2).strip().strip('*[]')

        start_pos = match.end()
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            next_section = re.search(r'\n\*\*[^S]', llm_response[start_pos:])
            end_pos = start_pos + next_section.start() if next_section else len(llm_response)

        description = llm_response[start_pos:end_pos].strip()
        description = re.sub(r'^\*?\*?\s*', '', description)[:300]

        steps.append({
            'step_number': step_num,
            'title': title,
            'description': description
        })

    return steps


def create_step_visual_guide_prompt(step: Dict[str, str], query: str) -> str:
    """
    Create a 4-panel grid prompt for ONE step.
    Each panel shows a different aspect of the same step.
    """
    query_lower = query.lower()

    # Formal Production-Grade Image Prompt Template
    prompt = f"""Generate a medically informative visual guide using a 2×2 grid layout.

Context:
This image explains Step {step['step_number']} of a medical assistance guide.

Step Description:
"{step['title']}: {step['description'][:200]}"

Grid Requirements:
Each panel must visually represent one sub-direction of the same step:

Top-Left Panel:
Show the primary action clearly and safely.

Top-Right Panel:
Show the correct method or technique (posture, tool usage, hand placement).

Bottom-Left Panel:
Show what NOT to do or common mistakes, using clear visual contrast.

Bottom-Right Panel:
Show the expected correct outcome or confirmation state.

Visual Style:
- Clear, instructional, non-graphic
- Neutral medical illustration style
- No blood, gore, or invasive depiction
- High clarity, simple background
- Universally understandable symbols

Restrictions:
- Do not add extra steps
- Do not contradict the step text
- Do not include text-heavy labels
- Avoid realism that may cause distress

Purpose:
This image must act as a complete visual explanation of Step {step['step_number']}.
"""
    return prompt


def process_single_step_image(step: Dict, query: str, query_hash: Optional[str] = None) -> Dict:
    """
    Process a single step: generate a dedicated 4-panel image.
    Includes fallback handling for image generation failures.
    """
    step_number = step['step_number']
    title = step['title']
    description = step['description'][:200]

    # Fallback text structure (Tier 2 degradation)
    fallback_text = {
        'action': f"Primary action for {title}",
        'method': f"How to perform: {description[:80]}...",
        'caution': "Common mistakes to avoid when performing this step.",
        'result': "Expected outcome when done correctly."
    }

    try:
        logger.info("Generating step visual guide", step_number=step_number)

        image_prompt = create_step_visual_guide_prompt(step, query)
        image_bytes = generate_image(image_prompt)
        image_url = None
        image_b64 = None
        image_failed = False
        s3_key = None

        if image_bytes:
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            if query_hash:
                image_url, s3_key = upload_image_to_s3(image_bytes, step_number, query_hash)
        else:
            # Tier 1: Image generation returned None
            image_failed = True
            logger.warning("Image generation returned None", step=step_number)

        return {
            'step_number': step_number,
            'title': title,
            'description': description,
            'image_prompt': image_prompt,
            'image': image_b64,
            'image_url': image_url,
            's3_key': s3_key,  # Store key for URL regeneration
            'is_composite': False,
            'panel_index': None,
            'image_failed': image_failed,
            'fallback_text': fallback_text if image_failed else None
        }

    except Exception as e:
        # Tier 1: Exception during image generation
        logger.error("Error generating step image", step=step_number, error=str(e))
        return {
            'step_number': step_number,
            'title': title,
            'description': description,
            'image_prompt': None,
            'image': None,
            'image_url': None,
            'image_failed': True,
            'fallback_text': fallback_text
        }


def calculate_image_budget(
    total_steps: int,
    elapsed_seconds: float = 0.0,
    lambda_timeout: int = 300,
    buffer_seconds: int = 60,
    seconds_per_image: float = 3.0,
) -> int:
    """
    Dynamically calculate how many images we can afford to generate.

    Factors: time already spent, Lambda timeout, estimated time per image.
    """
    remaining_time = lambda_timeout - elapsed_seconds - buffer_seconds
    if remaining_time <= 0:
        return 0

    max_affordable = int(remaining_time / seconds_per_image)
    # Hard cap at 10, soft floor at 3 (always try to generate a few)
    budget = max(min(max_affordable, 10), 0)

    logger.info("Image budget calculated",
                total_steps=total_steps,
                elapsed_s=round(elapsed_seconds, 1),
                remaining_s=round(remaining_time, 1),
                budget=budget)
    return budget


def prioritize_steps(steps: List[Dict], budget: int) -> List[Dict]:
    """
    Select the most important steps when budget < total steps.

    Priority: first step, last step, then steps with safety keywords,
    then remaining steps in order.
    """
    if budget >= len(steps):
        return steps

    if budget <= 0:
        return []

    safety_keywords = ["danger", "warning", "caution", "emergency", "avoid",
                       "do not", "critical", "immediately", "stop"]

    # Always include first and last
    selected_indices = {0, len(steps) - 1}

    # Score remaining steps by safety relevance
    scored = []
    for i, step in enumerate(steps):
        if i in selected_indices:
            continue
        text = (step.get('title', '') + ' ' + step.get('description', '')).lower()
        score = sum(1 for kw in safety_keywords if kw in text)
        scored.append((score, i))

    # Sort by score descending, pick top ones
    scored.sort(key=lambda x: -x[0])
    for _, idx in scored:
        if len(selected_indices) >= budget:
            break
        selected_indices.add(idx)

    # Return in original order
    prioritized = [steps[i] for i in sorted(selected_indices)]
    logger.info("Prioritized steps",
                original=len(steps),
                selected=len(prioritized),
                indices=sorted(selected_indices))
    return prioritized


def generate_all_step_images(
    steps: List[Dict],
    query: str,
    query_hash: Optional[str] = None,
    elapsed_seconds: float = 0.0
) -> List[Dict]:
    """
    Generate images using Step-Aligned Visual Guidance.
    1 step → 1 image (4-panel grid explaining that step in depth).

    Dynamic time budgeting: calculates how many images fit in remaining
    Lambda execution time, then prioritizes the most important steps.
    """
    # Dynamic budget based on time remaining
    budget = calculate_image_budget(
        total_steps=len(steps),
        elapsed_seconds=elapsed_seconds,
    )

    # Prioritize important steps if budget < total
    steps_to_generate = prioritize_steps(steps, budget)

    if not steps_to_generate:
        logger.warning("No image budget remaining")
        return []

    logger.info("Generating step-aligned images",
                step_count=len(steps_to_generate),
                budget=budget)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_step = {
            executor.submit(process_single_step_image, step, query, query_hash): step
            for step in steps_to_generate
        }

        results = []
        for future in concurrent.futures.as_completed(future_to_step):
            result = future.result()
            results.append(result)

    # Sort by step number
    try:
        results.sort(key=lambda x: int(re.sub(r'\D', '', str(x['step_number']))))
    except Exception:
        pass

    return results


def should_generate_images(query: str, response: str) -> bool:
    """Determine if step-by-step images should be generated."""
    visual_keywords = [
        "cpr", "cardiopulmonary", "chest compression", "heimlich",
        "bandage", "wrap", "splint", "immobilize", "position",
        "wound", "cut", "bleeding", "burn", "fracture", "sprain",
        "treat", "treatment", "first aid", "apply", "clean", "dress",
        "choking", "fainting", "unconscious", "recovery position",
        "how to", "steps", "procedure"
    ]

    combined_text = (query + " " + response).lower()
    return any(keyword in combined_text for keyword in visual_keywords)


def detect_medical_topic(query: str) -> Optional[str]:
    """Detect the primary medical topic from the query."""
    query_lower = query.lower()

    topics = {
        "cpr": ["cpr", "cardiopulmonary", "chest compression", "cardiac arrest"],
        "choking": ["choking", "heimlich", "can't breathe", "airway blocked"],
        "bleeding": ["bleeding", "wound", "cut", "blood", "laceration"],
        "burn": ["burn", "burned", "scalded"],
        "fracture": ["fracture", "broken bone", "broken arm", "broken leg"],
        "fainting": ["fainting", "fainted", "unconscious", "passed out"],
        "sprain": ["sprain", "twisted", "ankle", "wrist injury"],
    }

    for topic, keywords in topics.items():
        if any(keyword in query_lower for keyword in keywords):
            return topic

    return None


# Test function
if __name__ == "__main__":
    print("Testing Gemini Client with NEW SDK...")
    print(f"LLM Model: {LLM_MODEL_ID}")
    print(f"Image Model: {IMAGE_MODEL_ID}")

    # Test LLM
    response = invoke_llm("How do I perform CPR on an adult?")
    if response:
        print(f"\nLLM Response:\n{response[:500]}...")

    # Test Image
    image = generate_image("A person performing chest compressions on an adult for CPR")
    if image:
        print(f"\nImage generated: {len(image)} bytes")
