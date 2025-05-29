# lambda.tf - Lambda function configuration

resource "aws_lambda_function" "generate_text" {
  function_name = "${var.project_name}-generate-text-${var.resource_suffix}"
  role          = aws_iam_role.lambda_role.arn
  handler       = "main.lambda_handler"
  runtime       = "python3.9"
  timeout       = var.model_timeout
  memory_size   = var.model_memory_size
  
  # Package the Lambda function code
  filename      = "../dist/generate_text.zip"
  source_code_hash = filebase64sha256("../dist/generate_text.zip")
  
  environment {
    variables = {
      MODEL_BUCKET = var.model_bucket
      MODEL_KEY    = "model/transformer_model.pt"
      TOKENIZER_KEY = "model/tokenizer.json"
    }
  }
  
  tags = var.common_tags
}

resource "aws_lambda_function" "visualize_attention" {
  function_name = "${var.project_name}-visualize-attention-${var.resource_suffix}"
  role          = aws_iam_role.lambda_role.arn
  handler       = "main.lambda_handler"
  runtime       = "python3.9"
  timeout       = var.model_timeout
  memory_size   = var.model_memory_size
  
  # Package the Lambda function code
  filename      = "../dist/visualize_attention.zip"
  source_code_hash = filebase64sha256("../dist/visualize_attention.zip")
  
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

# Output values
output "generate_text_function_arn" {
  value = aws_lambda_function.generate_text.arn
}

output "generate_text_function_name" {
  value = aws_lambda_function.generate_text.function_name
}

output "visualize_attention_function_arn" {
  value = aws_lambda_function.visualize_attention.arn
}

output "visualize_attention_function_name" {
  value = aws_lambda_function.visualize_attention.function_name
}