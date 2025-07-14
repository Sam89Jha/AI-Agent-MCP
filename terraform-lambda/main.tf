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

# DynamoDB permissions for Lambda
resource "aws_iam_role_policy" "lambda_dynamodb" {
  name = "lambda_dynamodb_policy"
  role = aws_iam_role.lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.messages.arn,
          aws_dynamodb_table.calls.arn,
          aws_dynamodb_table.connections.arn,
          "${aws_dynamodb_table.connections.arn}/index/*"
        ]
      }
    ]
  })
}

# API Gateway Management API permissions for WebSocket
resource "aws_iam_role_policy" "lambda_apigateway_management" {
  name = "lambda_apigateway_management_policy"
  role = aws_iam_role.lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "execute-api:ManageConnections"
        ]
        Resource = "${aws_apigatewayv2_api.websocket.execution_arn}/*"
      }
    ]
  })
}

# Lambda: send_message
resource "aws_lambda_function" "send_message" {
  filename         = "lambda-send-message-fixed.zip"
  function_name    = "send-message"
  role             = aws_iam_role.lambda_role.arn
  handler          = "send_message.lambda_handler"
  runtime          = "python3.9"
  timeout          = 30
  memory_size      = 128
  environment { 
    variables = { 
      REGION = var.aws_region
      MESSAGES_TABLE = aws_dynamodb_table.messages.name
      CONNECTIONS_TABLE = aws_dynamodb_table.connections.name
      WEBSOCKET_ENDPOINT = "https://gslu2w0885.execute-api.us-east-1.amazonaws.com/prod"
    } 
  }
  tags = { Name = "send-message" }
}

# Lambda: make_call
resource "aws_lambda_function" "make_call" {
  filename         = "lambda-make-call-fixed.zip"
  function_name    = "make-call"
  role             = aws_iam_role.lambda_role.arn
  handler          = "make_call.lambda_handler"
  runtime          = "python3.9"
  timeout          = 30
  memory_size      = 128
  environment { 
    variables = { 
      REGION = var.aws_region
      CALLS_TABLE = aws_dynamodb_table.calls.name
      CONNECTIONS_TABLE = aws_dynamodb_table.connections.name
      WEBSOCKET_ENDPOINT = "https://gslu2w0885.execute-api.us-east-1.amazonaws.com/prod"
    } 
  }
  tags = { Name = "make-call" }
}

# Lambda: get_message
resource "aws_lambda_function" "get_message" {
  filename         = "lambda-get-message-fixed.zip"
  function_name    = "get-message"
  role             = aws_iam_role.lambda_role.arn
  handler          = "get_message.lambda_handler"
  runtime          = "python3.9"
  timeout          = 30
  memory_size      = 128
  environment { 
    variables = { 
      REGION = var.aws_region
      MESSAGES_TABLE = aws_dynamodb_table.messages.name
    } 
  }
  tags = { Name = "get-message" }
}

# Lambda: websocket_register
resource "aws_lambda_function" "websocket_register" {
  filename         = "lambda-websocket-register-fixed.zip"
  function_name    = "websocket-register"
  role             = aws_iam_role.lambda_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.9"
  timeout          = 30
  memory_size      = 128
  environment { 
    variables = { 
      REGION = var.aws_region
      CONNECTIONS_TABLE = aws_dynamodb_table.connections.name
    } 
  }
  tags = { Name = "websocket-register" }
}



