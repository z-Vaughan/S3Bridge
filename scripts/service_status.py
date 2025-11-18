#!/usr/bin/env python3
"""
Service Status Script
Shows detailed status and health of Universal S3 Library services
"""

import boto3
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.aws_config import AWSConfig

def check_infrastructure_status():
    """Check overall infrastructure health"""
    config = AWSConfig()
    status = {
        'cloudformation': False,
        'lambda_function': False,
        'api_gateway': False,
        'api_key': False
    }
    
    try:
        # Check CloudFormation stack
        cf = boto3.client('cloudformation')
        cf.describe_stacks(StackName=config.stack_name)
        status['cloudformation'] = True
    except Exception:
        pass
    
    try:
        # Check Lambda function
        lambda_client = boto3.client('lambda')
        lambda_client.get_function(FunctionName='universal-credential-service')
        status['lambda_function'] = True
    except Exception:
        pass
    
    try:
        # Check API Gateway
        api_url = config.get_api_gateway_url()
        if api_url:
            status['api_gateway'] = True
    except Exception:
        pass
    
    try:
        # Check API key
        cf = boto3.client('cloudformation')
        outputs = cf.describe_stacks(StackName=config.stack_name)['Stacks'][0]['Outputs']
        api_key = next(o['OutputValue'] for o in outputs if o['OutputKey'] == 'ApiKey')
        if api_key:
            status['api_key'] = True
    except Exception:
        pass
    
    return status

def get_lambda_metrics():
    """Get Lambda function metrics"""
    try:
        cloudwatch = boto3.client('cloudwatch')
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)
        
        # Get invocation count
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Invocations',
            Dimensions=[{'Name': 'FunctionName', 'Value': 'universal-credential-service'}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Sum']
        )
        
        total_invocations = sum(point['Sum'] for point in response['Datapoints'])
        
        # Get error count
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Errors',
            Dimensions=[{'Name': 'FunctionName', 'Value': 'universal-credential-service'}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Sum']
        )
        
        total_errors = sum(point['Sum'] for point in response['Datapoints'])
        
        return {
            'invocations_24h': int(total_invocations),
            'errors_24h': int(total_errors),
            'success_rate': (total_invocations - total_errors) / total_invocations * 100 if total_invocations > 0 else 100
        }
    except Exception:
        return {'invocations_24h': 0, 'errors_24h': 0, 'success_rate': 0}

def test_service_access(service_name):
    """Test if service can get credentials"""
    try:
        from src.universal_auth import UniversalAuthProvider
        auth = UniversalAuthProvider(service_name)
        credentials = auth.get_credentials()
        return True
    except Exception as e:
        return str(e)

def show_service_status():
    """Show comprehensive service status"""
    
    config = AWSConfig()
    
    print("🔍 Universal S3 Library - System Status")
    print(f"📍 Account: {config.account_id}")
    print(f"📍 Region: {config.region}")
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Infrastructure status
    print("🏗️  Infrastructure Status:")
    infra_status = check_infrastructure_status()
    
    for component, status in infra_status.items():
        icon = "✅" if status else "❌"
        print(f"   {icon} {component.replace('_', ' ').title()}")
    
    overall_health = "✅ Healthy" if all(infra_status.values()) else "⚠️  Issues Detected"
    print(f"   📊 Overall: {overall_health}")
    print()
    
    # Lambda metrics
    print("📈 Performance Metrics (24h):")
    metrics = get_lambda_metrics()
    print(f"   🔢 Invocations: {metrics['invocations_24h']}")
    print(f"   ❌ Errors: {metrics['errors_24h']}")
    print(f"   ✅ Success Rate: {metrics['success_rate']:.1f}%")
    print()
    
    # Service status
    print("🔧 Service Status:")
    
    try:
        # Get services from Lambda config
        lambda_client = boto3.client('lambda')
        response = lambda_client.get_function_configuration(FunctionName='universal-credential-service')
        env_vars = response.get('Environment', {}).get('Variables', {})
        
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
                'role': f"arn:aws:iam::{account_id}:role/service-role/universal-s3-access-role",
                'buckets': ['*']
            }
        
        if not services:
            print("   📭 No services configured")
        else:
            for service_name, service_config in services.items():
                # Test service access
                access_test = test_service_access(service_name)
                access_icon = "✅" if access_test is True else "❌"
                
                print(f"   {access_icon} {service_name}")
                print(f"      📦 Buckets: {', '.join(service_config.get('buckets', ['Unknown']))}")
                
                if access_test is not True:
                    print(f"      ⚠️  Error: {access_test}")
    
    except Exception as e:
        print(f"   ❌ Failed to load service status: {e}")
    
    print()
    
    # API Gateway info
    try:
        api_url = config.get_api_gateway_url()
        if api_url:
            print("🌐 API Gateway:")
            print(f"   🔗 Endpoint: {api_url}")
            
            # Test API accessibility
            try:
                import requests
                response = requests.get(f"{api_url}/credentials?service=test", timeout=5)
                if response.status_code in [400, 403]:  # Expected for test service
                    print("   ✅ API Gateway responding")
                else:
                    print(f"   ⚠️  Unexpected response: {response.status_code}")
            except Exception:
                print("   ❌ API Gateway not accessible")
    except Exception:
        print("🌐 API Gateway: ❌ Not configured")

def main():
    try:
        boto3.client('sts').get_caller_identity()
    except Exception as e:
        print(f"❌ AWS credentials not configured: {e}")
        return 1
    
    show_service_status()
    return 0

if __name__ == "__main__":
    sys.exit(main())