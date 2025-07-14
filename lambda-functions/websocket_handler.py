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
    Lambda function to handle WebSocket connections and call events.
    """
    try:
        logger.info(f"WebSocket event: {json.dumps(event)}")
        
        # Extract connection details
        connection_id = event.get('requestContext', {}).get('connectionId')
        route_key = event.get('requestContext', {}).get('routeKey')
        
        if not connection_id:
            return {
                'statusCode': 400,
                'body': 'Missing connection ID'
            }
        
        # Handle different WebSocket events
        if route_key == '$connect':
            return handle_connect(event, connection_id)
        elif route_key == '$disconnect':
            return handle_disconnect(event, connection_id)
        elif route_key == 'message':
            return handle_message(event, connection_id)
        else:
            return {
                'statusCode': 400,
                'body': f'Unknown route key: {route_key}'
            }
            
    except Exception as e:
        logger.error(f"WebSocket handler error: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'Internal server error: {str(e)}'
        }

def handle_connect(event: Dict[str, Any], connection_id: str) -> Dict[str, Any]:
    """
    Handle WebSocket connection.
    """
    try:
        # Extract booking code from query parameters
        query_params = event.get('queryStringParameters', {})
        booking_code = query_params.get('booking_code')
        
        if not booking_code:
            return {
                'statusCode': 400,
                'body': 'Missing booking_code parameter'
            }
        
        # Store connection in DynamoDB
        connections_table = dynamodb.Table(os.environ.get('CONNECTIONS_TABLE', 'websocket-connections-prod'))
        
        connection_item = {
            'connection_id': connection_id,
            'booking_code': booking_code,
            'timestamp': datetime.now().isoformat(),
            'ttl': int(datetime.now().timestamp()) + 86400  # 24 hours TTL
        }
        
        connections_table.put_item(Item=connection_item)
        logger.info(f"Connection {connection_id} stored for booking {booking_code}")
        
        return {
            'statusCode': 200,
            'body': 'Connected'
        }
        
    except Exception as e:
        logger.error(f"Connect error: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'Connection error: {str(e)}'
        }

def handle_disconnect(event: Dict[str, Any], connection_id: str) -> Dict[str, Any]:
    """
    Handle WebSocket disconnection.
    """
    try:
        # Remove connection from DynamoDB
        connections_table = dynamodb.Table(os.environ.get('CONNECTIONS_TABLE', 'websocket-connections-prod'))
        
        connections_table.delete_item(
            Key={'connection_id': connection_id}
        )
        logger.info(f"Connection {connection_id} removed")
        
        return {
            'statusCode': 200,
            'body': 'Disconnected'
        }
        
    except Exception as e:
        logger.error(f"Disconnect error: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'Disconnect error: {str(e)}'
        }

def handle_message(event: Dict[str, Any], connection_id: str) -> Dict[str, Any]:
    """
    Handle WebSocket message (call events).
    """
    try:
        # Parse message body
        body = json.loads(event.get('body', '{}'))
        message_type = body.get('type')
        booking_code = body.get('booking_code')
        sender = body.get('from')
        
        if not all([message_type, booking_code, sender]):
            return {
                'statusCode': 400,
                'body': 'Missing required fields: type, booking_code, from'
            }
        
        # Handle different message types
        if message_type in ['call_initiate', 'call_accept', 'call_reject', 'call_end', 'call_ringing', 'call_connected']:
            return handle_call_event(body, booking_code, sender)
        else:
            return {
                'statusCode': 400,
                'body': f'Unknown message type: {message_type}'
            }
            
    except Exception as e:
        logger.error(f"Message handling error: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'Message error: {str(e)}'
        }

def handle_call_event(event_data: Dict[str, Any], booking_code: str, sender: str) -> Dict[str, Any]:
    """
    Handle call-related events and broadcast to all connections.
    """
    try:
        message_type = event_data.get('type')
        if not message_type:
            return {
                'statusCode': 400,
                'body': 'Missing message type'
            }
        
        duration = event_data.get('duration', 0)
        timestamp = datetime.now().isoformat()
        
        # Create call log entry
        call_log = {
            'message': get_call_message(str(message_type), sender, duration),
            'status': get_call_status(str(message_type)),
            'duration': duration,
            'timestamp': timestamp,
            'from': sender
        }
        
        # Store call log in DynamoDB
        calls_table = dynamodb.Table(os.environ.get('CALLS_TABLE', 'call-logs-prod'))
        
        call_item = {
            'booking_code': booking_code,
            'timestamp': timestamp,
            'call_type': message_type,
            'sender': sender,
            'duration': duration,
            'status': get_call_status(str(message_type)),
            'message': call_log['message']
        }
        
        calls_table.put_item(Item=call_item)
        
        # Prepare WebSocket broadcast message
        broadcast_message = {
            'type': message_type,
            'from': sender,
            'booking_code': booking_code,
            'timestamp': timestamp,
            'call_log': call_log
        }
        
        # Broadcast to all connections for this booking
        connections = get_connections_for_booking(booking_code)
        
        for connection_id in connections:
            try:
                apigatewaymanagementapi.post_to_connection(
                    ConnectionId=connection_id,
                    Data=json.dumps(broadcast_message)
                )
                logger.info(f"Call event sent to connection: {connection_id}")
            except Exception as e:
                logger.error(f"Failed to send to connection {connection_id}: {str(e)}")
                remove_connection(connection_id)
        
        logger.info(f"Call event broadcasted to {len(connections)} connections")
        
        return {
            'statusCode': 200,
            'body': 'Call event processed'
        }
        
    except Exception as e:
        logger.error(f"Call event error: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'Call event error: {str(e)}'
        }

def get_call_message(message_type: str, sender: str, duration: int = 0) -> str:
    """
    Generate appropriate call message based on type.
    """
    messages = {
        'call_initiate': f'Incoming call from {sender.capitalize()}',
        'call_accept': f'Call accepted by {sender.capitalize()}',
        'call_reject': f'Call rejected by {sender.capitalize()}',
        'call_end': f'Call ended by {sender.capitalize()} - Duration: {duration} seconds',
        'call_ringing': f'Call ringing - Incoming call from {sender.capitalize()}',
        'call_connected': 'Call connected'
    }
    return messages.get(message_type, f'Call event: {message_type}')

def get_call_status(message_type: str) -> str:
    """
    Get call status from message type.
    """
    status_map = {
        'call_initiate': 'initiated',
        'call_accept': 'connected',
        'call_reject': 'rejected',
        'call_end': 'ended',
        'call_ringing': 'ringing',
        'call_connected': 'connected'
    }
    return status_map.get(message_type, 'unknown')

def get_connections_for_booking(booking_code: str) -> list:
    """
    Get all WebSocket connections for a booking code.
    """
    try:
        connections_table = dynamodb.Table(os.environ.get('CONNECTIONS_TABLE', 'websocket-connections-prod'))
        
        response = connections_table.query(
            IndexName='booking_code-index',
            KeyConditionExpression='booking_code = :booking_code',
            ExpressionAttributeValues={':booking_code': booking_code}
        )
        
        return [item['connection_id'] for item in response.get('Items', [])]
        
    except Exception as e:
        logger.error(f"Error getting connections: {str(e)}")
        return []

def remove_connection(connection_id: str):
    """
    Remove a stale WebSocket connection.
    """
    try:
        connections_table = dynamodb.Table(os.environ.get('CONNECTIONS_TABLE', 'websocket-connections-prod'))
        connections_table.delete_item(Key={'connection_id': connection_id})
        logger.info(f"Removed stale connection: {connection_id}")
    except Exception as e:
        logger.error(f"Error removing connection: {str(e)}") 