#!/usr/bin/env python3
"""
Local test script for make_call Lambda function
"""

import json
import os
import sys

# Add the current directory to Python path
sys.path.append('.')

# Set environment variables for local testing
os.environ["CALLS_TABLE"] = "calls"
os.environ["CONNECTIONS_TABLE"] = "connections"
os.environ["REGION"] = "us-east-1"
os.environ["WEBSOCKET_ENDPOINT"] = "wss://7mcjiv4x73.execute-api.us-east-1.amazonaws.com/prod"

# Import the Lambda handler
from make_call import lambda_handler

def test_make_call():
    """Test the make_call Lambda function locally"""
    
    print("🧪 Testing make_call Lambda function locally...")
    print("=" * 50)
    
    # Simulate an API Gateway event
    event = {
        "body": json.dumps({
            "booking_code": "TEST123",
            "caller_type": "passenger",
            "call_type": "voice",
            "action": "initiate",
            "duration": 0
        })
    }
    
    context = {
        "function_name": "make-call",
        "function_version": "$LATEST",
        "invoked_function_arn": "arn:aws:lambda:us-east-1:123456789012:function:make-call",
        "memory_limit_in_mb": "128",
        "aws_request_id": "test-request-id",
        "log_group_name": "/aws/lambda/make-call",
        "log_stream_name": "test-log-stream"
    }
    
    try:
        print("📞 Initiating test call...")
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
                print(f"📞 Call initiated successfully!")
                print(f"   Booking: {body.get('data', {}).get('booking_code', 'N/A')}")
                print(f"   Caller: {body.get('data', {}).get('caller_type', 'N/A')}")
                print(f"   Action: {body.get('data', {}).get('action', 'N/A')}")
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
    test_make_call() 