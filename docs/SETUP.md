# Setup Guide - Universal S3 Library

Complete setup instructions for deploying the Universal S3 Library infrastructure.

## Prerequisites

- AWS CLI configured with admin permissions
- Python 3.9+
- Git (for cloning repository)

## Quick Setup

```bash
# 1. Clone repository
git clone <repository-url> universal_s3_library
cd universal_s3_library

# 2. Install dependencies
pip install -r requirements.txt

# 3. Deploy infrastructure
python scripts/setup.py --admin-user your-username

# 4. Set API key (from setup output)
export UNIVERSAL_S3_API_KEY=your-api-key-here

# 5. Add your first service
python scripts/add_service.py myapp "myapp-*" --permissions read-write
```

## Detailed Setup Process

### 1. Infrastructure Deployment

The setup script automatically deploys:
- CloudFormation stack with Lambda functions and API Gateway
- API key for authentication
- IAM roles for service access

```bash
python scripts/setup.py --admin-user admin
```

**Output includes**:
- API Gateway URL
- API Key for authentication
- Next steps for service configuration

### 2. API Key Configuration

Set the API key as an environment variable:

```bash
# Linux/macOS
export UNIVERSAL_S3_API_KEY=your-api-key-here

# Windows
set UNIVERSAL_S3_API_KEY=your-api-key-here

# PowerShell
$env:UNIVERSAL_S3_API_KEY="your-api-key-here"
```

**Alternative**: Store in application configuration or deployment config file.

### 3. Service Management

Add services for different applications:

```bash
# Analytics service (read-only)
python scripts/add_service.py analytics "company-analytics-*,*-analytics-*" --permissions read-only

# Application service (read-write)
python scripts/add_service.py webapp "webapp-prod-*" --permissions read-write

# Admin service (full access)
python scripts/add_service.py admin "*" --permissions admin
```

## Infrastructure Components

### CloudFormation Resources

- **Lambda Function**: `universal-credential-service`
- **API Gateway**: REST API with API key authentication
- **IAM Roles**: Lambda execution role and service-specific roles
- **API Key**: For client authentication

### Service Roles

Each service gets its own IAM role with least-privilege access:

```
service-role/analytics-s3-access-role    # Read-only analytics buckets
service-role/webapp-s3-access-role       # Read-write webapp buckets  
service-role/admin-s3-access-role        # Full S3 access
```

## Configuration Options

### Setup Script Options

```bash
python scripts/setup.py [OPTIONS]

Options:
  --admin-user TEXT    Username for universal service access (default: admin)
  --force             Force redeploy if already exists
  --help              Show help message
```

### Service Permissions

- `read-only`: GetObject, ListBucket
- `read-write`: GetObject, PutObject, DeleteObject, ListBucket (default)
- `admin`: Full S3 access (s3:*)

## Verification

Test your deployment:

```python
from universal_s3_library import UniversalS3Client

# Test with your service
client = UniversalS3Client("test-bucket", "your-service")
success = client.write_json({"test": "data"}, "test.json")
print(f"Test successful: {success}")
```

## Troubleshooting

### Common Issues

**API Key Not Found**:
```bash
# Check environment variable
echo $UNIVERSAL_S3_API_KEY

# Or get from CloudFormation
aws cloudformation describe-stacks --stack-name universal-s3-library \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiKey`].OutputValue' --output text
```

**Service Not Found**:
- Verify service was added via `add_service.py`
- Check Lambda function logs in CloudWatch

**Access Denied**:
- Verify bucket name matches service patterns
- Check IAM role permissions

### Debug Commands

```bash
# Check CloudFormation stack
aws cloudformation describe-stacks --stack-name universal-s3-library

# Test Lambda function
aws lambda invoke --function-name universal-credential-service \
  --payload '{"queryStringParameters":{"service":"test"}}' response.json

# View logs
aws logs filter-log-events --log-group-name "/aws/lambda/universal-credential-service"
```

## Security Considerations

- **API Key Storage**: Treat as secret, store securely
- **Key Rotation**: Consider periodic API key rotation
- **Network Access**: API Gateway is public but requires valid API key
- **Audit Logging**: All requests logged to CloudWatch

## Cleanup

To remove the infrastructure:

```bash
aws cloudformation delete-stack --stack-name universal-s3-library
```

**Note**: This will delete all Lambda functions, API Gateway, and IAM roles created by the setup.