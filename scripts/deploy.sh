#!/bin/bash

# NavieTakie Simulation Deployment Script
# This script deploys the complete system to AWS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="navietakie"
REGION="us-east-1"
DOMAIN="sameer-jha.com"
DAX_SUBDOMAIN="dax"
PAX_SUBDOMAIN="pax"
MCP_SUBDOMAIN="mcp"

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        error "AWS CLI is not installed. Please install it first."
    fi
    
    # Check if Terraform is installed
    if ! command -v terraform &> /dev/null; then
        error "Terraform is not installed. Please install it first."
    fi
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install it first."
    fi
    
    # Check if Node.js is installed
    if ! command -v node &> /dev/null; then
        error "Node.js is not installed. Please install it first."
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS credentials not configured. Please run 'aws configure' first."
    fi
    
    success "All prerequisites are met!"
}

# Build frontend applications
build_frontend() {
    log "Building frontend applications..."
    
    # Build DAX app
    log "Building DAX app..."
    cd frontend/dax-app
    npm install
    npm run build
    cd ../..
    
    # Build PAX app
    log "Building PAX app..."
    cd frontend/pax-app
    npm install
    npm run build
    cd ../..
    
    success "Frontend applications built successfully!"
}

# Deploy infrastructure with Terraform
deploy_infrastructure() {
    log "Deploying infrastructure with Terraform..."
    
    cd terraform
    
    # Initialize Terraform
    log "Initializing Terraform..."
    terraform init
    
    # Plan deployment
    log "Planning deployment..."
    terraform plan -var="project_name=$PROJECT_NAME" \
                   -var="region=$REGION" \
                   -var="domain=$DOMAIN" \
                   -var="dax_subdomain=$DAX_SUBDOMAIN" \
                   -var="pax_subdomain=$PAX_SUBDOMAIN" \
                   -var="mcp_subdomain=$MCP_SUBDOMAIN" \
                   -out=tfplan
    
    # Ask for confirmation
    echo
    read -p "Do you want to proceed with the deployment? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Deployment cancelled by user."
        exit 0
    fi
    
    # Apply deployment
    log "Applying Terraform configuration..."
    terraform apply tfplan
    
    # Get outputs
    log "Getting deployment outputs..."
    terraform output -json > ../deployment-outputs.json
    
    cd ..
    
    success "Infrastructure deployed successfully!"
}

# Deploy Lambda functions
deploy_lambda_functions() {
    log "Deploying Lambda functions..."
    
    # Create deployment package for each function
    for func in send_message make_call get_message; do
        log "Deploying $func function..."
        
        cd lambda-functions
        
        # Create deployment package
        zip -r "../$func.zip" "$func.py" requirements.txt
        
        # Deploy to AWS Lambda
        aws lambda update-function-code \
            --function-name "$func" \
            --zip-file "fileb://../$func.zip" \
            --region "$REGION"
        
        # Update function configuration
        aws lambda update-function-configuration \
            --function-name "$func" \
            --timeout 30 \
            --memory-size 128 \
            --region "$REGION"
        
        cd ..
        
        # Clean up
        rm "$func.zip"
    done
    
    success "Lambda functions deployed successfully!"
}

