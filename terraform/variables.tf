# Variables for AI-Driven Chat & Voice Assistant Demo

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "ec2_key_name" {
  description = "Name of the EC2 key pair for SSH access"
  type        = string
  default     = "demo-key"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "NavieTakieSimulation"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "demo"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 30
}

variable "lambda_memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 128
}

variable "dynamodb_billing_mode" {
  description = "DynamoDB billing mode"
  type        = string
  default     = "PAY_PER_REQUEST"
}

variable "cloudfront_price_class" {
  description = "CloudFront price class"
  type        = string
  default     = "PriceClass_100"
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
} 