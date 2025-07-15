#!/usr/bin/env python3
"""
Test script to verify MCP server deployment
"""

import requests
import json
import time

def test_mcp_server():
    """Test the MCP server endpoints"""
    
    base_url = "http://3.213.220.153"
    
    print("🔍 Testing MCP Server Deployment")
    print("=" * 50)
    
    # Test 1: Root endpoint
    print("\n1. Testing root endpoint...")
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Health endpoint
    print("\n2. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Health: {data}")
        else:
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Send message endpoint
    print("\n3. Testing send message endpoint...")
    try:
        payload = {
            "booking_code": "TEST123",
            "message": "Hello from test script",
            "sender": "driver",
            "message_type": "text"
        }
        response = requests.post(f"{base_url}/api/v1/send_message", 
                               json=payload, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {data}")
        else:
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 4: AI Agent endpoint
    print("\n4. Testing AI Agent endpoint...")
    try:
        payload = {
            "booking_code": "TEST123",
            "user_input": "Send a test message",
            "user_type": "driver",
            "intent": "send_message"
        }
        response = requests.post(f"{base_url}/api/v1/ai_agent", 
                               json=payload, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {data}")
        else:
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ MCP Server test completed!")

if __name__ == "__main__":
    test_mcp_server() 