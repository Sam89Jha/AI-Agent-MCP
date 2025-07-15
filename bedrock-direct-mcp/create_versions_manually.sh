#!/bin/bash

echo "🔧 Creating Bedrock Agent Versions and Alias Manually..."

# Set variables
REGION="us-east-1"
AGENT_ID="BXHDRBNNAS"
S3_BUCKET="bedrock-agent-schemas-418960606395"

echo "Agent ID: ${AGENT_ID}"
echo "S3 Bucket: ${S3_BUCKET}"

# Get the DRAFT version
echo "🔍 Getting DRAFT version..."
DRAFT_VERSION=$(aws bedrock-agent list-agent-versions --agent-id ${AGENT_ID} --region ${REGION} --query 'agentVersionSummaries[?agentVersion==`DRAFT`].agentVersion' --output text)

if [ -z "${DRAFT_VERSION}" ]; then
    echo "❌ No DRAFT version found. Creating one..."
    # Create a new version from the agent
    aws bedrock-agent create-agent-version --agent-id ${AGENT_ID} --region ${REGION}
    DRAFT_VERSION="DRAFT"
fi

echo "Using version: ${DRAFT_VERSION}"

# Create Action Groups
echo "🔧 Creating Action Groups..."

echo "Creating send_message action group..."
aws bedrock-agent create-agent-action-group \
  --agent-id ${AGENT_ID} \
  --agent-version ${DRAFT_VERSION} \
  --action-group-name "send_message" \
  --description "Send messages between drivers and passengers via MCP server" \
  --api-schema "{\"s3\":{\"s3BucketName\":\"${S3_BUCKET}\",\"s3ObjectKey\":\"send_message_schema.json\"}}" \
  --region ${REGION}

echo "Creating make_call action group..."
aws bedrock-agent create-agent-action-group \
  --agent-id ${AGENT_ID} \
  --agent-version ${DRAFT_VERSION} \
  --action-group-name "make_call" \
  --description "Initiate voice calls between drivers and passengers via MCP server" \
  --api-schema "{\"s3\":{\"s3BucketName\":\"${S3_BUCKET}\",\"s3ObjectKey\":\"make_call_schema.json\"}}" \
  --region ${REGION}

echo "Creating get_messages action group..."
aws bedrock-agent create-agent-action-group \
  --agent-id ${AGENT_ID} \
  --agent-version ${DRAFT_VERSION} \
  --action-group-name "get_messages" \
  --description "Retrieve conversation history via MCP server" \
  --api-schema "{\"s3\":{\"s3BucketName\":\"${S3_BUCKET}\",\"s3ObjectKey\":\"get_messages_schema.json\"}}" \
  --region ${REGION}

# Prepare the agent with the new action groups
echo "🔄 Preparing agent with new action groups..."
aws bedrock-agent prepare-agent --agent-id ${AGENT_ID} --region ${REGION}

echo "⏳ Agent preparation started. This may take several minutes..."
echo "Check the AWS console for progress."
echo ""
echo "After preparation completes, you can:"
echo "1. Create a version from the DRAFT in AWS console"
echo "2. Create an alias pointing to that version"
echo "3. Test the agent" 