# Outputs for NavieTakieSimulation

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.main.function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.main.arn
}

output "api_gateway_url" {
  description = "URL of the main API Gateway"
  value       = "https://${aws_api_gateway_rest_api.main.id}.execute-api.${var.aws_region}.amazonaws.com/${var.environment}"
}

output "websocket_api_gateway_url" {
  description = "URL of the WebSocket API Gateway"
  value       = "wss://${aws_api_gateway_rest_api.websocket.id}.execute-api.${var.aws_region}.amazonaws.com/${var.environment}"
}

output "dynamodb_messages_table" {
  description = "Name of the messages DynamoDB table"
  value       = aws_dynamodb_table.messages.name
}

output "dynamodb_connections_table" {
  description = "Name of the connections DynamoDB table"
  value       = aws_dynamodb_table.connections.name
}

output "dynamodb_calls_table" {
  description = "Name of the calls DynamoDB table"
  value       = aws_dynamodb_table.calls.name
}

output "cloudwatch_log_group" {
  description = "Name of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.lambda_logs.name
} 