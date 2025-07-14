# AI-Driven Chat & Voice Assistant Demo (Grab-style)
## Project Documentation & Implementation Plan

---

## 📋 **Project Overview**

This project implements a fully functional AI-powered internal assistant for a driver and passenger system (Grab-style simulation). The system handles chat and voice communication flows, interprets user commands via AWS Bedrock AI Agent, and manages backend APIs through an MCP server.

---

## 🏗️ **Architecture Overview**

```
┌─────────────────┐                    ┌─────────────────┐
│   DAX Web App   │                    │   PAX Web App   │
│   (Driver UI)   │                    │ (Passenger UI)  │
└─────────┬───────┘                    └─────────┬───────┘
          │                                      │
          │ Voice/Text Input                     │ Voice/Text Input
          ▼                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AWS Bedrock AI Agent                         │
│              (Central Orchestrator)                             │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          │ Tool Calls
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MCP Server (FastAPI)                         │
│              (API Gateway + Lambda + FastAPI)                   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Backend API (Lambda)                    │
│  ├── POST /send_message (stores message)                        │
│  ├── POST /make_call (logs simulated call)                      │
│  └── GET /get_message (retrieves messages)                      │
└─────────────────────────────────────────────────────────────────┘
```

### **Flow Examples:**

**Driver → Passenger Flow:**
```
DAX Web App → AI Agent → MCP Server (EC2) → Backend API (Lambda) → PAX Web App
```

**Passenger → Driver Flow:**
```
PAX Web App → AI Agent → MCP Server (EC2) → Backend API (Lambda) → DAX Web App
```

### **Deployment Architecture:**

**MCP Server (EC2):**
- **Purpose**: API Gateway between AI Agent and Backend
- **Technology**: Python FastAPI
- **Hosting**: EC2 instance
- **Domain**: mcp.sameer-jha.com
- **Functions**: 
  - Receive requests from Bedrock AI Agent
  - Forward to Lambda functions
  - Handle authentication and validation

**Backend API (Lambda):**
- **Purpose**: Core business logic and data storage
- **Technology**: Python Lambda functions
- **Hosting**: AWS Lambda (via Terraform)
- **Functions**:
  - Store and retrieve messages
  - Handle call logging
  - Manage booking data

### **URL Structure:**

**Web Applications:**
- **DAX App (Driver)**: `https://dax.sameer-jha.com` (S3 + CloudFront)
- **PAX App (Passenger)**: `https://pax.sameer-jha.com` (S3 + CloudFront)

**Backend Services:**
- **MCP Server**: `https://mcp.sameer-jha.com` (EC2 t3.micro)
  - Endpoint: `https://mcp.sameer-jha.com/api/v1/`
- **Lambda Functions**: Direct invocation (no public URLs)
  - `send_message` function
  - `make_call` function  
  - `get_message` function

**AI Agent:**
- **Bedrock Agent**: AWS Console managed
  - No public URL (internal AWS service)
  - Accessible via AWS SDK/API

**Database:**
- **DynamoDB**: AWS managed service (on-demand pricing)
  - No public URL (internal AWS service)

---

## 📦 **Infrastructure Components**

### 1. **Terraform Infrastructure**
- **AWS Lambda Functions**:
  - `mcp_server` - Routes actions from AI agent to backend
  - `backend_api` - Mock implementation of core APIs
- **AWS API Gateway REST API**:
  - `/send_message` (POST)
  - `/make_call` (POST) 
  - `/get_message` (GET)
- **IAM Roles & Permissions**:
  - Lambda execution roles
  - Bedrock access permissions
  - API Gateway integration
- **CloudWatch Logging**:
  - Lambda function logs
  - API Gateway access logs

### 2. **AI Agent Configuration (Bedrock)**
- **Agent Type**: Anthropic Claude 3.5 Sonnet
- **Action Group**: OpenAPI schema integration with MCP server
- **Tool Calling**: Enabled for API interactions
- **Test Utterances**: Sample voice/text commands
- **Slot Mapping**: Intent extraction configuration
- **Integration**: Direct API calls to MCP server endpoints
- **Configuration**: AWS Console + Terraform for IAM permissions

### 3. **MCP Server (FastAPI on EC2)**
- **Purpose**: API Gateway between AI Agent and Backend
- **Functions**:
  - Receive structured requests from AI Agent
  - Forward to appropriate Lambda endpoints
  - Validate and log requests
  - Handle authentication and rate limiting
  - Return results to agent
