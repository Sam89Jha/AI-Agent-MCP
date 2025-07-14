"""
In-memory cache system to replace DynamoDB for local development.
Provides thread-safe storage for messages and calls.
"""

import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
import json

class InMemoryCache:
    """Thread-safe in-memory cache for storing messages and calls."""
    
    def __init__(self):
        self._messages = {}  # booking_code -> List[message]
        self._calls = {}     # booking_code -> List[call]
        self._lock = threading.Lock()
    
    def add_message(self, booking_code: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a message to the cache."""
        with self._lock:
            if booking_code not in self._messages:
                self._messages[booking_code] = []
            
            message_id = f"{booking_code}_{message_data['timestamp']}"
            message_item = {
                'booking_code': booking_code,
                'timestamp': message_data['timestamp'],
                'message': message_data['message'],
                'sender': message_data['sender'],
                'message_type': message_data.get('message_type', 'text'),
                'message_id': message_id
            }
            
            self._messages[booking_code].append(message_item)
            
            return {
                'success': True,
                'message': 'Message sent successfully',
                'data': {
                    'booking_code': booking_code,
                    'timestamp': message_data['timestamp'],
                    'message_id': message_id
                }
            }
    
    def get_messages(self, booking_code: str, limit: int = 50, start_key: Optional[str] = None) -> Dict[str, Any]:
        """Get messages for a booking code."""
        with self._lock:
            if booking_code not in self._messages:
                return {
                    'success': True,
                    'booking_code': booking_code,
                    'messages': [],
                    'count': 0,
                    'has_more': False
                }
            
            messages = self._messages[booking_code]
            
            # Sort by timestamp (newest first)
            messages.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Apply pagination
            if start_key:
                # Simple pagination - find the message after start_key
                start_index = 0
                for i, msg in enumerate(messages):
                    if msg['message_id'] == start_key:
                        start_index = i + 1
                        break
                messages = messages[start_index:]
            
            # Apply limit
            messages = messages[:limit]
            
            # Convert to expected format
            formatted_messages = []
            for msg in messages:
                formatted_msg = {
                    'id': msg['message_id'],
                    'booking_code': msg['booking_code'],
                    'timestamp': msg['timestamp'],
                    'message': msg['message'],
                    'sender': msg['sender'],
                    'message_type': msg['message_type']
                }
                formatted_messages.append(formatted_msg)
            
            return {
                'success': True,
                'booking_code': booking_code,
                'messages': formatted_messages,
                'count': len(formatted_messages),
                'has_more': len(self._messages[booking_code]) > len(formatted_messages)
            }
    
    def add_call(self, booking_code: str, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a call record to the cache."""
        with self._lock:
            if booking_code not in self._calls:
                self._calls[booking_code] = []
            
            call_id = f"{booking_code}_call_{call_data['timestamp']}"
            call_item = {
                'booking_code': booking_code,
                'timestamp': call_data['timestamp'],
                'call_type': call_data.get('call_type', 'voice'),
                'duration': call_data.get('duration', 0),
                'status': call_data.get('status', 'initiated'),
                'call_id': call_id
            }
            
            self._calls[booking_code].append(call_item)
            
            return {
                'success': True,
                'message': 'Call initiated successfully',
                'data': {
                    'booking_code': booking_code,
                    'timestamp': call_data['timestamp'],
                    'call_id': call_id,
                    'call_type': call_item['call_type'],
                    'status': call_item['status']
                }
            }
    
    def get_calls(self, booking_code: str) -> Dict[str, Any]:
        """Get calls for a booking code."""
        with self._lock:
            if booking_code not in self._calls:
                return {
                    'success': True,
                    'booking_code': booking_code,
                    'calls': [],
                    'count': 0
                }
            
            calls = self._calls[booking_code]
            calls.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return {
                'success': True,
                'booking_code': booking_code,
                'calls': calls,
                'count': len(calls)
            }
    
    def clear_cache(self):
        """Clear all cached data (for testing)."""
        with self._lock:
            self._messages.clear()
            self._calls.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_messages = sum(len(messages) for messages in self._messages.values())
            total_calls = sum(len(calls) for calls in self._calls.values())
            
            return {
                'total_booking_codes': len(self._messages),
                'total_messages': total_messages,
                'total_calls': total_calls,
                'booking_codes': list(self._messages.keys())
            }

# Global cache instance
cache = InMemoryCache() 