output "aws_region" {
  value = var.aws_region
}

output "cluster_name" {
  value = module.eks.cluster_name
}

output "ecr_repository_name" {
  value = aws_ecr_repository.api.name
}

output "ecr_repository_url" {
  value = aws_ecr_repository.api.repository_url
}

output "github_actions_role_arn" {
  value = aws_iam_role.github_actions.arn
}

output "bedrock_irsa_role_arn" {
  value = aws_iam_role.bedrock.arn
}
