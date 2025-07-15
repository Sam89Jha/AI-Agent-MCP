#!/bin/bash

echo "🔧 Creating Lambda Execution Role..."

# Create the trust policy for Lambda
cat > lambda-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create the execution policy
cat > lambda-execution-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeAgent"
      ],
      "Resource": "*"
    }
  ]
}
EOF

# Create the role
echo "Creating Lambda execution role..."
aws iam create-role \
  --role-name lambda-execution-role \
  --assume-role-policy-document file://lambda-trust-policy.json \
  --region us-east-1

# Attach the execution policy
echo "Attaching execution policy..."
aws iam put-role-policy \
  --role-name lambda-execution-role \
  --policy-name lambda-execution-policy \
  --policy-document file://lambda-execution-policy.json \
  --region us-east-1

# Attach the basic Lambda execution policy
echo "Attaching AWS managed Lambda execution policy..."
aws iam attach-role-policy \
  --role-name lambda-execution-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \
  --region us-east-1

echo "✅ Lambda execution role created!"
echo "Role ARN: arn:aws:iam::418960606395:role/lambda-execution-role"

# Clean up temporary files
rm lambda-trust-policy.json lambda-execution-policy.json 