- **Technology**: Python FastAPI
- **Deployment**: EC2 instance with Docker
- **Domain**: mcp.sameer-jha.com
- **Load Balancer**: Application Load Balancer (optional)

### 4. **Backend API (Lambda Functions)**
- **Technology**: Python Lambda functions
- **Storage**: DynamoDB for persistent storage
- **Endpoints**:
  - `POST /send_message` - Store booking messages
  - `POST /make_call` - Log simulated calls
  - `GET /get_message` - Retrieve messages by booking code
- **Deployment**: AWS Lambda via Terraform
- **Direct Invocation**: MCP server calls Lambda functions directly (no API Gateway)

---

## 🎯 **Frontend Applications**

### 1. **DAX Web App (Driver Interface)**
- **Technology**: React.js (Mobile-first design)
- **Features**:
  - Voice input capability (Browser Speech Recognition API)
  - Text prompt interface
  - Real-time chat room (WhatsApp-style)
  - Call details display
  - Booking code management
  - Mobile-responsive UI
- **Hosting**: dax.sameer-jha.com
- **Voice Input Flow**:
  1. User clicks microphone button
  2. Browser's Speech Recognition API captures audio
  3. Speech converted to text in browser
  4. Text sent to Bedrock AI Agent
  5. AI Agent interprets intent and calls MCP server
  6. MCP server forwards to Backend API (Lambda)
  7. Response displayed in chat room

### 2. **PAX Web App (Passenger Interface)**
- **Technology**: React.js (Mobile-first design)
- **Features**:
  - Voice input capability (Browser Speech Recognition API)
  - Text prompt interface
  - Real-time chat room (WhatsApp-style)
  - Call details display
  - Booking code management
  - Mobile-responsive UI
- **Hosting**: pax.sameer-jha.com
- **Voice Input Flow**:
  1. User clicks microphone button
  2. Browser's Speech Recognition API captures audio
  3. Speech converted to text in browser
  4. Text sent to Bedrock AI Agent
  5. AI Agent interprets intent and calls MCP server
  6. MCP server forwards to Backend API (Lambda)
  7. Response displayed in chat room

---

## 🔧 **Implementation Phases**

### **Phase 1: Infrastructure Setup**
1. **Terraform Configuration**
   - Create `terraform/` directory
   - Define Lambda functions, API Gateway, IAM roles
   - Set up CloudWatch logging
   - Configure Bedrock permissions

2. **Deployment Scripts**
   - Package FastAPI apps for Lambda
   - Create deployment automation
   - Set up environment variables

### **Phase 2: Backend Services**
1. **MCP Server Development (EC2)**
   - FastAPI application with Lambda integration
   - Docker containerization
   - EC2 deployment configuration
   - Domain and SSL setup

2. **Backend API Development (Lambda)**
   - Lambda function implementations
   - DynamoDB integration
   - Direct Lambda invocation (no API Gateway)
   - Error handling and logging

### **Phase 3: AI Agent Configuration**
1. **Bedrock Agent Setup**
   - Agent creation and configuration
   - Action group definition
   - OpenAPI schema integration
   - Test utterance configuration

### **Phase 4: Frontend Applications**
1. **DAX Web App**
   - Voice input implementation
   - Bedrock API integration
   - Real-time response handling

2. **PAX Web App**
   - Polling mechanism
   - Message display interface
   - Booking code management

### **Phase 5: Integration & Testing**
1. **End-to-End Testing**
   - Complete flow validation
   - Error handling verification
   - Performance testing

2. **Documentation & Deployment**
   - README creation
   - Deployment instructions
   - Cost optimization verification

---

## 💰 **Cost Optimization Strategy**

### **Estimated Costs (1-week demo)**
- **Lambda Functions**: ~$0.01 (infrequent calls)
- **EC2 Instance**: ~$0.50-1.00 (t3.micro)
- **DynamoDB**: ~$0.01 (on-demand pricing)
- **S3 + CloudFront**: Free tier eligible
- **Bedrock Usage**: ~$0.50-1.00 (depending on traffic)
- **Total Estimated Cost**: ~$1-2 for demo period

### **Cost Optimization Measures**
- Use Lambda for serverless scaling
- **No API Gateway** (direct Lambda invocation)
- **S3 + CloudFront** for web hosting (free tier)
- **t3.micro EC2** instance (free tier eligible)
- **DynamoDB on-demand** pricing (pay per request)
- Implement efficient polling intervals
- Minimize Bedrock API calls
- Implement request caching where possible

