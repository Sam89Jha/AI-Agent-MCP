# Lambda Functions Deployment Guide

## Overview

The NavieTakieSimulation project uses **4 main Lambda functions** that are deployed as a **single Lambda function** with a unified handler that routes to the appropriate function based on the event type.

## Lambda Functions Structure

### 1. **`send_message.py`** - Message Handling
**Purpose**: Send messages, store in DynamoDB, broadcast via WebSocket

**Features**:
- ✅ Stores messages in DynamoDB table
- ✅ Caches messages in memory for quick retrieval
- ✅ Broadcasts real-time updates via WebSocket
- ✅ Handles message types (text, call, system)

**API Endpoint**: `POST /api/v1/send_message`

### 2. **`make_call.py`** - Call Management
**Purpose**: Handle call initiation, acceptance, rejection, and termination

**Features**:
- ✅ Initiates calls between driver and passenger
- ✅ Manages call states (ringing, connected, ended)
- ✅ Broadcasts call events via WebSocket
- ✅ Tracks call duration and logs

**API Endpoint**: `POST /api/v1/make_call`

### 3. **`get_message.py`** - Message Retrieval
**Purpose**: Retrieve message history from DynamoDB

**Features**:
- ✅ Retrieves messages from DynamoDB
- ✅ Supports pagination and filtering
- ✅ Returns message history for booking codes
- ✅ Handles different message types

**API Endpoint**: `GET /api/v1/get_message`

### 4. **`websocket_handler.py`** - WebSocket Management
**Purpose**: Handle WebSocket connections and real-time communication

**Features**:
- ✅ Manages WebSocket connections ($connect, $disconnect)
- ✅ Handles real-time message broadcasting
- ✅ Routes call events to connected clients
- ✅ Stores connections in DynamoDB

**WebSocket Routes**: `$connect`, `$disconnect`, `$default`

## Folder Structure

```
lambda-functions/
├── lambda_handler.py          # Main entry point (routes to functions)
├── send_message.py           # Message handling
├── make_call.py             # Call management
├── get_message.py           # Message retrieval
├── websocket_handler.py     # WebSocket handling
├── in_memory_cache.py       # Local caching (dev only)
├── requirements.txt         # Python dependencies
└── README.md               # Documentation
```

## Deployment Architecture

### Single Lambda Function Approach

Instead of deploying 4 separate Lambda functions, we use a **single Lambda function** with a unified handler that routes to the appropriate function based on the event type:

```python
# lambda_handler.py - Main entry point
def lambda_handler(event, context):
    function_type = determine_function_type(event)
    
    if function_type == 'send_message':
        return send_message_handler(event, context)
    elif function_type == 'make_call':
        return make_call_handler(event, context)
    elif function_type == 'get_message':
        return get_message_handler(event, context)
    elif function_type == 'websocket':
        return websocket_handler(event, context)
```

### Benefits of Single Lambda Approach

1. **Cost Effective**: Single function instead of 4 separate functions
2. **Simplified Management**: One deployment, one monitoring
3. **Shared Resources**: Common dependencies and utilities
4. **Easier Testing**: Single function to test and debug

## AWS Infrastructure

### DynamoDB Tables

1. **Messages Table** (`navietakie-messages-production`)
   - Hash Key: `booking_code`
   - Range Key: `timestamp`
   - Stores all messages

2. **Connections Table** (`navietakie-connections-production`)
   - Hash Key: `connection_id`
   - GSI: `booking_code-index`
   - Stores WebSocket connections

3. **Calls Table** (`navietakie-calls-production`)
   - Hash Key: `booking_code`
   - Range Key: `timestamp`
   - Stores call logs

### API Gateway

1. **REST API Gateway** (`navietakie-api-production`)
   - `POST /api/v1/send_message`
   - `POST /api/v1/make_call`
   - `GET /api/v1/get_message`

2. **WebSocket API Gateway** (`navietakie-websocket-production`)
   - `$connect` - Connect to WebSocket
   - `$disconnect` - Disconnect from WebSocket
   - `$default` - Handle messages

### IAM Roles and Permissions

