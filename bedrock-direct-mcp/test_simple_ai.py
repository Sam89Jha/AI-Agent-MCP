#!/usr/bin/env python3
"""
Test script for Simple AI Agent
"""

import requests
import json

# Test the simple AI agent
def test_simple_ai_agent():
    """Test the simple AI agent with various inputs"""
    
    # Test cases
    test_cases = [
        {
            "message": "Send a message to the passenger saying I'll be there in 5 minutes",
            "booking_code": "12345",
            "user_type": "driver"
        },
        {
            "message": "Make a call to the passenger",
            "booking_code": "12345", 
            "user_type": "driver"
        },
        {
            "message": "Get the message history",
            "booking_code": "12345",
            "user_type": "driver"
        },
        {
            "message": "Send message: I'm running late",
            "booking_code": "67890",
            "user_type": "driver"
        },
        {
            "message": "Call the passenger now",
            "booking_code": "67890",
            "user_type": "driver"
        }
    ]
    
    print("🤖 Testing Simple AI Agent")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}:")
        print(f"Input: {test_case['message']}")
        print(f"Booking: {test_case['booking_code']}")
        print(f"User Type: {test_case['user_type']}")
        
        try:
            # Make request to the AI agent
            response = requests.post(
                "http://localhost:8000/chat",
                json=test_case,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Response: {result['response']}")
                print(f"🎯 Intent: {result['intent']}")
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

def test_agent_test():
    """Test the agent test endpoint"""
    try:
        response = requests.get("http://localhost:8000/test")
        if response.status_code == 200:
            print("✅ Agent test passed")
            result = response.json()
            for test_result in result['test_results']:
                print(f"Input: {test_result['input']}")
                print(f"Response: {test_result['response']}")
                print(f"Intent: {test_result['intent']}")
                print("-" * 30)
        else:
            print(f"❌ Agent test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Agent test exception: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting Simple AI Agent Tests")
    print("Make sure the server is running on http://localhost:8000")
    print("=" * 50)
    
    # Test health first
    test_health()
    print()
    
    # Test agent functionality
    test_simple_ai_agent()
    print()
    
    # Test agent test endpoint
    test_agent_test() 