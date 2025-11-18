# Service Management Operations - S3Bridge

Complete guide for managing services with the expanded S3Bridge feature set.

## Available Operations

### Core Service Operations
- **Add Service**: Create new service with IAM role and permissions
- **List Services**: Show all configured services and their status
- **Edit Service**: Modify existing service bucket patterns or permissions
- **Remove Service**: Delete service and clean up IAM resources
- **Test Service**: Comprehensive testing of service functionality
- **Status Check**: System health and performance monitoring
- **Backup/Restore**: Configuration backup and disaster recovery

## Unified Service Manager

The `service_manager.py` script provides a single interface for all operations:

```bash
# Show all available commands
python scripts/service_manager.py --help

# List services
python scripts/service_manager.py list

# Add service
python scripts/service_manager.py add myapp "myapp-*" --permissions read-write

# Edit service
python scripts/service_manager.py edit myapp --bucket-patterns "myapp-*,shared-*"

# Remove service
python scripts/service_manager.py remove myapp --force

# System status
python scripts/service_manager.py status

# Backup
python scripts/service_manager.py backup --file backup_20241201.json

# Restore
python scripts/service_manager.py restore backup_20241201.json --dry-run
```

## Individual Operations

### 1. List Services (`list_services.py`)

Shows all configured services with detailed information:

```bash
python scripts/list_services.py
```

**Output includes**:
- Service names and bucket patterns
- IAM role ARNs and creation dates
- Service status (Active, Missing role, Missing config)
- Account and region information

### 2. Add Service (`add_service.py`)

Creates new services with IAM roles and Lambda configuration:

```bash
python scripts/add_service.py SERVICE_NAME BUCKET_PATTERNS [OPTIONS]

# Examples:
python scripts/add_service.py analytics "company-analytics-*" --permissions read-only
python scripts/add_service.py webapp "webapp-prod-*,webapp-staging-*" --permissions read-write
python scripts/add_service.py admin "*" --permissions admin
```

**Options**:
- `--permissions`: read-only, read-write, admin (default: read-write)

### 3. Edit Service (`edit_service.py`)

Modifies existing service configurations:

```bash
python scripts/edit_service.py SERVICE_NAME [OPTIONS]

# Examples:
python scripts/edit_service.py webapp --bucket-patterns "webapp-*,shared-data-*"
python scripts/edit_service.py analytics --permissions read-write
python scripts/edit_service.py myapp --bucket-patterns "myapp-*" --permissions admin
```

**Options**:
- `--bucket-patterns`: Update bucket access patterns
- `--permissions`: Change permission level

### 4. Remove Service (`remove_service.py`)

Removes services and cleans up AWS resources:

```bash
python scripts/remove_service.py SERVICE_NAME [OPTIONS]

# Examples:
python scripts/remove_service.py oldservice
python scripts/remove_service.py testservice --force  # Skip confirmation
```

**What gets removed**:
- IAM role and policies
- Lambda environment variables
- Service configuration

**Options**:
- `--force`: Skip confirmation prompt

### 5. Test Service (`test_service.py`)

Comprehensive testing of service functionality:

```bash
python scripts/test_service.py SERVICE_NAME BUCKET_NAME [OPTIONS]

# Examples:
python scripts/test_service.py webapp "webapp-test-bucket"
python scripts/test_service.py analytics "company-analytics-data" --credentials-only
```

**Test categories**:
- **Credential Access**: Can service obtain AWS credentials?
- **S3 Operations**: Write, read, list, delete operations
- **Bucket Validation**: Security boundary enforcement

**Options**:
- `--credentials-only`: Test only credential access
- `--s3-only`: Test only S3 operations
- `--validation-only`: Test only bucket validation

### 6. Service Status (`service_status.py`)

System health and performance monitoring:

```bash
python scripts/service_status.py
```

