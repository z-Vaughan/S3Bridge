#!/usr/bin/env python3
"""
Edit Service Script
Modifies existing service configuration
"""

import boto3
import json
import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.aws_config import AWSConfig

def edit_service(service_name, bucket_patterns=None, permissions=None):
    """Edit existing service configuration"""
    
    config = AWSConfig()
    
    if not config.is_deployed():
        print("S3Bridge not deployed. Run setup first.")
        return False
    
    try:
        lambda_client = boto3.client('lambda')
        iam = boto3.client('iam')
        
        # Get current environment variables
        response = lambda_client.get_function_configuration(FunctionName='s3bridge-credential-service')
        env_vars = response.get('Environment', {}).get('Variables', {})
        
        service_env_key = f'SERVICE_{service_name.upper()}'
        
        if service_env_key not in env_vars:
            print(f"Service '{service_name}' not found")
            return False
        
        # Get current configuration
        current_config = json.loads(env_vars[service_env_key])
        print(f"Current configuration for '{service_name}':")
        print(f"  Buckets: {', '.join(current_config['buckets'])}")
        print(f"  Role: {current_config['role']}")
        
        # Update bucket patterns if provided
        if bucket_patterns:
            current_config['buckets'] = bucket_patterns
            print(f"Updated buckets: {', '.join(bucket_patterns)}")
        
        # Update IAM policy if permissions changed
        if permissions:
            s3_actions = {
                'read-only': ['s3:GetObject', 's3:ListBucket'],
                'read-write': ['s3:GetObject', 's3:PutObject', 's3:DeleteObject', 's3:ListBucket'],
                'admin': ['s3:*']
            }
            
            # Create S3 resources from bucket patterns
            s3_resources = []
            for pattern in current_config['buckets']:
                s3_resources.extend([
                    f"arn:aws:s3:::{pattern}",
                    f"arn:aws:s3:::{pattern}/*"
                ])
            
            # Update IAM policy
            policy_doc = {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Action": s3_actions[permissions],
                    "Resource": s3_resources
                }]
            }
            
            role_name = f"{service_name}-s3-access-role"
            iam.put_role_policy(
                RoleName=role_name,
                PolicyName=f"{service_name}S3AccessPolicy",
                PolicyDocument=json.dumps(policy_doc)
            )
            print(f"Updated IAM policy with {permissions} permissions")
        
        # Update Lambda environment
        env_vars[service_env_key] = json.dumps(current_config)
        lambda_client.update_function_configuration(
            FunctionName='s3bridge-credential-service',
            Environment={'Variables': env_vars}
        )
        
        print(f"Service '{service_name}' updated successfully")
        return True
        
    except Exception as e:
        print(f"Failed to edit service: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Edit service in S3Bridge')
    parser.add_argument('service_name', help='Service name to edit')
    parser.add_argument('--bucket-patterns', help='Comma-separated bucket patterns')
    parser.add_argument('--permissions', choices=['read-only', 'read-write', 'admin'], 
                       help='Access level')
    
    args = parser.parse_args()
    
    if not args.bucket_patterns and not args.permissions:
        print("Must specify --bucket-patterns or --permissions to edit")
        return 1
    
    bucket_patterns = None
    if args.bucket_patterns:
        bucket_patterns = [p.strip() for p in args.bucket_patterns.split(',')]
    
    success = edit_service(args.service_name, bucket_patterns, args.permissions)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())