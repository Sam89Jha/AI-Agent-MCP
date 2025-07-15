# AI Intent API for Driver-Passenger Communication

This is a simple AI-powered API that detects user intent and calls the MCP server to handle driver-passenger communication.

## Architecture

```
User Input → AI Intent API → AWS Bedrock → Intent Detection → MCP Server → Response
```

## Features

- **AWS Bedrock Integration**: Uses Claude 3 Haiku for fast intent detection
- **Fallback Mechanism**: Keyword-based intent detection if Bedrock fails
- **MCP Server Integration**: Calls appropriate MCP endpoints based on detected intent
- **RESTful API**: Easy to integrate with any frontend application

## Supported Intents

1. **send_message** - Send text messages between drivers and passengers
2. **make_call** - Initiate voice calls between drivers and passengers  
3. **get_messages** - Retrieve conversation history
4. **unknown** - When intent is unclear

## API Endpoints

### POST /detect_intent
Detect intent from user input and call appropriate MCP server endpoint.

**Request Body:**
```json
{
  "booking_code": "12345",
  "user_type": "driver",
  "user_input": "Send a message to the passenger saying I'll be there in 5 minutes"
}
```

**Response:**
```json
{
  "intent": "send_message",
  "confidence": 0.95,
  "response": "✅ Message sent successfully! The passenger will receive your message.",
  "success": true,
  "mcp_result": {
    "success": true,
    "data": {...},
    "status_code": 200
  }
}
```

### GET /health
Health check endpoint.

### GET /test
Test the API with sample inputs.

## Setup

1. **Install Dependencies:**
   ```bash
   pip install -r requirements_ai_intent.txt
   ```

2. **Run the Server:**
   ```bash
   python ai_intent_api.py
   ```

3. **Test the API:**
   ```bash
   python test_ai_intent.py
   ```

## Example Usage

### Using curl:
```bash
curl -X POST "http://localhost:8000/detect_intent" \
  -H "Content-Type: application/json" \
  -d '{
    "booking_code": "12345",
    "user_type": "driver", 
    "user_input": "Send a message to the passenger saying I will be there in 5 minutes"
  }'
```

### Using Python:
```python
import requests

response = requests.post(
    "http://localhost:8000/detect_intent",
    json={
        "booking_code": "12345",
        "user_type": "driver",
        "user_input": "Make a call to the passenger"
    }
)

result = response.json()
print(f"Intent: {result['intent']}")
print(f"Response: {result['response']}")
```

## Integration with Frontend Apps

Your frontend apps (DAX/PAX) can now call this API instead of directly calling MCP server:

```javascript
// Example frontend integration
async function sendUserInput(bookingCode, userType, userInput) {
  const response = await fetch('/detect_intent', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      booking_code: bookingCode,
      user_type: userType,
      user_input: userInput
    })
  });
  
  const result = await response.json();
  return result;
}
```

## Benefits

1. **AI-Powered**: Uses AWS Bedrock for intelligent intent detection
2. **Reliable**: Fallback to keyword matching if AI fails
3. **Simple**: Single API endpoint for all communication needs
4. **Scalable**: Can be deployed on any cloud platform
5. **Maintainable**: Clean separation of concerns

## Deployment

The API can be deployed on:
- AWS Lambda (serverless)
- AWS Elastic Beanstalk
- Docker containers
- Any cloud platform supporting Python

## Configuration

Update the MCP server URL in `ai_intent_api.py`:
```python
ai_detector = AIIntentDetector("YOUR_MCP_SERVER_URL")
```

## Testing

Run the comprehensive test suite:
```bash
python test_ai_intent.py
```

This will test:
- Direct Bedrock integration
- API endpoints
- Intent detection accuracy
- MCP server integration 