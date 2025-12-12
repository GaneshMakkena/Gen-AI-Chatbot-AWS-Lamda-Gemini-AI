"""
Bedrock Client - Utility module for AWS Bedrock API interactions.
Handles LLM inference and step-by-step image generation using bearer token authentication.
"""

import os
import json
import base64
import re
import uuid
import requests
import boto3
import concurrent.futures
from typing import Optional, Dict, Any, List, Tuple

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration - BEDROCK_REGION for explicit setting, AWS_REGION as fallback (auto-set in Lambda)
AWS_REGION = os.getenv("BEDROCK_REGION") or os.getenv("AWS_REGION", "us-east-1")
BEARER_TOKEN = os.getenv("AWS_BEARER_TOKEN_BEDROCK")
LLM_MODEL_ID = os.getenv("BEDROCK_LLM_MODEL", "mistral.mistral-large-3-675b-instruct")
IMAGE_MODEL_ID = "amazon.titan-image-generator-v1"

# S3 bucket for storing generated images
IMAGES_BUCKET = os.getenv("IMAGES_BUCKET", "")

# Image settings
IMAGE_WIDTH = 512
IMAGE_HEIGHT = 512

# Bedrock API endpoints
BEDROCK_BASE_URL = f"https://bedrock-runtime.{AWS_REGION}.amazonaws.com"

# S3 client (initialized lazily)
_s3_client = None

def get_s3_client():
    """Get or create S3 client."""
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client('s3', region_name=AWS_REGION)
    return _s3_client


def upload_image_to_s3(image_base64: str, step_number: str, query_hash: str) -> Optional[str]:
    """
    Upload a base64 image to S3 and return the public URL.
    
    Args:
        image_base64: Base64 encoded image data
        step_number: Step number for the filename
        query_hash: Hash of the query for unique identification
    
    Returns:
        Public URL of the uploaded image, or None on error
    """
    if not IMAGES_BUCKET:
        print("IMAGES_BUCKET not configured, returning base64")
        return None
    
    try:
        # Decode base64 to binary
        image_data = base64.b64decode(image_base64)
        
        # Generate unique key
        image_key = f"steps/{query_hash}/step_{step_number}_{uuid.uuid4().hex[:8]}.png"
        
        # Upload to S3
        s3 = get_s3_client()
        s3.put_object(
            Bucket=IMAGES_BUCKET,
            Key=image_key,
            Body=image_data,
            ContentType='image/png'
        )
        
        # Return the public URL
        image_url = f"https://{IMAGES_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{image_key}"
        print(f"Uploaded image to S3: {image_url}")
        return image_url
        
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return None


def get_headers() -> Dict[str, str]:
    """Get authorization headers for Bedrock API."""
    return {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }


def clean_llm_response(response: str) -> str:
    """
    Clean the LLM response by removing reasoning tags and other artifacts.
    """
    if not response:
        return response
    
    # Remove <reasoning>...</reasoning> tags and their content
    cleaned = re.sub(r'<reasoning>.*?</reasoning>', '', response, flags=re.DOTALL)
    cleaned = re.sub(r'<thinking>.*?</thinking>', '', cleaned, flags=re.DOTALL)
    
    # Also handle unclosed tags
    cleaned = re.sub(r'<reasoning>.*$', '', cleaned, flags=re.DOTALL)
    cleaned = re.sub(r'<thinking>.*$', '', cleaned, flags=re.DOTALL)
    
    # Clean up extra whitespace
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    cleaned = cleaned.strip()
    
    return cleaned


