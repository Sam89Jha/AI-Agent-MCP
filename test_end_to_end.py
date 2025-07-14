#!/usr/bin/env python3
"""
End-to-End Test for NavieTakieSimulation
Tests all components working together on local machine.
"""

import requests
import json
import time
import sys
import os
from datetime import datetime

# Configuration
LOCAL_CONFIG = {
    'mcp_server_url': 'http://localhost:8000',
    'dax_app_url': 'http://localhost:3001',
    'pax_app_url': 'http://localhost:3002',
    'test_booking_code': 'E2E_TEST_123'
}

def test_mcp_server_health():
    """Test MCP server health endpoint."""
    print("🏥 Testing MCP Server Health...")
    try:
        response = requests.get(f"{LOCAL_CONFIG['mcp_server_url']}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ MCP Server is healthy")
            print(f"   📊 Status: {data.get('status')}")
            print(f"   🌍 Region: {data.get('region')}")
            print(f"   🔧 Services: {data.get('services')}")
            return True
        else:
            print(f"   ❌ MCP Server health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ MCP Server not reachable: {str(e)}")
        return False

def test_send_message():
    """Test sending a message through MCP server."""
    print("\n📨 Testing Send Message...")
    try:
        payload = {
            "booking_code": LOCAL_CONFIG['test_booking_code'],
            "message": "Hello from end-to-end test!",
            "sender": "driver",
            "message_type": "text"
        }
        
        response = requests.post(
            f"{LOCAL_CONFIG['mcp_server_url']}/api/v1/send_message",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Message sent successfully")
            print(f"   📝 Response: {data.get('message')}")
            return True
        else:
            print(f"   ❌ Send message failed: {response.status_code}")
            print(f"   📝 Error: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Send message request failed: {str(e)}")
        return False

def test_make_call():
    """Test making a call through MCP server."""
    print("\n📞 Testing Make Call...")
    try:
        payload = {
            "booking_code": LOCAL_CONFIG['test_booking_code'],
            "call_type": "voice",
            "duration": 30,
            "status": "initiated"
        }
        
        response = requests.post(
            f"{LOCAL_CONFIG['mcp_server_url']}/api/v1/make_call",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Call initiated successfully")
            print(f"   📝 Response: {data.get('message')}")
            return True
        else:
            print(f"   ❌ Make call failed: {response.status_code}")
            print(f"   📝 Error: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Make call request failed: {str(e)}")
        return False

def test_get_messages():
    """Test getting messages through MCP server."""
    print("\n📥 Testing Get Messages...")
    try:
        response = requests.get(
            f"{LOCAL_CONFIG['mcp_server_url']}/api/v1/get_message/{LOCAL_CONFIG['test_booking_code']}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            messages = data.get('data', {}).get('messages', [])
            print(f"   ✅ Retrieved {len(messages)} messages")
            for msg in messages:
                print(f"   📝 {msg['sender']}: {msg['message']} ({msg['timestamp']})")
            return True
        else:
            print(f"   ❌ Get messages failed: {response.status_code}")
            print(f"   📝 Error: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Get messages request failed: {str(e)}")
        return False

def test_ai_agent():
    """Test AI agent endpoint."""
    print("\n🤖 Testing AI Agent...")
    try:
        payload = {
            "booking_code": LOCAL_CONFIG['test_booking_code'],
            "user_input": "Send a test message",
            "user_type": "driver",
            "intent": "send_message"
        }
        
        response = requests.post(
            f"{LOCAL_CONFIG['mcp_server_url']}/api/v1/ai_agent",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ AI Agent processed request successfully")
            print(f"   📝 Response: {data.get('message', 'No message')}")
            return True
        else:
            print(f"   ❌ AI Agent failed: {response.status_code}")
            print(f"   📝 Error: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ AI Agent request failed: {str(e)}")
        return False

def test_react_apps():
    """Test if React apps are accessible."""
    print("\n🌐 Testing React Apps...")
    
    # Test DAX App
    try:
        response = requests.get(LOCAL_CONFIG['dax_app_url'], timeout=5)
        if response.status_code == 200:
            print(f"   ✅ DAX App is accessible at {LOCAL_CONFIG['dax_app_url']}")
        else:
            print(f"   ⚠️  DAX App returned status {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ DAX App not accessible: {str(e)}")
    
    # Test PAX App
    try:
        response = requests.get(LOCAL_CONFIG['pax_app_url'], timeout=5)
        if response.status_code == 200:
            print(f"   ✅ PAX App is accessible at {LOCAL_CONFIG['pax_app_url']}")
        else:
            print(f"   ⚠️  PAX App returned status {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ PAX App not accessible: {str(e)}")

def main():
    """Run all end-to-end tests."""
    print("🧪 NavieTakieSimulation End-to-End Test")
    print("=" * 50)
    print(f"🔧 Test Booking Code: {LOCAL_CONFIG['test_booking_code']}")
    print(f"⏰ Test Time: {datetime.now().isoformat()}")
    print("")
    
    # Test results
    tests = []
    
    # Test MCP Server
    tests.append(("MCP Server Health", test_mcp_server_health()))
    
    # Test API endpoints
    tests.append(("Send Message", test_send_message()))
    tests.append(("Make Call", test_make_call()))
    tests.append(("Get Messages", test_get_messages()))
    tests.append(("AI Agent", test_ai_agent()))
    
    # Test React apps
    test_react_apps()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print("=" * 50)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your local environment is working correctly.")
        print("\n💡 Next Steps:")
        print("   1. Open DAX App: http://localhost:3001")
        print("   2. Open PAX App: http://localhost:3002")
        print("   3. Use booking code: E2E_TEST_123")
        print("   4. Test sending messages and making calls")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check your setup.")
        print("\n🔧 Troubleshooting:")
        print("   1. Make sure MCP server is running: uvicorn app:app --host 0.0.0.0 --port 8000")
        print("   2. Make sure React apps are running: npm start")
        print("   3. Check if ports 8000, 3001, 3002 are available")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 