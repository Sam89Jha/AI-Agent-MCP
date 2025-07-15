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
  region = "us-east-1"
}

# S3 bucket for OpenAPI schemas
resource "aws_s3_bucket" "bedrock_schemas" {
  bucket = "bedrock-agent-schemas-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_versioning" "bedrock_schemas" {
  bucket = aws_s3_bucket.bedrock_schemas.id
  versioning_configuration {
    status = "Enabled"
  }
}

# IAM role for Bedrock Agent
resource "aws_iam_role" "bedrock_agent_role" {
  name = "bedrock-agent-role-direct"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
      }
    ]
  })
}

# Attach Bedrock permissions
resource "aws_iam_role_policy_attachment" "bedrock_full_access" {
  role       = aws_iam_role.bedrock_agent_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonBedrockFullAccess"
}

# Create OpenAPI schemas for MCP endpoints
locals {
  mcp_server_url = "http://mcp-server-env.eba-r23dy2pd.us-west-2.elasticbeanstalk.com"
}

# Send Message API Schema
resource "aws_s3_object" "send_message_schema" {
  bucket = aws_s3_bucket.bedrock_schemas.id
  key    = "send_message_schema.json"
  content = jsonencode({
    openapi = "3.0.0"
    info = {
      title   = "Send Message API"
      version = "1.0.0"
    }
    servers = [
      {
        url = local.mcp_server_url
      }
    ]
    paths = {
      "/api/v1/send_message" = {
        post = {
          summary     = "Send a message"
          description = "Send a message between driver and passenger"
          requestBody = {
            required = true
            content = {
              "application/json" = {
                schema = {
                  type = "object"
                  properties = {
                    booking_code = {
                      type = "string"
                      description = "Booking code for the trip"
                    }
                    from_user = {
                      type = "string"
                      description = "User type (driver or passenger)"
                    }
                    to_user = {
                      type = "string"
                      description = "User type to send message to"
                    }
                    message = {
                      type = "string"
                      description = "Message content"
                    }
                  }
                  required = ["booking_code", "from_user", "to_user", "message"]
                }
              }
            }
          }
          responses = {
            "200" = {
              description = "Message sent successfully"
              content = {
                "application/json" = {
                  schema = {
                    type = "object"
                    properties = {
                      success = {
                        type = "boolean"
                      }
                      message = {
                        type = "string"
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  })
}

# Make Call API Schema
resource "aws_s3_object" "make_call_schema" {
  bucket = aws_s3_bucket.bedrock_schemas.id
  key    = "make_call_schema.json"
  content = jsonencode({
    openapi = "3.0.0"
    info = {
      title   = "Make Call API"
      version = "1.0.0"
    }
    servers = [
      {
        url = local.mcp_server_url
      }
    ]
    paths = {
      "/api/v1/make_call" = {
        post = {
          summary     = "Make a call"
          description = "Initiate a voice call between driver and passenger"
          requestBody = {
            required = true
            content = {
              "application/json" = {
                schema = {
                  type = "object"
                  properties = {
                    booking_code = {
                      type = "string"
                      description = "Booking code for the trip"
                    }
                    from_user = {
                      type = "string"
                      description = "User type initiating the call"
                    }
                    to_user = {
                      type = "string"
                      description = "User type to call"
                    }
                  }
                  required = ["booking_code", "from_user", "to_user"]
                }
              }
            }
          }
          responses = {
            "200" = {
              description = "Call initiated successfully"
              content = {
                "application/json" = {
                  schema = {
                    type = "object"
                    properties = {
                      success = {
                        type = "boolean"
                      }
                      message = {
                        type = "string"
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  })
}

# Get Messages API Schema
resource "aws_s3_object" "get_messages_schema" {
  bucket = aws_s3_bucket.bedrock_schemas.id
  key    = "get_messages_schema.json"
  content = jsonencode({
    openapi = "3.0.0"
    info = {
      title   = "Get Messages API"
      version = "1.0.0"
    }
    servers = [
      {
        url = local.mcp_server_url
      }
    ]
    paths = {
      "/api/v1/get_message/{booking_code}" = {
        get = {
          summary     = "Get messages"
          description = "Retrieve conversation history for a booking"
          parameters = [
            {
              name        = "booking_code"
              in          = "path"
              required    = true
              description = "Booking code for the trip"
              schema = {
                type = "string"
              }
            }
          ]
          responses = {
            "200" = {
              description = "Messages retrieved successfully"
              content = {
                "application/json" = {
                  schema = {
                    type = "object"
                    properties = {
                      success = {
                        type = "boolean"
                      }
                      messages = {
                        type = "array"
                        items = {
                          type = "object"
                          properties = {
                            id = {
                              type = "string"
                            }
                            booking_code = {
                              type = "string"
                            }
                            from_user = {
                              type = "string"
                            }
                            to_user = {
                              type = "string"
                            }
                            message = {
                              type = "string"
                            }
                            timestamp = {
                              type = "string"
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  })
}

# Bedrock Agent
resource "aws_bedrock_agent" "agent" {
  agent_name              = "driver-assistant-direct"
  description             = "AI Agent for driver-passenger communication with direct MCP integration"
  instruction             = "You are an AI assistant that helps drivers and passengers communicate. You can send messages, make calls, and retrieve conversation history by calling the MCP server APIs directly."
  agent_resource_role_arn = aws_iam_role.bedrock_agent_role.arn
  foundation_model        = "anthropic.claude-3-sonnet-20240229-v1:0"
}

# Bedrock Agent Alias
resource "aws_bedrock_agent_alias" "agent_alias" {
  agent_id           = aws_bedrock_agent.agent.id
  agent_alias_name   = "driver-assistant-direct-alias"
  description        = "Production alias for driver assistant agent with direct MCP integration"
  routing_configuration {
    agent_version = aws_bedrock_agent.agent.agent_version
  }
}

# Data source for current account
data "aws_caller_identity" "current" {}

# Outputs
output "s3_bucket_name" {
  value = aws_s3_bucket.bedrock_schemas.bucket
}

output "iam_role_arn" {
  value = aws_iam_role.bedrock_agent_role.arn
}

output "mcp_server_url" {
  value = local.mcp_server_url
}

output "agent_id" {
  value = aws_bedrock_agent.agent.id
}

output "alias_id" {
  value = aws_bedrock_agent_alias.agent_alias.id
} 