# Staging & Testing Plan
## AI-Driven Chat & Voice Assistant Demo

---

## 🧪 **Staging Environment Strategy**

### **Local Development Setup**
Before deploying to AWS, we'll test all components locally to ensure everything works correctly.

---

## 📋 **Testing Phases**

### **Phase 1: Local Infrastructure Testing**
- [ ] **Docker Compose Setup** - Local MCP server
- [ ] **Local Lambda Testing** - Python functions with DynamoDB Local
- [ ] **Database Testing** - DynamoDB Local setup
- [ ] **API Testing** - Postman/curl tests

### **Phase 2: Component Testing**
- [ ] **MCP Server** - FastAPI endpoints testing
- [ ] **Lambda Functions** - Individual function testing
- [ ] **Database Operations** - CRUD operations testing
- [ ] **API Integration** - End-to-end flow testing

### **Phase 3: Frontend Testing**
- [ ] **React Apps** - Local development server
- [ ] **Voice Input** - Browser Speech Recognition API
- [ ] **UI/UX Testing** - Mobile-responsive design
- [ ] **Integration Testing** - Frontend + Backend

### **Phase 4: AI Agent Testing**
- [ ] **Bedrock Agent** - Local configuration testing
- [ ] **Tool Calling** - API integration testing
- [ ] **Intent Recognition** - Voice/text command testing
- [ ] **Response Generation** - AI response validation

### **Phase 5: End-to-End Testing**
- [ ] **Complete Flow** - Driver → AI → MCP → Lambda → Passenger
- [ ] **Error Handling** - Edge cases and failures
- [ ] **Performance Testing** - Load and stress testing
- [ ] **Security Testing** - Input validation and sanitization

---

## 🛠️ **Local Development Setup**

### **1. MCP Server (Local)**
```bash
# Create local MCP server directory
mkdir -p staging/mcp-server
cd staging/mcp-server

# Create Docker Compose for local testing
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  mcp-server:
    build: .
    ports:
      - "8000:8000"
    environment:
      - AWS_REGION=us-east-1
      - DYNAMODB_TABLE=chat-messages-local
    volumes:
      - ./logs:/app/logs
EOF
```

### **2. Lambda Functions (Local)**
```bash
# Create local Lambda testing environment
mkdir -p staging/lambda-testing
cd staging/lambda-testing

# Create test scripts for each Lambda function
python3 -m venv venv
source venv/bin/activate
pip install boto3 moto pytest
```

### **3. DynamoDB Local**
```bash
# Run DynamoDB Local
docker run -p 8000:8000 amazon/dynamodb-local
```

### **4. React Apps (Local)**
```bash
# Create local React development environment
mkdir -p staging/frontend
cd staging/frontend

# Setup React apps with local backend URLs
npx create-react-app dax-app --template typescript
npx create-react-app pax-app --template typescript
```

---

## 🧪 **Testing Scripts**

### **1. MCP Server Tests**
```python
# staging/tests/test_mcp_server.py
import requests
import json

def test_mcp_server():
    base_url = "http://localhost:8000"
    
    # Test health endpoint
    response = requests.get(f"{base_url}/health")
    assert response.status_code == 200
    
    # Test send message
    payload = {
        "booking_code": "TEST123",
        "message": "Hello from test",
        "sender": "driver"
    }
    response = requests.post(f"{base_url}/api/v1/send_message", json=payload)
    assert response.status_code == 200
    
    # Test get messages
    response = requests.get(f"{base_url}/api/v1/get_message/TEST123")
    assert response.status_code == 200
```

### **2. Lambda Function Tests**
```python
# staging/tests/test_lambda_functions.py
import boto3
import json
from moto import mock_dynamodb

@mock_dynamodb
def test_send_message_lambda():
    # Setup mock DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.create_table(
        TableName='chat-messages-local',
        KeySchema=[
            {'AttributeName': 'booking_code', 'KeyType': 'HASH'},
            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'booking_code', 'AttributeType': 'S'},
            {'AttributeName': 'timestamp', 'AttributeType': 'S'}
        ]
    )
    
    # Test Lambda function
    event = {
        "booking_code": "TEST123",
        "message": "Test message",
        "sender": "driver"
    }
    
    # Import and test Lambda function
    from lambda_function import lambda_handler
    result = lambda_handler(event, None)
    assert result['statusCode'] == 200
```

