# main.tf - Main Terraform configuration

# Get the latest image tags from ECR (will be SHA tags from GitHub)
data "external" "latest_image_tags" {
  program = ["echo", "{\"generate_tag\":\"latest\",\"visualize_tag\":\"latest\"}"]
}

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.16"
    }
  }
  
  # Optional: Configure backend for state storage
  backend "s3" {
    bucket = "dom-terraform-state-bucket"
    key    = "transformer-model/terraform.tfstate"
    region = "eu-west-2"  
  }
}

provider "aws" {
  region = var.aws_region
}

# Create a random suffix for resource names to avoid conflicts
resource "random_string" "resource_suffix" {
  length  = 6
  special = false
  upper   = false
}

# Local variables
locals {
  project_name    = "transformer-model"
  resource_suffix = random_string.resource_suffix.result
  common_tags = {
    Project     = "TransformerModel"
    Environment = var.environment
    ManagedBy   = "Terraform"
    Owner       = "Dom McKean"
  }
}

# Create S3 bucket for model artifacts
module "model_storage" {
  source = "./s3"
  
  bucket_name = "${local.project_name}-artifacts-${local.resource_suffix}"
  common_tags = local.common_tags
}

# Create ECR repositories for container images
module "ecr_repositories" {
  source = "./ecr"
  
  project_name    = local.project_name
  resource_suffix = local.resource_suffix
  common_tags     = local.common_tags
}

# Create Lambda functions (container-based)
module "lambda_functions" {
  source = "./lambda"
  
  project_name    = local.project_name
  resource_suffix = local.resource_suffix
  model_bucket    = module.model_storage.bucket_name
  common_tags     = local.common_tags
  
  # Container image URIs (initially using latest tag)
  # Container image URIs using latest pushed tags (SHA-based)
  generate_text_image_uri       = "${module.ecr_repositories.generate_text_repository_url}:${data.external.latest_image_tags.result.generate_tag}"
  visualize_attention_image_uri = "${module.ecr_repositories.visualize_attention_repository_url}:${data.external.latest_image_tags.result.visualize_tag}"
}

# Create API Gateway
module "api_gateway" {
  source = "./api_gateway"
  
  project_name       = local.project_name
  resource_suffix    = local.resource_suffix
  generate_lambda_fn = module.lambda_functions.generate_text_function_arn
  visualize_lambda_fn = module.lambda_functions.visualize_attention_function_arn
  common_tags        = local.common_tags
}

# Set up monitoring and alerts
module "monitoring" {
  source = "./cloudwatch"
  
  project_name    = local.project_name
  resource_suffix = local.resource_suffix
  lambda_functions = [
    module.lambda_functions.generate_text_function_name,
    module.lambda_functions.visualize_attention_function_name
  ]
  cost_alert_threshold = var.cost_alert_threshold
  common_tags          = local.common_tags
}