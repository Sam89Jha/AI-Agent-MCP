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