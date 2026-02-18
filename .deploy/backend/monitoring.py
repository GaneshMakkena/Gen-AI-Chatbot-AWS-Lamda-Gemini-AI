"""
CloudWatch Metrics Module for MediBot
Custom metrics for business KPIs, API performance, and LLM health monitoring.

Uses aws-lambda-powertools for structured metric publishing.
"""

import os
import time
from typing import Optional, Dict
from functools import wraps
from contextlib import contextmanager

# Try to import powertools, fallback to manual metrics if not available
try:
    from aws_lambda_powertools import Metrics
    from aws_lambda_powertools.metrics import MetricUnit
    POWERTOOLS_AVAILABLE = True
except ImportError:
    POWERTOOLS_AVAILABLE = False
    MetricUnit = None

import boto3

# Environment config
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
SERVICE_NAME = os.getenv("POWERTOOLS_SERVICE_NAME", "medibot")
METRICS_NAMESPACE = os.getenv("METRICS_NAMESPACE", "MediBot")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Initialize metrics (powertools or manual)
if POWERTOOLS_AVAILABLE:
    metrics = Metrics(namespace=METRICS_NAMESPACE, service=SERVICE_NAME)
else:
    metrics = None

# Manual CloudWatch client for fallback
_cloudwatch = None


def get_cloudwatch():
    """Get or create CloudWatch client."""
    global _cloudwatch
    if _cloudwatch is None:
        _cloudwatch = boto3.client('cloudwatch', region_name=AWS_REGION)
    return _cloudwatch


# ============================================
# Metric Names (Constants)
# ============================================

class MetricName:
    # API Metrics
    API_REQUESTS = "ApiRequests"
    API_LATENCY = "ApiLatencyMs"
    API_ERRORS = "ApiErrors"
    API_4XX_ERRORS = "Api4xxErrors"
    API_5XX_ERRORS = "Api5xxErrors"

    # Chat Metrics
    CHAT_REQUESTS = "ChatRequests"
    CHAT_LATENCY = "ChatLatencyMs"
    CHAT_WITH_IMAGES = "ChatWithImages"
    CHAT_GUEST = "GuestChatRequests"
    CHAT_AUTHENTICATED = "AuthenticatedChatRequests"

    # LLM Metrics
    LLM_REQUESTS = "LlmRequests"
    LLM_LATENCY = "LlmLatencyMs"
    LLM_ERRORS = "LlmErrors"
    LLM_TOKEN_INPUT = "LlmInputTokens"
    LLM_TOKEN_OUTPUT = "LlmOutputTokens"

    # Image Generation Metrics
    IMAGE_REQUESTS = "ImageGenRequests"
    IMAGE_LATENCY = "ImageGenLatencyMs"
    IMAGE_ERRORS = "ImageGenErrors"
    IMAGE_FALLBACKS = "ImageFallbacks"

    # User Metrics
    ACTIVE_USERS = "ActiveUsers"
    NEW_SIGNUPS = "NewSignups"
    GUEST_TRIAL_LIMIT = "GuestTrialLimitHit"

    # Health Profile Metrics
    PROFILE_READS = "ProfileReads"
    PROFILE_UPDATES = "ProfileUpdates"
    REPORT_ANALYSES = "ReportAnalyses"

    # Security Metrics
    AUTH_FAILURES = "AuthFailures"
    RATE_LIMIT_HITS = "RateLimitHits"
    SUSPICIOUS_REQUESTS = "SuspiciousRequests"


# ============================================
# Metric Publishing Functions
# ============================================

def publish_metric(
    name: str,
    value: float = 1,
    unit: str = "Count",
    dimensions: Optional[Dict[str, str]] = None
):
    """
    Publish a single metric to CloudWatch.

    Uses powertools if available, otherwise manual boto3 call.
    """
    # Add standard dimensions
    all_dimensions = {
        "Environment": ENVIRONMENT,
        "Service": SERVICE_NAME
    }
    if dimensions:
        all_dimensions.update(dimensions)

    if POWERTOOLS_AVAILABLE and metrics:
        # Use powertools
        pt_unit = getattr(MetricUnit, unit, MetricUnit.Count)
        for dim_name, dim_value in all_dimensions.items():
            metrics.add_dimension(name=dim_name, value=dim_value)
        metrics.add_metric(name=name, unit=pt_unit, value=value)
    else:
        # Manual CloudWatch put
        try:
            cw = get_cloudwatch()
            cw.put_metric_data(
                Namespace=METRICS_NAMESPACE,
                MetricData=[{
                    "MetricName": name,
                    "Value": value,
                    "Unit": unit,
                    "Dimensions": [
                        {"Name": k, "Value": v}
                        for k, v in all_dimensions.items()
                    ]
                }]
            )
        except Exception as e:
            print(f"Failed to publish metric {name}: {e}")


def publish_latency(name: str, duration_ms: float, dimensions: Optional[Dict[str, str]] = None):
    """Publish a latency metric in milliseconds."""
    publish_metric(name, duration_ms, "Milliseconds", dimensions)


