# Output the knowledge base ID
output "cloudfront_domain_name" {
  value = aws_cloudfront_distribution.ecs_distribution.domain_name
  description = "The domain name of the CloudFront distribution"
}

output "cognito_hosted_ui_url" {
  value = "https://${aws_cognito_user_pool_domain.main.domain}.auth.${var.aws_region}.amazoncognito.com/login?client_id=${aws_cognito_user_pool_client.client.id}&response_type=code&scope=email+openid+profile&redirect_uri=https://${aws_cloudfront_distribution.ecs_distribution.domain_name}/oauth2/idpresponse"
}

output "stack_outputs" {
  value = aws_cloudformation_stack.kb-stack.outputs
}