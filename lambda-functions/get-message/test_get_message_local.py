#!/usr/bin/env python3
"""
Local test script for get_message Lambda function
"""

import json
import os
import sys

# Add the current directory to Python path
sys.path.append('.')

# Set environment variables for local testing
os.environ["MESSAGES_TABLE"] = "messages"
os.environ["REGION"] = "us-east-1"

# Import the Lambda handler
from get_message import lambda_handler

def test_get_message():
    """Test the get_message Lambda function locally"""
    
    print("🧪 Testing get_message Lambda function locally...")
    print("=" * 50)
    
    # Simulate an API Gateway event with query parameters
    event = {
        "queryStringParameters": {
            "booking_code": "TEST123",
            "limit": "10"
        }
    }
    
    context = {
        "function_name": "get-message",
        "function_version": "$LATEST",
        "invoked_function_arn": "arn:aws:lambda:us-east-1:123456789012:function:get-message",
        "memory_limit_in_mb": "128",
        "aws_request_id": "test-request-id",
        "log_group_name": "/aws/lambda/get-message",
        "log_stream_name": "test-log-stream"
    }
    
    try:
        print("📥 Getting messages...")
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
                messages = body.get('data', {}).get('messages', [])
                print(f"📋 Found {len(messages)} messages")
                for i, msg in enumerate(messages):
                    print(f"  {i+1}. {msg.get('message', 'N/A')} (from {msg.get('sender', 'N/A')})")
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
    test_get_message() 