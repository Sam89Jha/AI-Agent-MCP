import json
import boto3
import os
from datetime import datetime
from typing import Dict, Any
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
apigatewaymanagementapi = boto3.client('apigatewaymanagementapi', endpoint_url=os.environ.get('WEBSOCKET_ENDPOINT'))

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function to send messages and broadcast via WebSocket.
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Extract message data
        body = json.loads(event.get('body', '{}'))
        booking_code = body.get('booking_code')
        message = body.get('message')
        sender = body.get('sender')
        message_type = body.get('message_type', 'text')
        
        if not all([booking_code, message, sender]):
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': 'Missing required fields: booking_code, message, sender'
                })
            }
        
        # Generate message ID
        message_id = f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(message) % 1000:03d}"
        timestamp = datetime.now().isoformat()
        
        # Store in DynamoDB
        table_name = os.environ.get('DYNAMODB_TABLE', 'chat-messages-prod')
        table = dynamodb.Table(table_name)
        
        item = {
            'booking_code': booking_code,
            'timestamp': timestamp,
            'message_id': message_id,
            'message': message,
            'sender': sender,
            'message_type': message_type,
            'id': message_id
        }
        
        table.put_item(Item=item)
        logger.info(f"Message stored in DynamoDB: {message_id}")
        
        # Prepare message for WebSocket broadcast
        websocket_message = {
            'type': 'new_message',
            'booking_code': booking_code,
            'message': {
                'id': message_id,
                'text': message,
                'sender': sender,
                'timestamp': timestamp,
                'type': message_type
            }
        }
        
        # Broadcast via WebSocket API Gateway
        try:
            # Get all connections for this booking code
            connections = get_connections_for_booking(booking_code)
            
            for connection_id in connections:
                try:
                    apigatewaymanagementapi.post_to_connection(
                        ConnectionId=connection_id,
                        Data=json.dumps(websocket_message)
                    )
                    logger.info(f"Message sent to connection: {connection_id}")
                except Exception as e:
                    logger.error(f"Failed to send to connection {connection_id}: {str(e)}")
                    # Remove stale connection
                    remove_connection(connection_id)
            
            logger.info(f"Message broadcasted to {len(connections)} connections")
            
        except Exception as e:
            logger.error(f"WebSocket broadcast error: {str(e)}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'message': 'Message sent successfully',
                'data': {
                    'id': message_id,
                    'booking_code': booking_code,
                    'message': message,
                    'sender': sender,
                    'timestamp': timestamp,
                    'type': message_type
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

def get_connections_for_booking(booking_code: str) -> list:
    """
    Get all WebSocket connections for a booking code.
    In production, this would query a connection table in DynamoDB.
    """
    # For now, return empty list - in production, query connection table
    # This would be implemented with a separate DynamoDB table tracking connections
    return []

def remove_connection(connection_id: str):
    """
    Remove a stale WebSocket connection.
    """
    # In production, remove from connection table
    pass 