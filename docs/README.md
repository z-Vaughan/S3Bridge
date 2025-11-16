# Universal S3 Library Documentation

A modular, account-agnostic credential service for secure S3 access across multiple applications and AWS accounts using API key authentication.

## Features

- **Centralized Credential Service**: Single endpoint for temporary AWS credentials
- **Multi-Application Support**: Serves credentials to any valid requesting application
- **Minimal IAM Setup**: No per-application role configuration required
- **API Key Authentication**: Simple and secure authentication without external dependencies
- **Complete S3 Operations**: JSON, text, file upload/download operations
- **Production Ready**: Thread-safe with error handling and retry logic

## Quick Start

```python
from universal_s3_library import UniversalS3Client

# Set API key (from deployment)
import os
os.environ['UNIVERSAL_S3_API_KEY'] = 'your-api-key-here'

# Choose appropriate service tier for your use case
s3_client = UniversalS3Client(
    bucket_name="your-bucket-name",
    service_name="analytics"  # Options: analytics, universal, custom services
)

# Immediate S3 access with security validation
data = {"config": "value"}
s3_client.write_json(data, "config/settings.json")
config = s3_client.read_json("config/settings.json")
```

**Service Tiers**:
- `analytics`: Read-only access to analytics buckets
- `universal`: Full admin access
- Custom services: Configured via add_service script

**Prerequisites**: AWS credentials configured, API key from deployment - no additional setup needed.

## Installation

1. Clone the repository to your project
2. Install dependencies: `pip install -r requirements.txt`
3. Deploy infrastructure: `python scripts/setup.py --admin-user <username>`
4. Set API key: `export UNIVERSAL_S3_API_KEY=<key-from-setup>`

**No IAM roles, policies, or AWS configuration required for your application.**

## How It Works

The library provides **temporary AWS credentials** through a centralized service:

1. **Request**: Application requests credentials via API key authentication
2. **Validate**: Service validates API key and service permissions
3. **Issue**: Temporary credentials (1-hour duration) returned to application
4. **Access**: Application uses credentials for direct S3 operations
5. **Refresh**: Automatic credential renewal before expiration

**Deployed Infrastructure**:
- **Credential Service**: `universal-credential-service` Lambda
- **API Gateway**: With API key authentication
- **IAM Roles**: Service-specific roles with least privilege access

## API Reference

### UniversalS3Client

#### Core Methods
- `file_exists(key)` - Check if file exists
- `read_json(key)` - Read JSON file
- `write_json(data, key)` - Write JSON data
- `read_text(key)` - Read text file  
- `write_text(content, key)` - Write text content
- `upload_file(local_path, key)` - Upload file
- `download_file(key, local_path)` - Download file
- `list_objects(prefix)` - List objects with prefix
- `delete_object(key)` - Delete object

### UniversalAuthProvider

#### Methods
- `get_credentials()` - Get current AWS credentials
- `credentials_expired()` - Check if credentials need refresh
- `invalidate_credentials()` - Force credential refresh
- `reset_authentication()` - Reset auth state

## Multi-Application Integration

This library serves as the **central credential provider** for multiple applications:

```python
# Analytics Application (read-only analytics buckets)
analytics_client = UniversalS3Client("company-analytics-data", "analytics")

# General Applications (custom bucket patterns)
app_client = UniversalS3Client("app-data-bucket", "myapp")

# Admin Application (full access)
admin_client = UniversalS3Client("any-bucket", "universal")
```

**Security Tiers**:
- **analytics**: Read-only access to `*-analytics-*` buckets
- **universal**: Full admin access to all buckets (`*`)
- **Custom services**: Configured bucket patterns and permissions

**Benefits**:
- **Least Privilege**: Each service gets minimal required permissions
- **Multi-Layer Security**: API Gateway + Lambda + IAM + Client validation
- **Centralized Control**: All access managed through single service
- **Zero Trust**: Every request validated at multiple points

## Error Handling

The library handles common scenarios:
- **Expired Credentials**: Automatic refresh
- **Network Issues**: Retry logic
- **Authentication Failures**: Clear error messages
- **S3 Errors**: Graceful degradation

## Security Features

- **API Key Authentication**: Simple, secure authentication mechanism
- **Service-Based Access Control**: Different permission tiers per service type
- **Bucket Pattern Validation**: Client-side bucket access validation
- **Temporary Credentials**: 1-hour maximum duration with automatic refresh
- **Audit Trail**: All access attempts logged via CloudWatch

## Adding New Services

See [SERVICES.md](SERVICES.md) for complete guide on adding new service tiers to the Universal S3 Library.

## Production Features

- **Thread Safety**: Atomic credential refresh, no shared state
- **High Availability**: Single reliable endpoint with monitoring
- **Fail Secure**: Any validation failure denies access
- **Monitoring**: Built-in error handling and retry logic
- **Scalability**: Supports unlimited concurrent applications