#!/bin/bash

echo "🚀 Deploying Simple AI Agent..."

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements_simple_ai.txt

# Test the agent locally first
echo "🧪 Testing agent locally..."
python simple_ai_agent.py

echo ""
echo "✅ Simple AI Agent is ready!"
echo ""
echo "🔧 To run the server:"
echo "python simple_ai_server.py"
echo ""
echo "🧪 To test the agent:"
echo "python test_simple_ai.py"
echo ""
echo "📋 Available endpoints:"
echo "- GET  / - Root endpoint with info"
echo "- POST /chat - Send message to AI agent"
echo "- GET  /health - Health check"
echo "- GET  /test - Test agent with sample inputs"
echo ""
echo "🌐 The server will run on http://localhost:8000"
echo "📖 API docs will be available at http://localhost:8000/docs" 