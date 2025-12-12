"""
Lambda Handler - Wraps FastAPI for AWS Lambda deployment using Mangum.
"""
from mangum import Mangum
from api_server import app

# Mangum adapter for AWS Lambda + API Gateway
# api_gateway_base_path strips the stage name (e.g., /production) from the path
handler = Mangum(app, lifespan="off", api_gateway_base_path="/production")
