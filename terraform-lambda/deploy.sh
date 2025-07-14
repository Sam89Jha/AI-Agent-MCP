#!/bin/bash

# Terraform deployment script for Lambda functions
# This script handles existing resources gracefully

set -e

echo "🚀 Starting Terraform deployment..."

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

echo "✅ AWS credentials configured"

# Initialize Terraform
echo "📦 Initializing Terraform..."
terraform init

# Plan the deployment
echo "📋 Planning deployment..."
terraform plan -out=tfplan

# Ask for confirmation
echo ""
echo "🔍 Review the plan above. Do you want to apply? (y/N)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "🚀 Applying Terraform configuration..."
    terraform apply tfplan
    
    echo ""
    echo "✅ Deployment completed!"
    echo ""
    echo "📊 Outputs:"
    terraform output
    
    echo ""
    echo "🔗 API Gateway URLs:"
    echo "HTTP API: $(terraform output -raw api_gateway_invoke_url)"
    echo "WebSocket API: $(terraform output -raw websocket_api_gateway_url)"
    
    echo ""
    echo "📋 DynamoDB Tables:"
    echo "Messages: $(terraform output -raw dynamodb_messages_table)"
    echo "Calls: $(terraform output -raw dynamodb_calls_table)"
    echo "Connections: $(terraform output -raw dynamodb_connections_table)"
    
else
    echo "❌ Deployment cancelled"
    exit 1
fi 