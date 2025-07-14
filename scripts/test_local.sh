#!/bin/bash

# Local Testing Script for NavieTakie Simulation
# This script tests the complete system locally with local Lambda API handlers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
    
    # Check if Python is installed
    if ! command -v python3 &> /dev/null; then
        error "Python3 is not installed. Please install it first."
    fi
    
    # Check if pip is installed
    if ! command -v pip3 &> /dev/null; then
        error "pip3 is not installed. Please install it first."
    fi
    
    # Check if Node.js is installed
    if ! command -v node &> /dev/null; then
        error "Node.js is not installed. Please install it first."
    fi
    
    success "All prerequisites are met!"
}

# Setup virtual environment
setup_environment() {
    log "Setting up Python virtual environment..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    pip install -r mcp-server/requirements.txt
    pip install -r lambda-functions/requirements.txt
    
    success "Virtual environment setup complete!"
}

# Start MCP Server
start_mcp_server() {
    log "Starting MCP Server with local Lambda handlers..."
    
    # Set environment to local
    export ENVIRONMENT=local
    
    # Start MCP server
    cd mcp-server
    python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload &
    MCP_PID=$!
    cd ..
    
    # Wait for server to start
    sleep 3
    
    # Test server health
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        success "MCP Server is running on http://localhost:8000"
    else
        error "MCP Server failed to start"
    fi
}

# Test API endpoints
test_api_endpoints() {
    log "Testing API endpoints..."
    
    # Test send message
    log "Testing send message endpoint..."
    curl -X POST "http://localhost:8000/api/v1/send_message" \
        -H "Content-Type: application/json" \
        -d '{
            "booking_code": "TEST123",
            "message": "Hello from local test!",
            "sender": "driver",
            "message_type": "text"
        }'
    echo ""
    
    # Test make call
    log "Testing make call endpoint..."
    curl -X POST "http://localhost:8000/api/v1/make_call" \
        -H "Content-Type: application/json" \
        -d '{
            "booking_code": "TEST123",
            "caller_type": "driver",
            "call_type": "voice",
            "action": "initiate",
            "duration": 0
        }'
    echo ""
    
    # Test get messages
    log "Testing get messages endpoint..."
    curl -X GET "http://localhost:8000/api/v1/get_message/TEST123"
    echo ""
    
    success "API endpoints tested successfully!"
}

# Test AI Agent endpoint
test_ai_agent() {
    log "Testing AI Agent endpoint..."
    
    # Test send message intent
    curl -X POST "http://localhost:8000/api/v1/ai_agent" \
        -H "Content-Type: application/json" \
        -d '{
            "booking_code": "TEST123",
            "user_input": "Send message: Hello from AI agent!",
            "user_type": "driver"
        }'
    echo ""
    
    # Test make call intent
    curl -X POST "http://localhost:8000/api/v1/ai_agent" \
        -H "Content-Type: application/json" \
        -d '{
            "booking_code": "TEST123",
            "user_input": "Call the passenger",
            "user_type": "driver"
        }'
    echo ""
    
    success "AI Agent endpoint tested successfully!"
}

# Start frontend apps (optional)
start_frontend_apps() {
    log "Starting frontend applications..."
    
    # Start DAX app
    cd frontend/dax-app
    npm install
    npm start &
    DAX_PID=$!
    cd ../..
    
    # Start PAX app
    cd frontend/pax-app
    npm install
    npm start &
    PAX_PID=$!
    cd ../..
    
    success "Frontend apps started!"
    log "DAX App: http://localhost:3000"
    log "PAX App: http://localhost:3001"
}

# Show testing instructions
show_instructions() {
    echo ""
    echo "🎉 Local Testing Setup Complete!"
    echo "================================"
    echo ""
    echo "📡 MCP Server: http://localhost:8000"
    echo "📱 DAX App: http://localhost:3000"
    echo "📱 PAX App: http://localhost:3001"
    echo ""
    echo "🧪 Test the system:"
    echo "1. Open DAX app in browser"
    echo "2. Enter booking code: TEST123"
    echo "3. Send a message or make a call"
    echo "4. Open PAX app and connect with same booking code"
    echo "5. Watch real-time updates!"
    echo ""
    echo "🔧 API Testing:"
    echo "- Health check: curl http://localhost:8000/health"
    echo "- Send message: curl -X POST http://localhost:8000/api/v1/send_message"
    echo "- Make call: curl -X POST http://localhost:8000/api/v1/make_call"
    echo "- Get messages: curl http://localhost:8000/api/v1/get_message/TEST123"
    echo ""
    echo "🛑 To stop all services: Ctrl+C"
    echo ""
}

# Cleanup function
cleanup() {
    log "Cleaning up..."
    
    # Kill background processes
    if [ ! -z "$MCP_PID" ]; then
        kill $MCP_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$DAX_PID" ]; then
        kill $DAX_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$PAX_PID" ]; then
        kill $PAX_PID 2>/dev/null || true
    fi
    
    success "Cleanup complete!"
}

# Main function
main() {
    log "Starting local testing setup..."
    echo ""
    
    # Check prerequisites
    check_prerequisites
    
    # Setup environment
    setup_environment
    
    # Start MCP server
    start_mcp_server
    
    # Test API endpoints
    test_api_endpoints
    
    # Test AI Agent
    test_ai_agent
    
    # Start frontend apps (optional)
    read -p "Do you want to start frontend apps? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        start_frontend_apps
    fi
    
    # Show instructions
    show_instructions
    
    # Wait for user to stop
    echo "Press Ctrl+C to stop all services..."
    wait
}

# Trap cleanup on exit
trap cleanup EXIT

# Run main function
main "$@" 