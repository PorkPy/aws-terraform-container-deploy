variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "resource_suffix" {
  description = "Suffix to add to resource names for uniqueness"
  type        = string
}

variable "lambda_functions" {
  description = "List of Lambda function names to monitor"
  type        = list(string)
}

variable "cost_alert_threshold" {
  description = "Monthly cost threshold for alerts (USD)"
  type        = number
  default     = 5
}

variable "common_tags" {
  description = "Common tags to apply to resources"
  type        = map(string)
}

# CloudWatch Log Group for Lambda functions
resource "aws_cloudwatch_log_group" "lambda_log_groups" {
  count = length(var.lambda_functions)
  
  name              = "/aws/lambda/${var.lambda_functions[count.index]}"
  retention_in_days = 14
  
  tags = var.common_tags
}

# CloudWatch Alarm for Lambda errors
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  count = length(var.lambda_functions)
  
  alarm_name          = "${var.lambda_functions[count.index]}-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "This metric monitors lambda function errors"
  
  dimensions = {
    FunctionName = var.lambda_functions[count.index]
  }
  
  tags = var.common_tags
}