import json
import os
from datetime import datetime
from typing import Dict, Any
from in_memory_cache import cache

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function to make a call and log it in DynamoDB.
    
    Expected event format:
    {
        "booking_code": "string",
        "call_type": "voice" | "video" (optional),
        "duration": number (optional),
        "timestamp": "string" (optional),
        "status": "initiated" | "connected" | "ended" (optional)
    }
    """
    try:
        # Parse input
        booking_code = event.get('booking_code')
        call_type = event.get('call_type', 'voice')
        duration = event.get('duration', 0)
        timestamp = event.get('timestamp', datetime.now().isoformat())
        status = event.get('status', 'initiated')
        
        # Validate required fields
        if not booking_code:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required field: booking_code'
                })
            }
        
        # Validate call_type
        if call_type not in ['voice', 'video']:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Invalid call_type. Must be "voice" or "video"'
                })
            }
        
        # Create call message
        call_message = f"Call {status} - {call_type} call"
        
        # Create item for DynamoDB
        item = {
            'booking_code': booking_code,
            'timestamp': timestamp,
            'message': call_message,
            'sender': 'system',
            'message_type': 'call',
            'call_details': {
                'call_type': call_type,
                'duration': duration,
                'status': status
            }
        }
        
        # Store in in-memory cache
        result = cache.add_call(str(booking_code), item)
        
        # Return success response
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        print(f"Error in make_call: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Internal server error: {str(e)}'
            })
        } 