# Testing Guide - S3Bridge

Comprehensive testing framework for the S3Bridge with multiple test suites covering all operations and scenarios.

## Test Structure

### Test Suites

1. **`test_operations.py`** - Core service operations testing
2. **`test_integration.py`** - End-to-end workflow testing
3. **`test_mock_aws.py`** - Mock AWS service testing
4. **`test_performance.py`** - Performance and scalability testing

### Test Runner

- **`run_tests.py`** - Unified test runner for all suites

## Running Tests

### All Tests
```bash
# Run complete test suite
python tests/run_tests.py

# Individual test suites
python tests/test_operations.py
python tests/test_integration.py
python tests/test_mock_aws.py
python tests/test_performance.py
```

### Specific Test Categories
```bash
# Unit tests only
python -m unittest tests.test_operations

# Integration tests only  
python -m unittest tests.test_integration

# Performance tests only
python -m unittest tests.test_performance
```

## Test Coverage

### Service Operations Tests (`test_operations.py`)

**TestServiceOperations**:
- `test_add_service()` - Service creation with IAM roles
- `test_list_services()` - Service listing and configuration retrieval
- `test_remove_service()` - Service deletion and cleanup
- `test_edit_service()` - Service modification
- `test_service_status()` - Infrastructure health monitoring
- `test_backup_restore()` - Configuration backup/restore
- `test_test_service()` - Service functionality testing

**TestAuthProvider**:
- `test_auth_provider_init()` - Authentication provider initialization
- `test_api_key_from_env()` - API key environment variable handling

**TestS3Client**:
- `test_s3_client_init()` - S3 client initialization
- `test_bucket_validation()` - Bucket access validation

**TestConfigManagement**:
- `test_aws_config()` - AWS configuration management
- `test_deployment_config_save_load()` - Configuration persistence

### Integration Tests (`test_integration.py`)

**TestServiceManagerIntegration**:
- `test_service_manager_commands()` - CLI command integration

**TestEndToEndWorkflow**:
- `test_complete_service_lifecycle()` - Full service lifecycle (add→list→edit→remove)

**TestErrorHandling**:
- `test_aws_credential_errors()` - AWS credential error handling
- `test_service_not_found_errors()` - Missing service error handling
- `test_invalid_bucket_patterns()` - Bucket validation error handling

**TestBackupRestoreIntegration**:
- `test_backup_restore_cycle()` - Complete backup and restore workflow

**TestPerformanceMonitoring**:
- `test_status_monitoring()` - System health monitoring integration

**TestServiceTesting**:
- `test_comprehensive_service_test()` - End-to-end service testing

### Mock AWS Tests (`test_mock_aws.py`)

**TestMockAddService**:
- `test_add_service_success()` - Successful service addition
- `test_add_service_existing_role()` - Handling existing IAM roles

**TestMockListServices**:
- `test_list_services_with_data()` - Service listing with mock data

**TestMockRemoveService**:
- `test_remove_service_complete()` - Complete service removal

**TestMockEditService**:
- `test_edit_service_bucket_patterns()` - Service configuration editing

**TestMockServiceStatus**:
- `test_infrastructure_status_healthy()` - Infrastructure health checks
- `test_lambda_metrics()` - Performance metrics collection

**TestMockBackupRestore**:
- `test_backup_creation()` - Configuration backup creation

**TestMockServiceTesting**:
- `test_credential_testing()` - Credential access testing
- `test_s3_operations_testing()` - S3 operations testing

### Performance Tests (`test_performance.py`)

**TestPerformance**:
- `test_credential_caching_performance()` - Credential caching efficiency
- `test_concurrent_s3_operations()` - Concurrent operation handling
- `test_memory_usage_stability()` - Memory usage under load
- `test_service_management_performance()` - Service operation speed
- `test_error_handling_performance()` - Error handling efficiency

**TestScalability**:
- `test_many_services_performance()` - Performance with many services

## Test Environment Setup

### Prerequisites
```bash
# Install test dependencies
pip install -r requirements.txt

# No AWS credentials needed for mock tests
# Real AWS credentials needed only for integration tests
```

### Environment Variables
```bash
# For testing API key functionality
export S3BRIDGE_API_KEY=test-key-123

# For integration tests (optional)
export AWS_PROFILE=test-profile
```

## Mock Testing Strategy

### AWS Service Mocking
- **boto3 clients**: Mocked using `unittest.mock.Mock`
- **AWS responses**: Realistic mock responses for all services
- **Error scenarios**: Mocked AWS exceptions and error conditions
- **Performance**: Simulated operation timing and concurrency

### Benefits
- **Safe testing**: No real AWS resources created/modified
- **Fast execution**: No network calls to AWS
- **Predictable results**: Controlled mock responses
- **Cost-free**: No AWS charges for testing

## Test Data and Fixtures

### Common Test Data
```python
# Service configuration
test_service = "test-service"
test_bucket_patterns = ["test-*", "app-test-*"]
test_permissions = "read-write"

# Mock AWS responses
mock_account_id = "123456789012"
mock_region = "us-east-1"
mock_role_arn = "arn:aws:iam::123456789012:role/service-role/test-service-s3-access-role"
```

### Temporary Files
- Backup files created in temporary directories
- Automatic cleanup after tests
- No persistent test artifacts

## Continuous Integration

### Test Automation
```bash
# CI/CD pipeline test command
python tests/run_tests.py

# Exit codes:
# 0 = All tests passed
# 1 = Some tests failed
```

### Test Reports
- Detailed test output with pass/fail status
- Performance metrics for scalability tests
- Error details for failed tests
- Summary statistics

## Debugging Tests

### Verbose Output
```bash
# Run with verbose output
python -m unittest tests.test_operations -v

# Debug specific test
python -m unittest tests.test_operations.TestServiceOperations.test_add_service -v
```

### Test Isolation
- Each test method is independent
- Mock objects reset between tests
- No shared state between test cases
- Temporary files cleaned up automatically

## Best Practices

### Writing New Tests
1. **Use descriptive test names**: `test_add_service_with_existing_role()`
2. **Mock external dependencies**: AWS services, file system, network
3. **Test error conditions**: Not just happy path scenarios
4. **Verify all interactions**: Assert all expected calls were made
5. **Clean up resources**: Use temporary files and proper teardown

### Test Organization
1. **Group related tests**: Use test classes for logical grouping
2. **Separate concerns**: Unit tests vs integration tests vs performance tests
3. **Mock appropriately**: Mock at the right level of abstraction
4. **Test realistic scenarios**: Use realistic test data and workflows

### Performance Testing
1. **Measure what matters**: Focus on user-facing performance
2. **Set reasonable thresholds**: Based on actual usage requirements
3. **Test under load**: Concurrent operations and many services
4. **Monitor resource usage**: Memory, CPU, network calls

This comprehensive testing framework ensures the S3Bridge is reliable, performant, and ready for production use across all supported operations and scenarios.