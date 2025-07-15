#!/bin/bash

# User data script for MCP Server EC2 instance
# This script installs and configures the MCP server

set -e

# Update system
yum update -y

# Install required packages
yum install -y \
    python3 \
    python3-pip \
    git \
    nginx \
    docker \
    docker-compose

# Start and enable Docker
systemctl start docker
systemctl enable docker

# Create application directory
mkdir -p /opt/mcp-server
cd /opt/mcp-server

# Download application from GitHub (replace with your repo)
# git clone https://github.com/yourusername/AI-Agent-MCP.git .

# Or create minimal files directly
cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
boto3==1.34.0
requests==2.31.0
pydantic==2.5.0
EOF

cat > app.py << 'EOF'
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import logging
import requests
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MCP Server",
    description="Pure Orchestrator - Routes requests to API Gateway",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
API_GATEWAY_URL = "${api_gateway_url}"
WEBSOCKET_URL = "${websocket_url}"
REGION = "${region}"

# HTTP client for API Gateway calls
class APIGatewayClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'MCP-Server/1.0'
        })
    
    def call_api(self, endpoint: str, payload: Dict[str, Any] = None, method: str = 'POST') -> Dict[str, Any]:
        try:
            url = f"{API_GATEWAY_URL}{endpoint}"
            logger.info(f"Calling API: {url}")
            
            if method == 'POST':
                response = self.session.post(url, json=payload, timeout=30)
            else:
                response = self.session.get(url, params=payload, timeout=30)
            
            response.raise_for_status()
            result = response.json()
            logger.info(f"API response: {result}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"API Gateway error: {str(e)}")

# Initialize API Gateway client
api_client = APIGatewayClient()

# Pydantic models
class MessageRequest(BaseModel):
    booking_code: str
    message: str
    sender: str
    message_type: Optional[str] = "text"

class CallRequest(BaseModel):
    booking_code: str
    caller_type: str
    call_type: str = "voice"
    action: str
    duration: Optional[int] = 0

class AIAgentRequest(BaseModel):
    booking_code: str
    user_input: str
    user_type: str
    intent: Optional[str] = None
    confidence: Optional[float] = None

# Health check endpoint
@app.get("/")
async def root():
    return {"message": "MCP Server is running", "status": "healthy", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "region": REGION,
        "services": {"api_gateway": "healthy"}
    }

# AI Agent endpoint - main entry point
@app.post("/api/v1/ai_agent")
async def ai_agent_handler(request: AIAgentRequest):
    try:
        logger.info(f"AI Agent request: {request.booking_code}")
        
        # Determine intent
        intent = request.intent or _detect_intent(request.user_input)
        logger.info(f"Detected intent: {intent}")
        
        # Route based on intent
        if intent in ["send_message", "message", "send"]:
            return await _handle_send_message(request)
        elif intent in ["make_call", "call", "phone"]:
            return await _handle_make_call(request)
        elif intent in ["get_messages", "messages", "history"]:
            return await _handle_get_messages(request)
        else:
            return await _handle_send_message(request)
            
    except Exception as e:
        logger.error(f"AI Agent handler error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Send message endpoint
@app.post("/api/v1/send_message")
async def send_message(request: MessageRequest):
    try:
        logger.info(f"Send message: {request.booking_code}")
        
        payload = {
            "booking_code": request.booking_code,
            "message": request.message,
            "sender": request.sender,
            "timestamp": datetime.now().isoformat(),
            "message_type": request.message_type
        }
        
        result = api_client.call_api("/api/v1/send_message", payload)
        return result
        
    except Exception as e:
        logger.error(f"Send message error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Make call endpoint
@app.post("/api/v1/make_call")
async def make_call(request: CallRequest):
    try:
        logger.info(f"Make call: {request.booking_code}")
        
        payload = {
            "booking_code": request.booking_code,
            "caller_type": request.caller_type,
            "call_type": request.call_type,
            "action": request.action,
            "duration": request.duration,
            "timestamp": datetime.now().isoformat()
        }
        
        result = api_client.call_api("/api/v1/make_call", payload)
        return result
        
    except Exception as e:
        logger.error(f"Make call error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Get messages endpoint
@app.get("/api/v1/get_message/{booking_code}")
async def get_message(booking_code: str):
    try:
        logger.info(f"Get message: {booking_code}")
        
        result = api_client.call_api(f"/api/v1/get_message", {"booking_code": booking_code}, "GET")
        return result
        
    except Exception as e:
        logger.error(f"Get message error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Intent detection helper
def _detect_intent(user_input: str) -> str:
    input_lower = user_input.lower()
    
    call_keywords = ['call', 'phone', 'ring', 'dial', 'contact']
    if any(keyword in input_lower for keyword in call_keywords):
        return 'make_call'
    
    message_keywords = ['send', 'message', 'text', 'say', 'tell']
    if any(keyword in input_lower for keyword in message_keywords):
        return 'send_message'
    
    history_keywords = ['history', 'messages', 'previous', 'past']
    if any(keyword in input_lower for keyword in history_keywords):
        return 'get_messages'
    
    return 'send_message'

# AI Agent handlers
async def _handle_send_message(request: AIAgentRequest) -> Dict[str, Any]:
    message_content = _extract_message_content(request.user_input, 'send_message')
    
    payload = {
        "booking_code": request.booking_code,
        "message": message_content,
        "sender": request.user_type,
        "timestamp": datetime.now().isoformat(),
        "message_type": "text"
    }
    
    result = api_client.call_api("/api/v1/send_message", payload)
    
    return {
        "success": True,
        "data": {
            "text": message_content,
            "type": "text",
            "sender": request.user_type
        }
    }

async def _handle_make_call(request: AIAgentRequest) -> Dict[str, Any]:
    payload = {
        "booking_code": request.booking_code,
        "caller_type": request.user_type,
        "call_type": "voice",
        "action": "initiate",
        "duration": 0,
        "timestamp": datetime.now().isoformat()
    }
    
    result = api_client.call_api("/api/v1/make_call", payload)
    
    return {
        "success": True,
        "data": {
            "text": "Call initiated",
            "type": "call",
            "caller_type": request.user_type
        }
    }

async def _handle_get_messages(request: AIAgentRequest) -> Dict[str, Any]:
    result = api_client.call_api("/api/v1/get_message", {"booking_code": request.booking_code}, "GET")
    
    return {
        "success": True,
        "data": {
            "text": "Messages retrieved",
            "type": "history",
            "messages": result.get('data', {}).get('messages', [])
        }
    }

def _extract_message_content(user_input: str, intent: str) -> str:
    if intent == 'make_call':
        call_indicators = ['call', 'phone', 'ring', 'dial']
        for indicator in call_indicators:
            if indicator in user_input.lower():
                content = user_input.lower().replace(indicator, '').strip()
                return f"Call {content}" if content else "Call initiated"
        return "Call initiated"
    
    elif intent == 'send_message':
        message_indicators = ['send', 'message', 'text', 'say', 'tell']
        for indicator in message_indicators:
            if indicator in user_input.lower():
                content = user_input.lower().replace(indicator, '').strip()
                return content if content else "Message sent"
        return user_input
    
    else:
        return user_input

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(status_code=500, content={"error": "Internal server error"})
EOF

# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  mcp-server:
    build: .
    ports:
      - "80:8000"
    environment:
      - AWS_REGION=${region}
      - API_GATEWAY_URL=${api_gateway_url}
      - WEBSOCKET_URL=${websocket_url}
    restart: unless-stopped
EOF

# Build and start the Docker container
docker-compose up -d --build

# Configure nginx
cat > /etc/nginx/conf.d/mcp-server.conf << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Start nginx
systemctl start nginx
systemctl enable nginx

# Create logs directory
mkdir -p /opt/mcp-server/logs

# Set proper permissions
chown -R ec2-user:ec2-user /opt/mcp-server

echo "MCP Server deployment completed!" 