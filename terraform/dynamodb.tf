# DynamoDB Tables for NavieTakieSimulation

# Messages table
resource "aws_dynamodb_table" "messages" {
  name           = "${var.project_name}-messages-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "booking_code"
  range_key      = "timestamp"

  attribute {
    name = "booking_code"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# WebSocket connections table
resource "aws_dynamodb_table" "connections" {
  name           = "${var.project_name}-connections-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "connection_id"

  attribute {
    name = "connection_id"
    type = "S"
  }

  # Global Secondary Index for booking_code queries
  global_secondary_index {
    name            = "booking_code-index"
    hash_key        = "booking_code"
    projection_type = "ALL"
  }

  attribute {
    name = "booking_code"
    type = "S"
  }

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# Call logs table
resource "aws_dynamodb_table" "calls" {
  name           = "${var.project_name}-calls-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "booking_code"
  range_key      = "timestamp"

  attribute {
    name = "booking_code"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
} 