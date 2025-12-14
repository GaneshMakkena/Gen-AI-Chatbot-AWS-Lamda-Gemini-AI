"""
Health Profile Module for MediBot
Manages user health profiles for personalized RAG (Retrieval Augmented Generation).

Stores:
- Medical conditions (diabetes, hypertension, etc.)
- Medications
- Allergies
- Key health facts extracted from conversations and reports
"""

import os
import boto3
from typing import Any, Dict, List, Optional
from datetime import datetime

# Environment variables
HEALTH_PROFILE_TABLE = os.getenv("HEALTH_PROFILE_TABLE", "medibot-health-profiles-production")
AWS_REGION = os.getenv("BEDROCK_REGION", "us-east-1")

# DynamoDB client
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)


def get_table():
    """Get the DynamoDB table resource."""
    return dynamodb.Table(HEALTH_PROFILE_TABLE)


def get_health_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a user's complete health profile.
    
    Returns None if no profile exists.
    """
    try:
        table = get_table()
        response = table.get_item(Key={"user_id": user_id})
        return response.get("Item")
    except Exception as e:
        print(f"Error getting health profile: {e}")
        return None


def create_health_profile(user_id: str) -> Dict[str, Any]:
    """
    Create a new empty health profile for a user.
    """
    profile = {
        "user_id": user_id,
        "conditions": [],
        "medications": [],
        "allergies": [],
        "blood_type": "",
        "age": None,
        "gender": "",
        "key_facts": [],
        "report_summaries": [],
        "created_at": datetime.utcnow().isoformat(),
        "last_updated": datetime.utcnow().isoformat()
    }
    
    try:
        table = get_table()
        table.put_item(Item=profile)
        print(f"Created health profile for user {user_id[:8]}...")
        return profile
    except Exception as e:
        print(f"Error creating health profile: {e}")
        return profile


def get_or_create_profile(user_id: str) -> Dict[str, Any]:
    """
    Get existing profile or create a new one.
    """
    profile = get_health_profile(user_id)
    if profile is None:
        profile = create_health_profile(user_id)
    return profile


def add_condition(user_id: str, condition: str, source: str = "manual") -> bool:
    """
    Add a medical condition to the user's profile.
    
    Args:
        user_id: User identifier
        condition: Condition name (e.g., "Type 2 Diabetes")
        source: Where this info came from ("report", "chat", "manual")
    """
    profile = get_or_create_profile(user_id)
    
    # Check if condition already exists (case-insensitive)
    existing = [c.get("name", "").lower() if isinstance(c, dict) else c.lower() 
                for c in profile.get("conditions", [])]
    if condition.lower() in existing:
        print(f"Condition '{condition}' already exists for user")
        return True
    
    # Add new condition with metadata
    new_condition = {
        "name": condition,
        "added_at": datetime.utcnow().isoformat(),
        "source": source
    }
    
    try:
        table = get_table()
        table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET conditions = list_append(if_not_exists(conditions, :empty), :new), last_updated = :now",
            ExpressionAttributeValues={
                ":new": [new_condition],
                ":empty": [],
                ":now": datetime.utcnow().isoformat()
            }
        )
        print(f"Added condition '{condition}' for user {user_id[:8]}...")
        return True
    except Exception as e:
        print(f"Error adding condition: {e}")
        return False


def add_medication(user_id: str, medication: str, dosage: str = "", source: str = "manual") -> bool:
    """
    Add a medication to the user's profile.
    """
    profile = get_or_create_profile(user_id)
    
    # Check if medication already exists
    existing = [m.get("name", "").lower() if isinstance(m, dict) else m.lower() 
                for m in profile.get("medications", [])]
    if medication.lower() in existing:
        return True
    
    new_med = {
        "name": medication,
        "dosage": dosage,
        "added_at": datetime.utcnow().isoformat(),
        "source": source
    }
    
    try:
        table = get_table()
        table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET medications = list_append(if_not_exists(medications, :empty), :new), last_updated = :now",
            ExpressionAttributeValues={
                ":new": [new_med],
                ":empty": [],
                ":now": datetime.utcnow().isoformat()
            }
        )
        print(f"Added medication '{medication}' for user {user_id[:8]}...")
        return True
    except Exception as e:
        print(f"Error adding medication: {e}")
        return False


def add_allergy(user_id: str, allergy: str, source: str = "manual") -> bool:
    """
    Add an allergy to the user's profile.
    """
    profile = get_or_create_profile(user_id)
    
    existing = [a.get("name", "").lower() if isinstance(a, dict) else a.lower() 
                for a in profile.get("allergies", [])]
    if allergy.lower() in existing:
        return True
    
    new_allergy = {
        "name": allergy,
        "added_at": datetime.utcnow().isoformat(),
        "source": source
    }
    
    try:
        table = get_table()
        table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET allergies = list_append(if_not_exists(allergies, :empty), :new), last_updated = :now",
            ExpressionAttributeValues={
                ":new": [new_allergy],
                ":empty": [],
                ":now": datetime.utcnow().isoformat()
            }
        )
        return True
    except Exception as e:
        print(f"Error adding allergy: {e}")
        return False


def add_key_fact(user_id: str, fact: str, source: str = "chat") -> bool:
    """
    Add a key health fact to the user's profile.
    
    Examples:
    - "Family history of heart disease"
    - "Had knee surgery in 2020"
    - "Vegetarian diet"
    """
    profile = get_or_create_profile(user_id)
    
    # Check for similar existing facts (exact match)
    existing = [f.get("text", "").lower() if isinstance(f, dict) else f.lower() 
                for f in profile.get("key_facts", [])]
    if fact.lower() in existing:
        return True
    
    new_fact = {
        "text": fact,
        "added_at": datetime.utcnow().isoformat(),
        "source": source
    }
    
    try:
        table = get_table()
        table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET key_facts = list_append(if_not_exists(key_facts, :empty), :new), last_updated = :now",
            ExpressionAttributeValues={
                ":new": [new_fact],
                ":empty": [],
                ":now": datetime.utcnow().isoformat()
            }
        )
        return True
    except Exception as e:
        print(f"Error adding key fact: {e}")
        return False


def add_report_summary(
    user_id: str,
    summary: str,
    report_type: str = "general",
    source_file: str = ""
) -> bool:
    """
    Add a summarized report to the user's profile.
    """
    new_summary = {
        "summary": summary,
        "report_type": report_type,
        "source_file": source_file,
        "added_at": datetime.utcnow().isoformat()
    }
    
    try:
        table = get_table()
        
        # First ensure profile exists
        get_or_create_profile(user_id)
        
        table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET report_summaries = list_append(if_not_exists(report_summaries, :empty), :new), last_updated = :now",
            ExpressionAttributeValues={
                ":new": [new_summary],
                ":empty": [],
                ":now": datetime.utcnow().isoformat()
            }
        )
        return True
    except Exception as e:
        print(f"Error adding report summary: {e}")
        return False


def update_basic_info(
    user_id: str,
    age: Optional[int] = None,
    gender: Optional[str] = None,
    blood_type: Optional[str] = None
) -> bool:
    """
    Update basic health information.
    """
    try:
        table = get_table()
        
        # Build update expression dynamically
        update_parts = ["last_updated = :now"]
        values = {":now": datetime.utcnow().isoformat()}
        
        if age is not None:
            update_parts.append("age = :age")
            values[":age"] = age
        
        if gender is not None:
            update_parts.append("gender = :gender")
            values[":gender"] = gender
        
        if blood_type is not None:
            update_parts.append("blood_type = :blood_type")
            values[":blood_type"] = blood_type
        
        # Ensure profile exists first
        get_or_create_profile(user_id)
        
        table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET " + ", ".join(update_parts),
            ExpressionAttributeValues=values
        )
        return True
    except Exception as e:
        print(f"Error updating basic info: {e}")
        return False


def get_context_summary(user_id: str) -> str:
    """
    Generate a context summary for LLM prompting.
    
    This is the key function for RAG - it produces a text summary
    of the user's health profile that gets injected into the LLM prompt.
    
    Returns:
        A formatted string with the user's health context, or empty string if no profile.
    """
    profile = get_health_profile(user_id)
    
    if not profile:
        return ""
    
    parts = []
    
    # Add conditions
    conditions = profile.get("conditions", [])
    if conditions:
        condition_names = [c.get("name", c) if isinstance(c, dict) else c for c in conditions]
        parts.append(f"Medical conditions: {', '.join(condition_names)}")
    
    # Add medications
    medications = profile.get("medications", [])
    if medications:
        med_names = []
        for m in medications:
            if isinstance(m, dict):
                name = m.get("name", "")
                dosage = m.get("dosage", "")
                med_names.append(f"{name} {dosage}".strip())
            else:
                med_names.append(m)
        parts.append(f"Current medications: {', '.join(med_names)}")
    
    # Add allergies
    allergies = profile.get("allergies", [])
    if allergies:
        allergy_names = [a.get("name", a) if isinstance(a, dict) else a for a in allergies]
        parts.append(f"Known allergies: {', '.join(allergy_names)}")
    
    # Add basic info
    age = profile.get("age")
    gender = profile.get("gender")
    if age or gender:
        info = []
        if age:
            info.append(f"Age: {age}")
        if gender:
            info.append(f"Gender: {gender}")
        parts.append(", ".join(info))
    
    # Add key facts
    key_facts = profile.get("key_facts", [])
    if key_facts:
        fact_texts = [f.get("text", f) if isinstance(f, dict) else f for f in key_facts]
        parts.append(f"Other relevant information: {'; '.join(fact_texts)}")
    
    if not parts:
        return ""
    
    # Format as a clear context block
    context = """
=== USER HEALTH CONTEXT ===
{}
===========================
""".format("\n".join(f"• {part}" for part in parts))
    
    return context


def delete_health_profile(user_id: str) -> bool:
    """
    Delete a user's entire health profile.
    """
    try:
        table = get_table()
        table.delete_item(Key={"user_id": user_id})
        print(f"Deleted health profile for user {user_id[:8]}...")
        return True
    except Exception as e:
        print(f"Error deleting health profile: {e}")
        return False


def remove_condition(user_id: str, condition_name: str) -> bool:
    """
    Remove a specific condition from the user's profile.
    """
    profile = get_health_profile(user_id)
    if not profile:
        return False
    
    conditions = profile.get("conditions", [])
    updated = [c for c in conditions 
               if (c.get("name", c) if isinstance(c, dict) else c).lower() != condition_name.lower()]
    
    if len(updated) == len(conditions):
        return False  # Condition not found
    
    try:
        table = get_table()
        table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET conditions = :conditions, last_updated = :now",
            ExpressionAttributeValues={
                ":conditions": updated,
                ":now": datetime.utcnow().isoformat()
            }
        )
        return True
    except Exception as e:
        print(f"Error removing condition: {e}")
        return False
