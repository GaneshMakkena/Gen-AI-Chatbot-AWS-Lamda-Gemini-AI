"""
Centralized AWS Client Factory — Connection Pooling & Keep-Alive.

All modules should import AWS clients from here instead of creating their own.
Singleton pattern ensures connection reuse across Lambda invocations.
"""

import os
import boto3
from botocore.config import Config

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Shared botocore config with connection pooling and keep-alive
_boto_config = Config(
    region_name=AWS_REGION,
    retries={"max_attempts": 3, "mode": "adaptive"},
    tcp_keepalive=True,
    max_pool_connections=25,  # Default is 10; increase for parallel image uploads
)

# Singleton clients — initialized lazily, reused across invocations
_dynamodb_resource = None
_s3_client = None


def get_dynamodb_resource():
    """Get or create a shared DynamoDB resource with connection pooling."""
    global _dynamodb_resource
    if _dynamodb_resource is None:
        _dynamodb_resource = boto3.resource("dynamodb", config=_boto_config)
    return _dynamodb_resource


def get_dynamodb_table(table_name: str):
    """Get a DynamoDB Table object from the shared resource."""
    return get_dynamodb_resource().Table(table_name)


def get_s3_client():
    """Get or create a shared S3 client with connection pooling."""
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client("s3", config=_boto_config)
    return _s3_client
