# Service Management - S3Bridge

Guide for adding and managing services in the S3Bridge.

## Overview

The S3Bridge uses a service-tier architecture where each service gets specific bucket access patterns and permissions. Services are managed through IAM roles and Lambda configuration.

## Adding New Services

### Quick Add Service

```bash
python scripts/add_service.py SERVICE_NAME BUCKET_PATTERNS [OPTIONS]

# Examples:
python scripts/add_service.py analytics "company-analytics-*" --permissions read-only
python scripts/add_service.py webapp "webapp-prod-*,webapp-staging-*" --permissions read-write
python scripts/add_service.py admin "*" --permissions admin
```

### PowerShell (Windows)

```powershell
.\add_service.ps1 -ServiceName analytics -BucketPatterns "company-analytics-*" -Permissions read-only
```

## Service Configuration

### Permission Levels

| Level | S3 Actions | Use Case |
|-------|------------|----------|
| `read-only` | GetObject, ListBucket | Analytics, reporting |
| `read-write` | GetObject, PutObject, DeleteObject, ListBucket | Applications, data processing |
| `admin` | s3:* | Administrative tasks |

### Bucket Patterns

Use glob-style patterns to define bucket access:

```bash
# Single pattern
"myapp-*"

# Multiple patterns (comma-separated)
"myapp-*,*-myapp-data,shared-*"

# Analytics buckets
"*-analytics-*,analytics-*"

# All buckets (admin only)
"*"
```

## Service Management Process

### 1. Create Service

```bash
python scripts/add_service.py myservice "myservice-*" --permissions read-write
```

This automatically:
- Creates IAM role: `myservice-s3-access-role`
- Updates Lambda function configuration
- Deploys changes to AWS

### 2. Use Service

```python
from s3bridge import S3BridgeClient

client = S3BridgeClient("myservice-bucket", "myservice")
client.write_json({"data": "value"}, "config.json")
```

### 3. Verify Service

```python
# Test service access
try:
    client = S3BridgeClient("myservice-bucket", "myservice")
    success = client.write_json({"test": True}, "test.json")
    print(f"Service working: {success}")
except ValueError as e:
    print(f"Service error: {e}")
```

## Built-in Services

### Analytics Service
- **Permissions**: Read-only
- **Buckets**: `*-analytics-*`, `analytics-*`
- **Use Case**: Data analysis, reporting

```python
analytics = S3BridgeClient("company-analytics-data", "analytics")
reports = analytics.list_objects("reports/")
```

### Universal Service  
- **Permissions**: Full admin (s3:*)
- **Buckets**: `*` (all buckets)
- **Use Case**: Administrative tasks

```python
admin = S3BridgeClient("any-bucket", "universal")
admin.upload_file("backup.zip", "backups/daily.zip")
```

## Service Architecture

### IAM Role Structure

Each service gets a dedicated IAM role:

```
Role Name: {service-name}-s3-access-role
Path: /service-role/
Trust Policy: Lambda execution role
Permissions: Service-specific S3 access
```

### Lambda Configuration

Services are registered in the credential service Lambda:

```python
# In universal_credential_service.py
service_config = {
    'role': 'arn:aws:iam::ACCOUNT:role/service-role/myservice-s3-access-role',
    'buckets': ['myservice-*']
}
```

## Advanced Configuration

### Custom Bucket Validation

Client-side validation ensures services only access authorized buckets:

```python
# In universal_s3_client.py
service_patterns = {
    'myservice': ['myservice-*', 'shared-data-*'],
    'analytics': ['*-analytics-*']
}
```

### Environment-Specific Services

```bash
# Development environment
python scripts/add_service.py myapp-dev "myapp-dev-*" --permissions read-write

# Production environment  
python scripts/add_service.py myapp-prod "myapp-prod-*" --permissions read-write

# Staging environment
python scripts/add_service.py myapp-staging "myapp-staging-*" --permissions read-write
```

## Service Lifecycle

### Update Service Permissions

To modify service permissions, re-run add_service:

```bash
# Update from read-only to read-write
python scripts/add_service.py analytics "company-analytics-*" --permissions read-write
```

### Remove Service

Currently manual process:

1. Delete IAM role:
```bash
aws iam delete-role-policy --role-name myservice-s3-access-role --policy-name MyserviceS3AccessPolicy
aws iam delete-role --role-name myservice-s3-access-role
```

2. Remove from Lambda configuration (manual edit)

### Service Monitoring

Monitor service usage through CloudWatch:

```bash
# View credential requests
aws logs filter-log-events --log-group-name "/aws/lambda/s3bridge-credential-service" \
  --filter-pattern "myservice"

# Check for errors
aws logs filter-log-events --log-group-name "/aws/lambda/s3bridge-credential-service" \
  --filter-pattern "ERROR"
```

## Best Practices

### Service Naming
- Use descriptive names: `analytics`, `data-pipeline`, `web-app`
- Include environment: `myapp-prod`, `myapp-dev`
- Avoid generic names: `app`, `service`, `client`

### Bucket Patterns
- Be specific: `myapp-*` not `*`
- Use consistent naming: `{service}-{env}-{purpose}`
- Consider read vs write needs

### Security
- Use least privilege permissions
- Separate dev/staging/prod services
- Regular access reviews

## Troubleshooting

### Service Not Found
```
Error: Unknown service: myservice
```
**Solution**: Verify service was added and Lambda deployed

### Access Denied
```
Error: Service 'myservice' not authorized for bucket 'other-bucket'
```
**Solution**: Check bucket name matches service patterns

### Role Not Found
```
Error: Role arn:aws:iam::ACCOUNT:role/service-role/myservice-s3-access-role not found
```
**Solution**: Re-run add_service script to create role

### Debug Commands

```bash
# List all service roles
aws iam list-roles --path-prefix /service-role/

# Check specific role
aws iam get-role --role-name myservice-s3-access-role

# Test service directly
python -c "
from s3bridge import S3BridgeClient
client = S3BridgeClient('test-bucket', 'myservice')
print('Service configured correctly')
"
```