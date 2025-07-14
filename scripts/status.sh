#!/bin/bash

# Status Check Script
# Shows the status of all components in the local environment

echo "🔍 NavieTakieSimulation Component Status"
echo "========================================"

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Function to check component status
check_component() {
    local name=$1
    local port=$2
    local url=$3
    
    if check_port $port; then
        echo "✅ $name: Running on $url"
        return 0
    else
        echo "❌ $name: Not running (port $port)"
        return 1
    fi
}

echo "🔧 Environment: ${ENVIRONMENT:-local}"
echo ""

# Check MCP Server
echo "1. MCP Server (Backend API):"
check_component "MCP Server" 8000 "http://localhost:8000"
if check_port 8000; then
    echo "   📖 API Docs: http://localhost:8000/docs"
    echo "   🏥 Health: http://localhost:8000/health"
fi

echo ""

# Check DAX App
echo "2. DAX App (Driver Interface):"
check_component "DAX App" 3000 "http://localhost:3000"

echo ""

# Check PAX App
echo "3. PAX App (Passenger Interface):"
check_component "PAX App" 3001 "http://localhost:3001"

echo ""

# Lambda API Status
echo "4. Lambda APIs:"
echo "   📋 send_message: Simulated in MCP Server (local handlers)"
echo "   📋 make_call: Simulated in MCP Server (local handlers)"
echo "   📋 get_message: Simulated in MCP Server (local handlers)"
echo "   📋 websocket_handler: Integrated in MCP Server"
echo "   💡 Note: Lambda functions run on AWS in production"

echo ""

# Environment Variables
echo "5. Environment Configuration:"
echo "   🌐 API Base URL: ${REACT_APP_API_BASE_URL:-http://localhost:8000}"
echo "   🔌 WebSocket URL: ${REACT_APP_WEBSOCKET_URL:-ws://localhost:8000/ws}"
echo "   🔧 Environment: ${ENVIRONMENT:-local}"

echo ""

# Quick test
echo "6. Quick Health Check:"
if check_port 8000; then
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "   ✅ MCP Server is responding"
    else
        echo "   ⚠️  MCP Server is running but not responding"
    fi
else
    echo "   ❌ MCP Server is not running"
fi

echo ""
echo "🎯 Summary:"
echo "   - MCP Server: Backend API orchestrator (port 8000)"
echo "   - DAX App: Driver interface (port 3000)"
echo "   - PAX App: Passenger interface (port 3001)"
echo "   - Lambda APIs: Simulated locally, run on AWS in production" 