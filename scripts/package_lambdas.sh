#!/bin/bash
# scripts/package_lambdas.sh

set -e  # Exit on error

echo "Creating dist directory..."
mkdir -p dist

# Package generate_text function
echo "Packaging generate_text Lambda function..."

# Create temporary directory
TMP_DIR=$(mktemp -d)
echo "Using temporary directory: $TMP_DIR"

# Install dependencies
echo "Installing dependencies..."
pip install -r src/lambda_functions/generate_text/requirements.txt -t $TMP_DIR

# Copy Lambda function code
echo "Copying Lambda function code..."
cp src/lambda_functions/generate_text/*.py $TMP_DIR/

# Copy model and tokenizer class definitions
echo "Copying model classes..."
cp -r model/transformer.py $TMP_DIR/
cp -r model/tokenizer.py $TMP_DIR/

# Create zip file
echo "Creating zip file..."
cd $TMP_DIR
zip -r generate_text.zip .
mv generate_text.zip ../../dist/

# Clean up
cd ../../
rm -rf $TMP_DIR

echo "Lambda function packaging complete!"
echo "Zip file created at dist/generate_text.zip"