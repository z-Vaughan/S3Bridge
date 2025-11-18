# Troubleshooting Guide - S3Bridge

Common issues and solutions for the S3Bridge.

## Authentication Issues

### API Key Not Found

**Error:**
```
Exception: API key not found. Set S3BRIDGE_API_KEY environment variable or redeploy infrastructure.
```

**Solutions:**

1. **Set Environment Variable:**
```bash
# Linux/macOS
export S3BRIDGE_API_KEY=your-api-key-here

# Windows CMD
set S3BRIDGE_API_KEY=your-api-key-here

# PowerShell
$env:S3BRIDGE_API_KEY="your-api-key-here"
```

2. **Get API Key from CloudFormation:**
```bash
aws cloudformation describe-stacks --stack-name s3bridge \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiKey`].OutputValue' --output text
```

3. **Check Deployment Config:**
```python
from config.aws_config import AWSConfig
config = AWSConfig()
deployment_config = config.load_deployment_config()
if deployment_config:
    print(f"API Key: {deployment_config.get('api_key', 'Not found')}")
```

### Infrastructure Not Deployed

**Error:**
```
Exception: S3Bridge not deployed. Run: python -m s3bridge.setup
```

**Solution:**
```bash
# Deploy infrastructure
python scripts/setup.py --admin-user your-username

# Or force redeploy
python scripts/setup.py --admin-user your-username --force
```

## Service Configuration Issues

### Service Not Found

**Error:**
```
{'statusCode': 400, 'body': '{"error": "Unknown service: myservice"}'}
```

**Solutions:**

1. **Add the Service:**
```bash
python scripts/add_service.py myservice "myservice-*" --permissions read-write
```

2. **Check Service Registration:**
```bash
# View Lambda function code
aws lambda get-function --function-name s3bridge-credential-service
```

3. **Verify Service in Lambda:**
```python
# Check if service exists in Lambda environment variables
aws lambda get-function-configuration --function-name s3bridge-credential-service \
  --query 'Environment.Variables'
```

### Bucket Access Denied

**Error:**
```
ValueError: Service 'analytics' not authorized for bucket 'webapp-data'
```

**Solutions:**

1. **Check Bucket Patterns:**
```python
# Verify bucket name matches service patterns
# analytics service: *-analytics-*, analytics-*
# Use: company-analytics-data ✓
# Not: webapp-data ✗
```

2. **Update Service Patterns:**
```bash
# Add new bucket pattern to existing service
python scripts/add_service.py analytics "analytics-*,*-analytics-*,webapp-data" --permissions read-only
```

3. **Use Correct Service:**
```python
# Wrong service for bucket
client = S3BridgeClient("webapp-data", "analytics")  # ✗

# Correct service for bucket  
client = S3BridgeClient("webapp-data", "webapp")     # ✓
```

## AWS Infrastructure Issues

### CloudFormation Stack Errors

**Error:**
```
An error occurred (ValidationError) when calling the CreateStack operation
```

**Solutions:**

1. **Check AWS Credentials:**
```bash
aws sts get-caller-identity
```

2. **Verify Permissions:**
```bash
# Ensure user has CloudFormation, Lambda, IAM, API Gateway permissions
aws iam get-user-policy --user-name your-username --policy-name AdminPolicy
```

3. **Check Stack Status:**
```bash
aws cloudformation describe-stacks --stack-name s3bridge
```

### Lambda Function Errors

**Error:**
```
{'statusCode': 500, 'body': '{"error": "Role not found"}'}
```

**Solutions:**

1. **Check IAM Role Exists:**
```bash
aws iam get-role --role-name myservice-s3-access-role
```

2. **Recreate Service Role:**
```bash
python scripts/add_service.py myservice "myservice-*" --permissions read-write
```

3. **View Lambda Logs:**
```bash
aws logs filter-log-events --log-group-name "/aws/lambda/s3bridge-credential-service" \
  --start-time $(date -d "1 hour ago" +%s)000
```

## Network and API Issues

### API Gateway Timeout

**Error:**
```
requests.exceptions.Timeout: HTTPSConnectionPool(...): Read timed out.
```

**Solutions:**

1. **Increase Timeout:**
```python
# In universal_auth.py, modify timeout
response = requests.get(
    endpoint,
    params={'service': self.service_name, 'duration': '3600'},
    headers={'X-API-Key': api_key},
    timeout=60  # Increase from 30 to 60 seconds
)
```

2. **Check API Gateway Status:**
```bash
aws apigateway get-rest-apis
```

3. **Test API Directly:**
```bash
curl -H "X-API-Key: your-api-key" \
  "https://your-api-id.execute-api.region.amazonaws.com/prod/credentials?service=test"
