# Outputs for AI-Driven Chat & Voice Assistant Demo

output "mcp_server_public_ip" {
  description = "Public IP address of the MCP server"
  value       = aws_eip.mcp_server.public_ip
}

output "mcp_server_public_dns" {
  description = "Public DNS name of the MCP server"
  value       = aws_eip.mcp_server.public_dns
}

output "dax_app_cloudfront_url" {
  description = "CloudFront URL for DAX app"
  value       = "https://dax.sameer-jha.com"
}

output "pax_app_cloudfront_url" {
  description = "CloudFront URL for PAX app"
  value       = "https://pax.sameer-jha.com"
}

output "mcp_server_url" {
  description = "MCP server URL"
  value       = "https://mcp.sameer-jha.com"
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  value       = aws_dynamodb_table.messages.name
}

output "lambda_functions" {
  description = "Lambda function ARNs"
  value = {
    send_message = aws_lambda_function.send_message.arn
    make_call    = aws_lambda_function.make_call.arn
    get_message  = aws_lambda_function.get_message.arn
  }
}

output "s3_buckets" {
  description = "S3 bucket names"
  value = {
    dax_app = aws_s3_bucket.dax_app.bucket
    pax_app = aws_s3_bucket.pax_app.bucket
  }
}

output "cloudfront_distributions" {
  description = "CloudFront distribution IDs"
  value = {
    dax_app = aws_cloudfront_distribution.dax_app.id
    pax_app = aws_cloudfront_distribution.pax_app.id
  }
}

output "security_group_id" {
  description = "Security group ID for MCP server"
  value       = aws_security_group.mcp_server.id
}

output "iam_role_arns" {
  description = "IAM role ARNs"
  value = {
    lambda_role = aws_iam_role.lambda_role.arn
    ec2_role    = aws_iam_role.ec2_role.arn
  }
} 