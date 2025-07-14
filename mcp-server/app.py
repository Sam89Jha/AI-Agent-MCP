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

# Simple in-memory cache for local development
class InMemoryCache:
    def __init__(self):
        self._data = {}
        self._call_logs = {}  # Store call logs for each booking
    
    def set(self, key, value):
        self._data[key] = value
    
    def get(self, key, default=None):
        return self._data.get(key, default)
    
    def add_call_log(self, booking_code: str, call_log: dict):
        """Add a call log entry for a booking"""
        if booking_code not in self._call_logs:
            self._call_logs[booking_code] = []
        self._call_logs[booking_code].append(call_log)
    
    def get_call_logs(self, booking_code: str):
        """Get call logs for a booking"""
        return self._call_logs.get(booking_code, [])

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

# Initialize in-memory cache for local environment
cache = InMemoryCache()

# WebSocket connection manager
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

# Pydantic models
class MessageRequest(BaseModel):
    booking_code: str = Field(..., description="Booking code for the conversation")
    message: str = Field(..., description="Message content")
    sender: str = Field(..., description="Sender type: 'driver' or 'passenger'")
    message_type: Optional[str] = Field("text", description="Type of message")

class CallRequest(BaseModel):
    booking_code: str = Field(..., description="Booking code for the call")
    call_type: str = Field("voice", description="Type of call: 'voice' or 'video'")
    duration: Optional[int] = Field(0, description="Call duration in seconds")
    status: Optional[str] = Field("initiated", description="Call status")

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
            lambda_status = "not used (local environment)"
        
        # Test in-memory cache
        cache_status = "healthy"
        try:
            cache.set("health_test", "test_value")
            test_value = cache.get("health_test")
            if test_value != "test_value":
                cache_status = "error: cache not working"
        except Exception as e:
            cache_status = f"error: {str(e)}"
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            version="1.0.0",
            region=aws_region,
            services={
                "lambda": lambda_status,
                "cache": cache_status
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
    This endpoint receives requests from the AI Agent and routes them to appropriate handlers.
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

# Send message endpoint
@app.post("/api/v1/send_message", response_model=Dict[str, Any])
async def send_message(request: MessageRequest):
    """
    Send a message and store it in cache or DynamoDB.
    """
    try:
        logger.info(f"Send message request: {request.booking_code}")
        
        if config.is_local():
            # Use in-memory cache for local environment
            message_data = {
                "booking_code": request.booking_code,
                "message": request.message,
                "sender": request.sender,
                "timestamp": datetime.now().isoformat(),
                "message_type": request.message_type
            }
            
            # Store in cache
            cache_key = f"message:{request.booking_code}:{datetime.now().timestamp()}"
            cache.set(cache_key, message_data)
            
            # Also store in messages list for the booking
            messages_key = f"messages:{request.booking_code}"
            messages = cache.get(messages_key, [])
            if messages is None:
                messages = []
            messages.append(message_data)
            cache.set(messages_key, messages)
            
            # Map to frontend format
            frontend_message = {
                "id": f"{message_data.get('booking_code', '')}_{message_data.get('timestamp', '')}",
                "text": message_data.get("message", ""),
                "sender": message_data.get("sender", ""),
                "timestamp": message_data.get("timestamp", ""),
                "type": message_data.get("message_type", "text")
            }
            
            return {
                "success": True,
                "message": "Message sent successfully",
                "data": frontend_message,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Use Lambda for non-local environments
            payload = {
                "booking_code": request.booking_code,
                "message": request.message,
                "sender": request.sender,
                "timestamp": datetime.now().isoformat(),
                "message_type": request.message_type
            }
            
            # Invoke Lambda function
            function_name = config.get_lambda_function_name('send_message')
            if lambda_client:
                response = lambda_client.invoke(
                    FunctionName=function_name,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(payload)
                )
            else:
                raise HTTPException(status_code=500, detail="Lambda client not available")
            
            # Parse response
            result = json.loads(response['Payload'].read())
            
            if response['StatusCode'] != 200:
                raise HTTPException(status_code=500, detail="Lambda function error")
            
            # Parse Lambda response
            lambda_response = json.loads(result.get('body', '{}'))
            
            if result.get('statusCode') != 200:
                raise HTTPException(status_code=result.get('statusCode', 500), detail=lambda_response.get('error', 'Unknown error'))
            
            # Map to frontend format
            frontend_message = {
                "id": f"{lambda_response.get('booking_code', '')}_{lambda_response.get('timestamp', '')}",
                "text": lambda_response.get("message", ""),
                "sender": lambda_response.get("sender", ""),
                "timestamp": lambda_response.get("timestamp", ""),
                "type": lambda_response.get("message_type", "text")
            }
            
            return {
                "success": True,
                "message": "Message sent successfully",
                "data": frontend_message,
                "timestamp": datetime.now().isoformat()
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Send message error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Make call endpoint
@app.post("/api/v1/make_call", response_model=Dict[str, Any])
async def make_call(request: CallRequest):
    """
    Make a call and log it in cache or DynamoDB.
    """
    try:
        logger.info(f"Make call request: {request.booking_code}")
        
        if config.is_local():
            # Use in-memory cache for local environment
            call_data = {
                "booking_code": request.booking_code,
                "call_type": request.call_type,
                "duration": request.duration,
                "timestamp": datetime.now().isoformat(),
                "status": request.status
            }
            
            # Store in cache
            cache_key = f"call:{request.booking_code}:{datetime.now().timestamp()}"
            cache.set(cache_key, call_data)
            
            # Also store in calls list for the booking
            calls_key = f"calls:{request.booking_code}"
            calls = cache.get(calls_key, [])
            if calls is None:
                calls = []
            calls.append(call_data)
            cache.set(calls_key, calls)
            
            return {
                "success": True,
                "message": "Call initiated successfully",
                "data": call_data,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Use Lambda for non-local environments
            payload = {
                "booking_code": request.booking_code,
                "call_type": request.call_type,
                "duration": request.duration,
                "timestamp": datetime.now().isoformat(),
                "status": request.status
            }
            
            # Invoke Lambda function
            function_name = config.get_lambda_function_name('make_call')
            if lambda_client:
                response = lambda_client.invoke(
                    FunctionName=function_name,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(payload)
                )
            else:
                raise HTTPException(status_code=500, detail="Lambda client not available")
            
            # Parse response
            result = json.loads(response['Payload'].read())
            
            if response['StatusCode'] != 200:
                raise HTTPException(status_code=500, detail="Lambda function error")
            
            # Parse Lambda response
            lambda_response = json.loads(result.get('body', '{}'))
            
            if result.get('statusCode') != 200:
                raise HTTPException(status_code=result.get('statusCode', 500), detail=lambda_response.get('error', 'Unknown error'))
            
            return {
                "success": True,
                "message": "Call initiated successfully",
                "data": lambda_response,
                "timestamp": datetime.now().isoformat()
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Make call error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Get messages endpoint
@app.get("/api/v1/get_message/{booking_code}", response_model=Dict[str, Any])
async def get_message(booking_code: str):
    """
    Get all messages for a booking code from cache or DynamoDB.
    """
    try:
        logger.info(f"Get messages request: {booking_code}")
        
        if config.is_local():
            # Use in-memory cache for local environment
            messages_key = f"messages:{booking_code}"
            messages = cache.get(messages_key, [])
            if messages is None:
                messages = []
            
            # Map to frontend format
            frontend_messages = []
            for msg in messages:
                frontend_messages.append({
                    "id": f"{msg.get('booking_code', '')}_{msg.get('timestamp', '')}",
                    "text": msg.get("message", ""),
                    "sender": msg.get("sender", ""),
                    "timestamp": msg.get("timestamp", ""),
                    "type": msg.get("message_type", "text")
                })
            
            # Add call logs as messages
            call_logs = cache.get_call_logs(booking_code)
            for call_log in call_logs:
                frontend_messages.append({
                    "id": f"call_{call_log.get('timestamp', '')}",
                    "text": call_log.get("message", ""),
                    "sender": "ai",
                    "timestamp": call_log.get("timestamp", ""),
                    "type": "call",
                    "callDetails": {
                        "duration": call_log.get("duration", 0),
                        "status": call_log.get("status", "ended")
                    }
                })
            
            # Sort by timestamp
            frontend_messages.sort(key=lambda x: x.get("timestamp", ""))
            
            return {
                "success": True,
                "booking_code": booking_code,
                "data": {
                    "messages": frontend_messages,
                    "count": len(frontend_messages)
                },
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Use Lambda for non-local environments
            payload = {
                "booking_code": booking_code
            }
            
            # Invoke Lambda function
            function_name = config.get_lambda_function_name('get_message')
            if lambda_client:
                response = lambda_client.invoke(
                    FunctionName=function_name,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(payload)
                )
            else:
                raise HTTPException(status_code=500, detail="Lambda client not available")
            
            # Parse response
            result = json.loads(response['Payload'].read())
            
            if response['StatusCode'] != 200:
                raise HTTPException(status_code=500, detail="Lambda function error")
            
            # Parse Lambda response
            lambda_response = json.loads(result.get('body', '{}'))
            
            if result.get('statusCode') != 200:
                raise HTTPException(status_code=result.get('statusCode', 500), detail=lambda_response.get('error', 'Unknown error'))
            
            # Map Lambda messages to frontend format if needed
            lambda_messages = lambda_response.get('messages', [])
            frontend_messages = []
            for msg in lambda_messages:
                frontend_messages.append({
                    "id": f"{msg.get('booking_code', '')}_{msg.get('timestamp', '')}",
                    "text": msg.get("message", ""),
                    "sender": msg.get("sender", ""),
                    "timestamp": msg.get("timestamp", ""),
                    "type": msg.get("message_type", "text")
                })
            
            return {
                "success": True,
                "booking_code": booking_code,
                "data": {
                    "messages": frontend_messages,
                    "count": len(frontend_messages)
                },
                "timestamp": datetime.now().isoformat()
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get messages error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Helper functions
def _detect_intent(user_input: str) -> str:
    """
    Simple intent detection based on keywords.
    In a real implementation, this would use NLP or AI.
    """
    user_input_lower = user_input.lower()
    
    # Check for call intent first (more specific)
    call_keywords = ["call", "phone", "dial", "ring", "make call", "call to"]
    if any(keyword in user_input_lower for keyword in call_keywords):
        return "make_call"
    
    # Check for send message intent
    send_keywords = ["send", "message", "text", "tell", "inform", "notify"]
    if any(keyword in user_input_lower for keyword in send_keywords):
        return "send_message"
    
    # Check for get messages intent
    get_keywords = ["get", "messages", "history", "show", "read"]
    if any(keyword in user_input_lower for keyword in get_keywords):
        return "get_messages"
    
    # Default to send message
    return "send_message"

def _extract_message_content(user_input: str, intent: str) -> str:
    """
    Extract the actual message content from voice commands.
    """
    user_input_lower = user_input.lower()
    
    if intent == "send_message":
        # Look for the actual message after command words
        message = user_input
        
        # Try to find content after "that"
        if "that" in user_input_lower:
            parts = user_input.split("that", 1)
            if len(parts) > 1:
                message = parts[1].strip()
                logger.info(f"Extracted message after 'that': '{message}'")
                return message
        
        # Try to find content after "i am"
        if "i am" in user_input_lower:
            parts = user_input.split("i am", 1)
            if len(parts) > 1:
                message = parts[1].strip()
                logger.info(f"Extracted message after 'i am': '{message}'")
                return message
        
        # Try to find content after "i will"
        if "i will" in user_input_lower:
            parts = user_input.split("i will", 1)
            if len(parts) > 1:
                message = parts[1].strip()
                logger.info(f"Extracted message after 'i will': '{message}'")
                return message
        
        # Try to find content after "going"
        if "going" in user_input_lower:
            parts = user_input.split("going", 1)
            if len(parts) > 1:
                message = parts[1].strip()
                logger.info(f"Extracted message after 'going': '{message}'")
                return message
        
        # If no connectors found, try to remove common command words
        command_words = [
            "send", "message", "text", "tell", "inform", "notify",
            "to", "the", "passenger", "driver", "hi", "hello"
        ]
        
        words = user_input.split()
        filtered_words = []
        
        for word in words:
            word_lower = word.lower()
            if word_lower not in command_words:
                filtered_words.append(word)
        
        if filtered_words:
            message = " ".join(filtered_words)
            logger.info(f"Extracted message by filtering command words: '{message}'")
            return message
        
        # If all else fails, return the original input
        logger.info(f"No extraction possible, using original: '{user_input}'")
        return user_input
    
    return user_input

async def _handle_send_message(request: AIAgentRequest) -> Dict[str, Any]:
    """Handle send message intent"""
    # Extract the actual message content
    message_content = _extract_message_content(request.user_input, "send_message")
    
    logger.info(f"Extracted message content: '{message_content}' from '{request.user_input}'")
    
    message_request = MessageRequest(
        booking_code=request.booking_code,
        message=message_content,
        sender=request.user_type,
        message_type="text"
    )
    return await send_message(message_request)

async def _handle_make_call(request: AIAgentRequest) -> Dict[str, Any]:
    """Handle make call intent"""
    logger.info(f"Call intent detected: '{request.user_input}'")
    
    # Return call response for AI agent
    return {
        "success": True,
        "message": "Call initiated successfully",
        "data": {
            "text": "Call initiated",
            "type": "call",
            "call_type": "voice",
            "duration": 0,
            "status": "initiated"
        },
        "timestamp": datetime.now().isoformat()
    }

async def _handle_get_messages(request: AIAgentRequest) -> Dict[str, Any]:
    """Handle get messages intent"""
    return await get_message(request.booking_code)

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

# WebSocket endpoint for real-time communication
@app.websocket("/ws/{booking_code}")
async def websocket_endpoint(websocket: WebSocket, booking_code: str):
    await manager.connect(websocket, booking_code)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "call_initiate":
                # Add delay before ringing
                import asyncio
                await asyncio.sleep(2)  # 2 second delay
                
                # Log call initiation
                call_log = {
                    "message": f"Incoming call from {message.get('from', 'unknown')}",
                    "status": "initiated",
                    "duration": 0,
                    "timestamp": datetime.now().isoformat(),
                    "from": message.get("from")
                }
                cache.add_call_log(booking_code, call_log)
                
                # Broadcast call initiation to all clients in this booking
                await manager.broadcast_to_booking(json.dumps({
                    "type": "call_initiate",
                    "from": message.get("from"),
                    "booking_code": booking_code,
                    "timestamp": datetime.now().isoformat(),
                    "call_log": call_log
                }), booking_code)
                
            elif message.get("type") == "call_accept":
                # Add delay before connection
                import asyncio
                await asyncio.sleep(1)  # 1 second delay
                
                # Log call acceptance
                call_log = {
                    "message": f"Call accepted by {message.get('from', 'unknown')}",
                    "status": "connected",
                    "duration": 0,
                    "timestamp": datetime.now().isoformat(),
                    "from": message.get("from")
                }
                cache.add_call_log(booking_code, call_log)
                
                # Broadcast call acceptance
                await manager.broadcast_to_booking(json.dumps({
                    "type": "call_accept",
                    "from": message.get("from"),
                    "booking_code": booking_code,
                    "timestamp": datetime.now().isoformat(),
                    "call_log": call_log
                }), booking_code)
                
            elif message.get("type") == "call_reject":
                # Log call rejection
                call_log = {
                    "message": f"Call rejected by {message.get('from', 'unknown')}",
                    "status": "rejected",
                    "duration": 0,
                    "timestamp": datetime.now().isoformat(),
                    "from": message.get("from")
                }
                cache.add_call_log(booking_code, call_log)
                
                # Broadcast call rejection
                await manager.broadcast_to_booking(json.dumps({
                    "type": "call_reject",
                    "from": message.get("from"),
                    "booking_code": booking_code,
                    "timestamp": datetime.now().isoformat(),
                    "call_log": call_log
                }), booking_code)
                
            elif message.get("type") == "call_end":
                # Log call end with duration
                duration = message.get("duration", 0)
                call_log = {
                    "message": f"Call ended by {message.get('from', 'unknown')} - Duration: {duration} seconds",
                    "status": "ended",
                    "duration": duration,
                    "timestamp": datetime.now().isoformat(),
                    "from": message.get("from")
                }
                cache.add_call_log(booking_code, call_log)
                
                # Broadcast call end
                await manager.broadcast_to_booking(json.dumps({
                    "type": "call_end",
                    "from": message.get("from"),
                    "booking_code": booking_code,
                    "timestamp": datetime.now().isoformat(),
                    "call_log": call_log
                }), booking_code)
                
            elif message.get("type") == "call_ringing":
                # Log call ringing
                call_log = {
                    "message": f"Call ringing - Incoming call from {message.get('from', 'unknown')}",
                    "status": "ringing",
                    "duration": 0,
                    "timestamp": datetime.now().isoformat(),
                    "from": message.get("from")
                }
                cache.add_call_log(booking_code, call_log)
                
                # Broadcast call ringing state
                await manager.broadcast_to_booking(json.dumps({
                    "type": "call_ringing",
                    "from": message.get("from"),
                    "booking_code": booking_code,
                    "timestamp": datetime.now().isoformat(),
                    "call_log": call_log
                }), booking_code)
                
            elif message.get("type") == "call_connected":
                # Log call connected
                call_log = {
                    "message": f"Call connected",
                    "status": "connected",
                    "duration": 0,
                    "timestamp": datetime.now().isoformat(),
                    "from": message.get("from")
                }
                cache.add_call_log(booking_code, call_log)
                
                # Broadcast call connected state
                await manager.broadcast_to_booking(json.dumps({
                    "type": "call_connected",
                    "from": message.get("from"),
                    "booking_code": booking_code,
                    "timestamp": datetime.now().isoformat(),
                    "call_log": call_log
                }), booking_code)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, booking_code)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, booking_code)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 