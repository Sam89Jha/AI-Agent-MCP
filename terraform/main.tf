# Main Terraform Configuration
# AI-Driven Chat & Voice Assistant Demo

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
  
  default_tags {
    tags = {
      Project     = "NavieTakieSimulation"
      Environment = "demo"
      ManagedBy   = "terraform"
    }
  }
}

# =============================================================================
# EC2 INSTANCE (MCP Server)
# =============================================================================

# Security Group for EC2
resource "aws_security_group" "mcp_server" {
  name        = "mcp-server-sg"
  description = "Security group for MCP server"
  vpc_id      = data.aws_vpc.default.id

  # SSH access
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTP access
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS access
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # All outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "mcp-server-sg"
  }
}

# EC2 Instance for MCP Server
resource "aws_instance" "mcp_server" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = "t3.micro"
  key_name               = var.ec2_key_name
  vpc_security_group_ids = [aws_security_group.mcp_server.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name

  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    region = var.aws_region
  }))

  root_block_device {
    volume_size = 8
    volume_type = "gp3"
    encrypted   = true
  }

  tags = {
    Name = "mcp-server"
  }
}

# Elastic IP for EC2
resource "aws_eip" "mcp_server" {
  instance = aws_instance.mcp_server.id
  domain   = "vpc"

  tags = {
    Name = "mcp-server-eip"
  }
}

# =============================================================================
# LAMBDA FUNCTIONS (Backend API)
# =============================================================================

# Lambda execution role
resource "aws_iam_role" "lambda_role" {
  name = "lambda_execution_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# DynamoDB access for Lambda
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
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem"
        ]
        Resource = aws_dynamodb_table.messages.arn
      }
    ]
  })
}

# CloudWatch Logs for Lambda
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda function for sending messages
resource "aws_lambda_function" "send_message" {
  filename         = data.archive_file.send_message_zip.output_path
  function_name    = "send-message"
  role            = aws_iam_role.lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.9"
  timeout         = 30
  memory_size     = 128

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.messages.name
      REGION         = var.aws_region
    }
  }

  tags = {
    Name = "send-message"
  }
}

# Lambda function for making calls
resource "aws_lambda_function" "make_call" {
  filename         = data.archive_file.make_call_zip.output_path
  function_name    = "make-call"
  role            = aws_iam_role.lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.9"
  timeout         = 30
  memory_size     = 128

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.messages.name
      REGION         = var.aws_region
    }
  }

  tags = {
    Name = "make-call"
  }
}

# Lambda function for getting messages
resource "aws_lambda_function" "get_message" {
  filename         = data.archive_file.get_message_zip.output_path
  function_name    = "get-message"
  role            = aws_iam_role.lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.9"
  timeout         = 30
  memory_size     = 128

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.messages.name
      REGION         = var.aws_region
    }
  }

  tags = {
    Name = "get-message"
  }
}

# =============================================================================
# DYNAMODB TABLE
# =============================================================================

resource "aws_dynamodb_table" "messages" {
  name           = "chat-messages"
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
    Name = "chat-messages"
  }
}

# =============================================================================
# S3 BUCKETS (Web Hosting)
# =============================================================================

# S3 bucket for DAX app
resource "aws_s3_bucket" "dax_app" {
  bucket = "dax-app-${random_string.bucket_suffix.result}"

  tags = {
    Name = "dax-app"
  }
}

# S3 bucket for PAX app
resource "aws_s3_bucket" "pax_app" {
  bucket = "pax-app-${random_string.bucket_suffix.result}"

  tags = {
    Name = "pax-app"
  }
}

# S3 bucket versioning
resource "aws_s3_bucket_versioning" "dax_app" {
  bucket = aws_s3_bucket.dax_app.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_versioning" "pax_app" {
  bucket = aws_s3_bucket.pax_app.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 bucket public access block
resource "aws_s3_bucket_public_access_block" "dax_app" {
  bucket = aws_s3_bucket.dax_app.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_public_access_block" "pax_app" {
  bucket = aws_s3_bucket.pax_app.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# S3 bucket website configuration
resource "aws_s3_bucket_website_configuration" "dax_app" {
  bucket = aws_s3_bucket.dax_app.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html"
  }
}

resource "aws_s3_bucket_website_configuration" "pax_app" {
  bucket = aws_s3_bucket.pax_app.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html"
  }
}

