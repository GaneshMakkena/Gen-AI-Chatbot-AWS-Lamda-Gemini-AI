"""
Gemini Client - Using Google's NEW genai SDK for both LLM and Image generation.
Model: gemini-2.5-flash-image supports both text and image output.
"""

import os
import base64
import re
import uuid
import boto3
import concurrent.futures
from typing import Optional, Dict, Any, List

# NEW SDK - google-genai (not google-generativeai)
from google import genai

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
AWS_REGION = os.getenv("BEDROCK_REGION") or os.getenv("AWS_REGION", "us-east-1")

# Model IDs
LLM_MODEL_ID = os.getenv("GEMINI_LLM_MODEL", "gemini-2.5-pro")
IMAGE_MODEL_ID = "gemini-2.5-flash-image"  # Supports native image generation

# S3 bucket for storing generated images
IMAGES_BUCKET = os.getenv("IMAGES_BUCKET", "")

# Initialize Gemini client
client = None
if GOOGLE_API_KEY:
    client = genai.Client(api_key=GOOGLE_API_KEY)

# S3 client (initialized lazily)
_s3_client = None

def get_s3_client():
    """Get or create S3 client."""
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client('s3', region_name=AWS_REGION)
    return _s3_client


def upload_image_to_s3(image_bytes: bytes, step_number: str, query_hash: str) -> Optional[str]:
    """Upload image bytes to S3 and return a presigned URL."""
    if not IMAGES_BUCKET:
        print("IMAGES_BUCKET not configured")
        return None
    
    try:
        image_key = f"steps/{query_hash}/step_{step_number}_{uuid.uuid4().hex[:8]}.png"
        
        s3 = get_s3_client()
        s3.put_object(
            Bucket=IMAGES_BUCKET,
            Key=image_key,
            Body=image_bytes,
            ContentType='image/png'
        )
        
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': IMAGES_BUCKET, 'Key': image_key},
            ExpiresIn=7200
        )
        print(f"Uploaded image to S3: {presigned_url[:80]}...")
        return presigned_url
        
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return None


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


