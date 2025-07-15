#!/usr/bin/env python3
"""
Test script for AI Intent API
"""

import requests
import json

def test_ai_intent_api():
    """Test the AI Intent API with various inputs"""
    
    # Test cases
    test_cases = [
        {
            "booking_code": "12345",
            "user_type": "driver",
            "user_input": "Send a message to the passenger saying I'll be there in 5 minutes"
        },
        {
            "booking_code": "12345",
            "user_type": "driver", 
            "user_input": "Make a call to the passenger"
        },
        {
            "booking_code": "12345",
            "user_type": "driver",
            "user_input": "Get the message history"
        },
        {
            "booking_code": "67890",
            "user_type": "driver",
            "user_input": "Send message: I'm running late"
        },
        {
            "booking_code": "67890",
            "user_type": "driver",
            "user_input": "Call the passenger now"
        },
        {
            "booking_code": "11111",
            "user_type": "passenger",
            "user_input": "Send a message to the driver asking where they are"
        }
    ]
    
    print("🤖 Testing AI Intent API")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}:")
        print(f"Booking: {test_case['booking_code']}")
        print(f"User Type: {test_case['user_type']}")
        print(f"Input: {test_case['user_input']}")
        
        try:
            # Make request to the AI Intent API
            response = requests.post(
                "http://localhost:8000/detect_intent",
                json=test_case,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Intent: {result['intent']}")
                print(f"🎯 Confidence: {result['confidence']}")
                print(f"💬 Response: {result['response']}")
                print(f"✅ Success: {result['success']}")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
        
        print("-" * 40)

def test_health():
    """Test the health endpoint"""
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check exception: {str(e)}")

def test_api_test():
    """Test the API test endpoint"""
    try:
        response = requests.get("http://localhost:8000/test")
        if response.status_code == 200:
            print("✅ API test passed")
            result = response.json()
            for test_result in result['test_results']:
                print(f"Input: {test_result['input']['user_input']}")
                print(f"Intent: {test_result['intent']}")
                print(f"Confidence: {test_result['confidence']}")
                print(f"Response: {test_result['response']}")
                print(f"Reasoning: {test_result.get('reasoning', 'N/A')}")
                print("-" * 30)
        else:
            print(f"❌ API test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ API test exception: {str(e)}")

def test_direct_bedrock():
    """Test direct Bedrock integration"""
    try:
        import boto3
        import json
        
        bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        prompt = """
You are an AI assistant that helps drivers and passengers communicate. 
Analyze the following user input and determine the intent.

User Input: "Send a message to the passenger saying I'll be there in 5 minutes"

Possible intents:
1. send_message - User wants to send a text message
2. make_call - User wants to make a voice call
3. get_messages - User wants to see message history
4. unknown - Intent is unclear

Respond with ONLY a JSON object in this format:
{
    "intent": "send_message|make_call|get_messages|unknown",
    "confidence": 0.0-1.0,
    "extracted_message": "message content if sending message",
    "reasoning": "brief explanation of why this intent was chosen"
}
"""
        
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            body=json.dumps({
                "max_tokens": 200,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        )
        
        response_body = json.loads(response['body'].read())
        content = response_body['content'][0]['text']
        
        print("✅ Direct Bedrock test successful")
        print(f"Response: {content}")
        
    except Exception as e:
        print(f"❌ Direct Bedrock test failed: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting AI Intent API Tests")
    print("Make sure the server is running on http://localhost:8000")
    print("=" * 50)
    
    # Test health first
    test_health()
    print()
    
    # Test direct Bedrock integration
    print("🧪 Testing Direct Bedrock Integration...")
    test_direct_bedrock()
    print()
    
    # Test API functionality
    test_ai_intent_api()
    print()
    
    # Test API test endpoint
    test_api_test() 