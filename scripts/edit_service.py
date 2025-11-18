#!/usr/bin/env python3
"""
Edit Service Script
Modifies an existing service in the S3Bridge
"""

import boto3
import json
import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.aws_config import AWSConfig

def get_current_service_config(service_name):
    """Get current service configuration"""
    try:
        lambda_client = boto3.client('lambda')
        response = lambda_client.get_function_configuration(FunctionName='s3bridge-credential-service')
        env_vars = response.get('Environment', {}).get('Variables', {})
        
        service_key = f"SERVICE_{service_name.upper()}"
        if service_key in env_vars:
            return json.loads(env_vars[service_key])
        
        return None
    except Exception:
        return None

def update_iam_role_policy(service_name, bucket_patterns, permissions):
    """Update IAM role policy for service"""
    iam = boto3.client('iam')
    role_name = f"{service_name}-s3-access-role"
    policy_name = f"{service_name}S3AccessPolicy"
    
    # S3 permissions based on access level
    s3_actions = {
        'read-only': ['s3:GetObject', 's3:ListBucket'],
        'read-write': ['s3:GetObject', 's3:PutObject', 's3:DeleteObject', 's3:ListBucket'],
        'admin': ['s3:*']
    }
    
    # Create S3 resources from bucket patterns
    s3_resources = []
    for pattern in bucket_patterns:
        s3_resources.extend([
            f"arn:aws:s3:::{pattern}",
            f"arn:aws:s3:::{pattern}/*"
        ])
    
    # IAM policy document
    policy_doc = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": s3_actions[permissions],
            "Resource": s3_resources
        }]
    }
    
    try:
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_doc)
        )
        print(f"Updated IAM policy for {role_name}")
        return True
    except Exception as e:
        print(f"Failed to update IAM policy: {e}")
        return False

def update_lambda_config(service_name, bucket_patterns, role_arn):
    """Update service in Lambda configuration"""
    lambda_client = boto3.client('lambda')
    
    try:
        # Get current environment variables
        response = lambda_client.get_function_configuration(FunctionName='s3bridge-credential-service')
        env_vars = response.get('Environment', {}).get('Variables', {})
        
        # Update service configuration
        service_config = {
            'role': role_arn,
            'buckets': bucket_patterns
        }
        
        service_key = f"SERVICE_{service_name.upper()}"
        env_vars[service_key] = json.dumps(service_config)
        
        # Update Lambda function
        lambda_client.update_function_configuration(
            FunctionName='s3bridge-credential-service',
            Environment={'Variables': env_vars}
        )
        print(f"Updated Lambda configuration for {service_name}")
        return True
        
    except Exception as e:
        print(f"Failed to update Lambda configuration: {e}")
        return False

def edit_service(service_name, bucket_patterns=None, permissions=None):
    """Edit existing service configuration"""
    
    config = AWSConfig()
    
    if not config.is_deployed():
        print("S3Bridge not deployed")
        return False
    
    # Get current configuration
    current_config = get_current_service_config(service_name)
    if not current_config:
        print(f"Service '{service_name}' not found")
        print("Use add_service.py to create new services")
        return False
    
    print(f"Editing service: {service_name}")
    
    # Use current values if not specified
    if bucket_patterns is None:
        bucket_patterns = current_config.get('buckets', [])
    if permissions is None:
        # Determine current permissions from role policy
        permissions = 'read-write'  # Default assumption
    
    print(f"Bucket patterns: {bucket_patterns}")
    print(f"Permissions: {permissions}")
    
    role_arn = config.service_role_arn(service_name)
    
    success = True
    
    # Update IAM role policy
    if not update_iam_role_policy(service_name, bucket_patterns, permissions):
        success = False
    
    # Update Lambda configuration
    if not update_lambda_config(service_name, bucket_patterns, role_arn):
        success = False
    
    if success:
        print(f"Service '{service_name}' updated successfully!")
    else:
        print(f"Service update completed with warnings")
    
    return success

def main():
    parser = argparse.ArgumentParser(description='Edit existing service in S3Bridge')
    parser.add_argument('service_name', help='Service name to edit')
    parser.add_argument('--bucket-patterns', help='Comma-separated bucket patterns')
    parser.add_argument('--permissions', choices=['read-only', 'read-write', 'admin'], 
                       help='Access level')
    
    args = parser.parse_args()
    
    # Check AWS credentials
    try:
        boto3.client('sts').get_caller_identity()
    except Exception as e:
        print(f"AWS credentials not configured: {e}")
        return 1
    
    # Parse bucket patterns
    bucket_patterns = None
    if args.bucket_patterns:
        bucket_patterns = [p.strip() for p in args.bucket_patterns.split(',')]
    
    success = edit_service(args.service_name, bucket_patterns, args.permissions)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())