"""
Report Analyzer Module for MediBot
Uses Gemini Multimodal to analyze uploaded medical reports (PDFs, images)
and extract health information for the user's profile.
"""

import os
import json
import base64
import boto3
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

# Import health profile module
from health_profile import (
    add_condition,
    add_medication,
    add_allergy,
    add_key_fact,
    add_report_summary,
    update_basic_info
)

# Environment variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
REPORTS_BUCKET = os.getenv("REPORTS_BUCKET", "")
AWS_REGION = os.getenv("BEDROCK_REGION", "us-east-1")

# S3 client for fetching reports
s3_client = boto3.client("s3", region_name=AWS_REGION)

# Lazy-loaded Gemini client
_genai = None


def get_genai():
    """Lazy load the Gemini client."""
    global _genai
    if _genai is None:
        import google.generativeai as genai
        genai.configure(api_key=GOOGLE_API_KEY)
        _genai = genai
    return _genai


@dataclass
class ExtractedHealthInfo:
    """Container for extracted health information."""
    conditions: List[str]
    medications: List[Dict[str, str]]  # [{"name": "Metformin", "dosage": "500mg"}]
    allergies: List[str]
    age: Optional[int]
    gender: Optional[str]
    blood_type: Optional[str]
    key_facts: List[str]
    summary: str
    report_type: str  # "blood_test", "prescription", "diagnosis", "general"


# Extraction prompt
EXTRACTION_PROMPT = """
Analyze this medical document and extract health information.

Return a JSON object with these fields:
{
    "conditions": ["list of medical conditions/diagnoses mentioned"],
    "medications": [{"name": "medication name", "dosage": "dosage if mentioned"}],
    "allergies": ["list of allergies mentioned"],
    "age": null or number,
    "gender": null or "Male"/"Female",
    "blood_type": null or "O+", "A-", etc.,
    "key_facts": ["other important health facts like family history, surgeries, etc."],
    "summary": "Brief 2-3 sentence summary of the document",
    "report_type": "blood_test" | "prescription" | "diagnosis" | "imaging" | "general"
}

Important:
- Only extract information explicitly stated in the document
- For conditions, include the specific diagnosis (e.g., "Type 2 Diabetes" not just "Diabetes")
- For medications, include dosage if available
- For blood tests, note any abnormal values as key_facts
- Be conservative - don't infer or guess information

If the document is not a medical document or is unreadable, return:
{"error": "Not a valid medical document"}
"""


def get_report_from_s3(file_key: str) -> Optional[bytes]:
    """
    Fetch a report file from S3.
    
    Returns file bytes or None if failed.
    """
    if not REPORTS_BUCKET:
        print("REPORTS_BUCKET not configured")
        return None
    
    try:
        response = s3_client.get_object(Bucket=REPORTS_BUCKET, Key=file_key)
        return response["Body"].read()
    except Exception as e:
        print(f"Error fetching report from S3: {e}")
        return None