def invoke_llm(
    prompt: str,
    context: str = "",
    max_tokens: int = 2048,
    temperature: float = 0.7,
    thinking_mode: bool = False
) -> Optional[str]:
    """
    Invoke Gemini for medical research and treatment instructions.
    
    Args:
        prompt: User's query
        context: Additional context
        max_tokens: Maximum tokens in response
        temperature: Creativity level (0-1)
        thinking_mode: If True, show the model's reasoning process
    """
    
    if not client:
        print("Gemini client not initialized - missing API key")
        return None
    
    # Base system prompt
    system_prompt = """You are MediBot, an expert medical first aid assistant. You provide thorough, research-based medical guidance.

## Your Approach:
1. **Understand the Intent**: Determine if the user has a medical query or is just greeting/chatting.
2. **For Medical Issues**: Provide comprehensive research and step-by-step treatment.
3. **For General Chat**: Respond naturally and briefly, offering help.

## Response Format:
**IF (and ONLY IF) the user presents a medical situation or asks for first aid help**, use this format:

**Understanding Your Situation**
Brief explanation of the condition/problem

**Step-by-Step Treatment Guide**

**Step 1: [Action Title]**
Detailed instruction for this step

**Step 2: [Action Title]**
Detailed instruction for this step

(Continue for all necessary steps)

**⚠️ Important Warnings**
Any critical safety information

**When to Seek Professional Help**
Conditions that require medical attention

## Guidelines:
- Be warm, reassuring, and conversational
- Explain WHY each step is important
- Use simple, clear language anyone can understand
- Be specific about materials needed
- Include timing information where relevant
- Never diagnose serious conditions - recommend professional help"""
    
    # Add thinking mode instruction if enabled
    if thinking_mode:
        system_prompt += """

## Thinking Mode (ENABLED)
Before providing your response, you MUST first show your reasoning process inside <thinking></thinking> tags. 
Think through:
- What is the user asking?
- What medical knowledge applies here?
- What are the key safety considerations?
- What's the best way to structure the response?

Example:
<thinking>
The user is asking about treating a minor burn...
Key considerations: cooling, avoiding ice, pain management...
I should structure this with immediate first aid, then ongoing care...
</thinking>

Then provide your actual response after the thinking section."""
    
    try:
        full_prompt = f"Context: {context}\n\n{prompt}" if context else prompt
        combined_prompt = f"{system_prompt}\n\nUser: {full_prompt}"
        
        print(f"Calling Gemini LLM: {LLM_MODEL_ID} (thinking_mode={thinking_mode})")
        
        response = client.models.generate_content(
            model=LLM_MODEL_ID,
            contents=combined_prompt,
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
        print(f"Error invoking Gemini LLM: {e}")
        import traceback
        print(traceback.format_exc())
        return None


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


def generate_image(prompt: str) -> Optional[bytes]:
    """
    Generate an image using Gemini's native image generation.
    Uses gemini-2.5-flash-image model which supports image output.
    Returns raw image bytes.
    """
    if not client:
        print("Gemini client not initialized - missing API key")
        return None
    
    try:
        enhanced_prompt = f"Create a clear, professional medical illustration: {prompt}. Style: educational diagram, clean white background, anatomically accurate."
        
        print(f"Generating image with Gemini: {IMAGE_MODEL_ID}")
        
        response = client.models.generate_content(
            model=IMAGE_MODEL_ID,
            contents=enhanced_prompt,
        )
        
        # Extract image from response parts
        if response.parts:
            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data is not None:
                    # Get the image data
                    if hasattr(part.inline_data, 'data'):
                        print(f"Image generated successfully!")
                        return part.inline_data.data
        
        # Check candidates structure
        if hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts'):
                        for part in candidate.content.parts:
                            if hasattr(part, 'inline_data') and part.inline_data:
                                if hasattr(part.inline_data, 'data'):
                                    print(f"Image found in candidates!")
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


def create_step_image_prompt(step: Dict[str, str], query: str) -> str:
    """Create a specific image generation prompt for a treatment step."""
    query_lower = query.lower()
    
    context_keywords = {
        "cpr": "CPR cardiopulmonary resuscitation",
        "choking": "Heimlich maneuver choking first aid",
        "bleeding": "wound care bleeding control",
        "burn": "burn treatment first aid",
        "fracture": "bone fracture splinting",
        "sprain": "sprain treatment RICE",
        "cut": "wound cleaning bandaging",
        "wound": "wound care treatment",
    }
    
    medical_context = "first aid treatment"
    for keyword, context in context_keywords.items():
        if keyword in query_lower:
            medical_context = context
            break
    
    core_subject = re.sub(r'^(how to|what is|treat|cure)\s+', '', query_lower).strip()
    
    prompt = f"Medical illustration for {medical_context} on {core_subject}. Step {step['step_number']}: {step['title']}. "
    prompt += f"Clear educational diagram showing action on {core_subject}. {step['description'][:100]}. "
    prompt += "Professional medical illustration, clean white background, anatomically accurate."
    
    return prompt


def process_single_step(step: Dict, query: str, query_hash: Optional[str] = None) -> Dict:
    """Process a single step: generate prompt, generate image, upload to S3."""
    try:
        print(f"Generating image for Step {step['step_number']}: {step['title']}")
        
        image_prompt = create_step_image_prompt(step, query)
        image_bytes = generate_image(image_prompt)
        image_url = None
        image_b64 = None
        
        if image_bytes:
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            if query_hash:
                image_url = upload_image_to_s3(image_bytes, step['step_number'], query_hash)
            
        return {
            'step_number': step['step_number'],
            'title': step['title'],
            'description': step['description'][:200],
            'image_prompt': image_prompt,
            'image': image_b64,
            'image_url': image_url
        }
    except Exception as e:
        print(f"Error processing step {step['step_number']}: {e}")
        import traceback
        print(traceback.format_exc())
        return {
            'step_number': step['step_number'],
            'title': step['title'],
            'description': step['description'][:200],
            'image_prompt': None,
            'image': None,
            'image_url': None
        }


def generate_all_step_images(steps: List[Dict], query: str, query_hash: Optional[str] = None) -> List[Dict]:
    """Generate images for all extracted steps in PARALLEL."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_step = {
            executor.submit(process_single_step, step, query, query_hash): step 
            for step in steps
        }
        
        results = []
        for future in concurrent.futures.as_completed(future_to_step):
            res = future.result()
            results.append(res)
    
    try:
        results.sort(key=lambda x: int(re.sub(r'\D', '', str(x['step_number']))))
    except:
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
