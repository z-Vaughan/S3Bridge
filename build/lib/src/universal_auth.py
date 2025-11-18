"""
Universal Authentication Provider
Account-agnostic API key authentication and credential management
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path
import sys

# Add config to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.aws_config import AWSConfig

class S3BridgeAuthProvider:
    """S3Bridge authentication provider for AWS credentials via API key"""
    
    def __init__(self, service_name: str = "default"):
        """
        Initialize auth provider
        
        Args:
            service_name: Service identifier for credential API
        """
        self.service_name = service_name
        self._cached_credentials = None
        self._credentials_expiry = None
        self._config = AWSConfig()
        
    def get_credentials(self) -> Dict[str, Any]:
        """Get AWS credentials via API key authentication"""
        if self._cached_credentials and not self.credentials_expired():
            return self._cached_credentials
            
        return self._fetch_fresh_credentials()
    
    def credentials_expired(self) -> bool:
        """Check if cached credentials are expired"""
        if not self._credentials_expiry:
            return True
        return datetime.now(self._credentials_expiry.tzinfo) >= self._credentials_expiry
    
    def _fetch_fresh_credentials(self) -> Dict[str, Any]:
        """Fetch fresh credentials from API"""
        
        # Check if infrastructure is deployed
        if not self._config.is_deployed():
            raise Exception("S3Bridge not deployed. Run: python -m s3bridge.setup")
        
        # Get API Gateway URL
        api_url = self._config.get_api_gateway_url()
        if not api_url:
            raise Exception("API Gateway URL not found. Check deployment.")
        
        endpoint = f"{api_url}/credentials"
        
        # Get API key
        api_key = self._get_api_key()
        
        try:
            response = requests.get(
                endpoint,
                params={'service': self.service_name, 'duration': '3600'},
                headers={'X-API-Key': api_key},
                timeout=30
            )
            
            if response.status_code == 200:
                creds_data = response.json()
                
                # Cache credentials
                self._cached_credentials = {
                    'access_key': creds_data['AccessKeyId'],
                    'secret_key': creds_data['SecretAccessKey'],
                    'session_token': creds_data['SessionToken']
                }
                
                # Set expiry (10 minutes before actual expiry)
                expiry_time = datetime.fromisoformat(creds_data['Expiration'].replace('Z', '+00:00'))
                self._credentials_expiry = expiry_time - timedelta(minutes=10)
                
                return self._cached_credentials
            else:
                raise Exception(f"Credential service failed with status {response.status_code}: {response.text}")
                
        except Exception as e:
            raise Exception(f"S3Bridge credential service failed: {str(e)}")
    
    def _get_api_key(self) -> str:
        """Get API key from configuration or environment"""
        
        # Try environment variable first
        api_key = os.environ.get('S3BRIDGE_API_KEY')
        if api_key:
            return api_key
        
        # Try config file
        config = self._config.load_deployment_config()
        if config and 'api_key' in config:
            return config['api_key']
        
        # Try to get from CloudFormation outputs
        try:
            import boto3
            cf = boto3.client('cloudformation')
            outputs = cf.describe_stacks(StackName=self._config.stack_name)['Stacks'][0]['Outputs']
            api_key = next(o['OutputValue'] for o in outputs if o['OutputKey'] == 'ApiKey')
            
            # Save to config for future use
            if config:
                config['api_key'] = api_key
                self._config.save_deployment_config(
                    config['api_gateway_url'], 
                    config.get('admin_username', 'admin'),
                    api_key
                )
            
            return api_key
        except Exception:
            pass
        
        raise Exception("API key not found. Set S3BRIDGE_API_KEY environment variable or redeploy infrastructure.")
    
    def invalidate_credentials(self):
        """Force refresh of cached credentials"""
        self._cached_credentials = None
        self._credentials_expiry = None
    
    def reset_authentication(self):
        """Reset authentication state"""
        self.invalidate_credentials()