#!/bin/bash

echo "🧪 Testing Bedrock Agent with Direct MCP Integration..."

# Get agent details from Terraform outputs
AGENT_ID=$(terraform output -raw agent_id 2>/dev/null || echo "")
ALIAS_ID=$(terraform output -raw alias_id 2>/dev/null || echo "")

if [ -z "$AGENT_ID" ] || [ -z "$ALIAS_ID" ]; then
    echo "❌ Agent ID or Alias ID not found. Please run deploy.sh first."
    exit 1
fi

echo "Agent ID: ${AGENT_ID}"
echo "Alias ID: ${ALIAS_ID}"

# Test cases
echo ""
echo "🧪 Running test cases..."

echo "1. Testing message sending..."
aws bedrock-agent-runtime invoke-agent \
  --agent-id ${AGENT_ID} \
  --agent-alias-id ${ALIAS_ID} \
  --session-id test-session-1 \
  --input '{"text": "Send a message to the passenger saying hello"}' \
  --region us-east-1

echo ""
echo "2. Testing call initiation..."
aws bedrock-agent-runtime invoke-agent \
  --agent-id ${AGENT_ID} \
  --agent-alias-id ${ALIAS_ID} \
  --session-id test-session-2 \
  --input '{"text": "Make a call to the passenger"}' \
  --region us-east-1

echo ""
echo "3. Testing message retrieval..."
aws bedrock-agent-runtime invoke-agent \
  --agent-id ${AGENT_ID} \
  --agent-alias-id ${ALIAS_ID} \
  --session-id test-session-3 \
  --input '{"text": "Get the conversation history for booking ABC123"}' \
  --region us-east-1

echo ""
echo "✅ Test cases completed!"
echo ""
echo "📋 Manual testing:"
echo "aws bedrock-agent-runtime invoke-agent \\"
echo "  --agent-id ${AGENT_ID} \\"
echo "  --agent-alias-id ${ALIAS_ID} \\"
echo "  --session-id your-session \\"
echo "  --input '{\"text\": \"Your message here\"}' \\"
echo "  --region us-east-1" 