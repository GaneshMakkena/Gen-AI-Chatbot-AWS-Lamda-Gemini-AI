"""
Profile route module for MediBot.
Handles /profile, /analyze-report, /confirm-analysis endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends
from aws_lambda_powertools import Logger

from models.request_models import ProfileUpdateRequest, AnalyzeReportRequest, ConfirmAnalysisRequest
from dependencies import require_auth
from health_profile import (
    get_or_create_profile,
    add_condition,
    add_medication,
    add_allergy,
    update_basic_info,
    delete_health_profile,
    remove_condition,
)
from report_analyzer import analyze_report, confirm_and_save_analysis

logger = Logger(service="medibot")
router = APIRouter()


@router.get("/profile")
async def get_profile(user: dict = Depends(require_auth)):
    """Get user's health profile."""
    profile = get_or_create_profile(user["user_id"])

    return {
        "user_id": profile.get("user_id", ""),
        "conditions": profile.get("conditions", []),
        "medications": profile.get("medications", []),
        "allergies": profile.get("allergies", []),
        "blood_type": profile.get("blood_type", ""),
        "age": profile.get("age"),
        "gender": profile.get("gender", ""),
        "key_facts": profile.get("key_facts", []),
        "report_summaries": profile.get("report_summaries", []),
        "last_updated": profile.get("last_updated", ""),
    }


@router.put("/profile")
async def update_profile(
    request: ProfileUpdateRequest,
    user: dict = Depends(require_auth),
):
    """Update user's health profile manually."""
    user_id = user["user_id"]

    if request.conditions:
        for condition in request.conditions:
            add_condition(user_id, condition, source="manual")

    if request.medications:
        for med in request.medications:
            add_medication(user_id, med.get("name", ""), med.get("dosage", ""), source="manual")

    if request.allergies:
        for allergy in request.allergies:
            add_allergy(user_id, allergy, source="manual")

    if any([request.age, request.gender, request.blood_type]):
        update_basic_info(
            user_id, age=request.age, gender=request.gender, blood_type=request.blood_type
        )

    return {"message": "Profile updated", "user_id": user_id}


@router.delete("/profile")
async def delete_profile(user: dict = Depends(require_auth)):
    """Delete user's entire health profile."""
    success = delete_health_profile(user["user_id"])
    if success:
        return {"message": "Profile deleted"}
    raise HTTPException(status_code=500, detail="Failed to delete profile")


@router.delete("/profile/condition/{condition_name}")
async def remove_profile_condition(
    condition_name: str,
    user: dict = Depends(require_auth),
):
    """Remove a specific condition from user's profile."""
    success = remove_condition(user["user_id"], condition_name)
    if success:
        return {"message": f"Condition '{condition_name}' removed"}
    raise HTTPException(status_code=404, detail="Condition not found")


@router.post("/analyze-report")
async def analyze_uploaded_report(
    request: AnalyzeReportRequest,
    user: dict = Depends(require_auth),
):
    """Analyze an uploaded medical report using Gemini multimodal."""
    result = analyze_report(request.file_key, user["user_id"])

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Analysis failed"))

    return result


@router.post("/confirm-analysis")
async def confirm_report_analysis(
    request: ConfirmAnalysisRequest,
    user: dict = Depends(require_auth),
):
    """Confirm and save extracted health information from a report."""
    result = confirm_and_save_analysis(user["user_id"], request.extracted, request.file_key)

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Save failed"))

    return result
