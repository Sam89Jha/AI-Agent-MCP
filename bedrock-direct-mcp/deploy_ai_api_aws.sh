#!/bin/bash

# AI API Deployment Script for AWS
# This script deploys the AI Intent API to AWS

set -e

echo "🚀 Starting AI API deployment to AWS..."

# Configuration
APP_NAME="ai-intent-api"
ENVIRONMENT_NAME="ai-intent-api-env"
REGION="us-west-2"
PLATFORM="Python 3.9"

# Create deployment directory
DEPLOY_DIR="ai-api-deploy"
rm -rf $DEPLOY_DIR
mkdir -p $DEPLOY_DIR

echo "📦 Preparing deployment package..."

# Copy necessary files
cp ai_intent_api.py $DEPLOY_DIR/
cp requirements_ai_intent.txt $DEPLOY_DIR/requirements.txt

# Create Procfile for Elastic Beanstalk
cat > $DEPLOY_DIR/Procfile << EOF
web: uvicorn ai_intent_api:app --host 0.0.0.0 --port \$PORT
EOF

# Create .ebextensions for environment variables
mkdir -p $DEPLOY_DIR/.ebextensions
cat > $DEPLOY_DIR/.ebextensions/env.config << EOF
option_settings:
  aws:elasticbeanstalk:application:environment:
    MCP_SERVER_URL: "http://mcp-server-env.eba-r23dy2pd.us-west-2.elasticbeanstalk.com"
    AWS_REGION: "us-east-1"
EOF

# Create .ebignore to exclude unnecessary files
cat > $DEPLOY_DIR/.ebignore << EOF
*.pyc
__pycache__/
*.log
.env
.git/
.terraform/
*.tfstate*
test_*.py
deploy_*.sh
README.md
EOF

echo "🔧 Initializing Elastic Beanstalk application..."

# Initialize EB application (if not exists)
cd $DEPLOY_DIR

# Check if EB CLI is installed
if ! command -v eb &> /dev/null; then
    echo "❌ EB CLI not found. Please install it first:"
    echo "   pip install awsebcli"
    exit 1
fi

# Initialize EB application
if [ ! -f .elasticbeanstalk/config.yml ]; then
    echo "📝 Initializing new EB application..."
    eb init $APP_NAME --platform "$PLATFORM" --region $REGION --source codecommit/default
else
    echo "📝 Using existing EB configuration..."
fi

# Create environment if it doesn't exist
echo "🌍 Creating/updating EB environment..."
if ! eb status $ENVIRONMENT_NAME &> /dev/null; then
    echo "Creating new environment: $ENVIRONMENT_NAME"
    eb create $ENVIRONMENT_NAME --elb-type application --instance-type t3.micro
else
    echo "Environment $ENVIRONMENT_NAME already exists, deploying updates..."
fi

# Deploy the application
echo "🚀 Deploying to Elastic Beanstalk..."
eb deploy $ENVIRONMENT_NAME

# Get the application URL
echo "📋 Getting application URL..."
APP_URL=$(eb status $ENVIRONMENT_NAME --output json | grep -o '"CNAME": "[^"]*"' | cut -d'"' -f4)

if [ -n "$APP_URL" ]; then
    echo "✅ Deployment successful!"
    echo "🌐 Application URL: http://$APP_URL"
    echo "📊 Health check: http://$APP_URL/health"
    echo "📚 API docs: http://$APP_URL/docs"
    
    # Test the deployment
    echo "🧪 Testing deployment..."
    sleep 30  # Wait for deployment to complete
    
    if curl -f http://$APP_URL/health &> /dev/null; then
        echo "✅ Health check passed!"
    else
        echo "⚠️  Health check failed. Check the logs:"
        echo "   eb logs $ENVIRONMENT_NAME"
    fi
else
    echo "❌ Failed to get application URL"
    echo "Check the deployment status:"
    echo "   eb status $ENVIRONMENT_NAME"
fi

echo "🎉 AI API deployment completed!"
echo ""
echo "Next steps:"
echo "1. Update the MCP server to use the new AI API URL"
echo "2. Test the full integration"
echo "3. Configure Bedrock Agent to use the new AI API" 