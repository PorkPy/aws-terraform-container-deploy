variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "resource_suffix" {
  description = "Suffix to add to resource names for uniqueness"
  type        = string
}

variable "model_bucket" {
  description = "S3 bucket for model storage"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to resources"
  type        = map(string)
}

# New variables for ECR repositories
variable "generate_text_image_uri" {
  description = "ECR image URI for generate_text function"
  type        = string
}

variable "visualize_attention_image_uri" {
  description = "ECR image URI for visualize_attention function"
  type        = string
}

# IAM role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role-${var.resource_suffix}"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
  
  tags = var.common_tags
}

# IAM policy for Lambda
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-policy"
  role = aws_iam_role.lambda_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Effect = "Allow"
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Effect = "Allow"
        Resource = [
          "arn:aws:s3:::${var.model_bucket}",
          "arn:aws:s3:::${var.model_bucket}/*"
        ]
      }
    ]
  })
}

# Lambda function for text generation (Container-based)
resource "aws_lambda_function" "generate_text" {
  function_name = "${var.project_name}-generate-text-${var.resource_suffix}"
  role          = aws_iam_role.lambda_role.arn
  
  # Container configuration
  package_type = "Image"
  image_uri    = var.generate_text_image_uri
  
  timeout     = 30
  memory_size = 1024
  
  environment {
    variables = {
      MODEL_BUCKET = var.model_bucket
      MODEL_KEY    = "model/transformer_model.pt"
      TOKENIZER_KEY = "model/tokenizer.json"
    }
  }
  
  tags = var.common_tags
}

# Lambda function for attention visualization (Container-based)
resource "aws_lambda_function" "visualize_attention" {
  function_name = "${var.project_name}-visualize-attention-${var.resource_suffix}"
  role          = aws_iam_role.lambda_role.arn
  
  # Container configuration
  package_type = "Image"
  image_uri    = var.visualize_attention_image_uri
  
  timeout     = 30
  memory_size = 1024
  
  environment {
    variables = {
      MODEL_BUCKET = var.model_bucket
      MODEL_KEY    = "model/transformer_model.pt"
      TOKENIZER_KEY = "model/tokenizer.json"
      VISUALIZATION_BUCKET = var.model_bucket
      VISUALIZATION_PREFIX = "visualizations/"
    }
  }
  
  tags = var.common_tags
}

output "generate_text_function_arn" {
  value = aws_lambda_function.generate_text.invoke_arn
}

output "generate_text_function_name" {
  value = aws_lambda_function.generate_text.function_name
}

output "visualize_attention_function_arn" {
  value = aws_lambda_function.visualize_attention.invoke_arn
}

output "visualize_attention_function_name" {
  value = aws_lambda_function.visualize_attention.function_name
}