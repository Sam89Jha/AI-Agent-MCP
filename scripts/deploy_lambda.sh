#!/bin/bash

# Deploy Lambda Functions Script
# Deploys individual Lambda functions to AWS using Terraform

set -e

echo "🚀 Deploying NavieTakieSimulation Lambda Functions"
echo "=================================================="

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform is not installed. Please install it first."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "terraform/main.tf" ]; then
    echo "❌ Please run this script from the project root directory."
    exit 1
fi

# Set environment variables
export TF_VAR_project_name="navietakie"
export TF_VAR_environment="production"
export TF_VAR_aws_region="us-east-1"

echo "🔧 Environment Configuration:"
echo "  Project Name: $TF_VAR_project_name"
echo "  Environment: $TF_VAR_environment"
echo "  AWS Region: $TF_VAR_aws_region"
echo ""

# Navigate to terraform directory
cd terraform

# Initialize Terraform
echo "📦 Initializing Terraform..."
terraform init

# Plan the deployment
echo "📋 Planning deployment..."
terraform plan -out=tfplan

# Ask for confirmation
echo ""
read -p "Do you want to apply this plan? (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled."
    exit 1
fi

# Apply the plan
echo "🚀 Applying Terraform plan..."
terraform apply tfplan

# Get outputs
echo ""
echo "✅ Lambda deployment completed successfully!"
echo ""
echo "📊 Deployment Outputs:"
echo "======================"
terraform output

# Clean up
rm -f tfplan

echo ""
echo "🎉 Lambda functions deployed successfully!"
echo ""
echo "📝 Deployed Functions:"
echo "  ✅ send-message: Send chat messages"
echo "  ✅ make-call: Handle call operations"
echo "  ✅ get-message: Retrieve messages"
echo "  ✅ websocket-handler: Handle WebSocket events"
echo ""
echo "🔗 Lambda Functions:"
echo "  send-message: Handler: send_message.lambda_handler"
echo "  make-call: Handler: make_call.lambda_handler"
echo "  get-message: Handler: get_message.lambda_handler"
echo "  websocket-handler: Handler: websocket_handler.lambda_handler"
echo ""
echo "💡 Next steps:"
echo "1. Deploy the MCP server to EC2"
echo "2. Deploy the frontend apps to S3"
echo "3. Test each Lambda function individually"
echo "4. Set up API Gateway to route to these functions" 