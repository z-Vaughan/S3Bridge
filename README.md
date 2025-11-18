# Universal S3 Library

A modular, account-agnostic credential service for secure S3 access across multiple applications and AWS accounts.

## Quick Start

```bash
# Install
pip install universal-s3-library

# Setup infrastructure (one-time per AWS account)
python -m universal_s3_library.setup --admin-user myusername

# Set API key (from setup output)
export UNIVERSAL_S3_API_KEY=your-api-key-here

# Add services
python -m universal_s3_library.add_service analytics "company-analytics-*" --permissions read-only
python -m universal_s3_library.add_service app1 "app1-data-*" --permissions read-write
```

```python
from universal_s3_library import UniversalS3Client

# Use with any AWS account
s3_client = UniversalS3Client("your-bucket-name", "analytics")
data = {"config": "value"}
s3_client.write_json(data, "config/settings.json")
```

## Features

- **Account Agnostic**: Works with any AWS account
- **One-Command Setup**: CloudFormation deployment
- **Dynamic Service Onboarding**: Add services via script
- **API Key Authentication**: Simple and secure authentication
- **Multi-Tier Security**: Service-based access control

## Installation

### Prerequisites
- AWS CLI configured with admin permissions
- Python 3.9+

### Setup
```bash
# 1. Clone or download the library
git clone <repository-url> universal_s3_library
cd universal_s3_library

# 2. Install dependencies
pip install -r requirements.txt

# 3. Deploy infrastructure to your AWS account
python scripts/setup.py --admin-user your-username

# 4. Set the API key from setup output
export UNIVERSAL_S3_API_KEY=your-api-key-here

# 5. Add your first service
python scripts/add_service.py myapp "myapp-*" --permissions read-write
```

**Smart Setup**: The setup script automatically:
- Detects existing API Gateway endpoints
- Reuses existing infrastructure when possible
- Only creates new resources when necessary

## Service Management

### Unified Service Manager
```bash
# List all services
python scripts/service_manager.py list

# Add new service
python scripts/service_manager.py add myapp "myapp-*" --permissions read-write

# Edit existing service
python scripts/service_manager.py edit myapp --bucket-patterns "myapp-*,shared-*"

# Remove service
python scripts/service_manager.py remove myapp --force

# Show system status
python scripts/service_manager.py status

# Backup configurations
python scripts/service_manager.py backup --file my_backup.json

# Restore configurations
python scripts/service_manager.py restore my_backup.json --dry-run
```

### Individual Scripts
```bash
# Add service
python scripts/add_service.py analytics "company-analytics-*" --permissions read-only

# List services
python scripts/list_services.py

# Edit service
python scripts/edit_service.py webapp --bucket-patterns "webapp-*,shared-*"

# Remove service
python scripts/remove_service.py oldservice --force

# Test service
python scripts/test_service.py myapp "myapp-test-bucket"

# System status
python scripts/service_status.py
```

**Smart Management**: The service management tools automatically:
- Detect existing infrastructure and preserve it
- Validate service configurations before applying changes
- Provide comprehensive testing and monitoring capabilities
- Support backup and restore of all service configurations

### Valid Permissions
- `read-only`: GetObject, ListBucket
- `read-write`: GetObject, PutObject, DeleteObject, ListBucket (default)
- `admin`: Full S3 access (s3:*)

## Usage Examples

```python
from universal_s3_library import UniversalS3Client

# Analytics service (read-only)
analytics = UniversalS3Client("company-analytics-data", "analytics")
reports = analytics.list_objects("reports/")

# Application service (read-write)
app = UniversalS3Client("webapp-prod-uploads", "webapp")
app.write_json({"user": "data"}, "users/user123.json")

# Admin service (full access)
admin = UniversalS3Client("any-bucket", "admin")
admin.upload_file("backup.zip", "backups/daily.zip")
```

## Architecture

- **Lambda Functions**: Credential service with API key authentication
- **API Gateway**: Secure credential endpoint with API key authentication
- **IAM Roles**: Service-specific least-privilege roles
- **CloudFormation**: Infrastructure as code
- **Dynamic Configuration**: Account-aware service mapping

## Documentation

- [Setup Guide](docs/SETUP.md)
- [Service Management](docs/SERVICES.md)
- [API Reference](docs/API.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)