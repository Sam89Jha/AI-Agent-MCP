# Outputs for NavieTakieSimulation

# Lambda Function Names
output "send_message_function_name" {
  description = "Name of the send-message Lambda function"
  value       = aws_lambda_function.send_message.function_name
}

output "make_call_function_name" {
  description = "Name of the make-call Lambda function"
  value       = aws_lambda_function.make_call.function_name
}

output "get_message_function_name" {
  description = "Name of the get-message Lambda function"
  value       = aws_lambda_function.get_message.function_name
}

output "websocket_handler_function_name" {
  description = "Name of the websocket-handler Lambda function"
  value       = aws_lambda_function.websocket_handler.function_name
}

# Lambda Function ARNs
output "send_message_function_arn" {
  description = "ARN of the send-message Lambda function"
  value       = aws_lambda_function.send_message.arn
}

output "make_call_function_arn" {
  description = "ARN of the make-call Lambda function"
  value       = aws_lambda_function.make_call.arn
}

output "get_message_function_arn" {
  description = "ARN of the get-message Lambda function"
  value       = aws_lambda_function.get_message.arn
}

output "websocket_handler_function_arn" {
  description = "ARN of the websocket-handler Lambda function"
  value       = aws_lambda_function.websocket_handler.arn
}

# EC2 Instance
output "mcp_server_public_ip" {
  description = "Public IP of the MCP server"
  value       = aws_eip.mcp_server.public_ip
}

output "mcp_server_instance_id" {
  description = "Instance ID of the MCP server"
  value       = aws_instance.mcp_server.id
}

# S3 Buckets
output "dax_app_bucket_name" {
  description = "Name of the DAX app S3 bucket"
  value       = aws_s3_bucket.dax_app.bucket
}

output "pax_app_bucket_name" {
  description = "Name of the PAX app S3 bucket"
  value       = aws_s3_bucket.pax_app.bucket
}

# CloudFront Distributions
output "dax_app_url" {
  description = "URL of the DAX app CloudFront distribution"
  value       = "https://${aws_cloudfront_distribution.dax_app.domain_name}"
}

output "pax_app_url" {
  description = "URL of the PAX app CloudFront distribution"
  value       = "https://${aws_cloudfront_distribution.pax_app.domain_name}"
}

# CloudWatch Log Groups
output "lambda_log_groups" {
  description = "Names of the Lambda CloudWatch log groups"
  value       = [for log_group in aws_cloudwatch_log_group.lambda_logs : log_group.name]
} 