- **Lambda Execution Role**: Basic Lambda execution permissions
- **DynamoDB Access**: Read/write access to all tables
- **API Gateway Access**: Permission to manage WebSocket connections
- **CloudWatch Logs**: Permission to write logs

## Environment Variables

```bash
DYNAMODB_TABLE=navietakie-messages-production
CONNECTIONS_TABLE=navietakie-connections-production
CALLS_TABLE=navietakie-calls-production
WEBSOCKET_ENDPOINT=https://{api-id}.execute-api.us-east-1.amazonaws.com/production
ENVIRONMENT=production
```

## Deployment Process

### 1. Prerequisites

- AWS CLI configured
- Terraform installed
- Python 3.11+ for local testing

### 2. Deploy to AWS

```bash
# Deploy Lambda functions
./scripts/deploy_lambda.sh

# Or manually with Terraform
cd terraform
terraform init
terraform plan
terraform apply
```

### 3. Update Frontend Configuration

After deployment, update your frontend apps to use the new API Gateway URLs:

```javascript
// config.js
const config = {
  apiBaseUrl: 'https://{api-id}.execute-api.us-east-1.amazonaws.com/production',
  websocketUrl: 'wss://{websocket-id}.execute-api.us-east-1.amazonaws.com/production'
};
```

## Local Development

For local development, the MCP server simulates these Lambda functions:

```python
# mcp-server/app.py
if config.is_local():
    # Use local handlers
    result = await local_send_message_handler(payload)
else:
    # Use AWS Lambda
    response = lambda_client.invoke(...)
```

## Monitoring and Logging

### CloudWatch Logs

- **Log Group**: `/aws/lambda/navietakie-lambda`
- **Retention**: 14 days
- **Log Streams**: One per Lambda invocation

### Key Metrics to Monitor

1. **Invocation Count**: Number of function invocations
2. **Duration**: Function execution time
3. **Error Rate**: Failed invocations
4. **Throttles**: When function is throttled

## Testing

### Local Testing

```bash
# Start local environment
./scripts/test_local.sh

# Test API endpoints
curl -X POST http://localhost:8000/api/v1/send_message \
  -H "Content-Type: application/json" \
  -d '{"booking_code":"test","message":"Hello","sender":"driver"}'
```

### AWS Testing

```bash
# Test deployed Lambda function
aws lambda invoke \
  --function-name navietakie-lambda \
  --payload '{"function_type":"send_message","booking_code":"test","message":"Hello","sender":"driver"}' \
  response.json
```

## Troubleshooting

### Common Issues

1. **Lambda Timeout**: Increase timeout in Terraform configuration
2. **Memory Issues**: Increase memory allocation
3. **Permission Errors**: Check IAM role permissions
4. **WebSocket Connection Issues**: Verify API Gateway configuration

### Debugging

1. **Check CloudWatch Logs**: Look for error messages
2. **Test Individual Functions**: Use direct Lambda invocation
3. **Verify Environment Variables**: Ensure all required vars are set
4. **Check DynamoDB Tables**: Verify data is being stored correctly

## Cost Optimization

### Lambda Optimization

- **Memory**: Start with 512MB, adjust based on performance
- **Timeout**: Set to 30 seconds for most operations
- **Concurrency**: Monitor and adjust as needed

### DynamoDB Optimization

- **Billing Mode**: PAY_PER_REQUEST for development
- **Provisioned Capacity**: For production with predictable load
- **TTL**: Use TTL for connection cleanup

## Security Considerations

1. **API Gateway**: Consider adding authentication
2. **DynamoDB**: Use IAM policies for fine-grained access
3. **WebSocket**: Implement connection validation
4. **Environment Variables**: Use AWS Secrets Manager for sensitive data

## Next Steps

1. **Deploy Lambda Functions**: Run `./scripts/deploy_lambda.sh`
2. **Update Frontend**: Configure apps to use new API Gateway URLs
3. **Test End-to-End**: Verify all functionality works
4. **Monitor Performance**: Set up CloudWatch alarms
5. **Scale as Needed**: Adjust resources based on usage 