# API Gateway for NavieTakieSimulation

# Main REST API Gateway
resource "aws_api_gateway_rest_api" "main" {
  name        = "${var.project_name}-api-${var.environment}"
  description = "API Gateway for NavieTakieSimulation Lambda functions"
}

# WebSocket API Gateway
resource "aws_api_gateway_rest_api" "websocket" {
  name        = "${var.project_name}-websocket-${var.environment}"
  description = "WebSocket API Gateway for NavieTakieSimulation"
  api_key_source = "HEADER"
}

# WebSocket API Gateway deployment
resource "aws_api_gateway_deployment" "websocket" {
  rest_api_id = aws_api_gateway_rest_api.websocket.id
  depends_on = [
    aws_api_gateway_integration.websocket_connect,
    aws_api_gateway_integration.websocket_disconnect,
    aws_api_gateway_integration.websocket_message
  ]
}

# WebSocket API Gateway stage
resource "aws_api_gateway_stage" "websocket" {
  deployment_id = aws_api_gateway_deployment.websocket.id
  rest_api_id   = aws_api_gateway_rest_api.websocket.id
  stage_name    = var.environment
}

# WebSocket $connect route
resource "aws_api_gateway_resource" "websocket_connect" {
  rest_api_id = aws_api_gateway_rest_api.websocket.id
  parent_id   = aws_api_gateway_rest_api.websocket.root_resource_id
  path_part   = "$connect"
}

resource "aws_api_gateway_method" "websocket_connect" {
  rest_api_id   = aws_api_gateway_rest_api.websocket.id
  resource_id   = aws_api_gateway_resource.websocket_connect.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "websocket_connect" {
  rest_api_id = aws_api_gateway_rest_api.websocket.id
  resource_id = aws_api_gateway_resource.websocket_connect.id
  http_method = aws_api_gateway_method.websocket_connect.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.main.invoke_arn
}

# WebSocket $disconnect route
resource "aws_api_gateway_resource" "websocket_disconnect" {
  rest_api_id = aws_api_gateway_rest_api.websocket.id
  parent_id   = aws_api_gateway_rest_api.websocket.root_resource_id
  path_part   = "$disconnect"
}

resource "aws_api_gateway_method" "websocket_disconnect" {
  rest_api_id   = aws_api_gateway_rest_api.websocket.id
  resource_id   = aws_api_gateway_resource.websocket_disconnect.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "websocket_disconnect" {
  rest_api_id = aws_api_gateway_rest_api.websocket.id
  resource_id = aws_api_gateway_resource.websocket_disconnect.id
  http_method = aws_api_gateway_method.websocket_disconnect.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.main.invoke_arn
}

# WebSocket message route
resource "aws_api_gateway_resource" "websocket_message" {
  rest_api_id = aws_api_gateway_rest_api.websocket.id
  parent_id   = aws_api_gateway_rest_api.websocket.root_resource_id
  path_part   = "$default"
}

resource "aws_api_gateway_method" "websocket_message" {
  rest_api_id   = aws_api_gateway_rest_api.websocket.id
  resource_id   = aws_api_gateway_resource.websocket_message.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "websocket_message" {
  rest_api_id = aws_api_gateway_rest_api.websocket.id
  resource_id = aws_api_gateway_resource.websocket_message.id
  http_method = aws_api_gateway_method.websocket_message.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.main.invoke_arn
}

# Main API Gateway deployment
resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  depends_on = [
    aws_api_gateway_integration.send_message,
    aws_api_gateway_integration.make_call,
    aws_api_gateway_integration.get_message
  ]
}

# Main API Gateway stage
resource "aws_api_gateway_stage" "main" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = var.environment
}

# API Gateway resources and methods for Lambda functions
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

# Send message endpoint
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
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.send_message.id
  http_method = aws_api_gateway_method.send_message.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.main.invoke_arn
}

# Make call endpoint
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
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.make_call.id
  http_method = aws_api_gateway_method.make_call.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.main.invoke_arn
}

# Get message endpoint
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
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.get_message.id
  http_method = aws_api_gateway_method.get_message.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.main.invoke_arn
} 