#!/bin/bash

echo "🔧 Completing Bedrock Agent Setup..."

# Set variables
REGION="us-east-1"
AGENT_ID="BXHDRBNNAS"
S3_BUCKET="bedrock-agent-schemas-418960606395"

echo "Agent ID: ${AGENT_ID}"
echo "S3 Bucket: ${S3_BUCKET}"

# Get agent version
echo "🔍 Getting agent version..."
AGENT_VERSION=$(aws bedrock-agent list-agent-versions --agent-id ${AGENT_ID} --region ${REGION} --query 'agentVersionSummaries[0].agentVersion' --output text)
echo "Agent Version: ${AGENT_VERSION}"

# Create Action Groups
echo "🔧 Creating Action Groups..."

echo "Creating send_message action group..."
aws bedrock-agent create-agent-action-group \
  --agent-id ${AGENT_ID} \
  --agent-version ${AGENT_VERSION} \
  --action-group-name "send_message" \
  --description "Send messages between drivers and passengers via MCP server" \
  --api-schema "{\"s3\":{\"s3BucketName\":\"${S3_BUCKET}\",\"s3ObjectKey\":\"send_message_schema.json\"}}" \
  --region ${REGION}

echo "Creating make_call action group..."
aws bedrock-agent create-agent-action-group \
  --agent-id ${AGENT_ID} \
  --agent-version ${AGENT_VERSION} \
  --action-group-name "make_call" \
  --description "Initiate voice calls between drivers and passengers via MCP server" \
  --api-schema "{\"s3\":{\"s3BucketName\":\"${S3_BUCKET}\",\"s3ObjectKey\":\"make_call_schema.json\"}}" \
  --region ${REGION}

echo "Creating get_messages action group..."
aws bedrock-agent create-agent-action-group \
  --agent-id ${AGENT_ID} \
  --agent-version ${AGENT_VERSION} \
  --action-group-name "get_messages" \
  --description "Retrieve conversation history via MCP server" \
  --api-schema "{\"s3\":{\"s3BucketName\":\"${S3_BUCKET}\",\"s3ObjectKey\":\"get_messages_schema.json\"}}" \
  --region ${REGION}

# Create Agent Alias
echo "🏷️ Creating Agent Alias..."
ALIAS_ID=$(aws bedrock-agent create-agent-alias \
  --agent-id ${AGENT_ID} \
  --agent-alias-name "driver-assistant-direct-alias" \
  --description "Production alias for driver assistant agent with direct MCP integration" \
  --routing-configuration "[{\"agentVersion\":\"${AGENT_VERSION}\"}]" \
  --region ${REGION} \
  --query 'agentAlias.agentAliasId' \
  --output text)

echo "Alias ID: ${ALIAS_ID}"

# Save agent info to file
echo "Agent ID: ${AGENT_ID}" > agent-info.txt
echo "Alias ID: ${ALIAS_ID}" >> agent-info.txt
echo "S3 Bucket: ${S3_BUCKET}" >> agent-info.txt
echo "MCP Server URL: http://mcp-server-env.eba-r23dy2pd.us-west-2.elasticbeanstalk.com" >> agent-info.txt

echo "✅ Bedrock Agent setup complete!"
echo ""
echo "🔗 Agent Details:"
echo "Agent ID: ${AGENT_ID}"
echo "Agent Version: ${AGENT_VERSION}"
echo "Alias ID: ${ALIAS_ID}"
echo "S3 Bucket: ${S3_BUCKET}"
echo ""
echo "📋 Test the Bedrock Agent:"
echo "aws bedrock-agent-runtime invoke-agent \\"
echo "  --agent-id ${AGENT_ID} \\"
echo "  --agent-alias-id ${ALIAS_ID} \\"
echo "  --session-id test-session \\"
echo "  --input '{\"text\": \"Send a message to the passenger\"}' \\"
echo "  --region ${REGION}"
echo ""
echo "🧪 Or run: ./test_agent.sh" 