def analyze_report(file_key: str, user_id: str) -> Dict[str, Any]:
    """
    Analyze a medical report using Gemini multimodal.
    
    Args:
        file_key: S3 key of the uploaded report
        user_id: User ID for updating their health profile
    
    Returns:
        Dict with analysis results and status
    """
    # Get file from S3
    file_bytes = get_report_from_s3(file_key)
    if not file_bytes:
        return {
            "success": False,
            "error": "Failed to fetch report from storage"
        }
    
    # Determine file type from key
    file_ext = file_key.split(".")[-1].lower()
    
    try:
        # Use Gemini to analyze
        model = get_genai().GenerativeModel("gemini-2.0-flash")
        
        if file_ext in ["jpg", "jpeg", "png", "webp"]:
            # Image analysis
            image_data = base64.b64encode(file_bytes).decode("utf-8")
            mime_type = f"image/{'jpeg' if file_ext in ['jpg', 'jpeg'] else file_ext}"
            
            response = model.generate_content([
                EXTRACTION_PROMPT,
                {"mime_type": mime_type, "data": image_data}
            ])
        elif file_ext == "pdf":
            # PDF analysis - Gemini can handle PDFs directly
            pdf_data = base64.b64encode(file_bytes).decode("utf-8")
            
            response = model.generate_content([
                EXTRACTION_PROMPT,
                {"mime_type": "application/pdf", "data": pdf_data}
            ])
        else:
            return {
                "success": False,
                "error": f"Unsupported file type: {file_ext}"
            }
        
        # Parse response
        response_text = response.text
        
        # Extract JSON from response (handle markdown code blocks)
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        
        extracted = json.loads(response_text)
        
        # Check for error response
        if "error" in extracted:
            return {
                "success": False,
                "error": extracted["error"]
            }
        
        # Parse into ExtractedHealthInfo
        health_info = ExtractedHealthInfo(
            conditions=extracted.get("conditions", []),
            medications=extracted.get("medications", []),
            allergies=extracted.get("allergies", []),
            age=extracted.get("age"),
            gender=extracted.get("gender"),
            blood_type=extracted.get("blood_type"),
            key_facts=extracted.get("key_facts", []),
            summary=extracted.get("summary", ""),
            report_type=extracted.get("report_type", "general")
        )
        
        # Return for user confirmation (don't auto-update profile)
        return {
            "success": True,
            "extracted": {
                "conditions": health_info.conditions,
                "medications": health_info.medications,
                "allergies": health_info.allergies,
                "age": health_info.age,
                "gender": health_info.gender,
                "blood_type": health_info.blood_type,
                "key_facts": health_info.key_facts,
                "summary": health_info.summary,
                "report_type": health_info.report_type
            },
            "file_key": file_key,
            "user_id": user_id
        }
        
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Response was: {response_text[:500]}")
        return {
            "success": False,
            "error": "Failed to parse analysis results"
        }
    except Exception as e:
        print(f"Error analyzing report: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def confirm_and_save_analysis(
    user_id: str,
    extracted: Dict[str, Any],
    file_key: str
) -> Dict[str, Any]:
    """
    Save confirmed analysis results to user's health profile.
    
    Called after user confirms the extracted information.
    """
    saved_items = {
        "conditions": [],
        "medications": [],
        "allergies": [],
        "key_facts": [],
        "basic_info": False
    }
    
    try:
        # Add conditions
        for condition in extracted.get("conditions", []):
            if add_condition(user_id, condition, source="report"):
                saved_items["conditions"].append(condition)
        
        # Add medications
        for med in extracted.get("medications", []):
            if isinstance(med, dict):
                name = med.get("name", "")
                dosage = med.get("dosage", "")
            else:
                name = med
                dosage = ""
            if name and add_medication(user_id, name, dosage, source="report"):
                saved_items["medications"].append(name)
        
        # Add allergies
        for allergy in extracted.get("allergies", []):
            if add_allergy(user_id, allergy, source="report"):
                saved_items["allergies"].append(allergy)
        
        # Add key facts
        for fact in extracted.get("key_facts", []):
            if add_key_fact(user_id, fact, source="report"):
                saved_items["key_facts"].append(fact)
        
        # Update basic info
        age = extracted.get("age")
        gender = extracted.get("gender")
        blood_type = extracted.get("blood_type")
        if any([age, gender, blood_type]):
            update_basic_info(user_id, age=age, gender=gender, blood_type=blood_type)
            saved_items["basic_info"] = True
        
        # Save report summary
        summary = extracted.get("summary", "Medical report analyzed")
        report_type = extracted.get("report_type", "general")
        add_report_summary(user_id, summary, report_type, file_key)
        
        return {
            "success": True,
            "saved": saved_items,
            "message": "Health profile updated successfully"
        }
        
    except Exception as e:
        print(f"Error saving analysis: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def extract_facts_from_chat(
    user_id: str,
    user_message: str,
    assistant_response: str
) -> List[str]:
    """
    Extract health facts from a chat conversation.
    
    This runs after each chat to capture any health information
    the user mentions (e.g., "I have diabetes").
    """
    if not user_message or len(user_message) < 10:
        return []
    
    extraction_prompt = f"""
Analyze this conversation and extract any NEW health facts about the user.

User said: "{user_message}"

Look for:
- Medical conditions they mention having (e.g., "I have diabetes", "I was diagnosed with...")
- Medications they take (e.g., "I'm on metformin", "I take...")
- Allergies (e.g., "I'm allergic to...")
- Age, gender, or other relevant health info
- Medical history (surgeries, family history, etc.)

Return a JSON object:
{{
    "conditions": ["only conditions explicitly stated"],
    "medications": [{{"name": "med", "dosage": ""}}],
    "allergies": ["only allergies explicitly stated"],
    "key_facts": ["other health facts"],
    "age": null or number,
    "gender": null or string
}}

IMPORTANT: Only include facts EXPLICITLY stated by the user.
If no health facts are mentioned, return empty lists.
Do NOT infer or guess - only extract what the user directly said.
"""
    
    try:
        model = get_genai().GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(extraction_prompt)
        
        response_text = response.text
        
        # Extract JSON
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        
        extracted = json.loads(response_text)
        
        saved = []
        
        # Save extracted info (silently, in background)
        for condition in extracted.get("conditions", []):
            if condition and add_condition(user_id, condition, source="chat"):
                saved.append(f"Noted: {condition}")
        
        for med in extracted.get("medications", []):
            name = med.get("name", "") if isinstance(med, dict) else med
            dosage = med.get("dosage", "") if isinstance(med, dict) else ""
            if name and add_medication(user_id, name, dosage, source="chat"):
                saved.append(f"Noted medication: {name}")
        
        for allergy in extracted.get("allergies", []):
            if allergy and add_allergy(user_id, allergy, source="chat"):
                saved.append(f"Noted allergy: {allergy}")
        
        for fact in extracted.get("key_facts", []):
            if fact and add_key_fact(user_id, fact, source="chat"):
                saved.append(f"Noted: {fact}")
        
        # Update basic info
        age = extracted.get("age")
        gender = extracted.get("gender")
        if age or gender:
            update_basic_info(user_id, age=age, gender=gender)
        
        return saved
        
    except Exception as e:
        print(f"Error extracting facts from chat: {e}")
        return []
