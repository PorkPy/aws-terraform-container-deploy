#!/bin/bash

# Deployment script for transformer Lambda containers

set -e  # Exit on any error

echo "🚀 Starting container deployment..."

# Set environment variables
export REGION="eu-west-2"
export ACCOUNT_ID="632136105799"
export GENERATE_REPO="transformer-model-generate-text-q3ukv7"
export VISUALIZE_REPO="transformer-model-visualize-attention-q3ukv7"

# Activate conda environment
echo "📦 Activating conda environment..."
source ~/miniconda3/etc/profile.d/conda.sh
conda activate lambda_env

# Verify setup
echo "🔍 Verifying setup..."
aws sts get-caller-identity
docker --version

# Navigate to project root
echo "📁 Navigating to project..."
cd /mnt/c/Users/Dom/workspace/aws/aws-terraform-container-deploy

# ECR Login
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Build and push generate_text
echo "🏗️  Building generate_text container..."
cd src/lambda_functions/generate_text
docker build -t $GENERATE_REPO .
docker tag $GENERATE_REPO:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$GENERATE_REPO:latest

echo "📤 Pushing generate_text to ECR..."
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$GENERATE_REPO:latest

echo "🔄 Updating generate_text Lambda function..."
aws lambda update-function-code \
  --function-name transformer-model-generate-text-q3ukv7 \
  --image-uri $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$GENERATE_REPO:latest

# Build and push visualize_attention
echo "🏗️  Building visualize_attention container..."
cd ../visualize_attention
docker build -t $VISUALIZE_REPO .
docker tag $VISUALIZE_REPO:latest $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$VISUALIZE_REPO:latest

echo "📤 Pushing visualize_attention to ECR..."
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$VISUALIZE_REPO:latest

echo "🔄 Updating visualize_attention Lambda function..."
aws lambda update-function-code \
  --function-name transformer-model-visualize-attention-q3ukv7 \
  --image-uri $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$VISUALIZE_REPO:latest

echo "✅ Deployment complete!"
echo "🧪 Testing API..."

# Test the API
sleep 10
curl -X POST "https://0fc0dgwg69.execute-api.eu-west-2.amazonaws.com/generate" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, world!", "max_tokens": 10}'

echo ""
echo "🎉 Done! Check the output above for any errors."