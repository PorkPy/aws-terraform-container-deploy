#!/bin/bash
# scripts/deploy.sh

set -e

# Configuration
PROJECT_DIR=$(pwd)
DIST_DIR="$PROJECT_DIR/dist"
TERRAFORM_DIR="$PROJECT_DIR/terraform"
MODEL_DIR="$PROJECT_DIR/src/model"

echo "Starting deployment of Transformer Model to AWS..."

# Step 1: Prepare directories
mkdir -p $DIST_DIR

# Step 2: Package Lambda functions
echo "Packaging Lambda functions..."
cd $PROJECT_DIR/src/lambda_functions/generate_text
pip install -r requirements.txt -t .
zip -r $DIST_DIR/generate_text.zip .

cd $PROJECT_DIR/src/lambda_functions/visualize_attention
pip install -r requirements.txt -t .
zip -r $DIST_DIR/visualize_attention.zip .

# Step 3: Initialize Terraform
echo "Initializing Terraform..."
cd $TERRAFORM_DIR
terraform init

# Step 4: Apply Terraform configuration
echo "Applying Terraform configuration..."
terraform apply -auto-approve

# Step 5: Get outputs
S3_BUCKET=$(terraform output -raw model_bucket_name)
API_ENDPOINT=$(terraform output -raw api_endpoint)

# Step 6: Upload model to S3
echo "Uploading model files to S3..."
aws s3 cp $MODEL_DIR/transformer_model.pt s3://$S3_BUCKET/model/
aws s3 cp $MODEL_DIR/tokenizer.json s3://$S3_BUCKET/model/

echo "Deployment complete!"
echo "API Endpoint: $API_ENDPOINT"
echo "S3 Bucket: $S3_BUCKET"

# Step 7: Update Streamlit configuration
echo "Updating Streamlit configuration..."
echo "API_ENDPOINT=\"$API_ENDPOINT\"" > $PROJECT_DIR/src/streamlit/.env

echo "Your Transformer model is now deployed and ready to use!"