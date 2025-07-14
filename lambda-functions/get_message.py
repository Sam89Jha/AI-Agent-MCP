import json
import boto3
import os
from datetime import datetime
from typing import Dict, Any, List
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

# In-memory cache for messages (in production, use DynamoDB)
message_cache = {}

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function to retrieve messages for a booking code.
    Returns messages from cache first, then DynamoDB if needed.
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Extract booking code
        booking_code = event.get('booking_code')
        
        if not booking_code:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': 'Missing required field: booking_code'
                })
            }
        
        # Try to get messages from cache first
        cache_key = f"messages:{booking_code}"
        cached_messages = message_cache.get(cache_key, [])
        
        if cached_messages:
            logger.info(f"Retrieved {len(cached_messages)} messages from cache for booking {booking_code}")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'message': 'Messages retrieved from cache',
                    'data': {
                        'messages': cached_messages,
                        'count': len(cached_messages),
                        'source': 'cache'
                    }
                })
            }
        
        # If not in cache, get from DynamoDB
        logger.info(f"Cache miss for booking {booking_code}, retrieving from DynamoDB")
        messages = get_messages_from_dynamodb(booking_code)
        
        # Cache the messages for future requests
        message_cache[cache_key] = messages
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'message': 'Messages retrieved from DynamoDB',
                'data': {
                    'messages': messages,
                    'count': len(messages),
                    'source': 'dynamodb'
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

def get_messages_from_dynamodb(booking_code: str) -> List[Dict[str, Any]]:
    """
    Retrieve messages from DynamoDB for a booking code.
    """
    try:
        table_name = os.environ.get('DYNAMODB_TABLE', 'chat-messages-prod')
        table = dynamodb.Table(table_name)
        
        # Query DynamoDB for messages with this booking code
        response = table.query(
            KeyConditionExpression='booking_code = :booking_code',
            ExpressionAttributeValues={
                ':booking_code': booking_code
            },
            ScanIndexForward=False,  # Get newest first
            Limit=100  # Limit to last 100 messages
        )
        
        messages = []
        for item in response.get('Items', []):
            # Format message for frontend
            message = {
                'id': item.get('message_id', item.get('id', '')),
                'text': item.get('message', ''),
                'sender': item.get('sender', ''),
                'timestamp': item.get('timestamp', ''),
                'type': item.get('message_type', 'text')
            }
            
            # Add call details if this is a call message
            if item.get('message_type') == 'call' and 'call_details' in item:
                message['callDetails'] = item['call_details']
            
            messages.append(message)
        
        # Sort by timestamp (oldest first for display)
        messages.sort(key=lambda x: x.get('timestamp', ''))
        
        logger.info(f"Retrieved {len(messages)} messages from DynamoDB for booking {booking_code}")
        return messages
        
    except Exception as e:
        logger.error(f"Error retrieving messages from DynamoDB: {str(e)}")
        return [] 