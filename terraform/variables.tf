variable "project_name" {
  description = "Short name used to label AWS resources."
  type        = string
  default     = "ai-agent-poc"
}

variable "aws_region" {
  description = "AWS region for EKS, ECR, and Bedrock."
  type        = string
  default     = "us-east-1"
}

variable "github_repository" {
  description = "GitHub repository allowed to deploy, in owner/repository format."
  type        = string
}

variable "github_branch" {
  description = "Branch allowed to deploy from GitHub Actions."
  type        = string
  default     = "main"
}

variable "cluster_public_access_cidrs" {
  description = "CIDR blocks allowed to reach the EKS Kubernetes API endpoint. Use your runner's public IP with /32."
  type        = list(string)

  validation {
    condition     = length(var.cluster_public_access_cidrs) > 0
    error_message = "Set at least one trusted CIDR; do not expose the EKS API to 0.0.0.0/0."
  }
}

variable "bedrock_model_id" {
  description = "Bedrock foundation model ID used by the API."
  type        = string
  default     = "anthropic.claude-3-haiku-20240307-v1:0"
}
