variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "eu-west-2" # London region
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