terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "lambda_execution_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda: send_message
resource "aws_lambda_function" "send_message" {
  filename         = data.archive_file.send_message_zip.output_path
  function_name    = "send-message"
  role             = aws_iam_role.lambda_role.arn
  handler          = "send_message.lambda_handler"
  runtime          = "python3.9"
  timeout          = 30
  memory_size      = 128
  environment { variables = { REGION = var.aws_region } }
  tags = { Name = "send-message" }
}

# Lambda: make_call
resource "aws_lambda_function" "make_call" {
  filename         = data.archive_file.make_call_zip.output_path
  function_name    = "make-call"
  role             = aws_iam_role.lambda_role.arn
  handler          = "make_call.lambda_handler"
  runtime          = "python3.9"
  timeout          = 30
  memory_size      = 128
  environment { variables = { REGION = var.aws_region } }
  tags = { Name = "make-call" }
}

# Lambda: get_message
resource "aws_lambda_function" "get_message" {
  filename         = data.archive_file.get_message_zip.output_path
  function_name    = "get-message"
  role             = aws_iam_role.lambda_role.arn
  handler          = "get_message.lambda_handler"
  runtime          = "python3.9"
  timeout          = 30
  memory_size      = 128
  environment { variables = { REGION = var.aws_region } }
  tags = { Name = "get-message" }
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "lambda_logs" {
  for_each = toset([
    aws_lambda_function.send_message.function_name,
    aws_lambda_function.make_call.function_name,
    aws_lambda_function.get_message.function_name
  ])
  name              = "/aws/lambda/${each.value}"
  retention_in_days = 7
  tags = { Name = "${each.value}-logs" }
}

# Archive files for Lambda functions
data "archive_file" "send_message_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda-functions/send-message"
  output_path = "${path.module}/lambda-send-message.zip"
  excludes    = ["*.pyc", "__pycache__", "*.pyo"]
}
data "archive_file" "make_call_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda-functions/make-call"
  output_path = "${path.module}/lambda-make-call.zip"
  excludes    = ["*.pyc", "__pycache__", "*.pyo"]
}
data "archive_file" "get_message_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda-functions/get-message"
  output_path = "${path.module}/lambda-get-message.zip"
  excludes    = ["*.pyc", "__pycache__", "*.pyo"]
} 