variable "aws_region" {
  description = "AWS region to deploy resources in"
  type        = string
  default     = "us-east-1"
}

variable "ec2_key_name" {
  description = "Name of the EC2 key pair to use for SSH access"
  type        = string
  default     = "mcp-server-key"
} 