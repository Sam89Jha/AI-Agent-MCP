import json
import requests
import re
from typing import Dict, Any, Optional

class SimpleAIAgent:
    def __init__(self, mcp_server_url: str):
        self.mcp_server_url = mcp_server_url
        
    def detect_intent(self, user_input: str) -> Dict[str, Any]:
        """Simple intent detection using keyword matching"""
        user_input_lower = user_input.lower()
        
        # Intent patterns
        patterns = {
            'send_message': [
                r'send.*message',
                r'text.*passenger',
                r'write.*message',
                r'message.*send',
                r'tell.*passenger'
            ],
            'make_call': [
                r'make.*call',
                r'call.*passenger',
                r'voice.*call',
                r'phone.*call',
                r'ring.*passenger'
            ],
            'get_messages': [
                r'get.*message',
                r'read.*message',
                r'show.*message',
                r'history',
                r'conversation'
            ]
        }
        
        detected_intent = None
        confidence = 0
        
        for intent, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, user_input_lower):
                    detected_intent = intent
                    confidence = 0.8
                    break
            if detected_intent:
                break
        
        return {
            'intent': detected_intent,
            'confidence': confidence,
            'original_input': user_input
        }
    
    def extract_parameters(self, user_input: str, intent: str) -> Dict[str, Any]:
        """Extract parameters from user input"""
        params = {}
        
        # Extract booking code (simple pattern: 4-6 digit number)
        booking_match = re.search(r'\b(\d{4,6})\b', user_input)
        if booking_match:
            params['booking_code'] = booking_match.group(1)
        
        # Extract user type
        if 'driver' in user_input.lower():
            params['user_type'] = 'driver'
        elif 'passenger' in user_input.lower():
            params['user_type'] = 'passenger'
        else:
            params['user_type'] = 'driver'  # default
        
        # Extract message content for send_message
        if intent == 'send_message':
            # Remove intent keywords and extract the actual message
            message = user_input
            for keyword in ['send', 'message', 'text', 'tell', 'write']:
                message = re.sub(rf'\b{keyword}\b', '', message, flags=re.IGNORECASE)
            message = message.strip()
            if message:
                params['message'] = message
        
        return params
    
    def call_mcp_server(self, endpoint: str, method: str = 'GET', data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Call MCP server endpoint"""
        try:
            url = f"{self.mcp_server_url}/{endpoint}"
            
            if method.upper() == 'GET':
                response = requests.get(url, params=data or {}, timeout=30)
            else:
                response = requests.post(url, json=data or {}, timeout=30)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json(),
                    'status_code': response.status_code
                }
            else:
                return {
                    'success': False,
                    'error': f'MCP server error: {response.status_code} - {response.text}',
                    'status_code': response.status_code
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Connection error: {str(e)}',
                'status_code': 500
            }
    
    def process_request(self, user_input: str) -> Dict[str, Any]:
        """Main method to process user input and return response"""
        # Detect intent
        intent_result = self.detect_intent(user_input)
        intent = intent_result['intent']
        
        if not intent:
            return {
                'response': "I'm not sure what you want to do. You can ask me to:\n- Send a message to the passenger\n- Make a call to the passenger\n- Get message history",
                'intent': 'unknown',
                'success': False
            }
        
        # Extract parameters
        params = self.extract_parameters(user_input, intent)
        
        # Call appropriate MCP endpoint
        if intent == 'send_message':
            if not params.get('message'):
                return {
                    'response': "What message would you like to send to the passenger?",
                    'intent': intent,
                    'success': False,
                    'needs_message': True
                }
            
            result = self.call_mcp_server('send_message', 'POST', params)
            
        elif intent == 'make_call':
            result = self.call_mcp_server('make_call', 'POST', params)
            
        elif intent == 'get_messages':
            result = self.call_mcp_server('get_messages', 'GET', params)
        
        else:
            return {
                'response': f"I detected intent: {intent} but don't know how to handle it yet.",
                'intent': intent,
                'success': False
            }
        
        # Format response
        if result['success']:
            if intent == 'send_message':
                response = f"✅ Message sent successfully! The passenger will receive your message."
            elif intent == 'make_call':
                response = f"📞 Call initiated! Connecting you with the passenger."
            elif intent == 'get_messages':
                messages = result['data'].get('messages', [])
                if messages:
                    response = "📋 Recent messages:\n"
                    for msg in messages[-5:]:  # Show last 5 messages
                        response += f"- {msg.get('user_type', 'Unknown')}: {msg.get('message', 'No content')}\n"
                else:
                    response = "📋 No messages found in the conversation history."
        else:
            response = f"❌ Error: {result.get('error', 'Unknown error occurred')}"
        
        return {
            'response': response,
            'intent': intent,
            'success': result['success'],
            'mcp_result': result
        }

# Example usage
if __name__ == "__main__":
    # Initialize agent
    agent = SimpleAIAgent("http://mcp-server-env.eba-r23dy2pd.us-west-2.elasticbeanstalk.com")
    
    # Test examples
    test_inputs = [
        "Send a message to the passenger saying I'll be there in 5 minutes",
        "Make a call to the passenger",
        "Get the message history",
        "Send message: I'm running late",
        "Call the passenger now"
    ]
    
    print("🤖 Simple AI Agent Test")
    print("=" * 50)
    
    for user_input in test_inputs:
        print(f"\nUser: {user_input}")
        result = agent.process_request(user_input)
        print(f"Agent: {result['response']}")
        print(f"Intent: {result['intent']}")
        print("-" * 30) 