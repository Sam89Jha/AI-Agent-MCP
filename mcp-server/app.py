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
class UnifiedAPIRequest(BaseModel):
    booking_code: str = Field(..., description="Booking code")
    user_input: str = Field(..., description="User voice/text input")
    user_type: str = Field(..., description="User type: 'driver' or 'passenger'")
    intent: Optional[str] = Field(None, description="Detected intent")
    confidence: Optional[float] = Field(None, description="Intent confidence score")
    action: Optional[str] = Field(None, description="Action to perform")
    message_type: Optional[str] = Field("text", description="Type of message")
    call_type: Optional[str] = Field("voice", description="Type of call")
    duration: Optional[int] = Field(0, description="Call duration in seconds")

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    region: str
    services: Dict[str, str]

# Health check endpoint
@app.get("/healthcheck", response_model=HealthResponse)
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

# Unified API endpoint - main entry point for all interactions
@app.post("/api/v1/unified-api", response_model=Dict[str, Any])
async def unified_api_handler(request: UnifiedAPIRequest):
    """
    Unified API endpoint for all interactions.
    This endpoint receives requests and routes them to appropriate API Gateway endpoints based on intent or action.
    """
    try:
        logger.info(f"Unified API request received: {request.booking_code} - {request.user_input[:50]}...")
        
        # Determine the action based on intent or explicit action
        action = request.action
        intent = request.intent
        
        if not action and not intent:
            logger.error("No action or intent provided")
            raise HTTPException(status_code=400, detail="Action or intent is required")
        
        # Use action if provided, otherwise use intent
        target_action = action if action else intent
        logger.info(f"Using action/intent: {target_action}")
        
        # Route based on action/intent
        if target_action in ["send_message", "message", "send"]:
            return await _handle_send_message(request)
        elif target_action in ["make_call", "call", "phone"]:
            return await _handle_make_call(request)
        elif target_action in ["get_messages", "messages", "history"]:
            return await _handle_get_messages(request)
        else:
            logger.error(f"Unknown action/intent: {target_action}")
            raise HTTPException(status_code=400, detail=f"Unknown action/intent: {target_action}")
            
    except Exception as e:
        logger.error(f"Unified API handler error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Unified API handlers - these call API Gateway
async def _handle_send_message(request: UnifiedAPIRequest) -> Dict[str, Any]:
    """Handle send message intent by calling API Gateway"""
    # Use the user_input directly as it should already be the extracted message from AI
    message_content = request.user_input
    
    # Call send_message API Gateway
    payload = {
        "booking_code": request.booking_code,
        "message": message_content,
        "sender": request.user_type,
        "timestamp": datetime.now().isoformat(),
        "message_type": request.message_type or "text"
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

async def _handle_make_call(request: UnifiedAPIRequest) -> Dict[str, Any]:
    """Handle make call intent by calling API Gateway"""
    # Determine caller type
    caller_type = request.user_type
    
    # Call make_call API Gateway
    payload = {
        "booking_code": request.booking_code,
        "caller_type": caller_type,
        "call_type": request.call_type or "voice",
        "action": "initiate",
        "duration": request.duration or 0,
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

async def _handle_get_messages(request: UnifiedAPIRequest) -> Dict[str, Any]:
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