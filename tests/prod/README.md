# Production Tests

Live integration tests that work with real AWS resources.

## ⚠️ Important Warning

These tests interact with your actual AWS account and may:
- Create temporary S3 buckets
- Check existing infrastructure
- Use AWS API calls that may incur minimal charges

## Prerequisites

1. **AWS CLI configured** with valid credentials
2. **Appropriate permissions** for S3, IAM, Lambda, CloudFormation
3. **Python dependencies** installed (`pip install -r requirements.txt`)

## Running Tests

### Check Prerequisites Only
```bash
python tests/prod/run_prod_tests.py --check-only
```

### Run All Tests
```bash
python tests/prod/run_prod_tests.py
```

### Run Specific Test Types
```bash
# Integration tests only
python tests/prod/run_prod_tests.py --integration-only

# Workflow tests only  
python tests/prod/run_prod_tests.py --workflow-only
```

### Skip S3 Bucket Creation
```bash
python tests/prod/run_prod_tests.py --skip-s3-tests
```

## Test Categories

### 1. Live Integration Tests (`test_live_integration.py`)
- **TestLiveAWSConfig**: Validates AWS credentials and configuration
- **TestLiveInfrastructureStatus**: Checks deployment status
- **TestLiveS3Operations**: Creates temporary S3 bucket for testing
- **TestLiveServiceManagement**: Tests service listing functionality
- **TestLiveAuthentication**: Tests authentication components

### 2. Workflow Tests (`test_deployment_workflow.py`)
- **TestDeploymentWorkflow**: Validates deployment scripts and templates
- **TestServiceManagementWorkflow**: Tests service management commands
- **TestConfigurationManagement**: Tests configuration handling
- **TestLambdaFunction**: Validates Lambda function code

## What Gets Tested

### ✅ Safe Operations (Read-Only)
- AWS credential validation
- Account ID and region detection
- Infrastructure status checking
- Service listing
- Configuration file handling
- Script existence and help commands

### ⚠️ Resource Creation (Temporary)
- S3 bucket creation/deletion for testing
- S3 object operations (put/get/delete)
- Configuration file updates

### ❌ Not Tested (Too Risky)
- Actual infrastructure deployment
- IAM role creation/deletion
- Lambda function deployment
- API Gateway modifications

## Expected Outcomes

### If Infrastructure Not Deployed
- Most tests will pass with informational messages
- Some operations will fail gracefully (expected)
- No actual resources will be created except test S3 bucket

### If Infrastructure Is Deployed
- All tests should pass
- Real service status will be displayed
- Authentication tests may work with actual API

## Cleanup

Tests automatically clean up after themselves:
- Temporary S3 buckets are deleted
- Test objects are removed
- No permanent changes to your AWS account

## Troubleshooting

### Common Issues

1. **AWS Credentials Not Found**
   ```bash
   aws configure list
   ```

2. **Permission Denied**
   - Ensure your AWS user has necessary permissions
   - Check IAM policies for S3, Lambda, CloudFormation access

3. **Region Issues**
   - Tests use your default AWS region
   - Some operations may fail in certain regions

4. **Timeout Errors**
   - Network connectivity issues
   - AWS service availability

### Debug Mode

Add verbose output by modifying test files or running individual test classes:

```bash
python -m unittest tests.prod.test_live_integration.TestLiveAWSConfig -v
```

## Safety Features

- **User confirmation** required before running tests
- **Automatic cleanup** of created resources
- **Graceful failure** handling for missing infrastructure
- **Read-only operations** where possible
- **Temporary resource naming** to avoid conflicts