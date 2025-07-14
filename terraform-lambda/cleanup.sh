#!/bin/bash

# Terraform cleanup script
# This script safely removes all resources

set -e

echo "🧹 Starting Terraform cleanup..."

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

echo "✅ AWS credentials configured"

# Show what will be destroyed
echo "📋 Planning destruction..."
terraform plan -destroy -out=tfplan-destroy

# Ask for confirmation
echo ""
echo "⚠️  WARNING: This will destroy ALL resources including:"
echo "   - Lambda functions"
echo "   - API Gateway endpoints"
echo "   - DynamoDB tables (and all data)"
echo "   - CloudWatch log groups"
echo ""
echo "🔍 Review the plan above. Do you want to destroy? (y/N)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "🗑️  Destroying resources..."
    terraform apply tfplan-destroy
    
    echo ""
    echo "✅ Cleanup completed!"
    
else
    echo "❌ Cleanup cancelled"
    exit 1
fi 