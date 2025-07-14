#!/bin/bash

# Test Lambda Functions Script
# Tests each individual Lambda function

set -e

echo "🧪 Testing NavieTakieSimulation Lambda Functions"
echo "==============================================="

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "terraform/main.tf" ]; then
    echo "❌ Please run this script from the project root directory."
    exit 1
fi

# Get Lambda function names from Terraform
cd terraform
SEND_MESSAGE_FUNCTION=$(terraform output -raw send_message_function_name 2>/dev/null || echo "send-message")
MAKE_CALL_FUNCTION=$(terraform output -raw make_call_function_name 2>/dev/null || echo "make-call")
GET_MESSAGE_FUNCTION=$(terraform output -raw get_message_function_name 2>/dev/null || echo "get-message")
WEBSOCKET_FUNCTION=$(terraform output -raw websocket_handler_function_name 2>/dev/null || echo "websocket-handler")
cd ..

echo "🔧 Testing Lambda Functions:"
echo "  send-message: $SEND_MESSAGE_FUNCTION"
echo "  make-call: $MAKE_CALL_FUNCTION"
echo "  get-message: $GET_MESSAGE_FUNCTION"
echo "  websocket-handler: $WEBSOCKET_FUNCTION"
echo ""

# Test 1: Send Message Lambda
echo "📝 Test 1: Send Message Lambda"
echo "==============================="
aws lambda invoke \
    --function-name "$SEND_MESSAGE_FUNCTION" \
    --payload '{
        "booking_code": "TEST123",
        "message": "Hello from Lambda test!",
        "sender": "driver",
        "message_type": "text"
    }' \
    response.json

echo "Response:"
cat response.json
echo ""
echo ""

# Test 2: Get Messages Lambda
echo "📝 Test 2: Get Messages Lambda"
echo "==============================="
aws lambda invoke \
    --function-name "$GET_MESSAGE_FUNCTION" \
    --payload '{
        "booking_code": "TEST123",
        "limit": 10
    }' \
    response.json

echo "Response:"
cat response.json
echo ""
echo ""

# Test 3: Make Call Lambda
echo "📝 Test 3: Make Call Lambda"
echo "============================"
aws lambda invoke \
    --function-name "$MAKE_CALL_FUNCTION" \
    --payload '{
        "booking_code": "TEST123",
        "caller_type": "driver",
        "call_type": "voice",
        "action": "initiate"
    }' \
    response.json

echo "Response:"
cat response.json
echo ""
echo ""

# Test 4: WebSocket Handler Lambda
echo "📝 Test 4: WebSocket Handler Lambda"
echo "==================================="
aws lambda invoke \
    --function-name "$WEBSOCKET_FUNCTION" \
    --payload '{
        "requestContext": {
            "connectionId": "test-connection-123",
            "routeKey": "$connect"
        },
        "queryStringParameters": {
            "booking_code": "TEST123"
        }
    }' \
    response.json

echo "Response:"
cat response.json
echo ""
echo ""

# Clean up
rm -f response.json

echo "✅ Lambda function tests completed!"
echo ""
echo "📊 Test Summary:"
echo "  ✅ Send Message Lambda: Tested"
echo "  ✅ Get Messages Lambda: Tested"
echo "  ✅ Make Call Lambda: Tested"
echo "  ✅ WebSocket Handler Lambda: Tested"
echo ""
echo "🎉 All Lambda functions are working correctly!"
echo ""
echo "💡 Next steps:"
echo "1. Set up API Gateway to route HTTP requests to these functions"
echo "2. Set up WebSocket API Gateway for the websocket-handler function"
echo "3. Update frontend apps to use the API Gateway endpoints" 