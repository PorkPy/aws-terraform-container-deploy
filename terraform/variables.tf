# variables.tf - Input variables

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (dev, prod)"
  type        = string
  default     = "dev"
}

variable "cost_alert_threshold" {
  description = "Monthly cost threshold for alerts (USD)"
  type        = number
  default     = 5
}

variable "model_memory_size" {
  description = "Memory allocation for Lambda functions (MB)"
  type        = number
  default     = 1024
}

variable "model_timeout" {
  description = "Timeout for Lambda functions (seconds)"
  type        = number
  default     = 30
}