#!/bin/bash
# deploy.sh - Deploy MediBot to AWS
# Usage: ./deploy.sh [staging|production]

set -e

ENVIRONMENT=${1:-production}
STACK_NAME="medibot-$ENVIRONMENT"
REGION="ap-south-2"

echo "🚀 Deploying MediBot to AWS ($ENVIRONMENT)..."
echo ""

# Check prerequisites
command -v aws >/dev/null 2>&1 || { echo "❌ AWS CLI not installed. Run: brew install awscli"; exit 1; }
command -v sam >/dev/null 2>&1 || { echo "❌ SAM CLI not installed. Run: brew install aws-sam-cli"; exit 1; }

# Check if BEDROCK_TOKEN is set
if [ -z "$BEDROCK_TOKEN" ]; then
    echo "❌ BEDROCK_TOKEN environment variable not set"
    echo "   Run: export BEDROCK_TOKEN='your-bearer-token'"
    exit 1
fi

echo "📦 Step 1: Building Lambda package..."
cd infrastructure
sam build --use-container

echo ""
echo "☁️ Step 2: Deploying backend to AWS Lambda..."
sam deploy \
    --stack-name $STACK_NAME \
    --parameter-overrides "BedrockBearerToken=$BEDROCK_TOKEN Environment=$ENVIRONMENT" \
    --capabilities CAPABILITY_IAM \
    --no-fail-on-empty-changeset \
    --region $REGION

# Get outputs
echo ""
echo "📝 Getting deployment outputs..."
API_URL=$(aws cloudformation describe-stacks --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' --output text --region $REGION)
BUCKET_NAME=$(aws cloudformation describe-stacks --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucketName`].OutputValue' --output text --region $REGION)
CLOUDFRONT_URL=$(aws cloudformation describe-stacks --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontUrl`].OutputValue' --output text --region $REGION)
DISTRIBUTION_ID=$(aws cloudformation describe-stacks --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' --output text --region $REGION)

echo ""
echo "🔨 Step 3: Building frontend..."
cd ../frontend

# Update API URL
echo "NEXT_PUBLIC_API_URL=$API_URL" > .env.local
echo "   API URL: $API_URL"

# Build static export
npm run build

echo ""
echo "📤 Step 4: Uploading frontend to S3..."
aws s3 sync out/ s3://$BUCKET_NAME --delete --region $REGION

echo ""
echo "🔄 Step 5: Invalidating CloudFront cache..."
aws cloudfront create-invalidation --distribution-id $DISTRIBUTION_ID --paths "/*" --region $REGION >/dev/null

echo ""
echo "✅ =========================================="
echo "✅ Deployment Complete!"
echo "✅ =========================================="
echo ""
echo "🌐 Frontend URL: $CLOUDFRONT_URL"
echo "🔌 API URL:      $API_URL"
echo ""
echo "Test the API:"
echo "  curl $API_URL/health"
echo ""
