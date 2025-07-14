#!/bin/bash

# Start Local Environment Script
# Starts all components for local development

set -e

echo "🚀 Starting NavieTakieSimulation Local Environment"
echo "=================================================="

# Set environment
export ENVIRONMENT=local
export REACT_APP_ENVIRONMENT=local

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  Port $1 is already in use"
        return 1
    else
        return 0
    fi
}

# Function to start component
start_component() {
    local name=$1
    local port=$2
    local command=$3
    
    echo "Starting $name on port $port..."
    if check_port $port; then
        $command &
        echo "✅ $name started on port $port"
    else
        echo "❌ Failed to start $name - port $port is busy"
        return 1
    fi
}

# Check if we're in the right directory
if [ ! -f "config.py" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

echo "🔧 Environment: $ENVIRONMENT"
echo ""

# Start MCP Server
echo "1. Starting MCP Server..."
cd mcp-server
if check_port 8000; then
    echo "   Starting MCP Server on http://localhost:8000"
    uvicorn app:app --host 0.0.0.0 --port 8000 --reload &
    MCP_PID=$!
    echo "   ✅ MCP Server started (PID: $MCP_PID)"
    echo "   📖 API Docs: http://localhost:8000/docs"
else
    echo "   ❌ Port 8000 is busy"
    exit 1
fi
cd ..

# Wait a moment for MCP server to start
sleep 3

# Start DAX App
echo ""
echo "2. Starting DAX App..."
cd frontend/dax-app
if check_port 3001; then
    echo "   Starting DAX App on http://localhost:3001"
    PORT=3001 npm start &
    DAX_PID=$!
    echo "   ✅ DAX App started (PID: $DAX_PID)"
else
    echo "   ❌ Port 3001 is busy"
    exit 1
fi
cd ../..

# Start PAX App
echo ""
echo "3. Starting PAX App..."
cd frontend/pax-app
if check_port 3002; then
    echo "   Starting PAX App on http://localhost:3002"
    PORT=3002 npm start &
    PAX_PID=$!
    echo "   ✅ PAX App started (PID: $PAX_PID)"
else
    echo "   ❌ Port 3002 is busy"
    exit 1
fi
cd ../..

# Wait for all components to start
echo ""
echo "⏳ Waiting for components to start..."
sleep 5

# Test the setup
echo ""
echo "🧪 Testing local setup..."
echo "   Testing MCP Server health..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "   ✅ MCP Server is healthy"
else
    echo "   ❌ MCP Server health check failed"
fi

echo ""
echo "🎉 Local Environment Started Successfully!"
echo "=========================================="
echo "📱 DAX App (Driver): http://localhost:3001"
echo "👤 PAX App (Passenger): http://localhost:3002"
echo "🔧 MCP Server: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo "🏥 Health Check: http://localhost:8000/health"
echo ""
echo "💡 Tips:"
echo "   - Use Ctrl+C to stop all components"
echo "   - Check logs in each terminal window"
echo "   - Test the in-memory cache: python test_in_memory_cache.py"
echo ""
echo "🔄 Components are running with auto-reload enabled"
echo "   Any code changes will automatically restart the services" 