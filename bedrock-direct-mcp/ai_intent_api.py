import json
import requests
import boto3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

app = FastAPI(title="AI Intent API", description="AI-powered intent detection for driver-passenger communication")

# Initialize Bedrock client
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

class IntentRequest(BaseModel):
    booking_code: str
    user_type: str = "driver"  # driver or passenger
    user_input: str

class IntentResponse(BaseModel):
    intent: str
    confidence: float
    response: str
    success: bool
    mcp_result: Optional[Dict[str, Any]] = None

class AIIntentDetector:
    def __init__(self, mcp_server_url: str):
        self.mcp_server_url = mcp_server_url
        
    def detect_intent_with_bedrock(self, user_input: str) -> Dict[str, Any]:
        """Use AWS Bedrock to detect intent from user input"""
        
        # Create a prompt for intent detection
        prompt = f"""
You are a communication assistant for a Grab-like system. Your job is to understand natural language inputs from the user and route them to a backend API through structured parameters.

You will receive inputs like:
- "Send message to driver that I am waiting for him"
- "Call the passenger"
- "Show me the chat history"

You must extract and return these fields in the final API call:

- `user_type`: either "driver" or "passenger"
- `intent`: one of the following 3 values:
    - "send-message"
    - "make-call"
    - "get-message-list"
- `message`: only when the intent is "send-message", this is the actual content the user wants sent
- `user_input`: original user query (string)
- `confidence`: confidence score for intent (numeric)

---

🔹 Examples:

Input: "Send message to driver that I'm on the way"  
→ intent: `send-message`  
→ message: `"I'm on the way"`

Input: "Call the passenger now"  
→ intent: `make-call`  
→ message: `null`

Input: "Show me my message history"  
→ intent: `get-message-list`  
→ message: `null`

---

User Input: "{user_input}"

Respond with ONLY a JSON object in this format:
{{
    "intent": "send-message|make-call|get-message-list",
    "message": "extracted message content or null",
    "user_type": "driver|passenger",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation of why this intent was chosen"
}}
"""
        
        try:
            # Use Claude 3 Haiku for fast intent detection
            response = bedrock.invoke_model(
                modelId='anthropic.claude-3-haiku-20240307-v1:0',
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 200,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            
            response_body = json.loads(response['body'].read())
            content = response_body['content'][0]['text']
            
            # Extract JSON from response
            try:
                # Find JSON in the response
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end != 0:
                    json_str = content[start:end]
                    result = json.loads(json_str)
                    return result
                else:
                    raise ValueError("No JSON found in response")
                    
            except (json.JSONDecodeError, ValueError) as e:
                # Fallback to simple keyword matching
                return self.fallback_intent_detection(user_input)
                
        except Exception as e:
            print(f"Bedrock error: {str(e)}")
            # Fallback to simple keyword matching
            return self.fallback_intent_detection(user_input)
    
    def fallback_intent_detection(self, user_input: str) -> Dict[str, Any]:
        """Fallback intent detection using keyword matching"""
        user_input_lower = user_input.lower()
        
        if any(word in user_input_lower for word in ['send', 'message', 'text', 'write']):
            # Extract message content
            message = self._extract_message_fallback(user_input)
            return {
                "intent": "send-message",
                "message": message,
                "user_type": "driver",  # Default, will be overridden
                "confidence": 0.7,
                "reasoning": "Keyword matching: send/message/text detected"
            }
        elif any(word in user_input_lower for word in ['call', 'phone', 'ring', 'voice']):
            return {
                "intent": "make-call", 
                "message": None,
                "user_type": "driver",  # Default, will be overridden
                "confidence": 0.7,
                "reasoning": "Keyword matching: call/phone/ring detected"
            }
        elif any(word in user_input_lower for word in ['get', 'read', 'history', 'messages', 'list', 'show']):
            return {
                "intent": "get-message-list",
                "message": None,
                "user_type": "driver",  # Default, will be overridden
                "confidence": 0.7,
                "reasoning": "Keyword matching: get/read/history/messages/list/show detected"
            }
        else:
            return {
                "intent": "unknown",
                "message": None,
                "user_type": "driver",  # Default, will be overridden
                "confidence": 0.3,
                "reasoning": "No clear intent detected"
            }
    
    def _extract_message_fallback(self, user_input: str) -> str:
        """Simple message extraction for fallback"""
        import re
        content = user_input.lower()
        
        # Remove intent keywords
        for keyword in ['send', 'message', 'text', 'tell', 'say']:
            content = re.sub(rf'\b{keyword}\b', '', content)
        
        # Remove recipient phrases
        content = re.sub(r'\bto (driver|passenger)\b', '', content)
        
        # Remove connecting words
        content = re.sub(r'\b(that|saying|says|for)\b', '', content)
        
        # Clean up
        content = content.strip()
        return content if content else "Message sent"
    
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
    
    def process_request(self, booking_code: str, user_type: str, user_input: str) -> Dict[str, Any]:
        """Main method to process user input and return response"""
        
        # Detect intent using Bedrock
        intent_result = self.detect_intent_with_bedrock(user_input)
        intent = intent_result.get('intent', 'unknown')
        confidence = intent_result.get('confidence', 0.0)
        extracted_message = intent_result.get('message')
        
        # Map intent names to MCP server unified API actions
        intent_mapping = {
            'send-message': 'send_message',
            'make-call': 'make_call', 
            'get-message-list': 'get_messages'
        }
        mcp_action = intent_mapping.get(intent, intent)
        
        if intent == 'unknown':
            return {
                'intent': 'unknown',
                'confidence': confidence,
                'response': "I'm not sure what you want to do. You can ask me to:\n- Send a message to the passenger\n- Make a call to the passenger\n- Get message history",
                'success': False
            }
        
        # Call the unified API endpoint - pass detected intent as action
        unified_api_params = {
            'booking_code': booking_code,
            'user_input': user_input,  # Pass full user input to MCP
            'user_type': user_type,
            'action': mcp_action,  # Pass the mapped action
            'confidence': confidence  # Pass the confidence score
        }
        
        # If we have an extracted message from AI, use it instead of full user_input
        if intent == 'send-message' and extracted_message:
            unified_api_params['user_input'] = extracted_message
        
        result = self.call_mcp_server('api/v1/unified-api', 'POST', unified_api_params)
        
        # Format response based on MCP server response
        if result['success']:
            mcp_data = result['data']
            
            if intent == 'send-message':
                response = f"✅ Message sent successfully! The passenger will receive your message."
            elif intent == 'make-call':
                response = f"📞 Call initiated! Connecting you with the passenger."
            elif intent == 'get-message-list':
                messages = mcp_data.get('messages', [])
                if messages:
                    response = "📋 Recent messages:\n"
                    for msg in messages[-5:]:  # Show last 5 messages
                        response += f"- {msg.get('sender', 'Unknown')}: {msg.get('message', 'No content')}\n"
                else:
                    response = "📋 No messages found in the conversation history."
            else:
                # Handle any other intent
                response = mcp_data.get('text', f"✅ {intent} completed successfully!")
        else:
            response = f"❌ Error: {result.get('error', 'Unknown error occurred')}"
        
        return {
            'intent': intent,
            'confidence': confidence,
            'response': response,
            'success': result['success'],
            'mcp_result': result,
            'reasoning': intent_result.get('reasoning', '')
        }

# Initialize the AI intent detector
ai_detector = AIIntentDetector("http://mcp-server-env.eba-r23dy2pd.us-west-2.elasticbeanstalk.com")

@app.get("/")
async def root():
    return {
        "message": "AI Intent API for Driver-Passenger Communication",
        "endpoints": {
            "/detect_intent": "POST - Detect intent and call MCP server",
            "/health": "GET - Check if the API is healthy"
        }
    }

@app.post("/detect_intent", response_model=IntentResponse)
async def detect_intent(request: IntentRequest):
    """Detect intent from user input and call appropriate MCP server endpoint"""
    try:
        result = ai_detector.process_request(
            booking_code=request.booking_code,
            user_type=request.user_type,
            user_input=request.user_input
        )
        
        return IntentResponse(
            intent=result['intent'],
            confidence=result.get('confidence', 0.0),
            response=result['response'],
            success=result.get('success', False),
            mcp_result=result.get('mcp_result')
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI Intent API",
        "mcp_server": "http://mcp-server-env.eba-r23dy2pd.us-west-2.elasticbeanstalk.com",
        "bedrock": "enabled"
    }

@app.get("/test")
async def test_intent_detection():
    """Test the intent detection with sample inputs"""
    test_cases = [
        {
            "booking_code": "12345",
            "user_type": "driver",
            "user_input": "Send a message to the passenger saying I'll be there in 5 minutes"
        },
        {
            "booking_code": "12345",
            "user_type": "driver", 
            "user_input": "Make a call to the passenger"
        },
        {
            "booking_code": "12345",
            "user_type": "driver",
            "user_input": "Get the message history"
        }
    ]
    
    results = []
    for test_case in test_cases:
        result = ai_detector.process_request(**test_case)
        results.append({
            "input": test_case,
            "intent": result['intent'],
            "confidence": result.get('confidence', 0.0),
            "response": result['response'],
            "success": result.get('success', False),
            "reasoning": result.get('reasoning', '')
        })
    
    return {
        "test_results": results,
        "total_tests": len(results)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 