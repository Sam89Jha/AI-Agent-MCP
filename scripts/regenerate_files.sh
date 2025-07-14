#!/bin/bash

# Regenerate Files Script
# Recreates necessary files and directories after clean repository push

set -e

echo "🔄 Regenerating NavieTakieSimulation Files"
echo "=========================================="

# Function to create directory if it doesn't exist
create_dir() {
    local dir="$1"
    if [ ! -d "$dir" ]; then
        echo "📁 Creating directory: $dir"
        mkdir -p "$dir"
    fi
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo "🐍 Setting up Python virtual environment..."

# Check if Python is installed
if ! command_exists python3; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r mcp-server/requirements.txt
pip install -r lambda-functions/requirements.txt

# Install development dependencies
echo "🧪 Installing development dependencies..."
pip install pytest pytest-asyncio

echo "📦 Setting up Node.js dependencies..."

# Check if Node.js is installed
if ! command_exists node; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if npm is installed
if ! command_exists npm; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

# Install DAX app dependencies
echo "📱 Installing DAX app dependencies..."
cd frontend/dax-app
if [ ! -d "node_modules" ]; then
    npm install
fi
cd ../..

# Install PAX app dependencies
echo "📱 Installing PAX app dependencies..."
cd frontend/pax-app
if [ ! -d "node_modules" ]; then
    npm install
fi
cd ../..

echo "☁️  Setting up AWS/Terraform..."

# Check if AWS CLI is installed
if ! command_exists aws; then
    echo "⚠️  AWS CLI is not installed. You'll need it for deployment."
    echo "   Install with: brew install awscli (macOS) or follow AWS docs"
fi

# Check if Terraform is installed
if ! command_exists terraform; then
    echo "⚠️  Terraform is not installed. You'll need it for deployment."
    echo "   Install with: brew install terraform (macOS) or follow HashiCorp docs"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
create_dir "logs"
create_dir "temp"
create_dir "tmp"

# Create .gitkeep files to preserve empty directories
touch logs/.gitkeep
touch temp/.gitkeep
touch tmp/.gitkeep

echo "🔧 Setting up environment files..."

# Create example environment file
if [ ! -f ".env.example" ]; then
    echo "📝 Creating .env.example file..."
    cat > .env.example << EOF
# Environment Configuration
ENVIRONMENT=local
AWS_REGION=us-east-1

# MCP Server Configuration
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8000

# Frontend Configuration
DAX_APP_PORT=3000
PAX_APP_PORT=3001

# AWS Configuration (for production)
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=us-east-1

# DynamoDB Tables (for production)
DYNAMODB_TABLE=navietakie-messages-production
CONNECTIONS_TABLE=navietakie-connections-production
CALLS_TABLE=navietakie-calls-production

# API Gateway URLs (for production)
API_GATEWAY_URL=https://your-api-id.execute-api.us-east-1.amazonaws.com/production
WEBSOCKET_API_GATEWAY_URL=wss://your-websocket-id.execute-api.us-east-1.amazonaws.com/production
EOF
fi

echo "📋 Creating local configuration..."

# Create local config file
if [ ! -f "local_config.py" ]; then
    echo "📝 Creating local_config.py file..."
    cat > local_config.py << EOF
"""
Local configuration for development
This file is ignored by git and can be customized for local development
"""

# Local development settings
LOCAL_DEBUG = True
LOCAL_LOG_LEVEL = "INFO"

# Local API endpoints
LOCAL_API_BASE_URL = "http://localhost:8000"
LOCAL_WEBSOCKET_URL = "ws://localhost:8000/ws"

# Local ports
LOCAL_MCP_SERVER_PORT = 8000
LOCAL_DAX_APP_PORT = 3000
LOCAL_PAX_APP_PORT = 3001

# Local database settings (for testing)
LOCAL_DYNAMODB_ENDPOINT = "http://localhost:8000"
LOCAL_DYNAMODB_TABLE = "local-messages"
LOCAL_CONNECTIONS_TABLE = "local-connections"
LOCAL_CALLS_TABLE = "local-calls"
EOF
fi

echo "📝 Creating log files..."

# Create log files
touch logs/app.log
touch logs/error.log
touch logs/access.log

echo ""
echo "✅ Files regenerated successfully!"
echo ""
echo "📋 Generated files and directories:"
echo "  - Python virtual environment (venv/)"
echo "  - Node.js dependencies (node_modules/)"
echo "  - Log directories (logs/, temp/, tmp/)"
echo "  - Environment example (.env.example)"
echo "  - Local configuration (local_config.py)"
echo ""
echo "🚀 You can now run the application:"
echo ""
echo "💻 For local development:"
echo "  ./scripts/test_local.sh"
echo ""
echo "☁️  For AWS deployment:"
echo "  ./scripts/deploy_lambda.sh"
echo ""
echo "📊 For status check:"
echo "  ./scripts/status.sh"
echo ""
echo "🎉 Setup complete! Your development environment is ready." 