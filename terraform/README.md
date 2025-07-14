# Terraform Infrastructure
## AI-Driven Chat & Voice Assistant Demo

This directory contains the Terraform configuration for deploying the complete infrastructure for the NavieTakieSimulation project.

---

## 🏗️ **Infrastructure Components**

### **EC2 Instance (MCP Server)**
- **Instance Type**: t3.micro (free tier eligible)
- **Purpose**: Hosts the MCP server (FastAPI)
- **Security**: SSH, HTTP, HTTPS access
- **User Data**: Automatically installs and configures the MCP server

### **Lambda Functions (Backend API)**
- **send-message**: Stores messages in DynamoDB
- **make-call**: Logs call activities in DynamoDB
- **get-message**: Retrieves messages for a booking code
- **Runtime**: Python 3.9
- **Memory**: 128 MB each

### **DynamoDB Table**
- **Name**: chat-messages
- **Billing**: PAY_PER_REQUEST (on-demand)
- **Primary Key**: booking_code (String)
- **Sort Key**: timestamp (String)

### **S3 Buckets (Web Hosting)**
- **dax-app-***: Hosts the DAX (Driver) React app
- **pax-app-***: Hosts the PAX (Passenger) React app
- **Configuration**: Static website hosting with public read access

### **CloudFront Distributions**
- **DAX App**: https://dax.sameer-jha.com
- **PAX App**: https://pax.sameer-jha.com
- **Features**: HTTPS, caching, SPA routing support

---

## 🚀 **Quick Start**

### **Prerequisites**
1. **AWS CLI** installed and configured
2. **Terraform** installed (version >= 1.0)
3. **AWS credentials** with appropriate permissions

### **Deployment Steps**

#### **Option 1: Automated Deployment**
```bash
# Run the automated deployment script
./scripts/deploy.sh
```

#### **Option 2: Manual Deployment**
```bash
# 1. Create EC2 key pair (if not exists)
aws ec2 create-key-pair --key-name demo-key --query 'KeyMaterial' --output text > demo-key.pem
chmod 400 demo-key.pem

# 2. Initialize Terraform
cd terraform
terraform init

# 3. Plan deployment
terraform plan

# 4. Apply deployment
terraform apply

# 5. Get outputs
terraform output
```

---

## 📁 **File Structure**

```
terraform/
├── main.tf              # Main Terraform configuration
├── variables.tf         # Input variables
├── outputs.tf          # Output values
├── user_data.sh        # EC2 user data script
└── README.md           # This file
```

---

## 🔧 **Configuration**

### **Variables**
All variables are defined in `variables.tf` with sensible defaults:

- `aws_region`: AWS region (default: us-east-1)
- `ec2_key_name`: EC2 key pair name (default: demo-key)
- `instance_type`: EC2 instance type (default: t3.micro)
- `lambda_timeout`: Lambda timeout (default: 30 seconds)
- `lambda_memory_size`: Lambda memory (default: 128 MB)

### **Customization**
To customize the deployment, create a `terraform.tfvars` file:

```hcl
aws_region = "us-west-2"
instance_type = "t3.small"
lambda_memory_size = 256
```

---

## 💰 **Cost Estimation**

### **One Week Demo Cost**
- **EC2 (t3.micro)**: $0.00 (free tier)
- **Lambda Functions**: $0.00 (free tier)
- **DynamoDB**: $0.01 (minimal usage)
- **S3 + CloudFront**: $0.00 (free tier)
- **Total**: ~$0.12 for 1 week

### **Cost Optimization**
- ✅ Uses free tier eligible resources
- ✅ No API Gateway (direct Lambda invocation)
- ✅ On-demand DynamoDB billing
- ✅ Minimal resource allocation

---

## 🔍 **Monitoring**

### **CloudWatch Logs**
- Lambda function logs: `/aws/lambda/*`
- Log retention: 7 days
- Automatic log group creation

### **Health Checks**
- MCP Server: `http://<ec2-ip>/health`
- Lambda functions: Test via AWS CLI
- S3 buckets: Public read access

---

## 🛠️ **Troubleshooting**

### **Common Issues**

#### **EC2 Instance Not Starting**
```bash
# Check instance status
aws ec2 describe-instances --instance-ids <instance-id>

# View user data logs
ssh -i demo-key.pem ec2-user@<public-ip>
sudo cat /var/log/cloud-init-output.log
```

#### **Lambda Functions Not Working**
```bash
# Test Lambda function
aws lambda invoke --function-name send-message --payload '{"booking_code":"TEST","message":"test","sender":"test"}' response.json
cat response.json
```

#### **S3 Buckets Not Accessible**
```bash
# Check bucket policy
aws s3api get-bucket-policy --bucket <bucket-name>

# Test public access
curl https://<bucket-name>.s3.amazonaws.com/
```

---

## 🧹 **Cleanup**

### **Destroy Infrastructure**
```bash
cd terraform
terraform destroy
```

### **Manual Cleanup**
```bash
# Delete EC2 key pair
aws ec2 delete-key-pair --key-name demo-key

# Delete S3 buckets (if not empty)
aws s3 rb s3://<bucket-name> --force

# Delete CloudFront distributions
aws cloudfront delete-distribution --id <distribution-id>
```

---

## 📋 **Outputs**

After successful deployment, Terraform will output:

- **MCP Server IP**: Public IP address of the EC2 instance
- **Lambda ARNs**: Function ARNs for integration
- **S3 Bucket Names**: Bucket names for web app deployment
- **CloudFront URLs**: Distribution URLs for web apps

---

## 🔐 **Security**

### **IAM Roles**
- **Lambda Role**: DynamoDB access, CloudWatch logs
- **EC2 Role**: Lambda invocation, CloudWatch logs

### **Security Groups**
- **EC2**: SSH (22), HTTP (80), HTTPS (443)
- **Lambda**: No inbound rules (serverless)

### **Best Practices**
- ✅ Least privilege access
- ✅ Encrypted EBS volumes
- ✅ Public access limited to necessary ports
- ✅ CloudWatch monitoring enabled

---

## 📞 **Support**

For issues or questions:
1. Check CloudWatch logs for errors
2. Review Terraform plan output
3. Test individual components
4. Refer to AWS documentation

---

**Ready to deploy? Run `./scripts/deploy.sh` to start!** 🚀 