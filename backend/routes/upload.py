"""
Upload route module for MediBot.
Handles /upload-report and /upload/presigned-url endpoints.
"""

import os
import uuid
import time

import boto3
from fastapi import APIRouter, HTTPException, Depends
from aws_lambda_powertools import Logger

from models.request_models import UploadUrlRequest, PresignedUrlRequest
from models.response_models import UploadUrlResponse
from dependencies import require_auth

logger = Logger(service="medibot")
router = APIRouter()

REPORTS_BUCKET = os.getenv("REPORTS_BUCKET", "")


@router.post("/upload-report", response_model=UploadUrlResponse)
async def get_upload_url(
    request: UploadUrlRequest,
    user: dict = Depends(require_auth),
):
    """Get a presigned URL to upload a medical report."""
    if not REPORTS_BUCKET:
        raise HTTPException(status_code=500, detail="Reports bucket not configured")

    allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/jpg"]
    if request.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content type. Allowed: {allowed_types}",
        )

    file_ext = request.filename.split(".")[-1] if "." in request.filename else "pdf"
    file_key = f"reports/{user['user_id']}/{int(time.time())}_{uuid.uuid4().hex[:8]}.{file_ext}"

    s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION", "us-east-1"))
    try:
        upload_url = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": REPORTS_BUCKET,
                "Key": file_key,
                "ContentType": request.content_type,
            },
            ExpiresIn=3600,
        )

        return UploadUrlResponse(
            upload_url=upload_url,
            file_key=file_key,
            expires_in=3600,
        )
    except Exception as e:
        logger.error("Error generating presigned URL", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to generate upload URL")


@router.post("/upload/presigned-url")
async def generate_presigned_url(
    request: PresignedUrlRequest,
    user: dict = Depends(require_auth),
):
    """Generate a presigned URL for uploading files to S3."""
    user_id = user["user_id"]
    file_ext = request.filename.split(".")[-1].lower()

    key = f"uploads/{user_id}/{int(time.time())}_{uuid.uuid4().hex[:8]}.{file_ext}"

    try:
        from report_analyzer import REPORTS_BUCKET as ANALYZER_BUCKET, s3_client

        bucket = ANALYZER_BUCKET or REPORTS_BUCKET
        if not bucket:
            raise HTTPException(status_code=500, detail="Storage not configured")

        presigned_url = s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": bucket,
                "Key": key,
                "ContentType": request.content_type,
            },
            ExpiresIn=300,
        )

        return {"upload_url": presigned_url, "s3_key": key}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to generate presigned URL", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to generate upload URL")
