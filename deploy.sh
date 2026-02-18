#!/bin/bash
# deploy.sh - Deploy MediBot to AWS
# Usage: ./deploy.sh [staging|production]
#
# Prerequisites:
#   - AWS CLI installed and configured
#   - SAM CLI installed
#   - GOOGLE_API_KEY environment variable set
#   - Node.js and npm installed (for frontend build)

set -euo pipefail

ENVIRONMENT=${1:-production}
STACK_NAME="medibot-$ENVIRONMENT"
REGION="us-east-1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Deploying MediBot to AWS ($ENVIRONMENT)..."
echo ""

# ============================================
# Pre-flight Checks
# ============================================
command -v aws >/dev/null 2>&1 || { echo "❌ AWS CLI not installed. Run: brew install awscli"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js not installed. Run: brew install node"; exit 1; }
command -v pip3 >/dev/null 2>&1 || { echo "❌ pip3 not installed. Required for fallback packaging"; exit 1; }
command -v python3.11 >/dev/null 2>&1 || { echo "❌ python3.11 not installed. Required for Lambda-compatible fallback packaging"; exit 1; }

STACK_EXISTS="false"
if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" >/dev/null 2>&1; then
    STACK_EXISTS="true"
fi

if [ -z "${GOOGLE_API_KEY:-}" ] && [ "$STACK_EXISTS" != "true" ]; then
    echo "❌ GOOGLE_API_KEY environment variable not set"
    echo "   New stack creation requires this parameter."
    echo "   Run: export GOOGLE_API_KEY='your-google-api-key'"
    exit 1
fi

# Optional: fast model override (defaults to gemini-2.0-flash in template)
GEMINI_FAST_MODEL=${GEMINI_FAST_MODEL:-"gemini-2.0-flash"}
GEMINI_LLM_MODEL=${GEMINI_LLM_MODEL:-"gemini-2.5-pro"}
FRONTEND_DOMAIN=${FRONTEND_DOMAIN:-""}
ALARM_EMAIL=${ALARM_EMAIL:-""}

echo "   Environment:      $ENVIRONMENT"
echo "   Stack:            $STACK_NAME"
echo "   Region:           $REGION"
echo "   LLM Model:        $GEMINI_LLM_MODEL"
echo "   Fast Model:       $GEMINI_FAST_MODEL"
if [ -n "$FRONTEND_DOMAIN" ]; then
    echo "   Frontend Domain:  $FRONTEND_DOMAIN"
fi
if [ -n "$ALARM_EMAIL" ]; then
    echo "   Alarm Email:      $ALARM_EMAIL"
fi
if [ -z "${GOOGLE_API_KEY:-}" ]; then
    echo "   Google API Key:   using previous stack value"
else
    echo "   Google API Key:   provided via env"
fi
echo ""

USE_SAM="true"
if ! command -v sam >/dev/null 2>&1; then
    USE_SAM="false"
    echo "⚠️ SAM CLI not found; using AWS CLI fallback packaging."
fi

# ============================================
# Step 1: Build/package backend artifacts
# ============================================
echo "📦 Step 1: Building Lambda package..."
cd "$SCRIPT_DIR/infrastructure"

PACKAGED_TEMPLATE="packaged.yaml"
PACKAGE_BUCKET="${STACK_NAME}-cf-artifacts"

if [ "$USE_SAM" = "true" ]; then
    # Exclude test files, venv, and caches from the build
    sam build
else
    mkdir -p "$SCRIPT_DIR/.deploy/backend"
    rm -rf "$SCRIPT_DIR/.deploy/backend"/*
    rsync -a --delete \
        --exclude "__pycache__" \
        --exclude ".pytest_cache" \
        --exclude "tests" \
        --exclude "venv" \
        --exclude ".venv" \
        "$SCRIPT_DIR/backend/" "$SCRIPT_DIR/.deploy/backend/"

    python3.11 -m pip install \
        --platform manylinux2014_x86_64 \
        --implementation cp \
        --python-version 3.11 \
        --only-binary=:all: \
        -r "$SCRIPT_DIR/backend/requirements.txt" \
        -t "$SCRIPT_DIR/.deploy/backend" >/dev/null

    if ! aws s3api head-bucket --bucket "$PACKAGE_BUCKET" --region "$REGION" >/dev/null 2>&1; then
        aws s3api create-bucket --bucket "$PACKAGE_BUCKET" --region "$REGION" >/dev/null
    fi

    awk '
      /CodeUri:[[:space:]]+\.\.\/backend\// { print "      CodeUri: ../.deploy/backend/"; next }
      { print }
    ' template.yaml > template.deploy.yaml

    aws cloudformation package \
        --template-file template.deploy.yaml \
        --s3-bucket "$PACKAGE_BUCKET" \
        --output-template-file "$PACKAGED_TEMPLATE" \
        --region "$REGION" >/dev/null
fi

# ============================================
# Step 2: Deploy backend to AWS
# ============================================
echo ""
echo "☁️ Step 2: Deploying backend to AWS Lambda..."
PARAM_OVERRIDES=(
    "GeminiLlmModel=$GEMINI_LLM_MODEL"
    "GeminiFastModel=$GEMINI_FAST_MODEL"
    "Environment=$ENVIRONMENT"
)
if [ -n "$FRONTEND_DOMAIN" ]; then
    PARAM_OVERRIDES+=("FrontendDomain=$FRONTEND_DOMAIN")
fi
if [ -n "$ALARM_EMAIL" ]; then
    PARAM_OVERRIDES+=("AlarmEmail=$ALARM_EMAIL")
fi
if [ -n "${GOOGLE_API_KEY:-}" ]; then
    PARAM_OVERRIDES+=("GoogleApiKey=$GOOGLE_API_KEY")
fi

if [ "$USE_SAM" = "true" ]; then
    sam deploy \
        --stack-name "$STACK_NAME" \
        --parameter-overrides "${PARAM_OVERRIDES[@]}" \
        --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
        --no-fail-on-empty-changeset \
        --resolve-s3 \
        --region "$REGION"
else
    aws cloudformation deploy \
        --template-file "$PACKAGED_TEMPLATE" \
        --stack-name "$STACK_NAME" \
        --parameter-overrides "${PARAM_OVERRIDES[@]}" \
        --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
        --no-fail-on-empty-changeset \
        --region "$REGION"
fi

# ============================================
# Step 3: Fetch deployment outputs
# ============================================
echo ""
echo "📝 Step 3: Getting deployment outputs..."

get_output() {
    aws cloudformation describe-stacks --stack-name $STACK_NAME \
        --query "Stacks[0].Outputs[?OutputKey==\`$1\`].OutputValue" \
        --output text --region $REGION 2>/dev/null || echo ""
}

API_URL=$(get_output "ApiUrl")
BUCKET_NAME=$(get_output "FrontendBucketName")
CLOUDFRONT_URL=$(get_output "CloudFrontUrl")
DISTRIBUTION_ID=$(get_output "CloudFrontDistributionId")
COGNITO_USER_POOL_ID=$(get_output "CognitoUserPoolId")
COGNITO_CLIENT_ID=$(get_output "CognitoClientId")
FUNCTION_URL=$(get_output "FunctionUrl")

echo "   API URL:          $API_URL"
echo "   Function URL:     ${FUNCTION_URL:-N/A}"
echo "   CloudFront:       $CLOUDFRONT_URL"

# ============================================
# Step 4: Build frontend
# ============================================
echo ""
echo "🔨 Step 4: Building frontend..."
cd "$SCRIPT_DIR/frontend"

# Write .env for Vite build
# Use Function URL if available (supports long-running tasks), otherwise API Gateway
if [ -n "$FUNCTION_URL" ] && [ "$FUNCTION_URL" != "None" ]; then
    echo "VITE_API_URL=$FUNCTION_URL" > .env
else
    echo "VITE_API_URL=$API_URL" > .env
fi

echo "VITE_COGNITO_USER_POOL_ID=$COGNITO_USER_POOL_ID" >> .env
echo "VITE_COGNITO_CLIENT_ID=$COGNITO_CLIENT_ID" >> .env
echo "   API URL → $(grep VITE_API_URL .env | cut -d= -f2 | tail -n1)"

# Install dependencies (handles new packages like any new frontend modules)
echo "   Installing npm dependencies..."
npm ci --prefer-offline --silent 2>/dev/null || npm install --silent

# Build static export (Vite + TypeScript)
echo "   Running production build..."
npm run build

# ============================================
# Step 5: Upload frontend to S3
# ============================================
echo ""
echo "📤 Step 5: Uploading frontend to S3..."
aws s3 sync dist/ "s3://$BUCKET_NAME" \
    --delete \
    --region $REGION \
    --cache-control "public, max-age=31536000, immutable" \
    --exclude "index.html" \
    --exclude "*.json"

# index.html and JSON manifests should not be cached aggressively
aws s3 cp dist/index.html "s3://$BUCKET_NAME/index.html" \
    --region $REGION \
    --cache-control "public, max-age=0, must-revalidate" \
    --content-type "text/html"

# Upload any JSON files (manifest, etc.) with short cache
find dist -name "*.json" -exec sh -c '
    for f; do
        key="${f#dist/}"
        aws s3 cp "$f" "s3://'"$BUCKET_NAME"'/$key" \
            --region '"$REGION"' \
            --cache-control "public, max-age=0, must-revalidate" \
            --content-type "application/json" 2>/dev/null
    done
' sh {} +

# ============================================
# Step 6: Invalidate CloudFront cache
# ============================================
echo ""
echo "🔄 Step 6: Invalidating CloudFront cache..."
aws cloudfront create-invalidation \
    --distribution-id $DISTRIBUTION_ID \
    --paths "/*" \
    --region $REGION > /dev/null

# ============================================
# Step 7: Post-deploy verification
# ============================================
echo ""
echo "🔍 Step 7: Verifying deployment..."
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/health" 2>/dev/null || echo "000")
if [ "$HEALTH_STATUS" = "200" ]; then
    echo "   ✅ Health check passed (HTTP 200)"
else
    echo "   ⚠️ Health check returned HTTP $HEALTH_STATUS (may need a moment for cold start)"
fi

echo ""
echo "✅ =========================================="
echo "✅ Deployment Complete!"
echo "✅ =========================================="
echo ""
echo "🌐 Frontend URL: $CLOUDFRONT_URL"
echo "🔌 API URL:      $API_URL"
echo ""
echo "Test the API:"
echo "  curl ${API_URL}/health"
echo "  curl -X POST ${API_URL}/chat -H 'Content-Type: application/json' -d '{\"query\": \"Hello\"}'"
echo ""
