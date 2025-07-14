from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import os
import logging
import requests
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import traceback
import sys
import os
sys.path.append('..')
from config import get_config, get_cors_origins, get_backend_api_url

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MCP Server",
    description="Pure Orchestrator - Routes requests to API Gateway",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Get configuration
config = get_config()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTP client for API Gateway calls
class APIGatewayClient:
    """HTTP client for calling API Gateway endpoints."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'MCP-Server/1.0'
        })
    
    def call_send_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Call send_message API via HTTP."""
        try:
            url = get_backend_api_url('send_message')
            logger.info(f"Calling send_message API: {url}")
            
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Send message API response: {result}")
            return {
                'statusCode': response.status_code,
                'body': json.dumps(result)
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Send message API error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"API Gateway error: {str(e)}")
    
    def call_make_call(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Call make_call API via HTTP."""
        try:
            url = get_backend_api_url('make_call')
            logger.info(f"Calling make_call API: {url}")
            
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Make call API response: {result}")
            return {
                'statusCode': response.status_code,
                'body': json.dumps(result)
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Make call API error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"API Gateway error: {str(e)}")
    
    def call_get_message(self, booking_code: str) -> Dict[str, Any]:
        """Call get_message API via HTTP."""
        try:
            url = get_backend_api_url('get_message')
            params = {'booking_code': booking_code}
            logger.info(f"Calling get_message API: {url} with params: {params}")
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Get message API response: {result}")
            return {
                'statusCode': response.status_code,
                'body': json.dumps(result)
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Get message API error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"API Gateway error: {str(e)}")

# Initialize API Gateway client
api_gateway_client = APIGatewayClient()

# Pydantic models
class MessageRequest(BaseModel):
    booking_code: str = Field(..., description="Booking code for the conversation")
    message: str = Field(..., description="Message content")
    sender: str = Field(..., description="Sender type: 'driver' or 'passenger'")
    message_type: Optional[str] = Field("text", description="Type of message")

class CallRequest(BaseModel):
    booking_code: str = Field(..., description="Booking code for the call")
    caller_type: str = Field(..., description="Caller type: 'driver' or 'passenger'")
    call_type: str = Field("voice", description="Type of call: 'voice' or 'video'")
    action: str = Field(..., description="Call action: 'initiate', 'accept', 'reject', 'end'")
    duration: Optional[int] = Field(0, description="Call duration in seconds")

class AIAgentRequest(BaseModel):
    booking_code: str = Field(..., description="Booking code")
    user_input: str = Field(..., description="User voice/text input")
    user_type: str = Field(..., description="User type: 'driver' or 'passenger'")
    intent: Optional[str] = Field(None, description="Detected intent")
    confidence: Optional[float] = Field(None, description="Intent confidence score")

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    region: str
    services: Dict[str, str]

# Health check endpoint
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "MCP Server is running",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            version="1.0.0",
            region="us-east-1",
            services={
                "api_gateway": "healthy"
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# AI Agent endpoint - main entry point for AI interactions
@app.post("/api/v1/ai_agent", response_model=Dict[str, Any])
async def ai_agent_handler(request: AIAgentRequest):
    """
    Main endpoint for AI Agent interactions.
    This endpoint receives requests from the AI Agent and routes them to appropriate API Gateway endpoints.
    """
    try:
        logger.info(f"AI Agent request received: {request.booking_code} - {request.user_input[:50]}...")
        
        # Determine intent if not provided
        intent = request.intent
        if not intent:
            intent = _detect_intent(request.user_input)
        
        logger.info(f"Detected intent: {intent}")
        
        # Route based on intent
        if intent in ["send_message", "message", "send"]:
            return await _handle_send_message(request)
        elif intent in ["make_call", "call", "phone"]:
            return await _handle_make_call(request)
        elif intent in ["get_messages", "messages", "history"]:
            return await _handle_get_messages(request)
        else:
            # Default to send message if intent unclear
            return await _handle_send_message(request)
            
    except Exception as e:
        logger.error(f"AI Agent handler error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Send message endpoint - MCP only orchestrates, API Gateway handles everything
@app.post("/api/v1/send_message", response_model=Dict[str, Any])
async def send_message(request: MessageRequest):
    """
    Send a message by calling API Gateway.
    MCP server only orchestrates, API Gateway handles storage and WebSocket delivery.
    """
    try:
        logger.info(f"Send message request: {request.booking_code}")
        
        # Prepare payload for API Gateway
        payload = {
            "booking_code": request.booking_code,
            "message": request.message,
            "sender": request.sender,
            "timestamp": datetime.now().isoformat(),
            "message_type": request.message_type
        }
        
        # Call API Gateway
        logger.info(f"Calling API Gateway with payload: {payload}")
        result = api_gateway_client.call_send_message(payload)
        logger.info(f"API Gateway response: {result}")
        
        if result.get('statusCode') != 200:
            lambda_response = json.loads(result.get('body', '{}'))
            raise HTTPException(status_code=result.get('statusCode', 500), detail=lambda_response.get('error', 'Unknown error'))
        
        # Parse Lambda response
        lambda_response = json.loads(result.get('body', '{}'))
        logger.info(f"Parsed Lambda response: {lambda_response}")
        
        return lambda_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Send message error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Make call endpoint - MCP only orchestrates, API Gateway handles everything
@app.post("/api/v1/make_call", response_model=Dict[str, Any])
async def make_call(request: CallRequest):
    """
    Handle call operations by calling API Gateway.
    MCP server only orchestrates, API Gateway handles call logic and WebSocket delivery.
    """
    try:
        logger.info(f"Make call request: {request.booking_code} - {request.action}")
        
        # Prepare payload for API Gateway
        payload = {
            "booking_code": request.booking_code,
            "caller_type": request.caller_type,
            "call_type": request.call_type,
            "action": request.action,
            "duration": request.duration,
            "timestamp": datetime.now().isoformat()
        }
        
        # Call API Gateway
        result = api_gateway_client.call_make_call(payload)
        
        if result.get('statusCode') != 200:
            lambda_response = json.loads(result.get('body', '{}'))
            raise HTTPException(status_code=result.get('statusCode', 500), detail=lambda_response.get('error', 'Unknown error'))
        
        # Parse Lambda response
        lambda_response = json.loads(result.get('body', '{}'))
        
        return lambda_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Make call error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Get messages endpoint - MCP only orchestrates, API Gateway handles everything
@app.get("/api/v1/get_message/{booking_code}", response_model=Dict[str, Any])
async def get_message(booking_code: str):
    """
    Get messages by calling API Gateway.
    MCP server only orchestrates, API Gateway handles retrieval and caching.
    """
    try:
        logger.info(f"Get message request: {booking_code}")
        
        # Call API Gateway
        result = api_gateway_client.call_get_message(booking_code)
        
        if result.get('statusCode') != 200:
            lambda_response = json.loads(result.get('body', '{}'))
            raise HTTPException(status_code=result.get('statusCode', 500), detail=lambda_response.get('error', 'Unknown error'))
        
        # Parse Lambda response
        lambda_response = json.loads(result.get('body', '{}'))
        
        return lambda_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get message error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Intent detection helper
def _detect_intent(user_input: str) -> str:
    """Detect intent from user input"""
    input_lower = user_input.lower()
    
    # Call-related keywords
    call_keywords = ['call', 'phone', 'ring', 'dial', 'contact']
    if any(keyword in input_lower for keyword in call_keywords):
        return 'make_call'
    
    # Message-related keywords
    message_keywords = ['send', 'message', 'text', 'say', 'tell']
    if any(keyword in input_lower for keyword in message_keywords):
        return 'send_message'
    
    # History-related keywords
    history_keywords = ['history', 'messages', 'previous', 'past']
    if any(keyword in input_lower for keyword in history_keywords):
        return 'get_messages'
    
    # Default to send message
    return 'send_message'

# Message content extraction helper
def _extract_message_content(user_input: str, intent: str) -> str:
    """Extract message content from user input based on intent"""
    if intent == 'make_call':
        # Extract call-related content
        call_indicators = ['call', 'phone', 'ring', 'dial']
        for indicator in call_indicators:
            if indicator in user_input.lower():
                # Remove the call indicator and clean up
                content = user_input.lower().replace(indicator, '').strip()
                return f"Call {content}" if content else "Call initiated"
        return "Call initiated"
    
    elif intent == 'send_message':
        # Extract message content
        message_indicators = ['send', 'message', 'text', 'say', 'tell']
        for indicator in message_indicators:
            if indicator in user_input.lower():
                # Remove the message indicator and clean up
                content = user_input.lower().replace(indicator, '').strip()
                return content if content else "Message sent"
        return user_input
    
    else:
        return user_input

# AI Agent handlers - these call API Gateway
async def _handle_send_message(request: AIAgentRequest) -> Dict[str, Any]:
    """Handle send message intent by calling API Gateway"""
    message_content = _extract_message_content(request.user_input, 'send_message')
    
    # Call send_message API Gateway
    payload = {
        "booking_code": request.booking_code,
        "message": message_content,
        "sender": request.user_type,
        "timestamp": datetime.now().isoformat(),
        "message_type": "text"
    }
    
    result = api_gateway_client.call_send_message(payload)
    
    lambda_response = json.loads(result.get('body', '{}'))
    
    return {
        "success": True,
        "data": {
            "text": message_content,
            "type": "text",
            "sender": request.user_type
        }
    }

async def _handle_make_call(request: AIAgentRequest) -> Dict[str, Any]:
    """Handle make call intent by calling API Gateway"""
    # Determine caller type
    caller_type = request.user_type
    
    # Call make_call API Gateway
    payload = {
        "booking_code": request.booking_code,
        "caller_type": caller_type,
        "call_type": "voice",
        "action": "initiate",
        "duration": 0,
        "timestamp": datetime.now().isoformat()
    }
    
    result = api_gateway_client.call_make_call(payload)
    
    lambda_response = json.loads(result.get('body', '{}'))
    
    return {
        "success": True,
        "data": {
            "text": "Call initiated",
            "type": "call",
            "caller_type": caller_type
        }
    }

async def _handle_get_messages(request: AIAgentRequest) -> Dict[str, Any]:
    """Handle get messages intent by calling API Gateway"""
    # Call get_message API Gateway
    result = api_gateway_client.call_get_message(request.booking_code)
    
    lambda_response = json.loads(result.get('body', '{}'))
    
    return {
        "success": True,
        "data": {
            "text": "Messages retrieved",
            "type": "history",
            "messages": lambda_response.get('data', {}).get('messages', [])
        }
    }

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    ) 