def publish_count(name: str, count: int = 1, dimensions: Optional[Dict[str, str]] = None):
    """Publish a count metric."""
    publish_metric(name, float(count), "Count", dimensions)


def publish_error(name: str, error_type: str = "unknown", dimensions: Optional[Dict[str, str]] = None):
    """Publish an error metric with error type dimension."""
    dims = dimensions or {}
    dims["ErrorType"] = error_type
    publish_count(name, 1, dims)


# ============================================
# Context Managers & Decorators
# ============================================

@contextmanager
def measure_latency(metric_name: str, dimensions: Optional[Dict[str, str]] = None):
    """
    Context manager to measure and publish latency.

    Usage:
        with measure_latency(MetricName.LLM_LATENCY):
            response = call_llm()
    """
    start = time.time()
    try:
        yield
    finally:
        duration_ms = (time.time() - start) * 1000
        publish_latency(metric_name, duration_ms, dimensions)


def timed_metric(metric_name: str, error_metric: Optional[str] = None):
    """
    Decorator to measure function latency and publish metrics.

    Usage:
        @timed_metric(MetricName.LLM_LATENCY, MetricName.LLM_ERRORS)
        def call_llm():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                if error_metric:
                    publish_error(error_metric, type(e).__name__)
                raise
            finally:
                duration_ms = (time.time() - start) * 1000
                publish_latency(metric_name, duration_ms)
        return wrapper
    return decorator


# ============================================
# Specific Metric Helpers
# ============================================

def record_chat_request(
    is_authenticated: bool = False,
    has_images: bool = False,
    language: str = "English",
    latency_ms: Optional[float] = None
):
    """Record a chat request with all relevant dimensions."""
    dims = {
        "Language": language,
        "HasImages": str(has_images).lower()
    }

    publish_count(MetricName.CHAT_REQUESTS, 1, dims)

    if is_authenticated:
        publish_count(MetricName.CHAT_AUTHENTICATED)
    else:
        publish_count(MetricName.CHAT_GUEST)

    if has_images:
        publish_count(MetricName.CHAT_WITH_IMAGES)

    if latency_ms:
        publish_latency(MetricName.CHAT_LATENCY, latency_ms, dims)


def record_llm_call(
    model: str,
    latency_ms: float,
    input_tokens: int = 0,
    output_tokens: int = 0,
    success: bool = True
):
    """Record an LLM API call."""
    dims = {"Model": model}

    publish_count(MetricName.LLM_REQUESTS, 1, dims)
    publish_latency(MetricName.LLM_LATENCY, latency_ms, dims)

    if input_tokens > 0:
        publish_metric(MetricName.LLM_TOKEN_INPUT, input_tokens, "Count", dims)
    if output_tokens > 0:
        publish_metric(MetricName.LLM_TOKEN_OUTPUT, output_tokens, "Count", dims)

    if not success:
        publish_count(MetricName.LLM_ERRORS, 1, dims)


def record_image_generation(
    latency_ms: float,
    step_count: int = 1,
    fallback_count: int = 0,
    success: bool = True
):
    """Record image generation metrics."""
    publish_count(MetricName.IMAGE_REQUESTS, step_count)
    publish_latency(MetricName.IMAGE_LATENCY, latency_ms)

    if fallback_count > 0:
        publish_count(MetricName.IMAGE_FALLBACKS, fallback_count)

    if not success:
        publish_count(MetricName.IMAGE_ERRORS)


def record_security_event(event_type: str, ip_address: Optional[str] = None):
    """Record a security-related metric."""
    dims = {"EventType": event_type}

    if event_type == "auth_failure":
        publish_count(MetricName.AUTH_FAILURES, 1, dims)
    elif event_type == "rate_limit":
        publish_count(MetricName.RATE_LIMIT_HITS, 1, dims)
    elif event_type == "suspicious":
        publish_count(MetricName.SUSPICIOUS_REQUESTS, 1, dims)
    elif event_type == "guest_limit":
        publish_count(MetricName.GUEST_TRIAL_LIMIT, 1, dims)


def record_user_activity(activity_type: str, user_id: Optional[str] = None):
    """Record user activity metrics."""
    if activity_type == "active":
        publish_count(MetricName.ACTIVE_USERS)
    elif activity_type == "signup":
        publish_count(MetricName.NEW_SIGNUPS)
    elif activity_type == "profile_read":
        publish_count(MetricName.PROFILE_READS)
    elif activity_type == "profile_update":
        publish_count(MetricName.PROFILE_UPDATES)
    elif activity_type == "report_analysis":
        publish_count(MetricName.REPORT_ANALYSES)


# ============================================
# Flush Metrics (for Lambda)
# ============================================

def flush_metrics():
    """
    Flush all buffered metrics.
    Call at end of Lambda handler.
    """
    if POWERTOOLS_AVAILABLE and metrics:
        try:
            metrics.flush_metrics()
        except Exception as e:
            print(f"Failed to flush metrics: {e}")