# S3 bucket policy for public read
resource "aws_s3_bucket_policy" "dax_app" {
  bucket = aws_s3_bucket.dax_app.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.dax_app.arn}/*"
      }
    ]
  })
}

resource "aws_s3_bucket_policy" "pax_app" {
  bucket = aws_s3_bucket.pax_app.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.pax_app.arn}/*"
      }
    ]
  })
}

# =============================================================================
# CLOUDFRONT DISTRIBUTIONS
# =============================================================================

# CloudFront distribution for DAX app
resource "aws_cloudfront_distribution" "dax_app" {
  origin {
    domain_name = aws_s3_bucket_website_configuration.dax_app.website_endpoint
    origin_id   = "S3-dax-app"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  enabled             = true
  is_ipv6_enabled    = true
  default_root_object = "index.html"
  price_class         = "PriceClass_100"

  aliases = ["dax.sameer-jha.com"]

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-dax-app"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }

  # Cache behavior for SPA routing
  ordered_cache_behavior {
    path_pattern     = "/*"
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-dax-app"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Name = "dax-app-distribution"
  }
}

# CloudFront distribution for PAX app
resource "aws_cloudfront_distribution" "pax_app" {
  origin {
    domain_name = aws_s3_bucket_website_configuration.pax_app.website_endpoint
    origin_id   = "S3-pax-app"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  enabled             = true
  is_ipv6_enabled    = true
  default_root_object = "index.html"
  price_class         = "PriceClass_100"

  aliases = ["pax.sameer-jha.com"]

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-pax-app"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }

  # Cache behavior for SPA routing
  ordered_cache_behavior {
    path_pattern     = "/*"
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-pax-app"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Name = "pax-app-distribution"
  }
}

# =============================================================================
# IAM ROLES AND POLICIES
# =============================================================================

# EC2 role for MCP server
resource "aws_iam_role" "ec2_role" {
  name = "ec2_mcp_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# Lambda invocation for EC2
resource "aws_iam_role_policy" "ec2_lambda" {
  name = "ec2_lambda_policy"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          aws_lambda_function.send_message.arn,
          aws_lambda_function.make_call.arn,
          aws_lambda_function.get_message.arn
        ]
      }
    ]
  })
}

# CloudWatch Logs for EC2
resource "aws_iam_role_policy_attachment" "ec2_logs" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
}

# EC2 instance profile
resource "aws_iam_instance_profile" "ec2_profile" {
  name = "ec2_mcp_profile"
  role = aws_iam_role.ec2_role.name
}

# =============================================================================
# CLOUDWATCH LOG GROUPS
# =============================================================================

# CloudWatch Log Groups for Lambda functions
resource "aws_cloudwatch_log_group" "lambda_logs" {
  for_each = toset([
    aws_lambda_function.send_message.function_name,
    aws_lambda_function.make_call.function_name,
    aws_lambda_function.get_message.function_name
  ])

  name              = "/aws/lambda/${each.value}"
  retention_in_days = 7

  tags = {
    Name = "${each.value}-logs"
  }
}

# =============================================================================
# DATA SOURCES
# =============================================================================

# Get default VPC
data "aws_vpc" "default" {
  default = true
}

# Get Amazon Linux 2023 AMI
data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Random string for bucket names
resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# Archive files for Lambda functions
data "archive_file" "send_message_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../backend/lambda-functions/send_message"
  output_path = "${path.module}/send_message.zip"
}

data "archive_file" "make_call_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../backend/lambda-functions/make_call"
  output_path = "${path.module}/make_call.zip"
}

data "archive_file" "get_message_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../backend/lambda-functions/get_message"
  output_path = "${path.module}/get_message.zip"
} 