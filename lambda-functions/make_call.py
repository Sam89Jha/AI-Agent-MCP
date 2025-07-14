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

# In-memory cache for call states (in production, use DynamoDB)
call_cache = {}

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function to handle call operations with proper caller/callee logic.
    
    Expected event format:
    {
        "booking_code": "string",
        "caller_type": "driver" | "passenger",
        "call_type": "voice" | "video",
        "action": "initiate" | "accept" | "reject" | "end",
        "duration": number (optional),
        "timestamp": "string" (optional)
    }
    """
    try:
        logger.info(f"Received call event: {json.dumps(event)}")
        
        # Extract call data
        booking_code = event.get('booking_code')
        caller_type = event.get('caller_type')
        call_type = event.get('call_type', 'voice')
        action = event.get('action')
        duration = event.get('duration', 0)
        timestamp = event.get('timestamp', datetime.now().isoformat())
        
        # Validate required fields
        if not all([booking_code, caller_type, action]):
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': 'Missing required fields: booking_code, caller_type, action'
                })
            }
        
        # Validate caller_type
        if caller_type not in ['driver', 'passenger']:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': 'Invalid caller_type. Must be "driver" or "passenger"'
                })
            }
        
        # Validate action
        if action not in ['initiate', 'accept', 'reject', 'end']:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': 'Invalid action. Must be "initiate", "accept", "reject", or "end"'
                })
            }
        
        # Handle different call actions
        if action == 'initiate':
            return handle_call_initiate(booking_code, caller_type, call_type, timestamp)
        elif action == 'accept':
            return handle_call_accept(booking_code, caller_type, timestamp)
        elif action == 'reject':
            return handle_call_reject(booking_code, caller_type, timestamp)
        elif action == 'end':
            return handle_call_end(booking_code, caller_type, duration, timestamp)
        
    except Exception as e:
        logger.error(f"Lambda error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': f'Internal server error: {str(e)}'
            })
        }

def handle_call_initiate(booking_code: str, caller_type: str, call_type: str, timestamp: str) -> Dict[str, Any]:
    """Handle call initiation"""
    try:
        # Determine callee type
        callee_type = 'passenger' if caller_type == 'driver' else 'driver'
        
        # Store call state in cache
        call_state = {
            'booking_code': booking_code,
            'caller_type': caller_type,
            'callee_type': callee_type,
            'call_type': call_type,
            'status': 'initiated',
            'timestamp': timestamp,
            'duration': 0
        }
        
        call_cache[booking_code] = call_state
        
        # Store in DynamoDB
        table_name = os.environ.get('DYNAMODB_TABLE', 'chat-messages-prod')
        table = dynamodb.Table(table_name)
        
        call_message = f"Call initiated by {caller_type.title()}"
        
        item = {
            'booking_code': booking_code,
            'timestamp': timestamp,
            'message_id': f"call_{timestamp}",
            'message': call_message,
            'sender': 'system',
            'message_type': 'call',
            'call_details': {
                'caller_type': caller_type,
                'callee_type': callee_type,
                'call_type': call_type,
                'status': 'initiated',
                'duration': 0
            }
        }
        
        table.put_item(Item=item)
        
        # Prepare WebSocket messages for different user types
        caller_message = {
            'type': 'call_state_update',
            'call_state': 'calling',
            'user_type': caller_type,
            'message': 'Calling...',
            'show_buttons': ['cancel']
        }
        
        callee_message = {
            'type': 'call_state_update',
            'call_state': 'ringing',
            'user_type': callee_type,
            'message': f'Incoming call from {caller_type.title()}',
            'show_buttons': ['accept', 'reject']
        }
        
        # Send WebSocket messages
        send_websocket_message(booking_code, caller_type, caller_message)
        send_websocket_message(booking_code, callee_type, callee_message)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'message': 'Call initiated successfully',
                'data': {
                    'call_state': 'calling',
                    'caller_type': caller_type,
                    'callee_type': callee_type,
                    'message': 'Calling...'
                }
            })
        }
        
    except Exception as e:
        logger.error(f"Call initiate error: {str(e)}")
        raise

def handle_call_accept(booking_code: str, caller_type: str, timestamp: str) -> Dict[str, Any]:
    """Handle call acceptance"""
    try:
        # Get current call state
        call_state = call_cache.get(booking_code)
        if not call_state:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': 'No active call found for this booking'
                })
            }
        
        # Update call state
        call_state['status'] = 'connected'
        call_state['connected_at'] = timestamp
        call_cache[booking_code] = call_state
        
        # Store in DynamoDB
        table_name = os.environ.get('DYNAMODB_TABLE', 'chat-messages-prod')
        table = dynamodb.Table(table_name)
        
        call_message = f"Call accepted by {caller_type.title()}"
        
        item = {
            'booking_code': booking_code,
            'timestamp': timestamp,
            'message_id': f"call_{timestamp}",
            'message': call_message,
            'sender': 'system',
            'message_type': 'call',
            'call_details': {
                'caller_type': call_state['caller_type'],
                'callee_type': call_state['callee_type'],
                'call_type': call_state['call_type'],
                'status': 'connected',
                'duration': 0
            }
        }
        
        table.put_item(Item=item)
        
        # Prepare WebSocket messages for both users
        caller_message = {
            'type': 'call_state_update',
            'call_state': 'connected',
            'user_type': call_state['caller_type'],
            'message': 'Call connected',
            'show_buttons': ['end']
        }
        
        callee_message = {
            'type': 'call_state_update',
            'call_state': 'connected',
            'user_type': call_state['callee_type'],
            'message': 'Call connected',
            'show_buttons': ['end']
        }
        
        # Send WebSocket messages
        send_websocket_message(booking_code, call_state['caller_type'], caller_message)
        send_websocket_message(booking_code, call_state['callee_type'], callee_message)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'message': 'Call accepted successfully',
                'data': {
                    'call_state': 'connected',
                    'message': 'Call connected'
                }
            })
        }
        
    except Exception as e:
        logger.error(f"Call accept error: {str(e)}")
        raise

def handle_call_reject(booking_code: str, caller_type: str, timestamp: str) -> Dict[str, Any]:
    """Handle call rejection"""
    try:
        # Get current call state
        call_state = call_cache.get(booking_code)
        if not call_state:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': 'No active call found for this booking'
                })
            }
        
        # Update call state
        call_state['status'] = 'rejected'
        call_state['ended_at'] = timestamp
        call_cache[booking_code] = call_state
        
        # Store in DynamoDB
        table_name = os.environ.get('DYNAMODB_TABLE', 'chat-messages-prod')
        table = dynamodb.Table(table_name)
        
        call_message = f"Call rejected by {caller_type.title()}"
        
        item = {
            'booking_code': booking_code,
            'timestamp': timestamp,
            'message_id': f"call_{timestamp}",
            'message': call_message,
            'sender': 'system',
            'message_type': 'call',
            'call_details': {
                'caller_type': call_state['caller_type'],
                'callee_type': call_state['callee_type'],
                'call_type': call_state['call_type'],
                'status': 'rejected',
                'duration': 0
            }
        }
        
        table.put_item(Item=item)
        
        # Prepare WebSocket messages for both users
        caller_message = {
            'type': 'call_state_update',
            'call_state': 'ended',
            'user_type': call_state['caller_type'],
            'message': f'Call rejected by {caller_type.title()}',
            'show_buttons': []
        }
        
        callee_message = {
            'type': 'call_state_update',
            'call_state': 'ended',
            'user_type': call_state['callee_type'],
            'message': f'Call rejected by {caller_type.title()}',
            'show_buttons': []
        }
        
        # Send WebSocket messages
        send_websocket_message(booking_code, call_state['caller_type'], caller_message)
        send_websocket_message(booking_code, call_state['callee_type'], callee_message)
        
        # Clear call state after delay
        def clear_call_state():
            if booking_code in call_cache:
                del call_cache[booking_code]
        
        # In production, use a timer or DynamoDB TTL
        # For now, we'll clear it immediately
        clear_call_state()
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'message': 'Call rejected successfully',
                'data': {
                    'call_state': 'ended',
                    'message': f'Call rejected by {caller_type.title()}'
                }
            })
        }
        
    except Exception as e:
        logger.error(f"Call reject error: {str(e)}")
        raise

def handle_call_end(booking_code: str, caller_type: str, duration: int, timestamp: str) -> Dict[str, Any]:
    """Handle call ending"""
    try:
        # Get current call state
        call_state = call_cache.get(booking_code)
        if not call_state:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': 'No active call found for this booking'
                })
            }
        
        # Update call state
        call_state['status'] = 'ended'
        call_state['ended_at'] = timestamp
        call_state['duration'] = duration
        call_cache[booking_code] = call_state
        
        # Store in DynamoDB
        table_name = os.environ.get('DYNAMODB_TABLE', 'chat-messages-prod')
        table = dynamodb.Table(table_name)
        
        call_message = f"Call ended by {caller_type.title()} - Duration: {duration} seconds"
        
        item = {
            'booking_code': booking_code,
            'timestamp': timestamp,
            'message_id': f"call_{timestamp}",
            'message': call_message,
            'sender': 'system',
            'message_type': 'call',
            'call_details': {
                'caller_type': call_state['caller_type'],
                'callee_type': call_state['callee_type'],
                'call_type': call_state['call_type'],
                'status': 'ended',
                'duration': duration
            }
        }
        
        table.put_item(Item=item)
        
        # Prepare WebSocket messages for both users
        caller_message = {
            'type': 'call_state_update',
            'call_state': 'ended',
            'user_type': call_state['caller_type'],
            'message': f'Call ended - Duration: {duration} seconds',
            'show_buttons': []
        }
        
        callee_message = {
            'type': 'call_state_update',
            'call_state': 'ended',
            'user_type': call_state['callee_type'],
            'message': f'Call ended - Duration: {duration} seconds',
            'show_buttons': []
        }
        
        # Send WebSocket messages
        send_websocket_message(booking_code, call_state['caller_type'], caller_message)
        send_websocket_message(booking_code, call_state['callee_type'], callee_message)
        
        # Clear call state
        if booking_code in call_cache:
            del call_cache[booking_code]
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'message': 'Call ended successfully',
                'data': {
                    'call_state': 'ended',
                    'duration': duration,
                    'message': f'Call ended - Duration: {duration} seconds'
                }
            })
        }
        
    except Exception as e:
        logger.error(f"Call end error: {str(e)}")
        raise

def send_websocket_message(booking_code: str, user_type: str, message: Dict[str, Any]):
    """Send WebSocket message to specific user type"""
    try:
        # In production, this would query a connection table
        # For now, we'll broadcast to all connections for the booking
        connections = get_connections_for_booking(booking_code)
        
        for connection_id in connections:
            try:
                apigatewaymanagementapi.post_to_connection(
                    ConnectionId=connection_id,
                    Data=json.dumps(message)
                )
                logger.info(f"Call message sent to connection: {connection_id}")
            except Exception as e:
                logger.error(f"Failed to send to connection {connection_id}: {str(e)}")
                # Remove stale connection
                remove_connection(connection_id)
        
    except Exception as e:
        logger.error(f"WebSocket message error: {str(e)}")

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