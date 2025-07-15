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

output "websocket_register_function_name" {
  description = "Name of the websocket-register Lambda function"
  value       = aws_lambda_function.websocket_register.function_name
}

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

output "websocket_register_function_arn" {
  description = "ARN of the websocket-register Lambda function"
  value       = aws_lambda_function.websocket_register.arn
}

output "api_gateway_invoke_url" {
  description = "Base invoke URL for the HTTP API Gateway"
  value = "https://${aws_api_gateway_rest_api.main.id}.execute-api.${var.aws_region}.amazonaws.com/prod"
}

output "websocket_api_gateway_url" {
  description = "WebSocket API Gateway URL"
  value = "wss://${aws_apigatewayv2_api.websocket.id}.execute-api.${var.aws_region}.amazonaws.com/prod"
}

output "dynamodb_messages_table" {
  description = "Name of the messages DynamoDB table"
  value       = aws_dynamodb_table.messages.name
}

output "dynamodb_calls_table" {
  description = "Name of the calls DynamoDB table"
  value       = aws_dynamodb_table.calls.name
}

output "dynamodb_connections_table" {
  description = "Name of the connections DynamoDB table"
  value       = aws_dynamodb_table.connections.name
}

# =============================================================================
# MCP SERVER OUTPUTS
# =============================================================================

output "mcp_server_instance_id" {
  description = "ID of the MCP server EC2 instance"
  value       = aws_instance.mcp_server.id
}

output "mcp_server_public_ip" {
  description = "Public IP address of the MCP server"
  value       = aws_eip.mcp_server.public_ip
}

output "mcp_server_public_dns" {
  description = "Public DNS name of the MCP server"
  value       = aws_eip.mcp_server.public_dns
}

output "mcp_server_security_group_id" {
  description = "ID of the MCP server security group"
  value       = aws_security_group.mcp_server.id
}

output "mcp_server_iam_role_arn" {
  description = "ARN of the MCP server IAM role"
  value       = aws_iam_role.ec2_role.arn
}

output "mcp_server_url" {
  description = "URL to access the MCP server"
  value       = "http://${aws_eip.mcp_server.public_ip}"
}

output "mcp_server_health_check_url" {
  description = "Health check URL for the MCP server"
  value       = "http://${aws_eip.mcp_server.public_ip}/health"
} 