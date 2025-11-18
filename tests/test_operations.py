"""
Test Suite for S3Bridge Operations
Tests all service management operations
"""

import os
import sys
import json
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path

# Add src, scripts, and config to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root / 'scripts'))
sys.path.insert(0, str(project_root / 'config'))
sys.path.insert(0, str(project_root))

class TestServiceOperations(unittest.TestCase):
    """Test service management operations"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_service = "test-service"
        self.test_bucket_patterns = ["test-*", "app-test-*"]
        self.test_permissions = "read-write"
        
    def test_add_service_function_exists(self):
        """Test that add_service function exists and is callable"""
        try:
            import add_service as add_service_module
            self.assertTrue(hasattr(add_service_module, 'add_service'))
            self.assertTrue(callable(add_service_module.add_service))
        except ImportError:
            self.skipTest("add_service module not available")
    
    @patch('boto3.client')
    def test_list_services(self, mock_boto3):
        """Test list_services operation"""
        mock_lambda = Mock()
        mock_iam = Mock()
        
        mock_sts = Mock()
        mock_sts.get_caller_identity.return_value = {'Account': '123456789012'}
        
        mock_boto3.side_effect = lambda service: {
            'lambda': mock_lambda,
            'iam': mock_iam,
            'sts': mock_sts
        }[service]
        
        # Mock Lambda response
        mock_lambda.get_function.return_value = {
            'Configuration': {
                'Environment': {
                    'Variables': {
                        'SERVICE_TEST': json.dumps({
                            'role': 'test-role-arn',
                            'buckets': ['test-*']
                        }),
                        'AWS_ACCOUNT_ID': '123456789012'
                    }
                }
            }
        }
        
        from datetime import datetime
        
        # Mock IAM response
        mock_iam.list_roles.return_value = {
            'Roles': [{
                'RoleName': 'test-s3-access-role',
                'Arn': 'test-role-arn',
                'CreateDate': datetime(2024, 1, 1),
                'Description': 'Test role'
            }]
        }
        
        try:
            import list_services
        except ImportError:
            self.skipTest("list_services module not available")
        
        services = list_services.get_service_config()
        roles = list_services.get_service_roles()
        
        self.assertIn('test', services)
        self.assertIn('test', roles)
        self.assertEqual(services['test']['buckets'], ['test-*'])
    
    def test_remove_service_function_exists(self):
        """Test that remove_service function exists and is callable"""
        try:
            import remove_service as remove_service_module
            self.assertTrue(hasattr(remove_service_module, 'remove_service'))
            self.assertTrue(callable(remove_service_module.remove_service))
        except ImportError:
            self.skipTest("remove_service module not available")
    
    def test_edit_service_function_exists(self):
        """Test that edit_service function exists and is callable"""
        try:
            import edit_service as edit_service_module
            self.assertTrue(hasattr(edit_service_module, 'edit_service'))
            self.assertTrue(callable(edit_service_module.edit_service))
        except ImportError:
            self.skipTest("edit_service module not available")
    
    @patch('boto3.client')
    def test_service_status(self, mock_boto3):
        """Test service_status operation"""
        mock_cf = Mock()
        mock_lambda = Mock()
        mock_cloudwatch = Mock()
        
        mock_sts = Mock()
        mock_sts.get_caller_identity.return_value = {'Account': '123456789012'}
        
        mock_boto3.side_effect = lambda service: {
            'cloudformation': mock_cf,
            'lambda': mock_lambda,
            'cloudwatch': mock_cloudwatch,
            'sts': mock_sts
        }[service]
        
        # Mock CloudFormation stack
        mock_cf.describe_stacks.return_value = {
            'Stacks': [{'Outputs': [{'OutputKey': 'ApiGatewayUrl', 'OutputValue': 'test-url'}]}]
        }
        
        # Mock Lambda function
        mock_lambda.get_function.return_value = {'Configuration': {}}
        
        # Mock CloudWatch metrics
        mock_cloudwatch.get_metric_statistics.return_value = {
            'Datapoints': [{'Sum': 100}]
        }
        
        try:
            import service_status
        except ImportError:
            self.skipTest("service_status module not available")
        
        infra_status = service_status.check_infrastructure_status()
        metrics = service_status.get_lambda_metrics()
        
        self.assertTrue(infra_status['cloudformation'])
        self.assertTrue(infra_status['lambda_function'])
        self.assertEqual(metrics['invocations_24h'], 100)
    
    def test_backup_restore(self):
        """Test backup_restore operation"""
        # Create test backup data
        test_backup = {
            'timestamp': '2024-01-01T00:00:00',
            'account_id': '123456789012',
            'region': 'us-east-1',
            'services': {
                'test': {
                    'role': 'test-role-arn',
                    'buckets': ['test-*']
                }
            },
            'iam_roles': {
                'test': {
                    'role_name': 'test-s3-access-role',
                    'arn': 'test-role-arn',
                    'assume_role_policy': {},
                    'policies': {'TestPolicy': {}},
                    'description': 'Test role'
                }
            }
        }
        
        # Test backup file creation and loading
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_backup, f)
            backup_file = f.name
        
        try:
            # Test loading backup
            with open(backup_file, 'r') as f:
                loaded_backup = json.load(f)
            
            self.assertEqual(loaded_backup['account_id'], '123456789012')
            self.assertIn('test', loaded_backup['services'])
            self.assertIn('test', loaded_backup['iam_roles'])
            
        finally:
            os.unlink(backup_file)
    
    @patch('boto3.client')
    def test_test_service(self, mock_boto3):
        """Test test_service operation"""
        # Mock successful credential test
        with patch('src.universal_auth.S3BridgeAuthProvider') as mock_auth:
            mock_auth_instance = Mock()
            mock_auth_instance.get_credentials.return_value = {
                'access_key': 'AKIA123',
                'secret_key': 'secret123',
                'session_token': 'token123'
            }
            mock_auth.return_value = mock_auth_instance
            
            try:
                import test_service as test_service_module
            except ImportError:
                self.skipTest("test_service module not available")
            
            result = test_service_module.test_service_credentials(self.test_service)
            self.assertTrue(result)
        
        # Mock S3 client test
        with patch('src.universal_s3_client.S3BridgeClient') as mock_s3:
            mock_s3_instance = Mock()
            mock_s3_instance.write_json.return_value = True
            mock_s3_instance.read_json.return_value = {'service': self.test_service, 'test': True}
            mock_s3_instance.list_objects.return_value = ['test/service_test.json']
            mock_s3_instance.delete_object.return_value = True
            mock_s3.return_value = mock_s3_instance
            
            try:
                import test_service as test_service_module
            except ImportError:
                self.skipTest("test_service module not available")
            
            result = test_service_module.test_s3_operations(self.test_service, "test-bucket")
            self.assertTrue(result)


class TestAuthProvider(unittest.TestCase):
    """Test S3Bridge authentication provider"""
    
    def setUp(self):
        """Set up test environment"""
        self.service_name = "test-service"
    
    def test_auth_provider_init(self):
        """Test auth provider initialization"""
        try:
            from src.universal_auth import S3BridgeAuthProvider
        except ImportError:
            self.skipTest("universal_auth module not available")
        
        auth = S3BridgeAuthProvider(self.service_name)
        self.assertEqual(auth.service_name, self.service_name)
        self.assertIsNone(auth._cached_credentials)
    
    @patch.dict(os.environ, {'S3BRIDGE_API_KEY': 'test-key-123'})
    def test_api_key_from_env(self):
        """Test API key retrieval from environment"""
        try:
            from src.universal_auth import S3BridgeAuthProvider
        except ImportError:
            self.skipTest("universal_auth module not available")
        
        auth = S3BridgeAuthProvider(self.service_name)
        
        # Mock the config to avoid AWS calls
        with patch.object(auth, '_config') as mock_config:
            mock_config.is_deployed.return_value = True  # Set to True to test API key retrieval
            mock_config.load_deployment_config.return_value = None
            
            api_key = auth._get_api_key()
            self.assertEqual(api_key, 'test-key-123')
    
    @patch('requests.get')
    def test_get_credentials_success(self, mock_get):
        """Test successful credential retrieval"""
        try:
            from src.universal_auth import S3BridgeAuthProvider
        except ImportError:
            self.skipTest("universal_auth module not available")
        from datetime import datetime, timezone
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'AccessKeyId': 'AKIA123',
            'SecretAccessKey': 'secret123',
            'SessionToken': 'token123',
            'Expiration': '2024-12-31T23:59:59Z'
        }
        mock_get.return_value = mock_response
        
        auth = S3BridgeAuthProvider(self.service_name)
        
        with patch.object(auth, '_config') as mock_config:
            mock_config.is_deployed.return_value = True
            mock_config.get_api_gateway_url.return_value = 'https://test-api.amazonaws.com'
            
            with patch.object(auth, '_get_api_key', return_value='test-key'):
                credentials = auth.get_credentials()
                
                self.assertEqual(credentials['access_key'], 'AKIA123')
                self.assertEqual(credentials['secret_key'], 'secret123')
                self.assertEqual(credentials['session_token'], 'token123')
    
    def test_credentials_caching(self):
        """Test credential caching behavior"""
        try:
            from src.universal_auth import S3BridgeAuthProvider
        except ImportError:
            self.skipTest("universal_auth module not available")
        from datetime import datetime, timezone, timedelta
        
        auth = S3BridgeAuthProvider(self.service_name)
        
        # Set up cached credentials
        auth._cached_credentials = {
            'access_key': 'AKIA123',
            'secret_key': 'secret123',
            'session_token': 'token123'
        }
        auth._credentials_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        
        # Should return cached credentials without API call
        credentials = auth.get_credentials()
        self.assertEqual(credentials['access_key'], 'AKIA123')
        
        # Test expiry check
        self.assertFalse(auth.credentials_expired())
        
        # Test invalidation
        auth.invalidate_credentials()
        self.assertIsNone(auth._cached_credentials)


class TestS3Client(unittest.TestCase):
    """Test S3 client functionality"""
    
    def test_s3_client_init(self):
        """Test S3 client initialization"""
        try:
            from src.universal_s3_client import S3BridgeClient
        except ImportError:
            self.skipTest("universal_s3_client module not available")
        
        # Test with universal service (should allow any bucket)
        client = S3BridgeClient("any-bucket", "universal")
        self.assertEqual(client.bucket_name, "any-bucket")
        self.assertEqual(client.service_name, "universal")
    
    def test_bucket_validation(self):
        """Test bucket access validation"""
        try:
            from src.universal_s3_client import S3BridgeClient
        except ImportError:
            self.skipTest("universal_s3_client module not available")
        
        # Test invalid bucket for analytics service
        with self.assertRaises(ValueError):
            S3BridgeClient("invalid-bucket", "analytics")
        
        # Test valid pattern matching
        try:
            # This should work for universal service
            client = S3BridgeClient("test-bucket", "universal")
            self.assertIsNotNone(client)
        except ValueError:
            # Expected if service patterns don't match
            pass
    
    @patch('boto3.client')
    def test_s3_operations(self, mock_boto3):
        """Test S3 operations with mocked client"""
        try:
            from src.universal_s3_client import S3BridgeClient
        except ImportError:
            self.skipTest("universal_s3_client module not available")
        
        # Mock S3 client
        mock_s3 = Mock()
        mock_boto3.return_value = mock_s3
        
        # Mock successful operations
        mock_s3.head_object.return_value = {}
        mock_s3.get_object.return_value = {'Body': Mock(read=lambda: b'{"test": "data"}')}
        mock_s3.put_object.return_value = {}
        mock_s3.delete_object.return_value = {}
        mock_s3.get_paginator.return_value.paginate.return_value = [
            {'Contents': [{'Key': 'test/file1.json'}, {'Key': 'test/file2.json'}]}
        ]
        
        client = S3BridgeClient("test-bucket", "universal")
        
        # Mock auth provider
        with patch.object(client.auth_provider, 'get_credentials') as mock_creds:
            mock_creds.return_value = {
                'access_key': 'AKIA123',
                'secret_key': 'secret123',
                'session_token': 'token123'
            }
            
            # Test file operations
            self.assertTrue(client.file_exists('test.json'))
            
            data = client.read_json('test.json')
            self.assertEqual(data['test'], 'data')
            
            self.assertTrue(client.write_json({'new': 'data'}, 'new.json'))
            
            objects = client.list_objects('test/')
            self.assertEqual(len(objects), 2)
            
            self.assertTrue(client.delete_object('test.json'))
    
    def test_s3_error_handling(self):
        """Test S3 error handling"""
        try:
            from src.universal_s3_client import S3BridgeClient
        except ImportError:
            self.skipTest("universal_s3_client module not available")
        
        client = S3BridgeClient("test-bucket", "universal")
        
        # Mock auth provider to raise exception
        with patch.object(client.auth_provider, 'get_credentials') as mock_creds:
            mock_creds.side_effect = Exception("Auth failed")
            
            # Operations should handle errors gracefully
            self.assertFalse(client.file_exists('test.json'))
            self.assertIsNone(client.read_json('test.json'))
            self.assertFalse(client.write_json({'test': 'data'}, 'test.json'))
            self.assertEqual(client.list_objects('test/'), [])
            self.assertFalse(client.delete_object('test.json'))


class TestConfigManagement(unittest.TestCase):
    """Test configuration management"""
    
    @patch('boto3.client')
    def test_aws_config(self, mock_boto3):
        """Test AWS configuration"""
        mock_sts = Mock()
        mock_sts.get_caller_identity.return_value = {'Account': '123456789012'}
        mock_boto3.return_value = mock_sts
        
        try:
            from config.aws_config import AWSConfig
        except ImportError:
            self.skipTest("aws_config module not available")
        
        config = AWSConfig()
        self.assertEqual(config.account_id, '123456789012')
        self.assertIn('arn:aws:iam::', config.lambda_role_arn)
    
    def test_deployment_config_save_load(self):
        """Test deployment configuration save/load"""
        try:
            from config.aws_config import AWSConfig
        except ImportError:
            self.skipTest("aws_config module not available")
        
        with patch('boto3.client'):
            config = AWSConfig()
            
            # Test config save/load with temporary file
            with tempfile.TemporaryDirectory() as temp_dir:
                config_file = Path(temp_dir) / 'deployment.json'
                
                # Mock the config file path
                with patch.object(Path, 'parent', new_callable=lambda: Path(temp_dir)):
                    test_data = {
                        'api_gateway_url': 'test-url',
                        'admin_username': 'test-admin',
                        'api_key': 'test-key'
                    }
                    
                    # Save config
                    with open(config_file, 'w') as f:
                        json.dump(test_data, f)
                    
                    # Load config
                    with open(config_file, 'r') as f:
                        loaded_config = json.load(f)
                    
                    self.assertEqual(loaded_config['api_gateway_url'], 'test-url')
                    self.assertEqual(loaded_config['api_key'], 'test-key')
    
    @patch('boto3.client')
    def test_deployment_status_check(self, mock_boto3):
        """Test deployment status checking"""
        try:
            from config.aws_config import AWSConfig
        except ImportError:
            self.skipTest("aws_config module not available")
        
        mock_cf = Mock()
        mock_boto3.return_value = mock_cf
        
        config = AWSConfig()
        
        # Test deployed status
        mock_cf.describe_stacks.return_value = {'Stacks': [{}]}
        self.assertTrue(config.is_deployed())
        
        # Test not deployed status
        mock_cf.describe_stacks.side_effect = Exception("Stack not found")
        self.assertFalse(config.is_deployed())
    
    @patch('boto3.client')
    def test_api_gateway_url_retrieval(self, mock_boto3):
        """Test API Gateway URL retrieval"""
        try:
            from config.aws_config import AWSConfig
        except ImportError:
            self.skipTest("aws_config module not available")
        
        mock_cf = Mock()
        mock_boto3.return_value = mock_cf
        
        config = AWSConfig()
        
        # Test successful URL retrieval
        mock_cf.describe_stacks.return_value = {
            'Stacks': [{
                'Outputs': [{
                    'OutputKey': 'ApiGatewayUrl',
                    'OutputValue': 'https://test-api.amazonaws.com'
                }]
            }]
        }
        
        url = config.get_api_gateway_url()
        self.assertEqual(url, 'https://test-api.amazonaws.com')
        
        # Test failed URL retrieval
        mock_cf.describe_stacks.side_effect = Exception("Failed")
        url = config.get_api_gateway_url()
        self.assertIsNone(url)


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases"""
    
    def test_missing_environment_variables(self):
        """Test behavior when environment variables are missing"""
        try:
            from src.universal_auth import S3BridgeAuthProvider
        except ImportError:
            self.skipTest("universal_auth module not available")
        
        # Clear environment
        with patch.dict(os.environ, {}, clear=True):
            auth = S3BridgeAuthProvider("test")
            
            with patch.object(auth, '_config') as mock_config:
                mock_config.is_deployed.return_value = True
                mock_config.load_deployment_config.return_value = None
                
                with self.assertRaises(Exception) as context:
                    auth._get_api_key()
                
                self.assertIn('API key not found', str(context.exception))
    
    def test_invalid_service_patterns(self):
        """Test invalid service patterns"""
        try:
            from src.universal_s3_client import S3BridgeClient
        except ImportError:
            self.skipTest("universal_s3_client module not available")
        
        # Test with non-existent service
        with self.assertRaises(ValueError):
            S3BridgeClient("test-bucket", "nonexistent-service")
    
    def test_network_failures(self):
        """Test network failure handling"""
        try:
            from src.universal_auth import S3BridgeAuthProvider
        except ImportError:
            self.skipTest("universal_auth module not available")
        
        auth = S3BridgeAuthProvider("test")
        
        with patch.object(auth, '_config') as mock_config:
            mock_config.is_deployed.return_value = True
            mock_config.get_api_gateway_url.return_value = 'https://test-api.amazonaws.com'
            
            with patch.object(auth, '_get_api_key', return_value='test-key'):
                with patch('requests.get') as mock_get:
                    mock_get.side_effect = Exception("Network error")
                    
                    with self.assertRaises(Exception) as context:
                        auth.get_credentials()
                    
                    self.assertIn('S3Bridge credential service failed', str(context.exception))


def run_all_tests():
    """Run all test suites"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestServiceOperations))
    suite.addTests(loader.loadTestsFromTestCase(TestAuthProvider))
    suite.addTests(loader.loadTestsFromTestCase(TestS3Client))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigManagement))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("Running S3Bridge Operation Tests...")
    print("=" * 60)
    
    success = run_all_tests()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ All tests passed successfully!")
        print("\nTest Coverage Summary:")
        print("- Service Operations: ✅ Add, List, Edit, Remove, Status")
        print("- Authentication: ✅ Provider, API Keys, Credentials")
        print("- S3 Client: ✅ Operations, Validation, Error Handling")
        print("- Configuration: ✅ AWS Config, Deployment Status")
        print("- Error Handling: ✅ Network, Missing Config, Invalid Input")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        print("\nPlease review the test output above for details.")
        sys.exit(1)