---

## 🚀 **Stretch Goals (Optional)**

### **Advanced Features**
1. **WebSocket Implementation**
   - Real-time push notifications
   - Reduced polling overhead
   - Better user experience

2. **Advanced Speech-to-Text Integration**
   - AWS Transcribe integration (server-side processing)
   - Real-time voice streaming to AI Agent
   - Enhanced accuracy and language support
   - **Difference from Current**: Current uses browser API, stretch goal uses AWS Transcribe

3. **Container Deployment**
   - ECS deployment option
   - Docker containerization
   - Scalable architecture

4. **Test Harness**
   - Automated testing suite
   - Multiple booking simulation
   - Load testing capabilities

---

## 📁 **Project Structure**

```
NavieTakieSimulation/
├── terraform/                    # Infrastructure as Code
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── modules/
│       ├── lambda/
│       ├── ec2/
│       ├── dynamodb/
│       └── bedrock/
├── mcp-server/                   # MCP Server (FastAPI on EC2)
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── nginx.conf
│   └── docker-compose.yml
├── backend/                      # Backend API (Lambda)
│   ├── lambda-functions/
│   │   ├── send_message/
│   │   │   ├── lambda_function.py
│   │   │   └── requirements.txt
│   │   ├── make_call/
│   │   │   ├── lambda_function.py
│   │   │   └── requirements.txt
│   │   └── get_message/
│   │       ├── lambda_function.py
│   │       └── requirements.txt
│   └── dynamodb/
│       └── schema.json
├── frontend/                     # Frontend Applications
│   ├── dax-app/                 # Driver Interface (React)
│   │   ├── src/
│   │   ├── public/
│   │   ├── package.json
│   │   └── Dockerfile
│   └── pax-app/                 # Passenger Interface (React)
│       ├── src/
│       ├── public/
│       ├── package.json
│       └── Dockerfile
├── docs/                         # Documentation
│   ├── README.md
│   ├── API_DOCUMENTATION.md
│   └── DEPLOYMENT_GUIDE.md
├── scripts/                      # Deployment Scripts
│   ├── deploy.sh
│   ├── package.sh
│   └── test.sh
└── tests/                        # Test Suite
    ├── integration/
    ├── unit/
    └── e2e/
```

---

## ✅ **Success Criteria**

### **Functional Requirements**
- [ ] Voice/text commands processed by AI Agent
- [ ] Backend APIs respond correctly
- [ ] Real-time message exchange between driver and passenger
- [ ] Cost-effective deployment (<$5 for demo)
- [ ] Scalable architecture for future enhancements

### **Technical Requirements**
- [ ] Terraform infrastructure deployed successfully
- [ ] Lambda functions operational
- [ ] API Gateway endpoints accessible
- [ ] Bedrock Agent configured and functional
- [ ] Frontend applications responsive and user-friendly

### **Quality Requirements**
- [ ] Comprehensive error handling
- [ ] Proper logging and monitoring
- [ ] Security best practices implemented
- [ ] Documentation complete and accurate
- [ ] Testing coverage adequate

---

## 🚨 **Risk Mitigation**

### **Technical Risks**
1. **Bedrock API Limits**: Implement rate limiting and retry logic
2. **Lambda Cold Starts**: Use provisioned concurrency for critical functions
3. **API Gateway Timeouts**: Configure appropriate timeout values
4. **Cost Overruns**: Implement usage monitoring and alerts

### **Operational Risks**
1. **Deployment Failures**: Use blue-green deployment strategy
2. **Data Loss**: Implement backup strategies for in-memory data
3. **Security Vulnerabilities**: Regular security audits and updates
4. **Performance Issues**: Load testing and optimization

---

## 📞 **Next Steps**

1. **Confirm Requirements**: Review and approve this documentation
2. **Infrastructure Setup**: Begin with Terraform configuration
3. **Backend Development**: Create MCP server and backend API
4. **AI Agent Configuration**: Set up Bedrock Agent
5. **Frontend Development**: Build DAX and PAX applications
6. **Integration Testing**: End-to-end flow validation
7. **Deployment**: Production deployment and monitoring

---

**Ready to proceed with implementation? Please confirm if you have any questions or modifications to this plan.** 