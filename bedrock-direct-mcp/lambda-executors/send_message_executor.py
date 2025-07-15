import json
import requests
import os

def lambda_handler(event, context):
    """
    Lambda executor for send_message action group
    Calls MCP server send_message endpoint
    """
    try:
        # Extract parameters from the event
        body = event.get('body', {})
        if isinstance(body, str):
            body = json.loads(body)
        
        # Extract message parameters
        booking_code = body.get('booking_code')
        user_type = body.get('user_type', 'driver')  # driver or passenger
        message = body.get('message')
        
        if not booking_code or not message:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required parameters: booking_code and message'
                })
            }
        
        # MCP server URL
        mcp_server_url = os.environ.get('MCP_SERVER_URL', 'http://mcp-server-env.eba-r23dy2pd.us-west-2.elasticbeanstalk.com')
        
        # Call MCP server
        response = requests.post(
            f"{mcp_server_url}/send_message",
            json={
                'booking_code': booking_code,
                'user_type': user_type,
                'message': message
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'message': 'Message sent successfully',
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