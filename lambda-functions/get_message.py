import json
import os
from typing import Dict, Any
from in_memory_cache import cache

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function to get messages for a booking code from DynamoDB.
    
    Expected event format:
    {
        "booking_code": "string",
        "limit": number (optional),
        "start_key": "string" (optional for pagination)
    }
    """
    try:
        # Parse input
        booking_code = event.get('booking_code')
        limit = event.get('limit', 50)
        start_key = event.get('start_key')
        
        # Validate required fields
        if not booking_code:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required field: booking_code'
                })
            }
        
        # Get messages from in-memory cache
        result = cache.get_messages(str(booking_code), limit, start_key)
        
        # Return the result directly
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        print(f"Error in get_message: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Internal server error: {str(e)}'
            })
        } 