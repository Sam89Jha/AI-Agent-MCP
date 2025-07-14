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

# Create Docker Compose file for MCP server
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  mcp-server:
    build: .
    ports:
      - "80:8000"
      - "443:8000"
    environment:
      - AWS_REGION=${region}
      - DYNAMODB_TABLE=chat-messages
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
EOF

# Create Dockerfile for MCP server
cat > Dockerfile << 'EOF'
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Create requirements.txt
cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
boto3==1.34.0
python-multipart==0.0.6
pydantic==2.5.0
requests==2.31.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
EOF

# Create basic FastAPI app
cat > app.py << 'EOF'
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import boto3
import json
import os
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="MCP Server", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AWS clients
dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
lambda_client = boto3.client('lambda', region_name=os.getenv('AWS_REGION', 'us-east-1'))

# Models
class MessageRequest(BaseModel):
    booking_code: str
    message: str
    sender: str

class CallRequest(BaseModel):
    booking_code: str
    call_type: str
    duration: Optional[int] = 0

@app.get("/")
async def root():
    return {"message": "MCP Server is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/v1/send_message")
async def send_message(request: MessageRequest):
    try:
        # Call Lambda function
        response = lambda_client.invoke(
            FunctionName='send-message',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'booking_code': request.booking_code,
                'message': request.message,
                'sender': request.sender,
                'timestamp': datetime.now().isoformat()
            })
        )
        
        result = json.loads(response['Payload'].read())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/make_call")
async def make_call(request: CallRequest):
    try:
        # Call Lambda function
        response = lambda_client.invoke(
            FunctionName='make-call',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'booking_code': request.booking_code,
                'call_type': request.call_type,
                'duration': request.duration,
                'timestamp': datetime.now().isoformat()
            })
        )
        
        result = json.loads(response['Payload'].read())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/get_message/{booking_code}")
async def get_message(booking_code: str):
    try:
        # Call Lambda function
        response = lambda_client.invoke(
            FunctionName='get-message',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'booking_code': booking_code
            })
        )
        
        result = json.loads(response['Payload'].read())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

# Build and start the Docker container
cd /opt/mcp-server
docker-compose up -d --build

# Configure nginx as reverse proxy (optional)
cat > /etc/nginx/conf.d/mcp-server.conf << 'EOF'
server {
    listen 80;
    server_name mcp.sameer-jha.com;

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

# Create a simple status page
cat > /var/www/html/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>MCP Server Status</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .status { padding: 20px; border-radius: 5px; margin: 10px 0; }
        .healthy { background-color: #d4edda; color: #155724; }
        .error { background-color: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <h1>MCP Server Status</h1>
    <div id="status" class="status">Checking status...</div>
    <script>
        fetch('/health')
            .then(response => response.json())
            .then(data => {
                document.getElementById('status').innerHTML = 
                    '<div class="status healthy">✅ Server is healthy<br>Timestamp: ' + data.timestamp + '</div>';
            })
            .catch(error => {
                document.getElementById('status').innerHTML = 
                    '<div class="status error">❌ Server error: ' + error.message + '</div>';
            });
    </script>
</body>
</html>
EOF

# Log the completion
echo "MCP Server setup completed at $(date)" > /var/log/mcp-setup.log 