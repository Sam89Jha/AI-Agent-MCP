import json
import os
from datetime import datetime
from typing import Dict, Any
import logging
from in_memory_cache import cache

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# In-memory connection tracking (in production, use DynamoDB)
connections_cache = {}

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function to handle both HTTP API calls and WebSocket events for sending messages.
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Check if this is a WebSocket event
        if 'requestContext' in event and 'routeKey' in event.get('requestContext', {}):
            return handle_websocket_event(event, context)
        else:
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
        
        # Generate timestamp
        timestamp = datetime.now().isoformat()
        
        # Store in in-memory cache
        message_data = {
            'timestamp': timestamp,
            'message': message,
            'sender': sender,
            'message_type': message_type
        }
        
        result = cache.add_message(booking_code, message_data)
        logger.info(f"Message stored in cache: {result['data']['message_id']}")
        
        # Prepare message for WebSocket broadcast
        websocket_message = {
            'type': 'new_message',
            'booking_code': booking_code,
            'message': {
                'id': result['data']['message_id'],
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
                # In production, this would use API Gateway Management API
                logger.info(f"Would send to connection {connection_id}: {websocket_message}")
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
                    'id': result['data']['message_id'],
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

def handle_websocket_event(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle WebSocket events (connect, disconnect, message)."""
    try:
        connection_id = event.get('requestContext', {}).get('connectionId')
        route_key = event.get('requestContext', {}).get('routeKey')
        
        if not connection_id:
            return {
                'statusCode': 400,
                'body': 'Missing connection ID'
            }
        
        # Handle different WebSocket events
        if route_key == '$connect':
            return handle_websocket_connect(event, connection_id)
        elif route_key == '$disconnect':
            return handle_websocket_disconnect(event, connection_id)
        elif route_key == 'message':
            return handle_websocket_message(event, connection_id)
        else:
            return {
                'statusCode': 400,
                'body': f'Unknown route key: {route_key}'
            }
            
    except Exception as e:
        logger.error(f"WebSocket event error: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'Internal server error: {str(e)}'
        }

def handle_websocket_connect(event: Dict[str, Any], connection_id: str) -> Dict[str, Any]:
    """Handle WebSocket connection."""
    try:
        # Extract booking code from query parameters
        query_params = event.get('queryStringParameters', {})
        booking_code = query_params.get('booking_code')
        
        if not booking_code:
            return {
                'statusCode': 400,
                'body': 'Missing booking_code parameter'
            }
        
        # Store connection in memory cache
        if booking_code not in connections_cache:
            connections_cache[booking_code] = []
        
        connections_cache[booking_code].append(connection_id)
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

def handle_websocket_disconnect(event: Dict[str, Any], connection_id: str) -> Dict[str, Any]:
    """Handle WebSocket disconnection."""
    try:
        # Remove connection from memory cache
        for booking_code, connections in connections_cache.items():
            if connection_id in connections:
                connections.remove(connection_id)
                logger.info(f"Connection {connection_id} removed from booking {booking_code}")
                break
        
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

def handle_websocket_message(event: Dict[str, Any], connection_id: str) -> Dict[str, Any]:
    """Handle WebSocket message."""
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
        if message_type == 'send_message':
            return handle_websocket_send_message(body, booking_code, sender)
        else:
            return {
                'statusCode': 400,
                'body': f'Unknown message type: {message_type}'
            }
            
    except Exception as e:
        logger.error(f"WebSocket message error: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'Message error: {str(e)}'
        }

def handle_websocket_send_message(event_data: Dict[str, Any], booking_code: str, sender: str) -> Dict[str, Any]:
    """Handle send message via WebSocket."""
    try:
        message = event_data.get('message')
        message_type = event_data.get('message_type', 'text')
        
        if not message:
            return {
                'statusCode': 400,
                'body': 'Missing message content'
            }
        
        # Store message in cache
        timestamp = datetime.now().isoformat()
        message_data = {
            'timestamp': timestamp,
            'message': message,
            'sender': sender,
            'message_type': message_type
        }
        
        result = cache.add_message(booking_code, message_data)
        
        # Prepare broadcast message
        broadcast_message = {
            'type': 'new_message',
            'booking_code': booking_code,
            'message': {
                'id': result['data']['message_id'],
                'text': message,
                'sender': sender,
                'timestamp': timestamp,
                'type': message_type
            }
        }
        
        # Broadcast to all connections for this booking
        connections = get_connections_for_booking(booking_code)
        broadcast_count = 0
        
        for conn_id in connections:
            try:
                # In production, this would use API Gateway Management API
                logger.info(f"Would send to connection {conn_id}: {broadcast_message}")
                broadcast_count += 1
            except Exception as e:
                logger.error(f"Failed to send to connection {conn_id}: {str(e)}")
                remove_connection(conn_id)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'message': 'Message sent via WebSocket',
                'broadcast_count': broadcast_count
            })
        }
        
    except Exception as e:
        logger.error(f"WebSocket send message error: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'WebSocket send message error: {str(e)}'
        }

def get_connections_for_booking(booking_code: str) -> list:
    """Get all WebSocket connections for a booking code."""
    return connections_cache.get(booking_code, [])

def remove_connection(connection_id: str):
    """Remove a stale WebSocket connection."""
    for booking_code, connections in connections_cache.items():
        if connection_id in connections:
            connections.remove(connection_id)
            logger.info(f"Removed stale connection {connection_id} from booking {booking_code}")
            break 