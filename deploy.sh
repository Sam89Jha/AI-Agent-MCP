#!/bin/bash

echo "🚀 Deploying Bedrock Agent with Direct MCP Integration..."

# Set variables
REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "Account ID: ${ACCOUNT_ID}"
echo "Region: ${REGION}"

# Initialize Terraform
echo "🔧 Initializing Terraform..."
terraform init

# Plan the deployment
echo "📋 Planning deployment..."
terraform plan -out=tfplan

# Apply the infrastructure
echo "🏗️ Applying infrastructure..."
terraform apply tfplan

# Get outputs
S3_BUCKET=$(terraform output -raw s3_bucket_name)
ROLE_ARN=$(terraform output -raw iam_role_arn)
MCP_URL=$(terraform output -raw mcp_server_url)

echo "S3 Bucket: ${S3_BUCKET}"
echo "Role ARN: ${ROLE_ARN}"
echo "MCP URL: ${MCP_URL}"

# Create Bedrock Agent
echo "🤖 Creating Bedrock Agent..."
AGENT_ID=$(aws bedrock-agent create-agent \
  --agent-name "driver-assistant-direct" \
  --description "AI Agent for driver-passenger communication with direct MCP integration" \
  --instruction "You are an AI assistant that helps drivers and passengers communicate. You can send messages, make calls, and retrieve conversation history by calling the MCP server APIs directly." \
  --agent-resource-role-arn ${ROLE_ARN} \
  --foundation-model "anthropic.claude-3-sonnet-20240229-v1:0" \
  --region ${REGION} \
  --query 'agent.agentId' \
  --output text)

echo "Agent ID: ${AGENT_ID}"

# Wait for agent to be ready
echo "⏳ Waiting for agent to be ready..."
sleep 30

# Prepare the agent
echo "🔧 Preparing agent..."
aws bedrock-agent prepare-agent --agent-id ${AGENT_ID} --region ${REGION}

# Wait for preparation
echo "⏳ Waiting for agent preparation..."
sleep 60

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

echo "✅ Bedrock Agent deployment complete!"
echo ""
echo "🔗 Agent Details:"
echo "Agent ID: ${AGENT_ID}"
echo "Agent Version: ${AGENT_VERSION}"
echo "Alias ID: ${ALIAS_ID}"
echo "S3 Bucket: ${S3_BUCKET}"
echo "MCP Server URL: ${MCP_URL}"
echo ""
echo "📋 Test the Bedrock Agent:"
echo "aws bedrock-agent-runtime invoke-agent \\"
echo "  --agent-id ${AGENT_ID} \\"
echo "  --agent-alias-id ${ALIAS_ID} \\"
echo "  --session-id test-session \\"
echo "  --input '{\"text\": \"Send a message to the passenger\"}' \\"
echo "  --region ${REGION}" 