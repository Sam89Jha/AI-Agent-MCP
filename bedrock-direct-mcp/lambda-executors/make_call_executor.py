import json
import requests
import os

def lambda_handler(event, context):
    """
    Lambda executor for make_call action group
    Calls MCP server make_call endpoint
    """
    try:
        # Extract parameters from the event
        body = event.get('body', {})
        if isinstance(body, str):
            body = json.loads(body)
        
        # Extract call parameters
        booking_code = body.get('booking_code')
        user_type = body.get('user_type', 'driver')  # driver or passenger
        
        if not booking_code:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required parameter: booking_code'
                })
            }
        
        # MCP server URL
        mcp_server_url = os.environ.get('MCP_SERVER_URL', 'http://mcp-server-env.eba-r23dy2pd.us-west-2.elasticbeanstalk.com')
        
        # Call MCP server
        response = requests.post(
            f"{mcp_server_url}/make_call",
            json={
                'booking_code': booking_code,
                'user_type': user_type
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'message': 'Call initiated successfully',
                    'data': result
                })
            }
        else:
            return {
                'statusCode': response.status_code,
                'body': json.dumps({
                    'error': f'MCP server error: {response.text}'
                })
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Lambda executor error: {str(e)}'
            })
        } 