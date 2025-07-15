#!/bin/bash

echo "🧪 Testing Basic Bedrock Agent..."

AGENT_ID="BXHDRBNNAS"

echo "Agent ID: ${AGENT_ID}"

# Test basic agent invocation
echo "Testing basic agent invocation..."
aws bedrock-agent-runtime invoke-agent \
  --agent-id ${AGENT_ID} \
  --session-id test-session-basic \
  --input '{"text": "Hello, can you help me?"}' \
  --region us-east-1

echo ""
echo "✅ Basic test completed!"
echo ""
echo "📋 Manual testing:"
echo "aws bedrock-agent-runtime invoke-agent \\"
echo "  --agent-id ${AGENT_ID} \\"
echo "  --session-id your-session \\"
echo "  --input '{\"text\": \"Your message here\"}' \\"
echo "  --region us-east-1" 