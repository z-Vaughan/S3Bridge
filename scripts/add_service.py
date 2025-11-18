#!/usr/bin/env python3
"""
Add Service Script
Creates IAM role and updates Lambda configuration for new service
"""

import boto3
import json
import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.aws_config import AWSConfig

def find_existing_api_gateway():
    """Find existing API Gateway that uses s3bridge-credential-service"""
    try:
        api_client = boto3.client('apigateway')
        lambda_client = boto3.client('lambda')
        
        # Get s3bridge-credential-service function ARN
        try:
            func_response = lambda_client.get_function(FunctionName='s3bridge-credential-service')
            target_function_arn = func_response['Configuration']['FunctionArn']
        except lambda_client.exceptions.ResourceNotFoundException:
            return None
        
        # List all APIs
        apis = api_client.get_rest_apis()
        
        for api in apis['items']:
            api_id = api['id']
            try:
                # Get resources for this API
                resources = api_client.get_resources(restApiId=api_id)
                
                for resource in resources['items']:
                    # Check if this resource has GET method
                    if 'GET' in resource.get('resourceMethods', {}):
                        try:
                            # Get integration for GET method
                            integration = api_client.get_integration(
                                restApiId=api_id,
                                resourceId=resource['id'],
                                httpMethod='GET'
                            )
                            
                            # Check if integration points to our Lambda function
                            integration_uri = integration.get('uri', '')
                            if 's3bridge-credential-service' in integration_uri:
                                return api_id
                                
                        except Exception:
                            continue
                            
            except Exception:
                continue
                
        return None
        
    except Exception as e:
        print(f"WARNING: Could not search for existing API Gateway: {e}")
        return None

def create_service_role(service_name, bucket_patterns, permissions, config):
    """Create IAM role for service"""
    
    iam = boto3.client('iam')
    role_name = f"{service_name}-s3-access-role"
    
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
    
    # Trust policy for Lambda role
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"AWS": config.lambda_role_arn},
            "Action": "sts:AssumeRole"
        }]
    }
    
    try:
        # Create role
        iam.create_role(
            RoleName=role_name,
            Path='/service-role/',
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description=f"S3Bridge service role for {service_name}"
        )
        
        # Attach policy
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName=f"{service_name}S3AccessPolicy",
            PolicyDocument=json.dumps(policy_doc)
        )
        
        print(f"Created IAM role: {role_name}")
        return config.service_role_arn(service_name)
        
    except iam.exceptions.EntityAlreadyExistsException:
        print(f"Role {role_name} already exists, updating policy...")
        
        # Update existing policy
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName=f"{service_name}S3AccessPolicy",
            PolicyDocument=json.dumps(policy_doc)
        )
        
        return config.service_role_arn(service_name)

def update_lambda_config_only(service_name, bucket_patterns, role_arn):
    """Update only Lambda function code without touching API Gateway"""
    
    lambda_client = boto3.client('lambda')
    
    # Read current Lambda function code
    lambda_dir = Path(__file__).parent.parent / "lambda_functions"
    lambda_file = lambda_dir / "universal_credential_service.py"
    
    if not lambda_file.exists():
        print(f"Lambda function file not found: {lambda_file}")
        return
    
    with open(lambda_file, 'r') as f:
        lambda_code = f.read()
    
    # Insert service into service_roles dictionary
    service_entry = f"    '{service_name}': {{\n        'role': '{role_arn}',\n        'buckets': {bucket_patterns}\n    }},"
    
    # Find and update service_roles dictionary
    if 'service_roles = {' in lambda_code:
        lines = lambda_code.split('\n')
        new_lines = []
        in_service_roles = False
        
        for line in lines:
            if 'service_roles = {' in line:
                in_service_roles = True
                new_lines.append(line)
            elif in_service_roles and line.strip() == '}':
                # Add new service before closing brace
                new_lines.append(service_entry)
                new_lines.append(line)
                in_service_roles = False
            else:
                new_lines.append(line)
        
        # Write updated code back to file
        updated_code = '\n'.join(new_lines)
        with open(lambda_file, 'w') as f:
            f.write(updated_code)
        
        # Deploy updated Lambda function
        import zipfile
        import io
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.write(lambda_file, "lambda_function.py")
        
        try:
            lambda_client.update_function_code(
                FunctionName='s3bridge-credential-service',
                ZipFile=zip_buffer.getvalue()
            )
            print(f"Updated Lambda function code for service: {service_name}")
        except Exception as e:
            print(f"Failed to update Lambda function: {e}")
    else:
        print(f"Could not find service_roles dictionary in Lambda code")

def add_service(service_name, bucket_patterns, permissions='read-write'):
    """Add new service to S3Bridge"""
    
    config = AWSConfig()
    
    # Check if infrastructure is deployed (either CloudFormation or existing API Gateway)
    existing_api = find_existing_api_gateway()
    if not config.is_deployed() and not existing_api:
        print("S3Bridge not deployed. Run setup first:")
        print("   python scripts/setup.py")
        return False
    
    print(f"Adding service: {service_name}")
    print(f"Bucket patterns: {bucket_patterns}")
    print(f"Permissions: {permissions}")
    
    try:
        # Create IAM role
        role_arn = create_service_role(service_name, bucket_patterns, permissions, config)
        
        # Check for existing API Gateway
        existing_api = find_existing_api_gateway()
        if existing_api:
            print(f"Found existing API Gateway: {existing_api}")
            print(f"Will update existing endpoint instead of creating new one")
            # Update Lambda function code only
            update_lambda_config_only(service_name, bucket_patterns, role_arn)
            
            # Deploy Lambda changes only
            print(f"Deploying Lambda changes only...")
            import subprocess
            result = subprocess.run([sys.executable, str(Path(__file__).parent / 'deploy_lambda_only.py')], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"Lambda deployment successful")
            else:
                print(f"Lambda deployment failed: {result.stderr}")
                return False
        else:
            print(f"No existing API Gateway found")
            print(f"Run setup script to deploy infrastructure first:")
            print(f"   python scripts/setup.py --admin-user {config.load_deployment_config().get('admin_username', 'admin') if config.load_deployment_config() else 'admin'}")
            return False
        
        print(f"Service '{service_name}' added successfully!")
        print(f"API Endpoint: https://{existing_api}.execute-api.us-east-1.amazonaws.com/prod/credentials")
        print(f"Usage example:")
        print(f"   from s3bridge import S3BridgeClient")
        print(f"   client = S3BridgeClient('your-bucket', '{service_name}')")
        
        return True
        
    except Exception as e:
        print(f"Failed to add service: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Add service to S3Bridge')
    parser.add_argument('service_name', help='Service name (e.g., analytics, webapp)')
    parser.add_argument('bucket_patterns', help='Comma-separated bucket patterns (e.g., "app-*,*-data")')
    parser.add_argument('--permissions', choices=['read-only', 'read-write', 'admin'], 
                       default='read-write', help='Access level')

    
    args = parser.parse_args()
    
    # Parse bucket patterns
    bucket_patterns = [p.strip() for p in args.bucket_patterns.split(',')]
    
    success = add_service(args.service_name, bucket_patterns, args.permissions)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())