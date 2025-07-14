import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
messages_table = dynamodb.Table(os.environ.get('MESSAGES_TABLE', 'messages'))

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function to retrieve messages for a booking code from DynamoDB.
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Extract booking_code from queryStringParameters (GET query param)
        booking_code = None
        qsp = event.get('queryStringParameters')
        if qsp and isinstance(qsp, dict):
            booking_code = qsp.get('booking_code')
        
        # Extract pagination parameters (optional, from query params)
        limit = 50
        start_key = None
        if qsp and isinstance(qsp, dict):
            if 'limit' in qsp:
                try:
                    limit = int(qsp['limit'])
                except Exception:
                    pass
            if 'start_key' in qsp:
                start_key = qsp['start_key']
        
        if not booking_code:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': 'Missing required field: booking_code'
                })
            }
        
        # Get messages from DynamoDB
        result = get_messages_from_dynamodb(booking_code, limit, start_key)
        logger.info(f"Retrieved {result['count']} messages from DynamoDB for booking {booking_code}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'message': 'Messages retrieved from DynamoDB',
                'data': {
                    'messages': result['messages'],
                    'count': result['count'],
                    'has_more': result['has_more'],
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

def get_messages_from_dynamodb(booking_code: str, limit: int = 50, start_key: Optional[str] = None) -> Dict[str, Any]:
    """Get messages for a booking code from DynamoDB."""
    try:
        # Query DynamoDB for messages
        query_params = {
            'KeyConditionExpression': 'booking_code = :booking',
            'ExpressionAttributeValues': {':booking': booking_code},
            'ScanIndexForward': False,  # Sort by timestamp descending (newest first)
            'Limit': limit
        }
        
        # Add pagination if start_key provided
        if start_key:
            query_params['ExclusiveStartKey'] = {'booking_code': booking_code, 'message_id': start_key}
        
        response = messages_table.query(**query_params)
        
        # Format messages
        messages = []
        for item in response['Items']:
            formatted_msg = {
                'id': item['message_id'],
                'booking_code': item['booking_code'],
                'timestamp': item['timestamp'],
                'message': item['message'],
                'sender': item['sender'],
                'message_type': item.get('message_type', 'text')
            }
            messages.append(formatted_msg)
        
        return {
            'messages': messages,
            'count': len(messages),
            'has_more': 'LastEvaluatedKey' in response
        }
        
    except ClientError as e:
        logger.error(f"DynamoDB query error: {str(e)}")
        return {
            'messages': [],
            'count': 0,
            'has_more': False
        } 