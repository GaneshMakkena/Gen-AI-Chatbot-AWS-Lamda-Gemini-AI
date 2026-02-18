"""
Lambda Handler - Wraps FastAPI for AWS Lambda deployment using Mangum.

Cold Start Optimization:
- Heavy imports happen at module level (during init phase)
- AWS connections are pre-warmed during init
"""
import time
_init_start = time.time()

# Pre-import heavy modules during Lambda init phase
from mangum import Mangum  # noqa: E402
from api_server import app  # noqa: E402

# Pre-warm AWS connections during init (not on each request)
from aws_clients import get_dynamodb_resource, get_s3_client  # noqa: E402
get_dynamodb_resource()
get_s3_client()

# Pre-import the Gemini client to initialize the API connection
import gemini_client  # noqa: E402, F401

_init_ms = int((time.time() - _init_start) * 1000)
print(f"Lambda init completed in {_init_ms}ms")

# Mangum adapter for AWS Lambda + API Gateway
# api_gateway_base_path strips the stage name (e.g., /production) from the path
handler = Mangum(app, lifespan="off", api_gateway_base_path="/production")
