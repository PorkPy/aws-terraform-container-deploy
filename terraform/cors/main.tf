variable "api_id" {
  description = "ID of the API Gateway"
  type        = string
}

variable "api_resources" {
  description = "List of API resource IDs to enable CORS for"
  type        = list(string)
}

# This module is empty as CORS is now handled in the API Gateway v2 configuration
# It exists only to satisfy the module reference in main.tf