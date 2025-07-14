#!/usr/bin/env python3
"""
Local test script for send_message Lambda function
"""

import json
import os
import sys
from unittest.mock import Mock, patch

# Add the current directory to Python path
sys.path.append('.')

# Set environment variables for local testing
os.environ["MESSAGES_TABLE"] = "messages"
os.environ["CONNECTIONS_TABLE"] = "connections"
os.environ["REGION"] = "us-east-1"
os.environ["WEBSOCKET_ENDPOINT"] = "wss://7mcjiv4x73.execute-api.us-east-1.amazonaws.com/prod"

def mock_boto3():
    """Mock boto3 for local testing"""
    
    # Mock DynamoDB table
    mock_table = Mock()
    mock_table.put_item.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
    mock_table.query.return_value = {"Items": []}
    
    # Mock DynamoDB resource
    mock_dynamodb = Mock()
    mock_dynamodb.Table.return_value = mock_table
    
    # Mock API Gateway Management API
    mock_apigateway = Mock()
    mock_apigateway.post_to_connection.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
    
    return mock_dynamodb, mock_table, mock_apigateway

def test_send_message():
    """Test the send_message Lambda function locally"""
    
    print("🧪 Testing send_message Lambda function locally...")
    print("=" * 50)
    
    # Mock boto3
    mock_dynamodb, mock_table, mock_apigateway = mock_boto3()
    
    # Patch boto3 imports
    with patch('send_message.boto3') as mock_boto3_module:
        mock_boto3_module.resource.return_value = mock_dynamodb
        mock_boto3_module.client.return_value = mock_apigateway
        
        # Import the Lambda handler after patching
        from send_message import lambda_handler
        
        # Simulate an API Gateway event
        event = {
            "body": json.dumps({
                "booking_code": "TEST123",
                "message": "Hello from PAX! This is a test message.",
                "sender": "passenger",
                "message_type": "text"
            })
        }
        
        context = {
            "function_name": "send-message",
            "function_version": "$LATEST",
            "invoked_function_arn": "arn:aws:lambda:us-east-1:123456789012:function:send-message",
            "memory_limit_in_mb": "128",
            "aws_request_id": "test-request-id",
            "log_group_name": "/aws/lambda/send-message",
            "log_stream_name": "test-log-stream"
        }
        
        try:
            print("📤 Sending test message...")
            print(f"Event: {json.dumps(event, indent=2)}")
            print("-" * 30)
            
            response = lambda_handler(event, context)
            
            print("✅ Response received:")
            print(json.dumps(response, indent=2))
            
            # Check if response is successful
            if response.get('statusCode') == 200:
                print("🎉 SUCCESS: Lambda function executed successfully!")
                
                # Parse the response body
                body = json.loads(response.get('body', '{}'))
                if body.get('success'):
                    print(f"📤 Message sent successfully!")
                    print(f"   Booking: {body.get('data', {}).get('booking_code', 'N/A')}")
                    print(f"   Message: {body.get('data', {}).get('message', 'N/A')}")
                    print(f"   Sender: {body.get('data', {}).get('sender', 'N/A')}")
                else:
                    print(f"⚠️  API returned error: {body.get('error', 'Unknown error')}")
            else:
                print(f"⚠️  WARNING: Lambda returned status code {response.get('statusCode')}")
                
        except Exception as e:
            print(f"❌ ERROR: Lambda function failed with exception:")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            import traceback
            print("Full traceback:")
            print(traceback.format_exc())

if __name__ == "__main__":
    test_send_message() 