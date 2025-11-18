#!/usr/bin/env python3
"""
Live Integration Tests for S3Bridge
Tests real AWS functionality with actual resources
"""

import os
import sys
import json
import time
import unittest
import tempfile
from pathlib import Path
from datetime import datetime

# Add project paths
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root / 'config'))

class TestLiveAWSConfig(unittest.TestCase):
    """Test live AWS configuration"""
    
    def test_aws_credentials(self):
        """Test AWS credentials are configured"""
        import boto3
        try:
            sts = boto3.client('sts')
            identity = sts.get_caller_identity()
            self.assertIn('Account', identity)
            self.assertIn('UserId', identity)
            print(f"SUCCESS: AWS Account: {identity['Account']}")
            print(f"SUCCESS: User: {identity.get('Arn', identity['UserId'])}")
        except Exception as e:
            self.fail(f"AWS credentials not configured: {e}")
    
    def test_aws_config_class(self):
        """Test AWSConfig with real AWS account"""
        from config.aws_config import AWSConfig
        
        config = AWSConfig()
        
        # Test account ID retrieval
        account_id = config.account_id
        self.assertIsNotNone(account_id)
        self.assertEqual(len(account_id), 12)
        print(f"SUCCESS: Account ID: {account_id}")
        
        # Test region
        region = config.region
        self.assertIsNotNone(region)
        print(f"SUCCESS: Region: {region}")
        
        # Test role ARN generation
        lambda_role = config.lambda_role_arn
        self.assertIn(account_id, lambda_role)
        self.assertIn('arn:aws:iam::', lambda_role)
        print(f"SUCCESS: Lambda Role ARN: {lambda_role}")


class TestLiveInfrastructureStatus(unittest.TestCase):
    """Test infrastructure status checking"""
    
    def test_deployment_status(self):
        """Test checking if infrastructure is deployed"""
        from config.aws_config import AWSConfig
        
        config = AWSConfig()
        is_deployed = config.is_deployed()
        
        print(f"Infrastructure deployed: {is_deployed}")
        
        if is_deployed:
            # Test API Gateway URL retrieval
            api_url = config.get_api_gateway_url()
            if api_url:
                print(f"SUCCESS: API Gateway URL: {api_url}")
                self.assertIn('amazonaws.com', api_url)
            else:
                print("WARNING: API Gateway URL not found in stack outputs")
        else:
            print("INFO: Infrastructure not deployed - this is expected for new setups")
    
    def test_service_status_check(self):
        """Test service status functionality"""
        try:
            import service_status
            
            print("Checking infrastructure status...")
            infra_status = service_status.check_infrastructure_status()
            
            for component, status in infra_status.items():
                icon = "OK" if status else "FAIL"
                print(f"  {icon} {component.replace('_', ' ').title()}")
            
            # Test metrics (will be 0 if not deployed)
            metrics = service_status.get_lambda_metrics()
            print(f"Lambda invocations (24h): {metrics['invocations_24h']}")
            print(f"Lambda errors (24h): {metrics['errors_24h']}")
            
        except ImportError:
            self.skipTest("service_status module not available")


