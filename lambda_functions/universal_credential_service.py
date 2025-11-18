import json
import boto3
import os
from datetime import datetime

def get_service_config():
    """Load service configuration from environment variables"""
    
    # Base configuration
    config = {}
    
    # Load services from environment variables
    for key, value in os.environ.items():
        if key.startswith('SERVICE_'):
            service_name = key[8:].lower()  # Remove 'SERVICE_' prefix
            try:
                config[service_name] = json.loads(value)
            except json.JSONDecodeError:
                continue
    
    # Add universal service
    config['universal'] = {
        'role': f"arn:aws:iam::{os.environ['AWS_ACCOUNT_ID']}:role/service-role/s3bridge-access-role",
        'buckets': ['*']
    }
    
    return config

def lambda_handler(event, context):
    """
    S3Bridge credential service - returns temporary AWS credentials for registered services
    """
    
    try:
        # Extract parameters
        params = event.get('queryStringParameters') or {}
        service_name = params.get('service')
        duration = int(params.get('duration', '3600'))
        
        if not service_name:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'service parameter required'})
            }
        
        # Load service configuration
        service_roles = get_service_config()
        service_config = service_roles.get(service_name)
        
        if not service_config:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Unknown service: {service_name}'})
            }
        
        role_arn = service_config['role']
        
        # Assume role
        sts_client = boto3.client('sts')
        response = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName=f"{service_name}-session-{int(datetime.now().timestamp())}",
            DurationSeconds=min(duration, 3600)
        )
        
        credentials = response['Credentials']
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'AccessKeyId': credentials['AccessKeyId'],
                'SecretAccessKey': credentials['SecretAccessKey'],
                'SessionToken': credentials['SessionToken'],
                'Expiration': credentials['Expiration'].isoformat()
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }