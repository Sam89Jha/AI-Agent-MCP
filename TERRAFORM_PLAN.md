# Terraform Implementation Plan - Cost Optimized
## AI-Driven Chat & Voice Assistant Demo

---

## 💰 **Cost Optimization Strategy**

### **Cheapest Implementation Choices:**

1. **EC2 Instance**: t3.micro (free tier eligible) - $0.0084/hour
2. **Lambda Functions**: Pay per request - ~$0.01 for demo
3. **DynamoDB**: On-demand pricing - ~$0.01 for demo
4. **Bedrock**: Pay per token - ~$0.50-1.00 for demo
5. **Web Hosting**: S3 + CloudFront (free tier eligible)
6. **Domain**: Use existing sameer-jha.com

**Total Estimated Cost**: ~$1-2 for 1-week demo

---

## 🏗️ **Infrastructure Components**

### **1. EC2 Instance (MCP Server)**
```hcl
# t3.micro - Free tier eligible, 1 vCPU, 1 GB RAM
resource "aws_instance" "mcp_server" {
  ami           = "ami-0c02fb55956c7d316" # Amazon Linux 2023
  instance_type = "t3.micro"
  
  # Free tier: 750 hours/month
  # Cost: $0.0084/hour if exceeds free tier
}
```

### **2. Lambda Functions (Backend API)**
```hcl
# Three Lambda functions for backend operations
resource "aws_lambda_function" "send_message" {
  filename      = "backend/lambda-functions/send_message.zip"
  function_name = "send-message"
  role          = aws_iam_role.lambda_role.arn
  runtime       = "python3.9"
  timeout       = 30
}

resource "aws_lambda_function" "make_call" {
  filename      = "backend/lambda-functions/make_call.zip"
  function_name = "make-call"
  role          = aws_iam_role.lambda_role.arn
  runtime       = "python3.9"
  timeout       = 30
}

resource "aws_lambda_function" "get_message" {
  filename      = "backend/lambda-functions/get_message.zip"
  function_name = "get-message"
  role          = aws_iam_role.lambda_role.arn
  runtime       = "python3.9"
  timeout       = 30
}
```

### **3. DynamoDB Table**
```hcl
# On-demand pricing - pay per request
resource "aws_dynamodb_table" "messages" {
  name           = "chat-messages"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "booking_code"
  range_key      = "timestamp"
  
  attribute {
    name = "booking_code"
    type = "S"
  }
  
  attribute {
    name = "timestamp"
    type = "S"
  }
}
```

### **4. S3 Buckets (Web Hosting)**
```hcl
# Free tier: 5 GB storage, 20,000 GET requests
resource "aws_s3_bucket" "dax_app" {
  bucket = "dax-app-sameer-jha"
}

resource "aws_s3_bucket" "pax_app" {
  bucket = "pax-app-sameer-jha"
}

# Static website hosting
resource "aws_s3_bucket_website_configuration" "dax_app" {
  bucket = aws_s3_bucket.dax_app.id
  index_document {
    suffix = "index.html"
  }
}

resource "aws_s3_bucket_website_configuration" "pax_app" {
  bucket = aws_s3_bucket.pax_app.id
  index_document {
    suffix = "index.html"
  }
}
```

### **5. CloudFront Distributions**
```hcl
# Free tier: 1 TB data transfer out
resource "aws_cloudfront_distribution" "dax_app" {
  origin {
    domain_name = aws_s3_bucket.dax_app.bucket_regional_domain_name
    origin_id   = "S3-dax-app"
  }
  
  enabled             = true
  is_ipv6_enabled    = true
  default_root_object = "index.html"
  
  aliases = ["dax.sameer-jha.com"]
  
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-dax-app"
    
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
    
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }
}

resource "aws_cloudfront_distribution" "pax_app" {
  origin {
    domain_name = aws_s3_bucket.pax_app.bucket_regional_domain_name
    origin_id   = "S3-pax-app"
  }
  
  enabled             = true
  is_ipv6_enabled    = true
  default_root_object = "index.html"
  
  aliases = ["pax.sameer-jha.com"]
  
  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-pax-app"
    
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
    
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }
}
```

