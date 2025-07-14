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
connections_table = dynamodb.Table(os.environ.get('CONNECTIONS_TABLE', 'connections'))

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function to handle WebSocket connection registration.
    Apps call this to register their WebSocket connections.
    """
    try:
        logger.info(f"Received WebSocket registration event: {json.dumps(event)}")
        
        # Check if this is a WebSocket event from API Gateway
        if 'requestContext' in event and 'routeKey' in event.get('requestContext', {}):
            return handle_websocket_event(event, context)
        else:
            return handle_http_registration(event, context)
        
    except Exception as e:
        logger.error(f"Lambda error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': f'Internal server error: {str(e)}'
            })
        }

def handle_websocket_event(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle WebSocket events (connect, disconnect)."""
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
    """Handle WebSocket connection registration."""
    try:
        # Extract parameters from query string
        query_params = event.get('queryStringParameters', {}) or {}
        booking_code = query_params.get('booking_code')
        user_type = query_params.get('user_type', 'passenger')  # driver or passenger
        
        if not booking_code:
            return {
                'statusCode': 400,
                'body': 'Missing booking_code parameter'
            }
        
        # Validate user_type
        if user_type not in ['driver', 'passenger']:
            return {
                'statusCode': 400,
                'body': 'Invalid user_type. Must be "driver" or "passenger"'
            }
        
        # Store connection in DynamoDB
        connection_item = {
            'connection_id': connection_id,
            'booking_code': booking_code,
            'user_type': user_type,
            'timestamp': datetime.now().isoformat(),
            'status': 'connected'
        }
        
        try:
            connections_table.put_item(Item=connection_item)
            logger.info(f"Connection {connection_id} registered for booking {booking_code} as {user_type}")
        except ClientError as e:
            logger.error(f"DynamoDB connection error: {str(e)}")
            return {
                'statusCode': 500,
                'body': f'Connection storage error: {str(e)}'
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'message': 'WebSocket connection registered',
                'data': {
                    'connection_id': connection_id,
                    'booking_code': booking_code,
                    'user_type': user_type
                }
            })
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
                logger.info(f"Connection {connection_id} removed from booking {item['booking_code']}")
        except ClientError as e:
            logger.error(f"DynamoDB disconnect error: {str(e)}")
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'message': 'WebSocket connection removed'
            })
        }
    except Exception as e:
        logger.error(f"Disconnect error: {str(e)}")
        return {
            'statusCode': 500,
            'body': f'Disconnect error: {str(e)}'
        }

def handle_http_registration(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle HTTP registration requests (for testing/debugging)."""
    try:
        # Extract registration data
        body = json.loads(event.get('body', '{}'))
        connection_id = body.get('connection_id')
        booking_code = body.get('booking_code')
        user_type = body.get('user_type', 'passenger')
        
        if not all([connection_id, booking_code]):
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': 'Missing required fields: connection_id, booking_code'
                })
            }
        
        # Validate user_type
        if user_type not in ['driver', 'passenger']:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'success': False,
                    'error': 'Invalid user_type. Must be "driver" or "passenger"'
                })
            }
        
        # Store connection in DynamoDB
        connection_item = {
            'connection_id': connection_id,
            'booking_code': booking_code,
            'user_type': user_type,
            'timestamp': datetime.now().isoformat(),
            'status': 'connected'
        }
        
        try:
            connections_table.put_item(Item=connection_item)
            logger.info(f"HTTP registration: Connection {connection_id} for booking {booking_code} as {user_type}")
        except ClientError as e:
            logger.error(f"DynamoDB HTTP registration error: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'success': False,
                    'error': f'Database error: {str(e)}'
                })
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'message': 'WebSocket connection registered via HTTP',
                'data': {
                    'connection_id': connection_id,
                    'booking_code': booking_code,
                    'user_type': user_type
                }
            })
        }
        
    except Exception as e:
        logger.error(f"HTTP registration error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': f'Internal server error: {str(e)}'
            })
        } 