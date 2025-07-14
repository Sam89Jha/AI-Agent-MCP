# Lambda APIs Guide

## Overview

**Lambda APIs are NOT running on any port** - they are **serverless functions** that only execute when invoked. In local development, they are simulated by the MCP server's local handlers.

## Current Architecture

```
Frontend Apps → MCP Server → Lambda Functions (AWS) / Local Handlers (Local)
                     ↓
              WebSocket Manager → Real-time Updates
```

## Component Status

### ✅ Currently Running

1. **MCP Server** (Backend API Orchestrator)
   - **Port**: 8000
   - **URL**: http://localhost:8000
   - **Role**: Orchestrates Lambda function calls
   - **Status**: ✅ Running

2. **DAX App** (Driver Interface)
   - **Port**: 3000
   - **URL**: http://localhost:3000
   - **Role**: Driver chat and call interface
   - **Status**: ✅ Running

3. **PAX App** (Passenger Interface)
   - **Port**: 3001
   - **URL**: http://localhost:3001
   - **Role**: Passenger chat and call interface
   - **Status**: ✅ Running

### 📋 Lambda APIs (Simulated Locally)

1. **send_message**
   - **Local**: Simulated in MCP Server
   - **Production**: AWS Lambda function
   - **Purpose**: Send messages, store in DynamoDB, broadcast via WebSocket

2. **make_call**
   - **Local**: Simulated in MCP Server
   - **Production**: AWS Lambda function
   - **Purpose**: Handle voice/video calls with caller/callee logic

3. **get_message**
   - **Local**: Simulated in MCP Server
   - **Production**: AWS Lambda function
   - **Purpose**: Retrieve message history with caching

4. **websocket_handler**
   - **Local**: Integrated in MCP Server
   - **Production**: AWS Lambda function
   - **Purpose**: Manage WebSocket connections for real-time updates

## Environment Configuration

### Local Environment
```bash
# API URLs
API_BASE_URL=http://localhost:8000
WEBSOCKET_URL=ws://localhost:8000/ws

# Frontend Apps
DAX_APP_URL=http://localhost:3000
PAX_APP_URL=http://localhost:3001

# Lambda Functions
send_message=send-message-local (simulated)
make_call=make-call-local (simulated)
get_message=get-message-local (simulated)
```

### Production Environment
```bash
# API URLs
API_BASE_URL=https://mcp.sameer-jha.com
WEBSOCKET_URL=wss://mcp.sameer-jha.com/ws

# Frontend Apps
DAX_APP_URL=https://dax.sameer-jha.com
PAX_APP_URL=https://pax.sameer-jha.com

# Lambda Functions
send_message=send-message-prod (AWS Lambda)
make_call=make-call-prod (AWS Lambda)
get_message=get-message-prod (AWS Lambda)
```

## API Endpoints

### MCP Server Endpoints (Port 8000)

1. **Health Check**: `GET http://localhost:8000/health`
2. **AI Agent**: `POST http://localhost:8000/api/v1/ai_agent`
3. **Send Message**: `POST http://localhost:8000/api/v1/send_message`
4. **Make Call**: `POST http://localhost:8000/api/v1/make_call`
5. **Get Messages**: `GET http://localhost:8000/api/v1/get_message/{booking_code}`
6. **WebSocket**: `WS http://localhost:8000/ws/{booking_code}`
7. **API Docs**: `http://localhost:8000/docs`

### Lambda Function Endpoints (Production Only)

When deployed to AWS, these functions are invoked directly:

1. **send_message**: `POST /send-message-prod`
2. **make_call**: `POST /make-call-prod`
3. **get_message**: `GET /get-message-prod`
4. **websocket_handler**: `WS /websocket-prod`

## Local Development vs Production

### Local Development
- ✅ **Fast iteration** with in-memory handlers
- ✅ **No AWS costs** during development
- ✅ **Real-time features** with WebSocket
- ✅ **Full functionality** simulation

### Production
- ✅ **Scalable** serverless architecture
- ✅ **Persistent storage** with DynamoDB
- ✅ **Real-time features** with API Gateway WebSocket
- ✅ **Reliable** AWS infrastructure

## Quick Commands

### Check Status
```bash
./scripts/status.sh
```

### Start Local Environment
```bash
./scripts/start_local.sh
```

### Test Lambda Functions Locally
```bash
python test_in_memory_cache.py
```

### Deploy to Production
```bash
./scripts/deploy.sh
```

## Key Points

1. **Lambda APIs don't run on ports** - they're serverless functions
2. **Local development** uses simulated handlers in MCP server
3. **Production** uses actual AWS Lambda functions
4. **WebSocket** is handled by MCP server locally, API Gateway in production
5. **Environment variables** control which URLs are used
6. **All components are currently running** and healthy

## Troubleshooting

### If MCP Server is not responding:
```bash
curl http://localhost:8000/health
```

### If frontend apps can't connect:
```bash
# Check environment variables
echo $REACT_APP_API_BASE_URL
echo $REACT_APP_WEBSOCKET_URL
```

### If Lambda functions fail:
- **Local**: Check MCP server logs
- **Production**: Check AWS CloudWatch logs

## Next Steps

1. **Test the applications** by opening both frontend apps
2. **Try sending messages** between driver and passenger
3. **Test call functionality** with proper UI states
4. **Deploy to AWS** when ready for production 