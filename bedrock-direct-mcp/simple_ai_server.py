from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from simple_ai_agent import SimpleAIAgent
import uvicorn

app = FastAPI(title="Simple AI Agent", description="AI Agent for Driver-Passenger Communication")

# Initialize the AI agent
agent = SimpleAIAgent("http://mcp-server-env.eba-r23dy2pd.us-west-2.elasticbeanstalk.com")

class ChatRequest(BaseModel):
    message: str
    booking_code: str = "12345"  # Default booking code
    user_type: str = "driver"    # Default user type

class ChatResponse(BaseModel):
    response: str
    intent: str
    success: bool
    confidence: float = 0.0

@app.get("/")
async def root():
    return {
        "message": "Simple AI Agent for Driver-Passenger Communication",
        "endpoints": {
            "/chat": "POST - Send a message to the AI agent",
            "/health": "GET - Check if the agent is healthy"
        }
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a chat message and return AI response"""
    try:
        # Add booking code and user type to the message if not present
        enhanced_message = request.message
        if request.booking_code and request.booking_code not in enhanced_message:
            enhanced_message = f"Booking {request.booking_code}: {enhanced_message}"
        
        if request.user_type and request.user_type not in enhanced_message:
            enhanced_message = f"As {request.user_type}: {enhanced_message}"
        
        # Process the request
        result = agent.process_request(enhanced_message)
        
        return ChatResponse(
            response=result['response'],
            intent=result.get('intent', 'unknown'),
            success=result.get('success', False),
            confidence=result.get('confidence', 0.0)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent": "Simple AI Agent",
        "mcp_server": "http://mcp-server-env.eba-r23dy2pd.us-west-2.elasticbeanstalk.com"
    }

@app.get("/test")
async def test_agent():
    """Test the agent with sample inputs"""
    test_inputs = [
        "Send a message to the passenger saying I'll be there in 5 minutes",
        "Make a call to the passenger",
        "Get the message history"
    ]
    
    results = []
    for user_input in test_inputs:
        result = agent.process_request(user_input)
        results.append({
            "input": user_input,
            "response": result['response'],
            "intent": result.get('intent', 'unknown'),
            "success": result.get('success', False)
        })
    
    return {
        "test_results": results,
        "total_tests": len(results)
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 