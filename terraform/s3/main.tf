variable "bucket_name" {
  description = "Name of the S3 bucket for model artifacts"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to resources"
  type        = map(string)
}

resource "aws_s3_bucket" "model_artifacts" {
  bucket        = var.bucket_name
  force_destroy = true # Allows Terraform to delete the bucket even if it contains files

  tags = var.common_tags
}

output "bucket_name" {
  value = aws_s3_bucket.model_artifacts.bucket
}

output "bucket_arn" {
  value = aws_s3_bucket.model_artifacts.arn
}