# DynamoDB Tables
resource "aws_dynamodb_table" "messages" {
  name           = "messages"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "booking_code"
  range_key      = "message_id"
  
  attribute {
    name = "booking_code"
    type = "S"
  }
  
  attribute {
    name = "message_id"
    type = "S"
  }
  
  tags = { Name = "messages" }
  
  # Prevent accidental deletion
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_dynamodb_table" "calls" {
  name           = "calls"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "booking_code"
  
  attribute {
    name = "booking_code"
    type = "S"
  }
  
  tags = { Name = "calls" }
  
  # Prevent accidental deletion
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_dynamodb_table" "connections" {
  name           = "connections"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "connection_id"
  range_key      = "booking_code"
  
  attribute {
    name = "connection_id"
    type = "S"
  }
  
  attribute {
    name = "booking_code"
    type = "S"
  }
  
  attribute {
    name = "user_type"
    type = "S"
  }
  
  global_secondary_index {
    name               = "booking_code-index"
    hash_key           = "booking_code"
    range_key          = "user_type"
    projection_type    = "ALL"
  }
  
  tags = { Name = "connections" }
  
  # Prevent accidental deletion
  lifecycle {
    prevent_destroy = true
  }
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "lambda_logs" {
  for_each = toset([
    aws_lambda_function.send_message.function_name,
    aws_lambda_function.make_call.function_name,
    aws_lambda_function.get_message.function_name,
    aws_lambda_function.websocket_register.function_name
  ])
  name              = "/aws/lambda/${each.value}"
  retention_in_days = 7
  tags = { Name = "${each.value}-logs" }
  
  # Ignore changes to prevent conflicts with existing resources
  lifecycle {
    ignore_changes = [retention_in_days, tags]
  }
}



# --- API Gateway REST API (HTTP endpoints) ---
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

# API Gateway deployment and stage (HTTP)
resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  depends_on = [
    aws_api_gateway_integration.send_message,
    aws_api_gateway_integration.make_call,
    aws_api_gateway_integration.get_message,
    aws_api_gateway_integration.get_message_post
  ]
  
  # Force new deployment
  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_integration.send_message,
      aws_api_gateway_integration.make_call,
      aws_api_gateway_integration.get_message,
      aws_api_gateway_integration.get_message_post
    ]))
  }
}
resource "aws_api_gateway_stage" "main" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = "prod"
}

# --- API Gateway WebSocket API (v2) ---
resource "aws_apigatewayv2_api" "websocket" {
  name          = "websocket-api-gateway"
  protocol_type = "WEBSOCKET"
  route_selection_expression = "$request.body.action"
}

# WebSocket routes
resource "aws_apigatewayv2_route" "websocket_connect" {
  api_id    = aws_apigatewayv2_api.websocket.id
  route_key = "$connect"
  target    = "integrations/${aws_apigatewayv2_integration.websocket_connect.id}"
}

resource "aws_apigatewayv2_route" "websocket_disconnect" {
  api_id    = aws_apigatewayv2_api.websocket.id
  route_key = "$disconnect"
  target    = "integrations/${aws_apigatewayv2_integration.websocket_disconnect.id}"
}

resource "aws_apigatewayv2_route" "websocket_default" {
  api_id    = aws_apigatewayv2_api.websocket.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.websocket_default.id}"
}

# WebSocket integrations
resource "aws_apigatewayv2_integration" "websocket_connect" {
  api_id           = aws_apigatewayv2_api.websocket.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.websocket_register.invoke_arn
}

resource "aws_apigatewayv2_integration" "websocket_disconnect" {
  api_id           = aws_apigatewayv2_api.websocket.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.websocket_register.invoke_arn
}

resource "aws_apigatewayv2_integration" "websocket_default" {
  api_id           = aws_apigatewayv2_api.websocket.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.websocket_register.invoke_arn
}

# Lambda permissions for WebSocket API Gateway
resource "aws_lambda_permission" "websocket_connect" {
  statement_id  = "AllowExecutionFromWebSocketConnect"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.websocket_register.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.websocket.execution_arn}/*/*"
}

resource "aws_lambda_permission" "websocket_disconnect" {
  statement_id  = "AllowExecutionFromWebSocketDisconnect"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.websocket_register.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.websocket.execution_arn}/*/*"
}

resource "aws_lambda_permission" "websocket_default" {
  statement_id  = "AllowExecutionFromWebSocketDefault"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.websocket_register.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.websocket.execution_arn}/*/*"
}

# WebSocket API Gateway deployment and stage
resource "aws_apigatewayv2_stage" "websocket" {
  api_id = aws_apigatewayv2_api.websocket.id
  name   = "prod"
  auto_deploy = true
} 