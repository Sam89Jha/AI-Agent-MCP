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

# --- API Gateway REST API ---
resource "aws_api_gateway_rest_api" "main" {
  name        = "lambda-api-gateway"
  description = "API Gateway for Lambda HTTP endpoints"
}

# Root /api/v1 resource
resource "aws_api_gateway_resource" "api" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "api"
}
resource "aws_api_gateway_resource" "v1" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.api.id
  path_part   = "v1"
}

# /api/v1/send_message
resource "aws_api_gateway_resource" "send_message" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.v1.id
  path_part   = "send_message"
}
resource "aws_api_gateway_method" "send_message" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.send_message.id
  http_method   = "POST"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "send_message" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.send_message.id
  http_method             = aws_api_gateway_method.send_message.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.send_message.invoke_arn
}

# /api/v1/make_call
resource "aws_api_gateway_resource" "make_call" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.v1.id
  path_part   = "make_call"
}
resource "aws_api_gateway_method" "make_call" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.make_call.id
  http_method   = "POST"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "make_call" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.make_call.id
  http_method             = aws_api_gateway_method.make_call.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.make_call.invoke_arn
}

# /api/v1/get_message
resource "aws_api_gateway_resource" "get_message" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.v1.id
  path_part   = "get_message"
}
resource "aws_api_gateway_method" "get_message" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.get_message.id
  http_method   = "GET"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "get_message" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.get_message.id
  http_method             = aws_api_gateway_method.get_message.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.get_message.invoke_arn
}

resource "aws_api_gateway_method" "get_message_post" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.get_message.id
  http_method   = "POST"
  authorization = "NONE"
}
resource "aws_api_gateway_integration" "get_message_post" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.get_message.id
  http_method             = aws_api_gateway_method.get_message_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.get_message.invoke_arn
}

# Lambda permissions for API Gateway
resource "aws_lambda_permission" "apigw_send_message" {
  statement_id  = "AllowExecutionFromAPIGatewaySendMessage"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.send_message.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}
resource "aws_lambda_permission" "apigw_make_call" {
  statement_id  = "AllowExecutionFromAPIGatewayMakeCall"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.make_call.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}
resource "aws_lambda_permission" "apigw_get_message" {
  statement_id  = "AllowExecutionFromAPIGatewayGetMessage"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_message.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

# API Gateway deployment and stage
resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  depends_on = [
    aws_api_gateway_integration.send_message,
    aws_api_gateway_integration.make_call,
    aws_api_gateway_integration.get_message,
    aws_api_gateway_integration.get_message_post
  ]
}
resource "aws_api_gateway_stage" "main" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = "prod"
} 