#!/bin/bash

echo "🔧 Deploying Lambda Executors for Bedrock Agent..."

# Set variables
REGION="us-east-1"
AGENT_ID="BXHDRBNNAS"
S3_BUCKET="bedrock-agent-schemas-418960606395"

echo "Agent ID: ${AGENT_ID}"
echo "S3 Bucket: ${S3_BUCKET}"

# Create Lambda functions for each executor
echo "🔧 Creating Lambda Executors..."

# Send Message Executor
echo "Creating send_message executor..."
aws lambda create-function \
  --function-name send-message-executor \
  --runtime python3.9 \
  --role arn:aws:iam::418960606395:role/lambda-execution-role \
  --handler send_message_executor.lambda_handler \
  --zip-file fileb://lambda-executors/send_message_executor.zip \
  --environment Variables="{MCP_SERVER_URL=http://mcp-server-env.eba-r23dy2pd.us-west-2.elasticbeanstalk.com}" \
  --region ${REGION}

# Make Call Executor
echo "Creating make_call executor..."
aws lambda create-function \
  --function-name make-call-executor \
  --runtime python3.9 \
  --role arn:aws:iam::418960606395:role/lambda-execution-role \
  --handler make_call_executor.lambda_handler \
  --zip-file fileb://lambda-executors/make_call_executor.zip \
  --environment Variables="{MCP_SERVER_URL=http://mcp-server-env.eba-r23dy2pd.us-west-2.elasticbeanstalk.com}" \
  --region ${REGION}

# Get Messages Executor
echo "Creating get_messages executor..."
aws lambda create-function \
  --function-name get-messages-executor \
  --runtime python3.9 \
  --role arn:aws:iam::418960606395:role/lambda-execution-role \
  --handler get_messages_executor.lambda_handler \
  --zip-file fileb://lambda-executors/get_messages_executor.zip \
  --environment Variables="{MCP_SERVER_URL=http://mcp-server-env.eba-r23dy2pd.us-west-2.elasticbeanstalk.com}" \
  --region ${REGION}

# Get Lambda ARNs
SEND_MESSAGE_ARN=$(aws lambda get-function --function-name send-message-executor --region ${REGION} --query 'Configuration.FunctionArn' --output text)
MAKE_CALL_ARN=$(aws lambda get-function --function-name make-call-executor --region ${REGION} --query 'Configuration.FunctionArn' --output text)
GET_MESSAGES_ARN=$(aws lambda get-function --function-name get-messages-executor --region ${REGION} --query 'Configuration.FunctionArn' --output text)

echo "Lambda ARNs:"
echo "Send Message: ${SEND_MESSAGE_ARN}"
echo "Make Call: ${MAKE_CALL_ARN}"
echo "Get Messages: ${GET_MESSAGES_ARN}"

# Create Action Groups with Lambda executors
echo "🔧 Creating Action Groups with Lambda executors..."

echo "Creating send_message action group..."
aws bedrock-agent create-agent-action-group \
  --agent-id ${AGENT_ID} \
  --agent-version DRAFT \
  --action-group-name "send_message" \
  --description "Send messages between drivers and passengers via MCP server" \
  --api-schema "{\"s3\":{\"s3BucketName\":\"${S3_BUCKET}\",\"s3ObjectKey\":\"send_message_schema.json\"}}" \
  --action-group-executor "{\"lambda\":\"${SEND_MESSAGE_ARN}\"}" \
  --region ${REGION}

echo "Creating make_call action group..."
aws bedrock-agent create-agent-action-group \
  --agent-id ${AGENT_ID} \
  --agent-version DRAFT \
  --action-group-name "make_call" \
  --description "Initiate voice calls between drivers and passengers via MCP server" \
  --api-schema "{\"s3\":{\"s3BucketName\":\"${S3_BUCKET}\",\"s3ObjectKey\":\"make_call_schema.json\"}}" \
  --action-group-executor "{\"lambda\":\"${MAKE_CALL_ARN}\"}" \
  --region ${REGION}

echo "Creating get_messages action group..."
aws bedrock-agent create-agent-action-group \
  --agent-id ${AGENT_ID} \
  --agent-version DRAFT \
  --action-group-name "get_messages" \
  --description "Retrieve conversation history via MCP server" \
  --api-schema "{\"s3\":{\"s3BucketName\":\"${S3_BUCKET}\",\"s3ObjectKey\":\"get_messages_schema.json\"}}" \
  --action-group-executor "{\"lambda\":\"${GET_MESSAGES_ARN}\"}" \
  --region ${REGION}

# Prepare the agent with the new action groups
echo "🔄 Preparing agent with new action groups..."
aws bedrock-agent prepare-agent --agent-id ${AGENT_ID} --region ${REGION}

echo "✅ Lambda executors deployed and action groups created!"
echo "⏳ Agent preparation started. This may take several minutes..."
echo "Check the AWS console for progress."
echo ""
echo "After preparation completes, you can:"
echo "1. Create a version from the DRAFT in AWS console"
echo "2. Create an alias pointing to that version"
echo "3. Test the agent" 