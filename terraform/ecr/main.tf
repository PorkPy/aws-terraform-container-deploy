variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "resource_suffix" {
  description = "Suffix to add to resource names for uniqueness"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to resources"
  type        = map(string)
}

# ECR Repository for generate_text function
resource "aws_ecr_repository" "generate_text" {
  name = "${var.project_name}-generate-text-${var.resource_suffix}"
  
  image_scanning_configuration {
    scan_on_push = true
  }
  
  tags = var.common_tags
}

# ECR Repository for visualize_attention function
resource "aws_ecr_repository" "visualize_attention" {
  name = "${var.project_name}-visualize-attention-${var.resource_suffix}"
  
  image_scanning_configuration {
    scan_on_push = true
  }
  
  tags = var.common_tags
}

# Output the repository URLs
output "generate_text_repository_url" {
  description = "ECR repository URL for generate_text function"
  value       = aws_ecr_repository.generate_text.repository_url
}

output "visualize_attention_repository_url" {
  description = "ECR repository URL for visualize_attention function"
  value       = aws_ecr_repository.visualize_attention.repository_url
}

output "generate_text_repository_name" {
  description = "ECR repository name for generate_text function"
  value       = aws_ecr_repository.generate_text.name
}

output "visualize_attention_repository_name" {
  description = "ECR repository name for visualize_attention function"
  value       = aws_ecr_repository.visualize_attention.name
}