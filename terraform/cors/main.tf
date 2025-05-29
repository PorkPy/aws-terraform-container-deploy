variable "api_id" {
  description = "ID of the API Gateway"
  type        = string
}

variable "api_resources" {
  description = "List of API resource IDs to enable CORS for"
  type        = list(string)
}

resource "aws_api_gateway_method" "options" {
  count         = length(var.api_resources)
  rest_api_id   = var.api_id
  resource_id   = var.api_resources[count.index]
  http_method   = "OPTIONS"
  authorization_type = "NONE"
}

resource "aws_api_gateway_integration" "options" {
  count         = length(var.api_resources)
  rest_api_id   = var.api_id
  resource_id   = var.api_resources[count.index]
  http_method   = aws_api_gateway_method.options[count.index].http_method
  type          = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "options" {
  count         = length(var.api_resources)
  rest_api_id   = var.api_id
  resource_id   = var.api_resources[count.index]
  http_method   = aws_api_gateway_method.options[count.index].http_method
  status_code   = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "options" {
  count         = length(var.api_resources)
  rest_api_id   = var.api_id
  resource_id   = var.api_resources[count.index]
  http_method   = aws_api_gateway_method.options[count.index].http_method
  status_code   = aws_api_gateway_method_response.options[count.index].status_code
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}