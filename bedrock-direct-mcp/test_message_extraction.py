#!/usr/bin/env python3
"""
Test script to check message extraction
"""

import requests
import json

def test_message_extraction():
    """Test message extraction with different inputs"""
    
    base_url = "http://localhost:8000"
    
    test_cases = [
        # Send message flows
        {
            "booking_code": "12345",
            "user_type": "driver",
            "user_input": "Send a message to the passenger saying I'll be there in 5 minutes"
        },
        {
            "booking_code": "12345",
            "user_type": "driver",
            "user_input": "Tell the passenger I'm running late"
        },
        {
            "booking_code": "12345",
            "user_type": "driver",
            "user_input": "Message: I'm on my way"
        },
        # Make call flows
        {
            "booking_code": "12345",
            "user_type": "driver",
            "user_input": "Call the passenger now"
        },
        {
            "booking_code": "12345",
            "user_type": "passenger",
            "user_input": "Call the driver"
        },
        # Get messages flow
        {
            "booking_code": "12345",
            "user_type": "driver",
            "user_input": "Get the message history"
        },
        {
            "booking_code": "12345",
            "user_type": "passenger",
            "user_input": "Show me previous messages"
        },
        # Unknown/edge case
        {
            "booking_code": "12345",
            "user_type": "driver",
            "user_input": "What's the weather like?"
        },
        # Multiple sequential messages
        {
            "booking_code": "67890",
            "user_type": "driver",
            "user_input": "Send message: I'm at the pickup point"
        },
        {
            "booking_code": "67890",
            "user_type": "passenger",
            "user_input": "Tell the driver I'll be there in 2 minutes"
        },
        {
            "booking_code": "67890",
            "user_type": "driver",
            "user_input": "Get messages"
        }
    ]
    
    print("🧪 Testing Message Extraction")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}:")
        print(f"Input: {test_case['user_input']}")
        
        try:
            response = requests.post(
                f"{base_url}/detect_intent",
                json=test_case,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Intent: {data.get('intent')}")
                print(f"🎯 Confidence: {data.get('confidence')}")
                print(f"💬 Response: {data.get('response')}")
                
                # Check MCP result to see what was actually sent
                mcp_result = data.get('mcp_result', {})
                print(f"🪵 Full MCP result: {json.dumps(mcp_result, indent=2)}")
                if mcp_result.get('success'):
                    mcp_data = mcp_result.get('data', {}).get('data', {})
                    print(f"📤 Sent to MCP: {mcp_data.get('text', 'No text field')}")
                    print(f"📝 Message content: {mcp_data.get('text', 'No text field')}")
                    print(f"👤 Sender: {mcp_data.get('sender', 'No sender field')}")
                else:
                    print(f"❌ MCP Error: {mcp_result.get('error', 'Unknown error')}")
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"📝 Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {str(e)}")
        
        print("-" * 50)

if __name__ == "__main__":
    test_message_extraction() 