import json
import os
from datetime import datetime
from typing import Dict, Any
import logging
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
messages_table = dynamodb.Table(os.environ.get('MESSAGES_TABLE', 'messages'))
connections_table = dynamodb.Table(os.environ.get('CONNECTIONS_TABLE', 'connections'))

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function to handle HTTP API calls for sending messages.
    WebSocket connections are handled by websocket-register Lambda.
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        return handle_http_api_call(event, context)
        
    except Exception as e:
        logger.error(f"Lambda error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': f'Internal server error: {str(e)}'
            })
        }

def handle_http_api_call(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle HTTP API calls for sending messages."""
    try:
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
        
        # Generate timestamp and message ID
        timestamp = datetime.now().isoformat()
        message_id = f"{booking_code}_{timestamp}"
        
        # Store message in DynamoDB
        message_item = {
            'booking_code': booking_code,
            'message_id': message_id,
            'timestamp': timestamp,
            'message': message,
            'sender': sender,
            'message_type': message_type
        }
        
        try:
            messages_table.put_item(Item=message_item)
            logger.info(f"Message stored in DynamoDB: {message_id}")
        except ClientError as e:
            logger.error(f"DynamoDB error: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'success': False,
                    'error': f'Database error: {str(e)}'
                })
            }
        
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
        
        # Broadcast via WebSocket to all connections for this booking
        connections = get_connections_for_booking(booking_code)
        broadcast_count = 0
        
        for connection_id in connections:
            try:
                # Use API Gateway Management API to send WebSocket message
                send_websocket_message(connection_id, websocket_message)
                broadcast_count += 1
            except Exception as e:
                logger.error(f"Failed to send to connection {connection_id}: {str(e)}")
                # Remove stale connection
                remove_connection(connection_id)
        
        logger.info(f"Message broadcasted to {broadcast_count} connections")
        
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
                    'type': message_type,
                    'broadcast_count': broadcast_count
                }
            })
        }
        
    except Exception as e:
        logger.error(f"HTTP API call error: {str(e)}")
        raise



def get_connections_for_booking(booking_code: str) -> list:
    """Get all WebSocket connections for a booking code from DynamoDB."""
    try:
        response = connections_table.query(
            IndexName='booking_code-index',
            KeyConditionExpression=Key('booking_code').eq(booking_code)
        )
        return [item['connection_id'] for item in response['Items']]
    except ClientError as e:
        logger.error(f"DynamoDB query error: {str(e)}")
        return []

def remove_connection(connection_id: str):
    """Remove a stale WebSocket connection from DynamoDB."""
    try:
        # Query for all items with this connection_id (should be unique)
        response = connections_table.query(
            KeyConditionExpression=Key('connection_id').eq(connection_id)
        )
        for item in response['Items']:
            connections_table.delete_item(
                Key={
                    'connection_id': connection_id,
                    'booking_code': item['booking_code']
                }
            )
            logger.info(f"Removed stale connection {connection_id} from booking {item['booking_code']}")
    except ClientError as e:
        logger.error(f"DynamoDB remove connection error: {str(e)}")

def send_websocket_message(connection_id: str, message: Dict[str, Any]):
    """Send message to WebSocket connection using API Gateway Management API."""
    try:
        # Get API Gateway endpoint from environment
        endpoint = os.environ.get('WEBSOCKET_ENDPOINT')
        if not endpoint:
            logger.warning("WEBSOCKET_ENDPOINT not set, skipping WebSocket send")
            return
        
        # Create API Gateway Management API client
        apigatewaymanagementapi = boto3.client(
            'apigatewaymanagementapi',
            endpoint_url=endpoint
        )
        
        # Send message
        apigatewaymanagementapi.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(message)
        )
        
        logger.info(f"Message sent to connection {connection_id}")
        
    except Exception as e:
        logger.error(f"Failed to send WebSocket message: {str(e)}")
        raise 