### **6. IAM Roles and Policies**
```hcl
# Lambda execution role
resource "aws_iam_role" "lambda_role" {
  name = "lambda_execution_role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# DynamoDB access for Lambda
resource "aws_iam_role_policy" "lambda_dynamodb" {
  name = "lambda_dynamodb_policy"
  role = aws_iam_role.lambda_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = aws_dynamodb_table.messages.arn
      }
    ]
  })
}

# CloudWatch Logs for Lambda
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# EC2 role for MCP server
resource "aws_iam_role" "ec2_role" {
  name = "ec2_mcp_role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# Lambda invocation for EC2
resource "aws_iam_role_policy" "ec2_lambda" {
  name = "ec2_lambda_policy"
  role = aws_iam_role.ec2_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          aws_lambda_function.send_message.arn,
          aws_lambda_function.make_call.arn,
          aws_lambda_function.get_message.arn
        ]
      }
    ]
  })
}
```

---

## 📁 **Terraform File Structure**

```
terraform/
├── main.tf                    # Main configuration
├── variables.tf               # Input variables
├── outputs.tf                 # Output values
├── providers.tf               # Provider configuration
├── versions.tf                # Terraform and provider versions
└── modules/
    ├── lambda/
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── ec2/
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── dynamodb/
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    └── s3-cloudfront/
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

---

## 🚀 **Deployment Steps**

### **Phase 1: Infrastructure Setup**
1. **Initialize Terraform**
   ```bash
   cd terraform
   terraform init
   ```

2. **Plan and Apply**
   ```bash
   terraform plan
   terraform apply
   ```

3. **Verify Resources**
   - EC2 instance running
   - Lambda functions created
   - DynamoDB table active
   - S3 buckets accessible
   - CloudFront distributions deployed

### **Phase 2: Application Deployment**
1. **Deploy MCP Server to EC2**
2. **Upload Lambda function code**
3. **Deploy React apps to S3**
4. **Configure DNS records**

---

## 💡 **Cost Optimization Tips**

### **Free Tier Benefits:**
- **EC2**: 750 hours/month of t3.micro
- **Lambda**: 1M requests/month
- **DynamoDB**: 25 GB storage, 25 WCU/RCU
- **S3**: 5 GB storage, 20K GET requests
- **CloudFront**: 1 TB data transfer out

### **Cost Monitoring:**
```hcl
# Enable cost allocation tags
resource "aws_cost_allocation_tag" "project" {
  tag_key = "Project"
  tag_value = "NavieTakieSimulation"
}
```

### **Auto Scaling (Optional):**
```hcl
# Scale down EC2 during off-hours
resource "aws_autoscaling_schedule" "scale_down" {
  count                  = var.enable_auto_scaling ? 1 : 0
  scheduled_action_name  = "scale-down"
  min_size              = 0
  max_size              = 0
  desired_capacity      = 0
  recurrence           = "0 22 * * *" # 10 PM daily
}
```

---

## 🔧 **Environment Variables**

```hcl
# Lambda environment variables
resource "aws_lambda_function" "send_message" {
  # ... existing configuration ...
  
  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.messages.name
      REGION         = var.aws_region
    }
  }
}
```

---

## 📊 **Monitoring and Logging**

```hcl
# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "lambda_logs" {
  for_each = toset([
    aws_lambda_function.send_message.function_name,
    aws_lambda_function.make_call.function_name,
    aws_lambda_function.get_message.function_name
  ])
  
  name              = "/aws/lambda/${each.value}"
  retention_in_days = 7
}

# CloudWatch Alarms for cost monitoring
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  for_each = toset([
    aws_lambda_function.send_message.function_name,
    aws_lambda_function.make_call.function_name,
    aws_lambda_function.get_message.function_name
  ])
  
  alarm_name          = "${each.value}-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "1"
  alarm_description   = "Lambda function errors"
  
  dimensions = {
    FunctionName = each.value
  }
}
```

---

## ✅ **Success Criteria**

- [ ] All resources deployed successfully
- [ ] EC2 instance accessible via SSH
- [ ] Lambda functions invokable
- [ ] DynamoDB table operational
- [ ] S3 buckets hosting web apps
- [ ] CloudFront distributions active
- [ ] DNS records configured
- [ ] Cost within budget ($1-2 for demo)

---

**Ready to implement this cost-optimized infrastructure?** 