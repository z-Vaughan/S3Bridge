#!/usr/bin/env python3
"""
Remove Service Script
Removes a service from the S3Bridge
"""

import boto3
import json
import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.aws_config import AWSConfig

def remove_iam_role(service_name):
    """Remove IAM role for service"""
    iam = boto3.client('iam')
    role_name = f"{service_name}-s3-access-role"
    
    try:
        # List and delete role policies
        policies = iam.list_role_policies(RoleName=role_name)
        for policy_name in policies['PolicyNames']:
            iam.delete_role_policy(RoleName=role_name, PolicyName=policy_name)
            print(f"Deleted policy: {policy_name}")
        
        # Delete role
        iam.delete_role(RoleName=role_name)
        print(f"Deleted IAM role: {role_name}")
        return True
        
    except iam.exceptions.NoSuchEntityException:
        print(f"IAM role {role_name} not found")
        return False
    except Exception as e:
        print(f"Failed to delete IAM role: {e}")
        return False

def update_lambda_config(service_name):
    """Remove service from Lambda configuration"""
    lambda_client = boto3.client('lambda')
    
    try:
        # Get current environment variables
        response = lambda_client.get_function_configuration(FunctionName='s3bridge-credential-service')
        env_vars = response.get('Environment', {}).get('Variables', {})
        
        # Remove service environment variable
        service_key = f"SERVICE_{service_name.upper()}"
        if service_key in env_vars:
            del env_vars[service_key]
            
            # Update Lambda function
            lambda_client.update_function_configuration(
                FunctionName='s3bridge-credential-service',
                Environment={'Variables': env_vars}
            )
            print(f"Removed service from Lambda configuration")
            return True
        else:
            print(f"Service {service_name} not found in Lambda configuration")
            return False
            
    except Exception as e:
        print(f"Failed to update Lambda configuration: {e}")
        return False

def remove_service(service_name, force=False):
    """Remove service from S3Bridge"""
    
    config = AWSConfig()
    
    if not config.is_deployed():
        print("S3Bridge not deployed")
        return False
    
    print(f"Removing service: {service_name}")
    
    # Confirm removal unless forced
    if not force:
        confirm = input(f"Are you sure you want to remove service '{service_name}'? (y/N): ")
        if confirm.lower() != 'y':
            print("Operation cancelled")
            return False
    
    success = True
    
    # Remove from Lambda configuration
    if not update_lambda_config(service_name):
        success = False
    
    # Remove IAM role
    if not remove_iam_role(service_name):
        success = False
    
    if success:
        print(f"Service '{service_name}' removed successfully!")
        print(f"Note: Existing credentials will remain valid until expiry")
    else:
        print(f"Service removal completed with warnings")
    
    return success

def main():
    parser = argparse.ArgumentParser(description='Remove service from S3Bridge')
    parser.add_argument('service_name', help='Service name to remove')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    # Check AWS credentials
    try:
        boto3.client('sts').get_caller_identity()
    except Exception as e:
        print(f"AWS credentials not configured: {e}")
        return 1
    
    success = remove_service(args.service_name, args.force)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())