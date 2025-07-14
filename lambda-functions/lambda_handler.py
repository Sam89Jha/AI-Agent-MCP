"""
Unified Lambda Handler for NavieTakieSimulation
Routes to appropriate function based on event type
"""

import json
import os
from typing import Dict, Any
import logging

# Import the individual Lambda functions
from send_message import lambda_handler as send_message_handler
from make_call import lambda_handler as make_call_handler
from get_message import lambda_handler as get_message_handler
from websocket_handler import lambda_handler as websocket_handler

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler that routes to appropriate function based on event type.
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Determine function type from event
        function_type = determine_function_type(event)
        logger.info(f"Routing to function type: {function_type}")
        
        # Route to appropriate handler
        if function_type == 'send_message':
            return send_message_handler(event, context)
        elif function_type == 'make_call':
            return make_call_handler(event, context)
        elif function_type == 'get_message':
            return get_message_handler(event, context)
        elif function_type == 'websocket':
            return websocket_handler(event, context)
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': f'Unknown function type: {function_type}'
                })
            }
            
    except Exception as e:
        logger.error(f"Lambda handler error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Internal server error: {str(e)}'
            })
        }

def determine_function_type(event: Dict[str, Any]) -> str:
    """
    Determine which function to call based on the event structure.
    """
    # Check if it's a WebSocket event
    if 'requestContext' in event and 'routeKey' in event.get('requestContext', {}):
        return 'websocket'
    
    # Check if it's an API Gateway event
    if 'httpMethod' in event:
        path = event.get('path', '')
        if '/send_message' in path:
            return 'send_message'
        elif '/make_call' in path:
            return 'make_call'
        elif '/get_message' in path:
            return 'get_message'
    
    # Check if it's a direct Lambda invocation
    if 'function_type' in event:
        return event['function_type']
    
    # Default to send_message for backward compatibility
    return 'send_message' 