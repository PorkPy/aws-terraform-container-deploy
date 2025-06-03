output "api_endpoint" {
  description = "Base URL for the API Gateway"
  value       = module.api_gateway.api_endpoint
}

output "model_bucket_name" {
  description = "Name of the S3 bucket storing model files"
  value       = module.model_storage.bucket_name
}

output "generate_function_name" {
  description = "Name of the generate text Lambda function"
  value       = module.lambda_functions.generate_text_function_name
}

output "visualize_function_name" {
  description = "Name of the visualize attention Lambda function"
  value       = module.lambda_functions.visualize_attention_function_name
}

# ECR Repository outputs
output "generate_text_repository_url" {
  description = "ECR repository URL for generate_text function"
  value       = module.ecr_repositories.generate_text_repository_url
}

output "visualize_attention_repository_url" {
  description = "ECR repository URL for visualize_attention function"
  value       = module.ecr_repositories.visualize_attention_repository_url
}

output "generate_text_repository_name" {
  description = "ECR repository name for generate_text function"
  value       = module.ecr_repositories.generate_text_repository_name
}

output "visualize_attention_repository_name" {
  description = "ECR repository name for visualize_attention function"
  value       = module.ecr_repositories.visualize_attention_repository_name
}