# Deploy MCP Server to EC2
deploy_mcp_server() {
    log "Deploying MCP Server to EC2..."
    
    # Get EC2 instance ID from Terraform outputs
    EC2_INSTANCE_ID=$(jq -r '.ec2_instance_id.value' deployment-outputs.json)
    
    if [ "$EC2_INSTANCE_ID" = "null" ]; then
        error "EC2 instance ID not found in Terraform outputs"
    fi
    
    # Wait for EC2 instance to be ready
    log "Waiting for EC2 instance to be ready..."
    aws ec2 wait instance-running --instance-ids "$EC2_INSTANCE_ID"
    
    # Get instance public IP
    EC2_PUBLIC_IP=$(aws ec2 describe-instances \
        --instance-ids "$EC2_INSTANCE_ID" \
        --query 'Reservations[0].Instances[0].PublicIpAddress' \
        --output text)
    
    log "EC2 instance IP: $EC2_PUBLIC_IP"
    
    # Wait for SSH to be available
    log "Waiting for SSH to be available..."
    while ! nc -z "$EC2_PUBLIC_IP" 22; do
        sleep 5
    done
    
    # Copy MCP server files to EC2
    log "Copying MCP server files to EC2..."
    scp -o StrictHostKeyChecking=no -r mcp-server/* "ubuntu@$EC2_PUBLIC_IP:/home/ubuntu/mcp-server/"
    
    # Deploy MCP server on EC2
    ssh -o StrictHostKeyChecking=no "ubuntu@$EC2_PUBLIC_IP" << 'EOF'
        cd /home/ubuntu/mcp-server
        
        # Install Docker if not already installed
        if ! command -v docker &> /dev/null; then
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo usermod -aG docker $USER
        fi
        
        # Build and run MCP server
        docker build -t mcp-server .
        docker stop mcp-server || true
        docker rm mcp-server || true
        docker run -d \
            --name mcp-server \
            --restart unless-stopped \
            -p 8000:8000 \
            -e AWS_REGION=us-east-1 \
            mcp-server
EOF
    
    success "MCP Server deployed successfully!"
}

# Deploy frontend applications to S3
deploy_frontend() {
    log "Deploying frontend applications to S3..."
    
    # Get S3 bucket names from Terraform outputs
    DAX_BUCKET=$(jq -r '.dax_bucket_name.value' deployment-outputs.json)
    PAX_BUCKET=$(jq -r '.pax_bucket_name.value' deployment-outputs.json)
    
    if [ "$DAX_BUCKET" = "null" ] || [ "$PAX_BUCKET" = "null" ]; then
        error "S3 bucket names not found in Terraform outputs"
    fi
    
    # Deploy DAX app
    log "Deploying DAX app to S3..."
    aws s3 sync frontend/dax-app/build/ "s3://$DAX_BUCKET" --delete
    
    # Deploy PAX app
    log "Deploying PAX app to S3..."
    aws s3 sync frontend/pax-app/build/ "s3://$PAX_BUCKET" --delete
    
    success "Frontend applications deployed successfully!"
}

# Configure CloudFront distributions
configure_cloudfront() {
    log "Configuring CloudFront distributions..."
    
    # Get CloudFront distribution IDs from Terraform outputs
    DAX_DISTRIBUTION_ID=$(jq -r '.dax_cloudfront_distribution_id.value' deployment-outputs.json)
    PAX_DISTRIBUTION_ID=$(jq -r '.pax_cloudfront_distribution_id.value' deployment-outputs.json)
    
    if [ "$DAX_DISTRIBUTION_ID" = "null" ] || [ "$PAX_DISTRIBUTION_ID" = "null" ]; then
        error "CloudFront distribution IDs not found in Terraform outputs"
    fi
    
    # Create CloudFront invalidation for DAX
    log "Creating CloudFront invalidation for DAX..."
    aws cloudfront create-invalidation \
        --distribution-id "$DAX_DISTRIBUTION_ID" \
        --paths "/*"
    
    # Create CloudFront invalidation for PAX
    log "Creating CloudFront invalidation for PAX..."
    aws cloudfront create-invalidation \
        --distribution-id "$PAX_DISTRIBUTION_ID" \
        --paths "/*"
    
    success "CloudFront distributions configured successfully!"
}

# Run health checks
run_health_checks() {
    log "Running health checks..."
    
    # Get URLs from Terraform outputs
    DAX_URL=$(jq -r '.dax_url.value' deployment-outputs.json)
    PAX_URL=$(jq -r '.pax_url.value' deployment-outputs.json)
    MCP_URL=$(jq -r '.mcp_url.value' deployment-outputs.json)
    
    if [ "$DAX_URL" = "null" ] || [ "$PAX_URL" = "null" ] || [ "$MCP_URL" = "null" ]; then
        error "URLs not found in Terraform outputs"
    fi
    
    # Test MCP Server health
    log "Testing MCP Server health..."
    if curl -f "$MCP_URL/health" > /dev/null 2>&1; then
        success "MCP Server is healthy!"
    else
        warning "MCP Server health check failed"
    fi
    
    # Test DAX app
    log "Testing DAX app..."
    if curl -f "$DAX_URL" > /dev/null 2>&1; then
        success "DAX app is accessible!"
    else
        warning "DAX app accessibility check failed"
    fi
    
    # Test PAX app
    log "Testing PAX app..."
    if curl -f "$PAX_URL" > /dev/null 2>&1; then
        success "PAX app is accessible!"
    else
        warning "PAX app accessibility check failed"
    fi
    
    success "Health checks completed!"
}

# Display deployment summary
display_summary() {
    log "Deployment Summary:"
    echo
    
    # Read URLs from Terraform outputs
    DAX_URL=$(jq -r '.dax_url.value' deployment-outputs.json)
    PAX_URL=$(jq -r '.pax_url.value' deployment-outputs.json)
    MCP_URL=$(jq -r '.mcp_url.value' deployment-outputs.json)
    
    echo "🌐 Application URLs:"
    echo "   DAX (Driver): $DAX_URL"
    echo "   PAX (Passenger): $PAX_URL"
    echo "   MCP Server: $MCP_URL"
    echo
    
    echo "📊 Estimated Costs:"
    echo "   EC2 (t3.micro): ~$8.47/month"
    echo "   Lambda: ~$0.50/month"
    echo "   DynamoDB: ~$1.00/month"
    echo "   S3 + CloudFront: ~$0.50/month"
    echo "   Total: ~$10.47/month"
    echo
    
    echo "🔧 Next Steps:"
    echo "   1. Configure DNS records for your domain"
    echo "   2. Set up SSL certificates"
    echo "   3. Configure Bedrock Agent"
    echo "   4. Test the complete system"
    echo
    
    success "Deployment completed successfully!"
}

# Main deployment function
main() {
    log "Starting NavieTakie Simulation deployment..."
    echo
    
    # Check prerequisites
    check_prerequisites
    
    # Build frontend applications
    build_frontend
    
    # Deploy infrastructure
    deploy_infrastructure
    
    # Deploy Lambda functions
    deploy_lambda_functions
    
    # Deploy MCP Server
    deploy_mcp_server
    
    # Deploy frontend applications
    deploy_frontend
    
    # Configure CloudFront
    configure_cloudfront
    
    # Run health checks
    run_health_checks
    
    # Display summary
    display_summary
}

# Run main function
main "$@" 