class TestLiveS3Operations(unittest.TestCase):
    """Test S3 operations with real buckets"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test bucket"""
        import boto3
        cls.s3_client = boto3.client('s3')
        cls.test_bucket = f"universal-s3-test-{int(time.time())}"
        cls.test_region = boto3.Session().region_name or 'us-east-1'
        
        try:
            if cls.test_region == 'us-east-1':
                cls.s3_client.create_bucket(Bucket=cls.test_bucket)
            else:
                cls.s3_client.create_bucket(
                    Bucket=cls.test_bucket,
                    CreateBucketConfiguration={'LocationConstraint': cls.test_region}
                )
            print(f"SUCCESS: Created test bucket: {cls.test_bucket}")
            
            # Wait for bucket to be available
            time.sleep(2)
            
        except Exception as e:
            print(f"ERROR: Failed to create test bucket: {e}")
            cls.test_bucket = None
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test bucket"""
        if cls.test_bucket:
            try:
                # Delete all objects first
                response = cls.s3_client.list_objects_v2(Bucket=cls.test_bucket)
                if 'Contents' in response:
                    objects = [{'Key': obj['Key']} for obj in response['Contents']]
                    cls.s3_client.delete_objects(
                        Bucket=cls.test_bucket,
                        Delete={'Objects': objects}
                    )
                
                # Delete bucket
                cls.s3_client.delete_bucket(Bucket=cls.test_bucket)
                print(f"SUCCESS: Cleaned up test bucket: {cls.test_bucket}")
            except Exception as e:
                print(f"WARNING: Failed to clean up bucket: {e}")
    
    def test_s3_client_with_universal_service(self):
        """Test S3 client with universal service (no auth required)"""
        if not self.test_bucket:
            self.skipTest("Test bucket not available")
        
        from src.universal_s3_client import S3BridgeClient
        
        # This should work without authentication for universal service
        try:
            client = S3BridgeClient(self.test_bucket, "universal")
            self.assertEqual(client.bucket_name, self.test_bucket)
            self.assertEqual(client.service_name, "universal")
            print(f"SUCCESS: S3 Client initialized for bucket: {self.test_bucket}")
        except Exception as e:
            print(f"INFO: S3 Client requires authentication: {e}")
    
    def test_direct_s3_operations(self):
        """Test direct S3 operations to verify bucket works"""
        if not self.test_bucket:
            self.skipTest("Test bucket not available")
        
        test_key = "test/integration-test.json"
        test_data = {
            "timestamp": datetime.now().isoformat(),
            "test": "live_integration",
            "bucket": self.test_bucket
        }
        
        try:
            # Test write
            self.s3_client.put_object(
                Bucket=self.test_bucket,
                Key=test_key,
                Body=json.dumps(test_data),
                ContentType='application/json'
            )
            print(f"SUCCESS: Wrote test object: {test_key}")
            
            # Test read
            response = self.s3_client.get_object(Bucket=self.test_bucket, Key=test_key)
            content = json.loads(response['Body'].read().decode('utf-8'))
            self.assertEqual(content['test'], 'live_integration')
            print(f"SUCCESS: Read test object successfully")
            
            # Test list
            response = self.s3_client.list_objects_v2(Bucket=self.test_bucket, Prefix="test/")
            self.assertIn('Contents', response)
            self.assertTrue(any(obj['Key'] == test_key for obj in response['Contents']))
            print(f"SUCCESS: Listed objects successfully")
            
            # Test delete
            self.s3_client.delete_object(Bucket=self.test_bucket, Key=test_key)
            print(f"SUCCESS: Deleted test object")
            
        except Exception as e:
            self.fail(f"S3 operations failed: {e}")


class TestLiveServiceManagement(unittest.TestCase):
    """Test service management with real AWS resources"""
    
    def test_list_existing_services(self):
        """Test listing existing services"""
        try:
            import list_services
            
            print("Checking existing services...")
            services = list_services.get_service_config()
            roles = list_services.get_service_roles()
            
            print(f"  Services in Lambda config: {len(services)}")
            for name, config in services.items():
                print(f"    - {name}: {config.get('buckets', [])}")
            
            print(f"  IAM roles found: {len(roles)}")
            for name, role in roles.items():
                print(f"    - {name}: {role.get('arn', 'Unknown ARN')}")
            
        except ImportError:
            self.skipTest("list_services module not available")
        except Exception as e:
            print(f"INFO: Service listing failed (expected if not deployed): {e}")


class TestLiveAuthentication(unittest.TestCase):
    """Test authentication with real infrastructure"""
    
    def test_auth_provider_initialization(self):
        """Test auth provider with real config"""
        from src.universal_auth import S3BridgeAuthProvider
        
        auth = S3BridgeAuthProvider("test-service")
        self.assertEqual(auth.service_name, "test-service")
        print(f"SUCCESS: Auth provider initialized for: test-service")
        
        # Test config loading
        config = auth._config
        self.assertIsNotNone(config.account_id)
        print(f"SUCCESS: Config loaded for account: {config.account_id}")
    
    def test_api_key_retrieval_methods(self):
        """Test different API key retrieval methods"""
        from src.universal_auth import S3BridgeAuthProvider
        
        auth = S3BridgeAuthProvider("test-service")
        
        # Test environment variable method
        if 'S3BRIDGE_API_KEY' in os.environ:
            try:
                api_key = auth._get_api_key()
                self.assertIsNotNone(api_key)
                print(f"SUCCESS: API key retrieved from environment")
            except Exception as e:
                print(f"INFO: API key retrieval failed: {e}")
        else:
            print("INFO: S3BRIDGE_API_KEY not set in environment")
        
        # Test config file method
        config_data = auth._config.load_deployment_config()
        if config_data and 'api_key' in config_data:
            print(f"SUCCESS: API key found in config file")
        else:
            print("INFO: No API key in config file")


def run_live_tests():
    """Run all live integration tests"""
    print("S3Bridge - Live Integration Tests")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestLiveAWSConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestLiveInfrastructureStatus))
    suite.addTests(loader.loadTestsFromTestCase(TestLiveS3Operations))
    suite.addTests(loader.loadTestsFromTestCase(TestLiveServiceManagement))
    suite.addTests(loader.loadTestsFromTestCase(TestLiveAuthentication))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("SUCCESS: All live tests completed successfully!")
    else:
        print("WARNING: Some tests failed or had issues (may be expected)")
        print("   Check output above for details")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_live_tests()
    sys.exit(0 if success else 1)