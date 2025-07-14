# Configuration System Guide

## 🎯 **Environment-Specific Configuration System**

This project now supports three environments with automatic configuration management:

### **Environments:**

1. **Local** (`local`) - Development on your machine
2. **Staging** (`staging`) - Pre-production testing
3. **Production** (`production`) - Live deployment

---

## 🔧 **Configuration Files**

### **1. Python Configuration (`config.py`)**
- **Location**: Project root
- **Purpose**: Backend configuration (MCP Server, Lambda functions)
- **Usage**: `from config import get_config, get_api_url`

### **2. React App Configuration (`frontend/*/src/config.js`)**
- **Location**: `frontend/dax-app/src/config.js` and `frontend/pax-app/src/config.js`
- **Purpose**: Frontend configuration (API endpoints, features)
- **Usage**: `import CONFIG, API_ENDPOINTS from './config'`

---

## 🚀 **How to Run Different Environments**

### **Local Environment (Default)**
```bash
# Option 1: Use the start script
./scripts/start_local.sh

# Option 2: Manual start
export ENVIRONMENT=local
export REACT_APP_ENVIRONMENT=local

# Terminal 1: MCP Server
cd mcp-server && uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: DAX App
cd frontend/dax-app && npm start -- --port 3001

# Terminal 3: PAX App
cd frontend/pax-app && npm start -- --port 3002
```

### **Staging Environment**
```bash
export ENVIRONMENT=staging
export REACT_APP_ENVIRONMENT=staging

# Deploy to staging servers
# (Uses staging URLs and DynamoDB)
```

### **Production Environment**
```bash
export ENVIRONMENT=production
export REACT_APP_ENVIRONMENT=production

# Deploy to production servers
# (Uses production URLs and DynamoDB)
```

---

## 📋 **Environment Configurations**

### **Local Environment**
```python
{
    'mcp_server_url': 'http://localhost:8000',
    'dax_app_url': 'http://localhost:3001',
    'pax_app_url': 'http://localhost:3002',
    'api_base_url': 'http://localhost:8000',
    'use_in_memory_cache': True,
    'debug': True,
    'lambda_functions': {
        'send_message': 'send-message-local',
        'make_call': 'make-call-local',
        'get_message': 'get-message-local'
    },
    'database': {
        'type': 'in_memory',
        'table_name': 'chat-messages-local'
    }
}
```

### **Staging Environment**
```python
{
    'mcp_server_url': 'https://mcp-staging.sameer-jha.com',
    'dax_app_url': 'https://dax-staging.sameer-jha.com',
    'pax_app_url': 'https://pax-staging.sameer-jha.com',
    'api_base_url': 'https://mcp-staging.sameer-jha.com',
    'use_in_memory_cache': False,
    'debug': True,
    'lambda_functions': {
        'send_message': 'send-message-staging',
        'make_call': 'make-call-staging',
        'get_message': 'get-message-staging'
    },
    'database': {
        'type': 'dynamodb',
        'table_name': 'chat-messages-staging'
    }
}
```

### **Production Environment**
```python
{
    'mcp_server_url': 'https://mcp.sameer-jha.com',
    'dax_app_url': 'https://dax.sameer-jha.com',
    'pax_app_url': 'https://pax.sameer-jha.com',
    'api_base_url': 'https://mcp.sameer-jha.com',
    'use_in_memory_cache': False,
    'debug': False,
    'lambda_functions': {
        'send_message': 'send-message-prod',
        'make_call': 'make-call-prod',
        'get_message': 'get-message-prod'
    },
    'database': {
        'type': 'dynamodb',
        'table_name': 'chat-messages-prod'
    }
}
```

---

## 🔄 **Automatic Environment Detection**

### **Backend (Python)**
```python
# Environment is detected from ENVIRONMENT env var
# Defaults to 'local' if not set
from config import get_config
config = get_config()
```

### **Frontend (React)**
```javascript
// Environment is detected from:
// 1. REACT_APP_ENVIRONMENT env var
// 2. Hostname detection (localhost = local, staging subdomain = staging, etc.)
import CONFIG from './config'
```

---

## 🛠️ **Usage Examples**

### **Backend Configuration Usage**
```python
from config import get_config, get_api_url, is_local

config = get_config()

# Get API URL
api_url = get_api_url('/api/v1/send_message')

# Check environment
if is_local():
    print("Running in local mode")

# Get Lambda function name
function_name = config.get_lambda_function_name('send_message')
```

### **Frontend Configuration Usage**
```javascript
import CONFIG, API_ENDPOINTS from './config'

// Use API endpoints
const response = await fetch(API_ENDPOINTS.SEND_MESSAGE, {
    method: 'POST',
    body: JSON.stringify(data)
});

// Check environment
if (CONFIG.isLocal()) {
    console.log('Running locally');
}

// Use feature flags
if (CONFIG.features.voiceRecognition) {
    // Enable voice recognition
}
```

---

## 🧪 **Testing Configuration**

### **Test Current Configuration**
```bash
# Test Python configuration
python config.py

# Test React configuration (in browser console)
console.log(CONFIG);
console.log(API_ENDPOINTS);
```

### **Test Environment Switching**
```bash
# Test local
export ENVIRONMENT=local
python config.py

# Test staging
export ENVIRONMENT=staging
python config.py

# Test production
export ENVIRONMENT=production
python config.py
```

---

## 📊 **Configuration Features**

### **✅ What's Configured:**

- **URLs**: API endpoints, WebSocket URLs, app URLs
- **Database**: In-memory cache vs DynamoDB
- **Lambda Functions**: Environment-specific function names
- **CORS**: Environment-specific allowed origins
- **Debug Mode**: Local/staging = debug, production = no debug
- **Feature Flags**: Voice recognition, real-time updates, analytics
- **AWS Region**: Environment-specific AWS region

### **🔄 Auto-Detection:**

- **Backend**: Uses `ENVIRONMENT` environment variable
- **Frontend**: Uses `REACT_APP_ENVIRONMENT` or hostname detection
- **Fallback**: Always defaults to local if not specified

### **🔧 Easy Switching:**

- Change environment variable to switch configurations
- No code changes needed
- All components automatically adapt

---

## 🎯 **Quick Start Commands**

```bash
# Start local environment (all components)
./scripts/start_local.sh

# Start individual components
export ENVIRONMENT=local
cd mcp-server && uvicorn app:app --host 0.0.0.0 --port 8000 --reload
cd frontend/dax-app && npm start -- --port 3001
cd frontend/pax-app && npm start -- --port 3002

# Test configuration
python config.py
python test_in_memory_cache.py
```

**Status**: ✅ **Configuration System Complete** - Ready for all environments! 