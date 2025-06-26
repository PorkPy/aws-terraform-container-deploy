variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "resource_suffix" {
  description = "Suffix to add to resource names for uniqueness"
  type        = string
}

variable "generate_lambda_fn" {
  description = "ARN of the Lambda function for text generation"
  type        = string
}

variable "visualize_lambda_fn" {
  description = "ARN of the Lambda function for attention visualization"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to resources"
  type        = map(string)
}

# API Gateway HTTP API
resource "aws_apigatewayv2_api" "transformer_api" {
  name          = "${var.project_name}-api-${var.resource_suffix}"
  protocol_type = "HTTP"
  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = ["content-type"]
  }

  tags = var.common_tags
}

# API Gateway stage
resource "aws_apigatewayv2_stage" "stage" {
  api_id      = aws_apigatewayv2_api.transformer_api.id
  name        = "$default"
  auto_deploy = true
}

# API Gateway route for generate text
resource "aws_apigatewayv2_route" "generate_route" {
  api_id    = aws_apigatewayv2_api.transformer_api.id
  route_key = "POST /generate"
  target    = "integrations/${aws_apigatewayv2_integration.generate_integration.id}"
}

# API Gateway integration for generate text
resource "aws_apigatewayv2_integration" "generate_integration" {
  api_id                 = aws_apigatewayv2_api.transformer_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = var.generate_lambda_fn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

# API Gateway route for visualize attention
resource "aws_apigatewayv2_route" "visualize_route" {
  api_id    = aws_apigatewayv2_api.transformer_api.id
  route_key = "POST /visualize"
  target    = "integrations/${aws_apigatewayv2_integration.visualize_integration.id}"
}

# API Gateway integration for visualize attention
resource "aws_apigatewayv2_integration" "visualize_integration" {
  api_id                 = aws_apigatewayv2_api.transformer_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = var.visualize_lambda_fn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

# Lambda permission for generate text
resource "aws_lambda_permission" "generate_permission" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = "transformer-model-generate-text-${var.resource_suffix}"
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.transformer_api.execution_arn}/*/*/generate"
}

# Lambda permission for visualize attention
resource "aws_lambda_permission" "visualize_permission" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = "transformer-model-visualize-attention-${var.resource_suffix}"
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.transformer_api.execution_arn}/*/*/visualize"
}

output "api_endpoint" {
  value = aws_apigatewayv2_api.transformer_api.api_endpoint
}