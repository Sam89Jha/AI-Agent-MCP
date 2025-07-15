#!/bin/bash

echo "🏷️ Creating Agent Alias..."

AGENT_ID="BXHDRBNNAS"

# Create Agent Alias with version 1
echo "Creating alias for agent ${AGENT_ID}..."
ALIAS_ID=$(aws bedrock-agent create-agent-alias \
  --agent-id ${AGENT_ID} \
  --agent-alias-name "driver-assistant-direct-alias" \
  --description "Production alias for driver assistant agent with direct MCP integration" \
  --routing-configuration '[{"agentVersion":"1"}]' \
  --region us-east-1 \
  --query 'agentAlias.agentAliasId' \
  --output text)

echo "Alias ID: ${ALIAS_ID}"

# Save agent info to file
echo "Agent ID: ${AGENT_ID}" > agent-info.txt
echo "Alias ID: ${ALIAS_ID}" >> agent-info.txt
echo "S3 Bucket: bedrock-agent-schemas-418960606395" >> agent-info.txt
echo "MCP Server URL: http://mcp-server-env.eba-r23dy2pd.us-west-2.elasticbeanstalk.com" >> agent-info.txt

echo "✅ Alias created!"
echo ""
echo "🔗 Agent Details:"
echo "Agent ID: ${AGENT_ID}"
echo "Alias ID: ${ALIAS_ID}"
echo ""
echo "📋 Test the Bedrock Agent:"
echo "aws bedrock-agent-runtime invoke-agent \\"
echo "  --agent-id ${AGENT_ID} \\"
echo "  --agent-alias-id ${ALIAS_ID} \\"
echo "  --session-id test-session \\"
echo "  --input '{\"text\": \"Send a message to the passenger\"}' \\"
echo "  --region us-east-1" 