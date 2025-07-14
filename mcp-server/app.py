from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import boto3
import json
import os
import logging
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import traceback
import sys
import os
sys.path.append('..')
from config import get_config, get_cors_origins

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MCP Server",
    description="API Gateway between AI Agent and Backend Services",
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

# WebSocket connection manager for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, booking_code: str):
        await websocket.accept()
        if booking_code not in self.active_connections:
            self.active_connections[booking_code] = []
        self.active_connections[booking_code].append(websocket)
        logger.info(f"WebSocket connected for booking {booking_code}. Total connections: {len(self.active_connections[booking_code])}")
    
    def disconnect(self, websocket: WebSocket, booking_code: str):
        if booking_code in self.active_connections:
            self.active_connections[booking_code].remove(websocket)
            if not self.active_connections[booking_code]:
                del self.active_connections[booking_code]
        logger.info(f"WebSocket disconnected for booking {booking_code}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast_to_booking(self, message: str, booking_code: str):
        if booking_code in self.active_connections:
            for connection in self.active_connections[booking_code]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Error sending message to WebSocket: {e}")
                    # Remove broken connection
                    self.active_connections[booking_code].remove(connection)

manager = ConnectionManager()

# AWS clients (only for non-local environments)
aws_region = config.get('aws_region', 'us-east-1')
lambda_client = None
if not config.is_local():
    lambda_client = boto3.client('lambda', region_name=aws_region)

# Local Lambda API handlers for local testing
class LocalLambdaHandler:
    """Local handler to simulate Lambda functions for local testing."""
    
    def __init__(self):
        self.message_cache = {}
        self.call_cache = {}
    
    async def invoke_send_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Local implementation of send_message Lambda."""
        try:
            booking_code = payload.get('booking_code')
            message = payload.get('message')
            sender = payload.get('sender')
            message_type = payload.get('message_type', 'text')
            timestamp = payload.get('timestamp', datetime.now().isoformat())
            
            # Generate message ID
            message_id = f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(message) % 1000:03d}"
            
            # Store in local cache
            if booking_code not in self.message_cache:
                self.message_cache[booking_code] = []
            
            message_data = {
                'id': message_id,
                'booking_code': booking_code,
                'message': message,
                'sender': sender,
                'timestamp': timestamp,
                'type': message_type
            }
            
            self.message_cache[booking_code].append(message_data)
            
            # Limit cache to last 100 messages
            if len(self.message_cache[booking_code]) > 100:
                self.message_cache[booking_code].pop(0)
            
            # Broadcast via WebSocket
            websocket_message = {
                'type': 'new_message',
                'booking_code': booking_code,
                'message': message_data
            }
            
            if booking_code:
                await manager.broadcast_to_booking(json.dumps(websocket_message), booking_code)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'message': 'Message sent successfully',
                    'data': message_data
                })
            }
            
        except Exception as e:
            logger.error(f"Local send_message error: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'success': False,
                    'error': f'Internal server error: {str(e)}'
                })
            }
    
    async def invoke_make_call(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Local implementation of make_call Lambda."""
        try:
            booking_code = payload.get('booking_code')
            caller_type = payload.get('caller_type')
            call_type = payload.get('call_type', 'voice')
            action = payload.get('action')
            duration = payload.get('duration', 0)
            timestamp = payload.get('timestamp', datetime.now().isoformat())
            
            # Determine callee type
            callee_type = 'passenger' if caller_type == 'driver' else 'driver'
            
            # Store call state
            call_state = {
                'booking_code': booking_code,
                'caller_type': caller_type,
                'callee_type': callee_type,
                'call_type': call_type,
                'status': action,
                'timestamp': timestamp,
                'duration': duration
            }
            
            self.call_cache[booking_code] = call_state
            
            # Prepare WebSocket messages based on action
            if action == 'initiate':
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
                    'message': f'Incoming call from {caller_type.title() if caller_type else "Unknown"}',
                    'show_buttons': ['accept', 'reject']
                }
                
                if booking_code:
                    await manager.broadcast_to_booking(json.dumps(caller_message), booking_code)
                    await manager.broadcast_to_booking(json.dumps(callee_message), booking_code)
                
            elif action == 'accept':
                connected_message = {
                    'type': 'call_state_update',
                    'call_state': 'connected',
                    'user_type': caller_type,
                    'message': 'Call connected',
                    'show_buttons': ['end']
                }
                
                if booking_code:
                    await manager.broadcast_to_booking(json.dumps(connected_message), booking_code)
                
            elif action == 'reject':
                ended_message = {
                    'type': 'call_state_update',
                    'call_state': 'ended',
                    'user_type': caller_type,
                    'message': f'Call rejected by {caller_type.title() if caller_type else "Unknown"}',
                    'show_buttons': []
                }
                
                if booking_code:
                    await manager.broadcast_to_booking(json.dumps(ended_message), booking_code)
                
            elif action == 'end':
                ended_message = {
                    'type': 'call_state_update',
                    'call_state': 'ended',
                    'user_type': caller_type,
                    'message': f'Call ended - Duration: {duration} seconds',
                    'show_buttons': []
                }
                
                if booking_code:
                    await manager.broadcast_to_booking(json.dumps(ended_message), booking_code)
                
                # Clear call state
                if booking_code in self.call_cache:
                    del self.call_cache[booking_code]
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'message': f'Call {action} successfully',
                    'data': call_state
                })
            }
            
        except Exception as e:
            logger.error(f"Local make_call error: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'success': False,
                    'error': f'Internal server error: {str(e)}'
                })
            }
    
    async def invoke_get_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Local implementation of get_message Lambda."""
        try:
            booking_code = payload.get('booking_code')
            
            # Get messages from local cache
            messages = self.message_cache.get(booking_code, [])
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'message': 'Messages retrieved successfully',
                    'data': {
                        'messages': messages,
                        'count': len(messages),
                        'source': 'local_cache'
                    }
                })
            }
            
        except Exception as e:
            logger.error(f"Local get_message error: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'success': False,
                    'error': f'Internal server error: {str(e)}'
                })
            }

# Initialize local Lambda handler
local_lambda_handler = LocalLambdaHandler()

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
        # Test Lambda connectivity (only for non-local)
        lambda_status = "healthy"
        if not config.is_local() and lambda_client:
            try:
                lambda_client.list_functions(MaxItems=1)
            except Exception as e:
                lambda_status = f"error: {str(e)}"
        else:
            lambda_status = "local handlers (local environment)"
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            version="1.0.0",
            region=aws_region,
            services={
                "lambda": lambda_status
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
    This endpoint receives requests from the AI Agent and routes them to appropriate Lambda functions.
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

# Send message endpoint - MCP only orchestrates, Lambda handles everything
@app.post("/api/v1/send_message", response_model=Dict[str, Any])
async def send_message(request: MessageRequest):
    """
    Send a message by calling Lambda function.
    MCP server only orchestrates, Lambda handles storage and WebSocket delivery.
    """
    try:
        logger.info(f"Send message request: {request.booking_code}")
        
        # Prepare payload for Lambda
        payload = {
            "booking_code": request.booking_code,
            "message": request.message,
            "sender": request.sender,
            "timestamp": datetime.now().isoformat(),
            "message_type": request.message_type
        }
        
        # Call Lambda function (local or AWS)
        if config.is_local():
            # Use local handler
            result = await local_lambda_handler.invoke_send_message(payload)
        else:
            # Use AWS Lambda
            function_name = config.get_lambda_function_name('send_message')
            if lambda_client is None:
                raise HTTPException(status_code=500, detail="Lambda client not available")
            # Type assertion for lambda_client
            lambda_client_typed = lambda_client  # type: ignore
            response = lambda_client_typed.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') != 200:
            lambda_response = json.loads(result.get('body', '{}'))
            raise HTTPException(status_code=result.get('statusCode', 500), detail=lambda_response.get('error', 'Unknown error'))
        
        # Parse Lambda response
        lambda_response = json.loads(result.get('body', '{}'))
        
        return {
            "success": True,
            "message": "Message sent successfully",
            "data": lambda_response.get('data', {}),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Send message error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Make call endpoint - MCP only orchestrates, Lambda handles everything
@app.post("/api/v1/make_call", response_model=Dict[str, Any])
async def make_call(request: CallRequest):
    """
    Handle call operations by calling Lambda function.
    MCP server only orchestrates, Lambda handles call logic and WebSocket delivery.
    """
    try:
        logger.info(f"Make call request: {request.booking_code} - {request.action}")
        
        # Prepare payload for Lambda
        payload = {
            "booking_code": request.booking_code,
            "caller_type": request.caller_type,
            "call_type": request.call_type,
            "action": request.action,
            "duration": request.duration,
            "timestamp": datetime.now().isoformat()
        }
        
        # Call Lambda function (local or AWS)
        if config.is_local():
            # Use local handler
            result = await local_lambda_handler.invoke_make_call(payload)
        else:
            # Use AWS Lambda
            function_name = config.get_lambda_function_name('make_call')
            if lambda_client is None:
                raise HTTPException(status_code=500, detail="Lambda client not available")
            response = lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') != 200:
            lambda_response = json.loads(result.get('body', '{}'))
            raise HTTPException(status_code=result.get('statusCode', 500), detail=lambda_response.get('error', 'Unknown error'))
        
        # Parse Lambda response
        lambda_response = json.loads(result.get('body', '{}'))
        
        return {
            "success": True,
            "message": f"Call {request.action} successfully",
            "data": lambda_response.get('data', {}),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Make call error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Get messages endpoint - MCP only orchestrates, Lambda handles everything
@app.get("/api/v1/get_message/{booking_code}", response_model=Dict[str, Any])
async def get_message(booking_code: str):
    """
    Get messages by calling Lambda function.
    MCP server only orchestrates, Lambda handles retrieval and caching.
    """
    try:
        logger.info(f"Get message request: {booking_code}")
        
        # Prepare payload for Lambda
        payload = {
            "booking_code": booking_code
        }
        
        # Call Lambda function (local or AWS)
        if config.is_local():
            # Use local handler
            result = await local_lambda_handler.invoke_get_message(payload)
        else:
            # Use AWS Lambda
            function_name = config.get_lambda_function_name('get_message')
            if lambda_client is None:
                raise HTTPException(status_code=500, detail="Lambda client not available")
            response = lambda_client.invoke(
                FunctionName=function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') != 200:
            lambda_response = json.loads(result.get('body', '{}'))
            raise HTTPException(status_code=result.get('statusCode', 500), detail=lambda_response.get('error', 'Unknown error'))
        
        # Parse Lambda response
        lambda_response = json.loads(result.get('body', '{}'))
        
        return {
            "success": True,
            "message": "Messages retrieved successfully",
            "data": lambda_response.get('data', {}),
            "timestamp": datetime.now().isoformat()
        }
        
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

# AI Agent handlers - these call Lambda functions
async def _handle_send_message(request: AIAgentRequest) -> Dict[str, Any]:
    """Handle send message intent by calling Lambda"""
    message_content = _extract_message_content(request.user_input, 'send_message')
    
    # Call send_message Lambda
    payload = {
        "booking_code": request.booking_code,
        "message": message_content,
        "sender": request.user_type,
        "timestamp": datetime.now().isoformat(),
        "message_type": "text"
    }
    
    if config.is_local():
        result = await local_lambda_handler.invoke_send_message(payload)
    else:
        function_name = config.get_lambda_function_name('send_message')
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        result = json.loads(response['Payload'].read())
    
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
    """Handle make call intent by calling Lambda"""
    # Determine caller type
    caller_type = request.user_type
    
    # Call make_call Lambda
    payload = {
        "booking_code": request.booking_code,
        "caller_type": caller_type,
        "call_type": "voice",
        "action": "initiate",
        "duration": 0,
        "timestamp": datetime.now().isoformat()
    }
    
    if config.is_local():
        result = await local_lambda_handler.invoke_make_call(payload)
    else:
        function_name = config.get_lambda_function_name('make_call')
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        result = json.loads(response['Payload'].read())
    
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
    """Handle get messages intent by calling Lambda"""
    # Call get_message Lambda
    payload = {
        "booking_code": request.booking_code
    }
    
    if config.is_local():
        result = await local_lambda_handler.invoke_get_message(payload)
    else:
        function_name = config.get_lambda_function_name('get_message')
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        result = json.loads(response['Payload'].read())
    
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

# WebSocket endpoint for real-time updates
@app.websocket("/ws/{booking_code}")
async def websocket_endpoint(websocket: WebSocket, booking_code: str):
    await manager.connect(websocket, booking_code)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, booking_code) 