```

### Invalid API Key

**Error:**
```
{'message': 'Forbidden'}
```

**Solutions:**

1. **Verify API Key:**
```bash
# Get correct API key
aws apigateway get-api-keys --include-values
```

2. **Check Usage Plan:**
```bash
aws apigateway get-usage-plans
```

3. **Test with Correct Key:**
```python
import os
os.environ['S3BRIDGE_API_KEY'] = 'correct-api-key-here'
```

## S3 Operation Issues

### File Not Found

**Error:**
```
botocore.exceptions.NoSuchKey: The specified key does not exist.
```

**Solutions:**

1. **Check Object Key:**
```python
# List objects to verify key
objects = client.list_objects("config/")
print("Available objects:", objects)
```

2. **Verify Bucket Name:**
```python
# Ensure bucket exists and is accessible
try:
    objects = client.list_objects("")
    print(f"Bucket accessible, contains {len(objects)} objects")
except Exception as e:
    print(f"Bucket access error: {e}")
```

### Permission Denied

**Error:**
```
botocore.exceptions.ClientError: An error occurred (AccessDenied) when calling the PutObject operation
```

**Solutions:**

1. **Check Service Permissions:**
```bash
# Verify service has write permissions
aws iam get-role-policy --role-name myservice-s3-access-role --policy-name MyserviceS3AccessPolicy
```

2. **Update Permissions:**
```bash
# Change from read-only to read-write
python scripts/add_service.py myservice "myservice-*" --permissions read-write
```

## Debug Commands

### Check Infrastructure Status

```bash
# CloudFormation stack
aws cloudformation describe-stacks --stack-name s3bridge

# Lambda functions
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `universal`)]'

# API Gateway
aws apigateway get-rest-apis --query 'items[?name==`s3bridge`]'

# IAM roles
aws iam list-roles --path-prefix /service-role/ --query 'Roles[?contains(RoleName, `s3-access`)]'
```

### Test Components

```bash
# Test Lambda function directly
aws lambda invoke --function-name s3bridge-credential-service \
  --payload '{"queryStringParameters":{"service":"test"}}' \
  response.json && cat response.json

# Test API Gateway
curl -H "X-API-Key: $S3BRIDGE_API_KEY" \
  "$(aws cloudformation describe-stacks --stack-name s3bridge \
     --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' --output text)/credentials?service=test"
```

### View Logs

```bash
# Lambda logs
aws logs filter-log-events --log-group-name "/aws/lambda/s3bridge-credential-service" \
  --start-time $(date -d "1 hour ago" +%s)000

# API Gateway logs (if enabled)
aws logs filter-log-events --log-group-name "API-Gateway-Execution-Logs_your-api-id/prod"
```

## Performance Issues

### Slow Credential Refresh

**Symptoms:**
- Long delays on first request
- Frequent credential refreshes

**Solutions:**

1. **Check Network Connectivity:**
```bash
# Test API Gateway response time
time curl -H "X-API-Key: $S3BRIDGE_API_KEY" \
  "your-api-gateway-url/credentials?service=test"
```

2. **Optimize Credential Caching:**
```python
# In universal_auth.py, adjust cache timing
self._credentials_expiry = expiry_time - timedelta(minutes=5)  # Reduce buffer
```

### Large File Operations

**Symptoms:**
- Timeouts on large file uploads/downloads
- Memory errors

**Solutions:**

1. **Use Streaming Operations:**
```python
# For large files, use download_file instead of read_text
client.download_file("large_file.csv", "local_file.csv")

# Process locally
with open("local_file.csv", 'r') as f:
    for line in f:
        process_line(line)
```

2. **Implement Retry Logic:**
```python
import time
from botocore.exceptions import ClientError

def retry_operation(operation, max_retries=3):
    for attempt in range(max_retries):
        try:
            return operation()
        except ClientError as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
```

## Getting Help

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed request/response information
from s3bridge import S3BridgeClient
client = S3BridgeClient("test-bucket", "test-service")
```

### Collect Diagnostic Information

```bash
# Create diagnostic report
echo "=== AWS Configuration ===" > diagnostic.txt
aws sts get-caller-identity >> diagnostic.txt
echo -e "\n=== CloudFormation Stack ===" >> diagnostic.txt
aws cloudformation describe-stacks --stack-name s3bridge >> diagnostic.txt
echo -e "\n=== Lambda Functions ===" >> diagnostic.txt
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `universal`)]' >> diagnostic.txt
echo -e "\n=== Environment Variables ===" >> diagnostic.txt
env | grep UNIVERSAL >> diagnostic.txt
```

### Contact Support

When reporting issues, include:
- Error messages (full stack trace)
- AWS region and account ID
- Service name and bucket patterns
- Steps to reproduce
- Diagnostic information from above