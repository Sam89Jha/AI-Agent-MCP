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
calls_table = dynamodb.Table(os.environ.get('CALLS_TABLE', 'calls'))
connections_table = dynamodb.Table(os.environ.get('CONNECTIONS_TABLE', 'connections'))

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function to handle HTTP API calls for call operations.
    WebSocket connections are handled by websocket-register Lambda.
    """
    try:
        logger.info(f"Received call event: {json.dumps(event)}")
        # Parse body if present (API Gateway proxy integration)
        if 'body' in event and isinstance(event['body'], str):
            try:
                body = json.loads(event['body'])
                event.update(body)
            except Exception:
                pass
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
    """Handle HTTP API calls for call operations."""
    try:
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
            return handle_call_initiate(booking_code, caller_type, call_type, timestamp)  # type: ignore
        elif action == 'accept':
            return handle_call_accept(booking_code, caller_type, timestamp)  # type: ignore
        elif action == 'reject':
            return handle_call_reject(booking_code, caller_type, timestamp)  # type: ignore
        elif action == 'end':
            return handle_call_end(booking_code, caller_type, duration, timestamp)  # type: ignore
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': 'Invalid action'
                })
            }
        
    except Exception as e:
        logger.error(f"HTTP API call error: {str(e)}")
        raise

def handle_websocket_event(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle WebSocket events for call operations."""
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
        
        # Store connection in DynamoDB
        try:
            connections_table.put_item(
                Item={
                    'connection_id': connection_id,
                    'booking_code': booking_code,
                    'user_type': 'passenger' # Assuming a default user type for now
                }
            )
            logger.info(f"Connection {connection_id} stored for booking {booking_code}")
        except ClientError as e:
            logger.error(f"DynamoDB put_item error for connection: {e}")
            return {
                'statusCode': 500,
                'body': f'Connection error: {e.response["Error"]["Message"]}'
            }
        
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
        # Remove connection from DynamoDB
        try:
            connections_table.delete_item(
                Key={'connection_id': connection_id}
            )
            logger.info(f"Connection {connection_id} removed from DynamoDB")
        except ClientError as e:
            logger.error(f"DynamoDB delete_item error for connection: {e}")
            return {
                'statusCode': 500,
                'body': f'Disconnect error: {e.response["Error"]["Message"]}'
            }
        
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
    """Handle WebSocket message for call operations."""
    try:
        # Parse message body
        body = json.loads(event.get('body', '{}'))
        message_type = body.get('type')
        booking_code = body.get('booking_code')
        caller_type = body.get('caller_type')
        action = body.get('action')
        
        if not all([message_type, booking_code, caller_type, action]):
            return {
                'statusCode': 400,
                'body': 'Missing required fields: type, booking_code, caller_type, action'
            }
        
        # Handle different call message types
        if message_type == 'call_operation':
            return handle_websocket_call_operation(body, booking_code, caller_type, action)
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

def handle_websocket_call_operation(event_data: Dict[str, Any], booking_code: str, caller_type: str, action: str) -> Dict[str, Any]:
    """Handle call operation via WebSocket."""
    try:
        call_type = event_data.get('call_type', 'voice')
        duration = event_data.get('duration', 0)
        timestamp = datetime.now().isoformat()
        
        # Handle different call actions
        if action == 'initiate':
            return handle_call_initiate(booking_code, caller_type, call_type, timestamp)  # type: ignore
        elif action == 'accept':
            return handle_call_accept(booking_code, caller_type, timestamp)  # type: ignore
        elif action == 'reject':
            return handle_call_reject(booking_code, caller_type, timestamp)  # type: ignore
        elif action == 'end':
            return handle_call_end(booking_code, caller_type, duration, timestamp)  # type: ignore
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': f'Invalid action: {action}'
                })
            }
        
    except Exception as e:
        logger.error(f"WebSocket call operation error: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'WebSocket call operation error: {str(e)}'
        }

