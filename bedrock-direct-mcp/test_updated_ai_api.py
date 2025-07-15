#!/usr/bin/env python3
"""
Test script for the updated AI Intent API that calls the new unified MCP server endpoint.
"""

import requests
import json
import time

# Configuration
AI_API_URL = "http://localhost:8001"  # Local AI API
MCP_SERVER_URL = "http://mcp-server-env.eba-r23dy2pd.us-west-2.elasticbeanstalk.com"

def test_ai_api_health():
    """Test AI API health endpoint"""
    print("🔍 Testing AI API health...")
    try:
        response = requests.get(f"{AI_API_URL}/health")
        if response.status_code == 200:
            print("✅ AI API health check passed")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ AI API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ AI API health check error: {str(e)}")
        return False

def test_mcp_server_health():
    """Test MCP server health endpoint"""
    print("\n🔍 Testing MCP server health...")
    try:
        response = requests.get(f"{MCP_SERVER_URL}/healthcheck")
        if response.status_code == 200:
            print("✅ MCP server health check passed")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ MCP server health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ MCP server health check error: {str(e)}")
        return False

def test_intent_detection(test_cases):
    """Test intent detection with various inputs"""
    print(f"\n🧠 Testing intent detection with {len(test_cases)} test cases...")
    
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {test_case['description']} ---")
        print(f"Input: {test_case['user_input']}")
        
        try:
            payload = {
                "booking_code": test_case['booking_code'],
                "user_type": test_case['user_type'],
                "user_input": test_case['user_input']
            }
            
            response = requests.post(f"{AI_API_URL}/detect_intent", json=payload)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Intent detected: {result['intent']}")
                print(f"   Confidence: {result['confidence']}")
                print(f"   Success: {result['success']}")
                print(f"   Response: {result['response']}")
                
                if result.get('mcp_result'):
                    mcp_result = result['mcp_result']
                    print(f"   MCP Success: {mcp_result.get('success', False)}")
                    if not mcp_result.get('success'):
                        print(f"   MCP Error: {mcp_result.get('error', 'Unknown error')}")
                
                results.append({
                    'test_case': test_case,
                    'result': result,
                    'success': result['success']
                })
            else:
                print(f"❌ Request failed: {response.status_code}")
                print(f"   Error: {response.text}")
                results.append({
                    'test_case': test_case,
                    'result': None,
                    'success': False
                })
                
        except Exception as e:
            print(f"❌ Test case error: {str(e)}")
            results.append({
                'test_case': test_case,
                'result': None,
                'success': False
            })
    
    return results

def test_direct_mcp_calls():
    """Test direct calls to MCP server unified API"""
    print("\n🔗 Testing direct MCP server calls...")
    
    test_cases = [
        {
            "description": "Send message via unified API",
            "payload": {
                "booking_code": "TEST123",
                "user_input": "Hello from direct test",
                "user_type": "driver",
                "action": "send_message"
            }
        },
        {
            "description": "Make call via unified API", 
            "payload": {
                "booking_code": "TEST123",
                "user_input": "Call passenger",
                "user_type": "driver",
                "action": "make_call"
            }
        },
        {
            "description": "Get messages via unified API",
            "payload": {
                "booking_code": "TEST123", 
                "user_input": "Show messages",
                "user_type": "driver",
                "action": "get_messages"
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Direct MCP Test {i}: {test_case['description']} ---")
        
        try:
            response = requests.post(
                f"{MCP_SERVER_URL}/api/v1/unified-api",
                json=test_case['payload'],
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Direct MCP call successful")
                print(f"   Response: {result}")
            else:
                print(f"❌ Direct MCP call failed: {response.status_code}")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Direct MCP call error: {str(e)}")

def main():
    """Main test function"""
    print("🚀 Starting AI API and MCP Server Integration Tests")
    print("=" * 60)
    
    # Test health endpoints
    ai_health = test_ai_api_health()
    mcp_health = test_mcp_server_health()
    
    if not ai_health or not mcp_health:
        print("\n❌ Health checks failed. Cannot proceed with tests.")
        return
    
    # Test cases for intent detection
    test_cases = [
        {
            "description": "Send message intent",
            "booking_code": "TEST123",
            "user_type": "driver",
            "user_input": "Send a message to the passenger saying I'll be there in 5 minutes"
        },
        {
            "description": "Make call intent",
            "booking_code": "TEST123", 
            "user_type": "driver",
            "user_input": "Make a call to the passenger"
        },
        {
            "description": "Get message history intent",
            "booking_code": "TEST123",
            "user_type": "driver", 
            "user_input": "Get the message history"
        },
        {
            "description": "Simple send message",
            "booking_code": "TEST123",
            "user_type": "driver",
            "user_input": "Tell passenger I'm waiting"
        },
        {
            "description": "Call with urgency",
            "booking_code": "TEST123",
            "user_type": "driver",
            "user_input": "Call the passenger now"
        }
    ]
    
    # Test intent detection
    results = test_intent_detection(test_cases)
    
    # Test direct MCP calls
    test_direct_mcp_calls()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    successful_tests = sum(1 for r in results if r['success'])
    total_tests = len(results)
    
    print(f"Intent Detection Tests: {successful_tests}/{total_tests} successful")
    
    for i, result in enumerate(results, 1):
        status = "✅" if result['success'] else "❌"
        test_case = result['test_case']
        print(f"  {status} Test {i}: {test_case['description']}")
        if result['result']:
            print(f"     Intent: {result['result'].get('intent', 'unknown')}")
            print(f"     Confidence: {result['result'].get('confidence', 0.0)}")
    
    print(f"\n🎯 Overall Success Rate: {(successful_tests/total_tests)*100:.1f}%")
    
    if successful_tests == total_tests:
        print("🎉 All tests passed! AI API integration with unified MCP server is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")

if __name__ == "__main__":
    main() 