def invoke_llm(
    prompt: str,
    context: str = "",
    max_tokens: int = 2048,
    temperature: float = 0.7
) -> Optional[str]:
    """
    Invoke Mistral Large 3 for in-depth medical research and treatment instructions.
    """
    
    # Enhanced system prompt for thorough, conversational medical assistance
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
    
    # Request body for Mistral
    request_body = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context: {context}\n\n{prompt}" if context else prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    model_path = LLM_MODEL_ID.replace(":", "%3A")
    url = f"{BEDROCK_BASE_URL}/model/{model_path}/invoke"
    
    print(f"Calling LLM: {LLM_MODEL_ID}")
    
    try:
        response = requests.post(
            url,
            headers=get_headers(),
            json=request_body,
            timeout=180  # Longer timeout for thorough responses
        )
        
        print(f"LLM Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error response: {response.text}")
            return None
            
        result = response.json()
        
        # Extract response based on model output format
        raw_response = None
        if "choices" in result:
            raw_response = result["choices"][0]["message"]["content"]
        elif "content" in result:
            if isinstance(result["content"], list):
                raw_response = result["content"][0]["text"]
            else:
                raw_response = result["content"]
        elif "outputs" in result:
            raw_response = result["outputs"][0]["text"]
        elif "completion" in result:
            raw_response = result["completion"]
        else:
            print(f"Unknown response format: {result.keys()}")
            raw_response = json.dumps(result)
        
        return clean_llm_response(raw_response)
            
    except requests.exceptions.Timeout:
        print("LLM request timed out")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error invoking LLM: {e}")
        return None


def extract_treatment_steps(llm_response: str) -> List[Dict[str, str]]:
    """
    Parse the LLM response to extract individual treatment steps.
    Returns a list of dicts with 'step_number', 'title', and 'description'.
    """
    steps = []
    
    # Pattern to match "Step X: Title" or "**Step X: Title**"
    step_pattern = r'\*?\*?Step\s*(\d+)[:\s]*\*?\*?\s*\[?([^\]\n]+)\]?\*?\*?'
    
    # Find all step headers
    matches = list(re.finditer(step_pattern, llm_response, re.IGNORECASE))
    
    for i, match in enumerate(matches):
        step_num = match.group(1)
        title = match.group(2).strip().strip('*[]')
        
        # Get the content between this step and the next
        start_pos = match.end()
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            # Find the next section header or end of content
            next_section = re.search(r'\n\*\*[^S]', llm_response[start_pos:])
            if next_section:
                end_pos = start_pos + next_section.start()
            else:
                end_pos = len(llm_response)
        
        description = llm_response[start_pos:end_pos].strip()
        # Clean up the description
        description = re.sub(r'^\*?\*?\s*', '', description)
        description = description[:300]  # Limit for image prompt
        
        steps.append({
            'step_number': step_num,
            'title': title,
            'description': description
        })
    
    # If no steps found with the pattern, try alternative parsing
    if not steps:
        # Try numbered list format: "1. Action" or "1) Action"
        alt_pattern = r'(\d+)[.)\s]+([^\n]+)'
        alt_matches = re.findall(alt_pattern, llm_response)
        
        for num, content in alt_matches[:10]:  # Limit to 10 steps
            if len(content) > 10:  # Filter out short matches
                steps.append({
                    'step_number': num,
                    'title': content[:50].strip(),
                    'description': content.strip()
                })
    
    return steps


def generate_step_image(step: Dict[str, str], query_context: str) -> Optional[str]:
    """
    Generate an image for a specific treatment step.
    """
    # Create a detailed prompt for this step
    prompt = f"Medical first aid illustration, Step {step['step_number']}: {step['title']}. {step['description'][:100]}. Clear educational diagram showing the action being performed, professional medical illustration style, 512x512."
    
    # Clean up the prompt
    prompt = prompt.replace('\n', ' ').strip()
    prompt = re.sub(r'\s+', ' ', prompt)
    
    return generate_image(prompt)


def process_single_step(step: Dict, query: str, query_hash: Optional[str] = None) -> Dict:
    """
    Process a single step: generate prompt, generate image, and optionally upload to S3.
    """
    try:
        print(f"Generating image for Step {step['step_number']}: {step['title']}")
        
        # Create specific prompt
        image_prompt = create_step_image_prompt(step, query)
        
        # Generate image
        image_b64 = generate_image(image_prompt)
        image_url = None
        
        # Upload to S3 if we have an image and hash
        if image_b64 and query_hash:
            image_url = upload_image_to_s3(image_b64, step['step_number'], query_hash)
            
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
        return {
            'step_number': step['step_number'],
            'title': step['title'],
            'description': step['description'][:200],
            'image_prompt': None,
            'image': None,
            'image_url': None
        }


