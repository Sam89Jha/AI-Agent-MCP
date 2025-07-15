#!/bin/bash

echo "🔍 Checking Bedrock Agent Status..."

# Set variables
REGION="us-east-1"
AGENT_ID="BXHDRBNNAS"

echo "Agent ID: ${AGENT_ID}"

# Check if agent exists
echo "Checking if agent exists..."
AGENT_STATUS=$(aws bedrock-agent get-agent --agent-id ${AGENT_ID} --region ${REGION} --query 'agent.agentStatus' --output text 2>/dev/null)

if [ $? -eq 0 ]; then
    echo "Agent Status: ${AGENT_STATUS}"
    
    if [ "${AGENT_STATUS}" = "PREPARED" ]; then
        echo "✅ Agent is prepared!"
        
        # List versions
        echo "📋 Agent Versions:"
        aws bedrock-agent list-agent-versions --agent-id ${AGENT_ID} --region ${REGION}
        
        # List aliases
        echo "📋 Agent Aliases:"
        aws bedrock-agent list-agent-aliases --agent-id ${AGENT_ID} --region ${REGION}
        
    elif [ "${AGENT_STATUS}" = "NOT_PREPARED" ]; then
        echo "🔄 Agent is not prepared. Preparing agent..."
        aws bedrock-agent prepare-agent --agent-id ${AGENT_ID} --region ${REGION}
        echo "⏳ Agent preparation started. This may take several minutes..."
        echo "Check the AWS console for progress."
        
    else
        echo "⚠️ Agent status: ${AGENT_STATUS}"
        echo "Check the AWS console for more details."
    fi
else
    echo "❌ Could not retrieve agent status. Check permissions or agent ID."
fi 