**Monitoring includes**:
- Infrastructure status (CloudFormation, Lambda, API Gateway)
- Performance metrics (24-hour invocations, errors, success rate)
- Service health (credential access testing)
- API Gateway accessibility

### 7. Backup and Restore (`backup_restore.py`)

Configuration backup and disaster recovery:

```bash
# Backup current configuration
python scripts/backup_restore.py backup --file services_backup.json

# Restore from backup (dry run first)
python scripts/backup_restore.py restore services_backup.json --dry-run

# Actual restore
python scripts/backup_restore.py restore services_backup.json
```

**Backup includes**:
- All service configurations
- IAM roles and policies
- Lambda environment variables
- Metadata (timestamp, account, region)

## Workflow Examples

### Setting Up New Environment

```bash
# 1. Deploy infrastructure
python scripts/setup.py --admin-user myusername

# 2. Add services
python scripts/service_manager.py add analytics "company-analytics-*" --permissions read-only
python scripts/service_manager.py add webapp "webapp-*" --permissions read-write
python scripts/service_manager.py add admin "*" --permissions admin

# 3. Test services
python scripts/test_service.py analytics "company-analytics-data"
python scripts/test_service.py webapp "webapp-test-bucket"

# 4. Check status
python scripts/service_manager.py status

# 5. Backup configuration
python scripts/service_manager.py backup --file production_backup.json
```

### Modifying Existing Service

```bash
# 1. Check current configuration
python scripts/service_manager.py list

# 2. Edit service
python scripts/service_manager.py edit webapp --bucket-patterns "webapp-*,shared-*,temp-*"

# 3. Test changes
python scripts/test_service.py webapp "shared-data-bucket"

# 4. Backup updated configuration
python scripts/service_manager.py backup
```

### Disaster Recovery

```bash
# 1. Restore infrastructure
python scripts/setup.py --admin-user myusername --force

# 2. Restore services from backup
python scripts/service_manager.py restore production_backup.json --dry-run
python scripts/service_manager.py restore production_backup.json

# 3. Verify restoration
python scripts/service_manager.py status
python scripts/service_manager.py list
```

### Service Cleanup

```bash
# 1. List all services
python scripts/service_manager.py list

# 2. Remove unused services
python scripts/service_manager.py remove oldservice --force
python scripts/service_manager.py remove testservice --force

# 3. Verify cleanup
python scripts/service_manager.py status
```

## Best Practices

### Service Lifecycle Management

1. **Always test before production**: Use `test_service.py` after any changes
2. **Regular backups**: Backup configurations before major changes
3. **Monitor system health**: Use `service_status.py` for regular health checks
4. **Gradual rollouts**: Test service changes in non-production first

### Security Considerations

1. **Least privilege**: Use most restrictive permissions that meet requirements
2. **Regular audits**: Review service configurations periodically
3. **Backup security**: Store backup files securely
4. **Access monitoring**: Monitor CloudWatch logs for unusual access patterns

### Operational Efficiency

1. **Use unified manager**: `service_manager.py` for consistent operations
2. **Automate testing**: Include `test_service.py` in CI/CD pipelines
3. **Document changes**: Keep track of service modifications
4. **Monitor performance**: Regular status checks for proactive maintenance

## Troubleshooting Operations

### Service Won't Start
```bash
# Check infrastructure
python scripts/service_status.py

# Test specific service
python scripts/test_service.py myservice "test-bucket" --credentials-only

# Check service configuration
python scripts/list_services.py
```

### Permission Issues
```bash
# Edit service permissions
python scripts/edit_service.py myservice --permissions read-write

# Test bucket access
python scripts/test_service.py myservice "target-bucket" --validation-only
```

### Configuration Corruption
```bash
# Restore from backup
python scripts/backup_restore.py restore last_good_backup.json --dry-run
python scripts/backup_restore.py restore last_good_backup.json
```

This expanded feature set provides comprehensive service lifecycle management for the S3Bridge, making it production-ready for enterprise environments.