def generate_all_step_images(steps: List[Dict], query: str, query_hash: Optional[str] = None) -> List[Dict]:
    """
    Generate images for all extracted steps in PARALLEL.
    Returns list of dicts with step info, base64 image, and optional S3 URL.
    """
    # Use ThreadPoolExecutor for parallel generation
    # Max workers = 10 to ensure all steps run in a single batch (max 9-10s total)
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all tasks
        future_to_step = {
            executor.submit(process_single_step, step, query, query_hash): step 
            for step in steps
        }
        
        # Collect results
        results = []
        for future in concurrent.futures.as_completed(future_to_step):
            res = future.result()
            results.append(res)
            
    # Sort back into original order
    try:
        results.sort(key=lambda x: int(re.sub(r'\D', '', str(x['step_number']))))
    except:
        pass # Keep as is if sorting fails
        
    return results


def create_step_image_prompt(step: Dict[str, str], query: str) -> str:
    """
    Create a specific image generation prompt for a treatment step.
    """
    query_lower = query.lower()
    
    # Detect the medical context
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
            
    # Buid the prompt with SPECIFIC query context
    # Use the original query to ensure we capture "neck", "hand", etc.
    # We remove common "how to" prefixes to focus on the core subject
    core_subject = re.sub(r'^(how to|what is|treat|cure)\s+', '', query_lower).strip()
    
    prompt = f"Medical illustration for {medical_context} on {core_subject}. Step {step['step_number']}: {step['title']}. "
    prompt += f"Clear educational diagram showing action on {core_subject} if applicable. {step['description'][:100]}. "
    prompt += "Professional medical illustration, clean white background, anatomically accurate."
    
    return prompt


def generate_image(
    prompt: str,
    width: int = IMAGE_WIDTH,
    height: int = IMAGE_HEIGHT
) -> Optional[str]:
    """
    Generate a single medical procedure image using Titan Image Generator v1.
    """
    
    enhanced_prompt = f"Medical illustration, educational diagram, clear and professional: {prompt}"
    
    request_body = {
        "taskType": "TEXT_IMAGE",
        "textToImageParams": {
            "text": enhanced_prompt[:500]  # Titan has prompt length limits
        },
        "imageGenerationConfig": {
            "numberOfImages": 1,
            "quality": "standard",
            "height": height,
            "width": width,
            "cfgScale": 8.0,
            "seed": 0
        }
    }
    
    url = f"{BEDROCK_BASE_URL}/model/{IMAGE_MODEL_ID}/invoke"
    
    try:
        response = requests.post(
            url,
            headers=get_headers(),
            json=request_body,
            timeout=120
        )
        
        if response.status_code != 200:
            print(f"Image generation error: {response.text}")
            return None
            
        result = response.json()
        
        if "images" in result:
            return result["images"][0]
        elif "artifacts" in result:
            return result["artifacts"][0]["base64"]
        
        return None
            
    except Exception as e:
        print(f"Error generating image: {e}")
        return None


def should_generate_images(query: str, response: str) -> bool:
    """
    Determine if step-by-step images should be generated.
    """
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
    print("Testing Bedrock Client...")
    print(f"LLM Model: {LLM_MODEL_ID}")
    print(f"Image Model: {IMAGE_MODEL_ID}")
    
    # Test with CPR question
    response = invoke_llm("How do I perform CPR on an adult?")
    if response:
        print(f"\nLLM Response:\n{response[:500]}...")
        
        # Extract steps
        steps = extract_treatment_steps(response)
        print(f"\nExtracted {len(steps)} steps:")
        for step in steps:
            print(f"  Step {step['step_number']}: {step['title']}")
