# api_gateway.tf - API Gateway configuration

resource "aws_api_gateway_rest_api" "transformer_api" {
  name        = "${var.project_name}-api-${var.resource_suffix}"
  description = "API for transformer model inference"
  
  tags = var.common_tags
}

# Generate text endpoint
resource "aws_api_gateway_resource" "generate" {
  rest_api_id = aws_api_gateway_rest_api.transformer_api.id
  parent_id   = aws_api_gateway_rest_api.transformer_api.root_resource_id
  path_part   = "generate"
}

resource "aws_api_gateway_method" "generate_post" {
  rest_api_id   = aws_api_gateway_rest_api.transformer_api.id
  resource_id   = aws_api_gateway_resource.generate.id
  http_method   = "POST"
  authorization_type = "NONE"
}

resource "aws_api_gateway_integration" "generate_lambda" {
  rest_api_id = aws_api_gateway_rest_api.transformer_api.id
  resource_id = aws_api_gateway_resource.generate.id
  http_method = aws_api_gateway_method.generate_post.http_method
  
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.generate_lambda_fn
}

# Visualize attention endpoint
resource "aws_api_gateway_resource" "visualize" {
  rest_api_id = aws_api_gateway_rest_api.transformer_api.id
  parent_id   = aws_api_gateway_rest_api.transformer_api.root_resource_id
  path_part   = "visualize"
}

resource "aws_api_gateway_method" "visualize_post" {
  rest_api_id   = aws_api_gateway_rest_api.transformer_api.id
  resource_id   = aws_api_gateway_resource.visualize.id
  http_method   = "POST"
  authorization_type = "NONE"
}

resource "aws_api_gateway_integration" "visualize_lambda" {
  rest_api_id = aws_api_gateway_rest_api.transformer_api.id
  resource_id = aws_api_gateway_resource.visualize.id
  http_method = aws_api_gateway_method.visualize_post.http_method
  
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.visualize_lambda_fn
}

# Deploy the API
resource "aws_api_gateway_deployment" "deployment" {
  depends_on = [
    aws_api_gateway_integration.generate_lambda,
    aws_api_gateway_integration.visualize_lambda
  ]
  
  rest_api_id = aws_api_gateway_rest_api.transformer_api.id
  stage_name  = var.environment
}

# Enable CORS
module "cors" {
  source = "./cors"
  
  api_id       = aws_api_gateway_rest_api.transformer_api.id
  api_resources = [
    aws_api_gateway_resource.generate.id,
    aws_api_gateway_resource.visualize.id
  ]
}

# Output the API endpoint
output "api_endpoint" {
  value = "${aws_api_gateway_deployment.deployment.invoke_url}"
}