#!/usr/bin/env python3
"""
List Services Script
Shows all configured services in the S3Bridge
"""

import boto3
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.aws_config import AWSConfig

def get_service_config():
    """Load service configuration from Lambda environment variables"""
    try:
        lambda_client = boto3.client('lambda')
        response = lambda_client.get_function(FunctionName='s3bridge-credential-service')
        
        env_vars = response['Configuration'].get('Environment', {}).get('Variables', {})
        
        services = {}
        for key, value in env_vars.items():
            if key.startswith('SERVICE_'):
                service_name = key[8:].lower()
                try:
                    services[service_name] = json.loads(value)
                except json.JSONDecodeError:
                    continue
        
        # Add universal service
        account_id = env_vars.get('AWS_ACCOUNT_ID')
        if account_id:
            services['universal'] = {
                'role': f"arn:aws:iam::{account_id}:role/service-role/s3bridge-access-role",
                'buckets': ['*']
            }
        
        return services
    except Exception as e:
        print(f"Failed to load service configuration: {e}")
        return {}

def get_service_roles():
    """Get all service roles from IAM"""
    try:
        iam = boto3.client('iam')
        response = iam.list_roles(PathPrefix='/service-role/')
        
        service_roles = {}
        for role in response['Roles']:
            role_name = role['RoleName']
            if role_name.endswith('-s3-access-role'):
                service_name = role_name.replace('-s3-access-role', '')
                service_roles[service_name] = {
                    'arn': role['Arn'],
                    'created': role['CreateDate'].strftime('%Y-%m-%d %H:%M:%S'),
                    'description': role.get('Description', '')
                }
        
        return service_roles
    except Exception as e:
        print(f"Failed to load IAM roles: {e}")
        return {}

def list_services():
    """List all configured services"""
    
    config = AWSConfig()
    
    print("S3Bridge - Service Registry")
    print(f"Account: {config.account_id}")
    print(f"Region: {config.region}")
    print()
    
    # Get service configurations
    services = get_service_config()
    roles = get_service_roles()
    
    if not services and not roles:
        print("No services configured")
        return
    
    # Combine service info
    all_services = set(services.keys()) | set(roles.keys())
    
    print(f"Found {len(all_services)} services:")
    print()
    
    for service_name in sorted(all_services):
        service_config = services.get(service_name, {})
        role_info = roles.get(service_name, {})
        
        print(f"{service_name}")
        
        # Bucket patterns
        buckets = service_config.get('buckets', ['Unknown'])
        print(f"   Buckets: {', '.join(buckets)}")
        
        # Role information
        if role_info:
            print(f"   Role: {role_info['arn']}")
            print(f"   Created: {role_info['created']}")
        elif service_config.get('role'):
            print(f"   Role: {service_config['role']}")
        
        # Status
        has_config = service_name in services
        has_role = service_name in roles
        
        if has_config and has_role:
            status = "Active"
        elif has_config and not has_role:
            status = "Missing IAM role"
        elif not has_config and has_role:
            status = "Missing Lambda config"
        else:
            status = "Inactive"
        
        print(f"   Status: {status}")
        print()

def main():
    try:
        boto3.client('sts').get_caller_identity()
    except Exception as e:
        print(f"AWS credentials not configured: {e}")
        return 1
    
    list_services()
    return 0

if __name__ == "__main__":
    sys.exit(main())