### **3. Frontend Tests**
```javascript
// staging/tests/frontend.test.js
import { render, screen, fireEvent } from '@testing-library/react';
import App from '../src/App';

test('voice input works correctly', () => {
  render(<App />);
  
  const micButton = screen.getByRole('button', { name: /microphone/i });
  fireEvent.click(micButton);
  
  // Test voice input functionality
  expect(screen.getByText(/listening/i)).toBeInTheDocument();
});

test('message sending works', () => {
  render(<App />);
  
  const messageInput = screen.getByPlaceholderText(/type a message/i);
  const sendButton = screen.getByRole('button', { name: /send/i });
  
  fireEvent.change(messageInput, { target: { value: 'Test message' } });
  fireEvent.click(sendButton);
  
  expect(screen.getByText(/Test message/)).toBeInTheDocument();
});
```

---

## 📊 **Test Cases**

### **1. API Endpoints**
- [ ] **POST /api/v1/send_message**
  - Valid message → Success
  - Missing fields → Error
  - Invalid booking code → Error
  
- [ ] **POST /api/v1/make_call**
  - Valid call → Success
  - Missing booking code → Error
  
- [ ] **GET /api/v1/get_message/{booking_code}**
  - Existing messages → Success
  - No messages → Empty array
  - Invalid booking code → Error

### **2. Voice Input**
- [ ] **Browser Speech Recognition**
  - Microphone access → Success
  - Speech to text → Success
  - No microphone → Fallback to text
  
- [ ] **Command Recognition**
  - "Send message" → Triggers send
  - "Make call" → Triggers call
  - "Get messages" → Triggers fetch

### **3. UI/UX**
- [ ] **Mobile Responsive**
  - iPhone SE → Works
  - iPad → Works
  - Desktop → Works
  
- [ ] **Chat Interface**
  - Message bubbles → Correct display
  - Timestamps → Proper format
  - Sender labels → Clear identification

### **4. Error Handling**
- [ ] **Network Errors**
  - API timeout → Retry mechanism
  - Connection lost → Offline mode
  
- [ ] **Input Validation**
  - Empty messages → Prevented
  - Invalid booking codes → Error message
  - Special characters → Proper handling

---

## 🚀 **Staging Deployment**

### **Local Environment Setup**
```bash
# 1. Start DynamoDB Local
docker run -d -p 8000:8000 amazon/dynamodb-local

# 2. Start MCP Server
cd staging/mcp-server
docker-compose up -d

# 3. Start React Apps
cd staging/frontend/dax-app
npm start

cd staging/frontend/pax-app
npm start

# 4. Run Tests
cd staging/tests
python -m pytest test_*.py
```

### **Test URLs**
- **MCP Server**: http://localhost:8000
- **DAX App**: http://localhost:3000
- **PAX App**: http://localhost:3001
- **DynamoDB Local**: http://localhost:8000

---

## 📈 **Performance Testing**

### **Load Testing**
```bash
# Test MCP server with Apache Bench
ab -n 1000 -c 10 http://localhost:8000/health

# Test Lambda functions
python staging/load_tests/test_lambda_performance.py
```

### **Stress Testing**
```bash
# Test concurrent users
python staging/load_tests/stress_test.py --users 50 --duration 300
```

---

## 🔍 **Monitoring & Debugging**

### **Logs**
```bash
# MCP Server logs
docker logs staging-mcp-server-1

# Lambda function logs
tail -f staging/logs/lambda_*.log

# Frontend logs
tail -f staging/frontend/*/logs/*.log
```

### **Debugging Tools**
- **Postman** - API testing
- **Chrome DevTools** - Frontend debugging
- **AWS CLI** - Lambda function testing
- **DynamoDB Admin** - Database inspection

---

## ✅ **Success Criteria**

### **All Tests Must Pass**
- [ ] **Unit Tests**: 100% pass rate
- [ ] **Integration Tests**: All flows working
- [ ] **Performance Tests**: < 2s response time
- [ ] **Error Tests**: Proper error handling
- [ ] **UI Tests**: All interactions working

### **Quality Gates**
- [ ] **Code Coverage**: > 80%
- [ ] **Performance**: < 2s API response
- [ ] **Security**: No vulnerabilities
- [ ] **Accessibility**: WCAG 2.1 compliant

---

## 🚨 **Rollback Plan**

If staging tests fail:
1. **Stop all local services**
2. **Review logs and identify issues**
3. **Fix code and retest**
4. **Only proceed to production after all tests pass**

---

**Ready to start staging tests? Let me know when you want to begin Phase 1: Local Infrastructure Testing!** 🧪 