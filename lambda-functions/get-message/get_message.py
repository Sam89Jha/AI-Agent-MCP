import json
import os
from datetime import datetime
from typing import Dict, Any, List
import logging
from in_memory_cache import cache

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function to retrieve messages for a booking code from in-memory cache.
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Extract booking code and pagination parameters
        booking_code = event.get('booking_code')
        limit = event.get('limit', 50)
        start_key = event.get('start_key')
        
        if not booking_code:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': 'Missing required field: booking_code'
                })
            }
        
        # Get messages from in-memory cache
        result = cache.get_messages(booking_code, limit, start_key)
        
        logger.info(f"Retrieved {result['count']} messages from cache for booking {booking_code}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'message': 'Messages retrieved from cache',
                'data': {
                    'messages': result['messages'],
                    'count': result['count'],
                    'has_more': result['has_more'],
                    'source': 'cache'
                }
            })
        }
        
    except Exception as e:
        logger.error(f"Lambda error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': f'Internal server error: {str(e)}'
            })
        } 