def handle_call_initiate(booking_code: str, caller_type: str, call_type: str, timestamp: str) -> Dict[str, Any]:
    """Handle call initiation"""
    try:
        # Determine callee type
        callee_type = 'passenger' if caller_type == 'driver' else 'driver'
        
        # Store call in DynamoDB
        try:
            call_data = {
                'booking_code': booking_code,
                'caller_type': caller_type,
                'callee_type': callee_type,
                'call_type': call_type,
                'status': 'initiated',
                'timestamp': timestamp,
                'duration': 0
            }
            calls_table.put_item(Item=call_data)
            logger.info(f"Call initiated for booking {booking_code}: {call_data}")
        except ClientError as e:
            logger.error(f"DynamoDB put_item error for call: {e}")
            return {
                'statusCode': 500,
                'body': f'Call initiation error: {e.response["Error"]["Message"]}'
            }
        
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
        # Get current call state from DynamoDB
        try:
            calls_result = calls_table.get_item(Key={'booking_code': booking_code})
            if 'Item' not in calls_result:
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'success': False,
                        'error': 'No active call found for this booking'
                    })
                }
            call_data = calls_result['Item']
            if call_data['status'] != 'initiated':
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'success': False,
                        'error': 'Call is not in initiated state'
                    })
                }
        except ClientError as e:
            logger.error(f"DynamoDB get_item error for call: {e}")
            return {
                'statusCode': 500,
                'body': f'Call state retrieval error: {e.response["Error"]["Message"]}'
            }
        
        # Update call state (in a real implementation, you'd update the specific call)
        # For now, we'll just log the acceptance
        
        # Prepare WebSocket messages for both users
        connected_message = {
            'type': 'call_state_update',
            'call_state': 'connected',
            'message': 'Call connected',
            'show_buttons': ['end']
        }
        
        # Send WebSocket messages to both users
        send_websocket_message(booking_code, 'driver', connected_message)
        send_websocket_message(booking_code, 'passenger', connected_message)
        
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
        # Get current call state from DynamoDB
        try:
            calls_result = calls_table.get_item(Key={'booking_code': booking_code})
            if 'Item' not in calls_result:
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'success': False,
                        'error': 'No active call found for this booking'
                    })
                }
            call_data = calls_result['Item']
            if call_data['status'] != 'initiated':
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'success': False,
                        'error': 'Call is not in initiated state'
                    })
                }
        except ClientError as e:
            logger.error(f"DynamoDB get_item error for call: {e}")
            return {
                'statusCode': 500,
                'body': f'Call state retrieval error: {e.response["Error"]["Message"]}'
            }
        
        # Prepare WebSocket messages for both users
        rejected_message = {
            'type': 'call_state_update',
            'call_state': 'rejected',
            'message': 'Call rejected',
            'show_buttons': []
        }
        
        # Send WebSocket messages to both users
        send_websocket_message(booking_code, 'driver', rejected_message)
        send_websocket_message(booking_code, 'passenger', rejected_message)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'message': 'Call rejected successfully',
                'data': {
                    'call_state': 'rejected',
                    'message': 'Call rejected'
                }
            })
        }
        
    except Exception as e:
        logger.error(f"Call reject error: {str(e)}")
        raise

def handle_call_end(booking_code: str, caller_type: str, duration: int, timestamp: str) -> Dict[str, Any]:
    """Handle call ending"""
    try:
        # Get current call state from DynamoDB
        try:
            calls_result = calls_table.get_item(Key={'booking_code': booking_code})
            if 'Item' not in calls_result:
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'success': False,
                        'error': 'No active call found for this booking'
                    })
                }
            call_data = calls_result['Item']
            if call_data['status'] != 'initiated':
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'success': False,
                        'error': 'Call is not in initiated state'
                    })
                }
        except ClientError as e:
            logger.error(f"DynamoDB get_item error for call: {e}")
            return {
                'statusCode': 500,
                'body': f'Call state retrieval error: {e.response["Error"]["Message"]}'
            }
        
        # Prepare WebSocket messages for both users
        ended_message = {
            'type': 'call_state_update',
            'call_state': 'ended',
            'message': f'Call ended (Duration: {duration}s)',
            'show_buttons': []
        }
        
        # Send WebSocket messages to both users
        send_websocket_message(booking_code, 'driver', ended_message)
        send_websocket_message(booking_code, 'passenger', ended_message)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'message': 'Call ended successfully',
                'data': {
                    'call_state': 'ended',
                    'duration': duration,
                    'message': f'Call ended (Duration: {duration}s)'
                }
            })
        }
        
    except Exception as e:
        logger.error(f"Call end error: {str(e)}")
        raise

def send_websocket_message(booking_code: str, user_type: str, message: Dict[str, Any]):
    """
    Send WebSocket message to users of a specific type for a booking code.
    In production, this would use API Gateway Management API.
    """
    try:
        # In production, this would send via API Gateway Management API
        # For now, just log the message
        logger.info(f"Would send WebSocket message to {user_type} for booking {booking_code}: {message}")
        
    except Exception as e:
        logger.error(f"WebSocket send error: {str(e)}")

def get_connections_for_booking(booking_code: str) -> list:
    """Get all WebSocket connections for a booking code."""
    try:
        response = connections_table.query(
            IndexName='booking_code-index',
            KeyConditionExpression=Key('booking_code').eq(booking_code)
        )
        return [item['connection_id'] for item in response.get('Items', [])]
    except ClientError as e:
        logger.error(f"DynamoDB query error for connections: {e}")
        return []

def remove_connection(connection_id: str):
    """Remove a stale WebSocket connection."""
    try:
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
        logger.error(f"DynamoDB delete_item error for stale connection: {e}") 