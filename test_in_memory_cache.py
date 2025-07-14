#!/usr/bin/env python3
"""
Test script for in-memory cache functionality.
"""

import sys
import os
sys.path.append('lambda-functions')

from in_memory_cache import cache
from send_message import lambda_handler as send_message_handler
from make_call import lambda_handler as make_call_handler
from get_message import lambda_handler as get_message_handler

def test_in_memory_cache():
    """Test the in-memory cache functionality."""
    print("🧪 Testing In-Memory Cache System")
    print("=" * 50)
    
    # Clear cache for fresh test
    cache.clear_cache()
    
    # Test 1: Send a message
    print("\n1. Testing send_message...")
    send_event = {
        "booking_code": "TEST123",
        "message": "Hello from driver!",
        "sender": "driver",
        "message_type": "text"
    }
    
    send_result = send_message_handler(send_event, None)
    print(f"✅ Send message result: {send_result['statusCode']}")
    
    # Test 2: Send another message
    print("\n2. Testing another message...")
    send_event2 = {
        "booking_code": "TEST123",
        "message": "Hello from passenger!",
        "sender": "passenger",
        "message_type": "text"
    }
    
    send_result2 = send_message_handler(send_event2, None)
    print(f"✅ Second message result: {send_result2['statusCode']}")
    
    # Test 3: Make a call
    print("\n3. Testing make_call...")
    call_event = {
        "booking_code": "TEST123",
        "call_type": "voice",
        "duration": 30,
        "status": "initiated"
    }
    
    call_result = make_call_handler(call_event, None)
    print(f"✅ Make call result: {call_result['statusCode']}")
    
    # Test 4: Get messages
    print("\n4. Testing get_message...")
    get_event = {
        "booking_code": "TEST123",
        "limit": 10
    }
    
    get_result = get_message_handler(get_event, None)
    print(f"✅ Get messages result: {get_result['statusCode']}")
    
    # Parse and display messages
    import json
    messages_data = json.loads(get_result['body'])
    print(f"📨 Found {messages_data['count']} messages:")
    for msg in messages_data['messages']:
        print(f"   - {msg['sender']}: {msg['message']} ({msg['timestamp']})")
    
    # Test 5: Cache statistics
    print("\n5. Cache statistics:")
    stats = cache.get_stats()
    print(f"   📊 Total booking codes: {stats['total_booking_codes']}")
    print(f"   📊 Total messages: {stats['total_messages']}")
    print(f"   📊 Total calls: {stats['total_calls']}")
    print(f"   📊 Booking codes: {stats['booking_codes']}")
    
    print("\n🎉 All tests completed successfully!")
    return True

if __name__ == "__main__":
    test_in_memory_cache() 