# Lambda Functions for NavieTakieSimulation

## Overview

This directory contains the AWS Lambda functions for the NavieTakieSimulation project. The functions are designed to be deployed as a single Lambda function that routes to the appropriate handler based on the event type.

## Function Structure

### Core Functions

1. **`send_message.py`** - Handles message sending and storage
   - Stores messages in DynamoDB
   - Broadcasts via WebSocket
   - Handles different message types (text, call, system)

2. **`make_call.py`** - Handles call initiation and management
   - Initiates calls between driver and passenger
   - Manages call states (ringing, connected, ended)
   - Broadcasts call events via WebSocket

3. **`get_message.py`** - Handles message retrieval
   - Retrieves messages from DynamoDB
   - Supports pagination and filtering
   - Returns message history for booking codes

4. **`websocket_handler.py`** - Handles WebSocket connections
   - Manages WebSocket connections ($connect, $disconnect)
   - Handles real-time message broadcasting
   - Routes call events to connected clients

### Supporting Files

- **`lambda_handler.py`** - Main entry point that routes to appropriate function
- **`in_memory_cache.py`** - In-memory caching for local development
- **`requirements.txt`** - Python dependencies

## Deployment Structure

```
lambda-functions/
├── lambda_handler.py          # Main entry point
├── send_message.py           # Message handling
├── make_call.py             # Call management
├── get_message.py           # Message retrieval
├── websocket_handler.py     # WebSocket handling
├── in_memory_cache.py       # Local caching
├── requirements.txt         # Dependencies
└── README.md               # This file
```

## Environment Variables

The Lambda functions expect these environment variables:

- `DYNAMODB_TABLE` - DynamoDB table for messages
- `CONNECTIONS_TABLE` - DynamoDB table for WebSocket connections
- `CALLS_TABLE` - DynamoDB table for call logs
- `WEBSOCKET_ENDPOINT` - WebSocket API Gateway endpoint
- `ENVIRONMENT` - Environment (local, staging, production)

## API Endpoints

### Message API
- `POST /send_message` - Send a message
- `GET /get_message` - Retrieve messages

### Call API
- `POST /make_call` - Initiate or manage a call

### WebSocket API
- `$connect` - Connect to WebSocket
- `$disconnect` - Disconnect from WebSocket
- `message` - Handle real-time messages

## Local Development

For local development, the MCP server simulates these Lambda functions using local handlers. The functions use in-memory caching and local WebSocket management.

## AWS Deployment

The functions are deployed as a single Lambda function using Terraform. The main handler routes to the appropriate function based on the event type. 