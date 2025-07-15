#!/bin/bash

echo "🚀 Deploying AI Intent API..."

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements_ai_intent.txt

# Test direct Bedrock integration
echo "🧪 Testing Bedrock integration..."
python -c "
import boto3
import json
try:
    bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    print('✅ Bedrock client initialized successfully')
except Exception as e:
    print(f'❌ Bedrock error: {str(e)}')
"

echo ""
echo "✅ AI Intent API is ready!"
echo ""
echo "🔧 To run the server:"
echo "python ai_intent_api.py"
echo ""
echo "🧪 To test the API:"
echo "python test_ai_intent.py"
echo ""
echo "📋 Available endpoints:"
echo "- GET  / - Root endpoint with info"
echo "- POST /detect_intent - Detect intent and call MCP server"
echo "- GET  /health - Health check"
echo "- GET  /test - Test intent detection with sample inputs"
echo ""
echo "🌐 The server will run on http://localhost:8000"
echo "📖 API docs will be available at http://localhost:8000/docs"
echo ""
echo "📝 Example API call:"
echo 'curl -X POST "http://localhost:8000/detect_intent" \\'
echo '  -H "Content-Type: application/json" \\'
echo '  -d '"'"'{"booking_code": "12345", "user_type": "driver", "user_input": "Send a message to the passenger saying I will be there in 5 minutes"}'"'"'' 