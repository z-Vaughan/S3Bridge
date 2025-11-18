"""
Mock AWS Test Suite
Tests operations using mock AWS services for safe testing
"""

import os
import sys
import json
import unittest
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path

# Add src and scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

class MockAWSTestCase(unittest.TestCase):
    """Base class for mock AWS tests"""
    
    def setUp(self):
        """Set up mock AWS environment"""
        self.mock_account_id = '123456789012'
        self.mock_region = 'us-east-1'
        self.test_service = 'mock-test-service'
        self.test_bucket_patterns = ['mock-test-*']
        
        # Common mock responses
        self.mock_sts_response = {'Account': self.mock_account_id}
        self.mock_role_arn = f'arn:aws:iam::{self.mock_account_id}:role/service-role/{self.test_service}-s3-access-role'
        
    def create_mock_clients(self):
        """Create mock AWS clients"""
        mock_clients = {
            'sts': Mock(),
            'iam': Mock(),
            'lambda': Mock(),
            'cloudformation': Mock(),
            'cloudwatch': Mock(),
            'apigateway': Mock()
        }
        
        # Setup common responses
        mock_clients['sts'].get_caller_identity.return_value = self.mock_sts_response
        mock_clients['iam'].create_role.return_value = {'Role': {'Arn': self.mock_role_arn}}
        mock_clients['lambda'].get_function_configuration.return_value = {
            'Environment': {'Variables': {'AWS_ACCOUNT_ID': self.mock_account_id}}
        }
        
        return mock_clients

class TestMockAddService(MockAWSTestCase):
    """Test add_service with mock AWS"""
    
    @patch('boto3.client')
    def test_add_service_success(self, mock_boto3):
        """Test successful service addition"""
        mock_clients = self.create_mock_clients()
        mock_boto3.side_effect = lambda service: mock_clients[service]
        
        import add_service
        from config.aws_config import AWSConfig
        
        config = AWSConfig()
        
        # Test IAM role creation
        role_arn = add_service.create_service_role(self.test_service, self.test_bucket_patterns, 'read-write', config)
        
        self.assertEqual(role_arn, self.mock_role_arn)
        mock_clients['iam'].create_role.assert_called_once()
        mock_clients['iam'].put_role_policy.assert_called_once()
    
    @patch('boto3.client')
    def test_add_service_existing_role(self, mock_boto3):
        """Test adding service when role already exists"""
        mock_clients = self.create_mock_clients()
        
        # Mock role already exists
        from botocore.exceptions import ClientError
        mock_clients['iam'].create_role.side_effect = ClientError(
            {'Error': {'Code': 'EntityAlreadyExists'}}, 'CreateRole'
        )
        
        mock_boto3.side_effect = lambda service: mock_clients[service]
        
        import add_service
        from config.aws_config import AWSConfig
        
        config = AWSConfig()
        role_arn = add_service.create_service_role(self.test_service, self.test_bucket_patterns, 'read-write', config)
        
        # Should still return role ARN and update policy
        self.assertEqual(role_arn, self.mock_role_arn)
        mock_clients['iam'].put_role_policy.assert_called_once()

class TestMockListServices(MockAWSTestCase):
    """Test list_services with mock AWS"""
    
    @patch('boto3.client')
    def test_list_services_with_data(self, mock_boto3):
        """Test listing services with existing data"""
        mock_clients = self.create_mock_clients()
        
        # Mock Lambda function with services
        mock_clients['lambda'].get_function.return_value = {
            'Configuration': {
                'Environment': {
                    'Variables': {
                        'SERVICE_TEST1': json.dumps({
                            'role': 'arn:aws:iam::123456789012:role/service-role/test1-s3-access-role',
                            'buckets': ['test1-*']
                        }),
                        'SERVICE_TEST2': json.dumps({
                            'role': 'arn:aws:iam::123456789012:role/service-role/test2-s3-access-role',
                            'buckets': ['test2-*', 'shared-*']
                        }),
                        'AWS_ACCOUNT_ID': self.mock_account_id
                    }
                }
            }
        }
        
        # Mock IAM roles
        mock_clients['iam'].list_roles.return_value = {
            'Roles': [
                {
                    'RoleName': 'test1-s3-access-role',
                    'Arn': 'arn:aws:iam::123456789012:role/service-role/test1-s3-access-role',
                    'CreateDate': '2024-01-01T00:00:00Z',
                    'Description': 'Test service 1'
                },
                {
                    'RoleName': 'test2-s3-access-role',
                    'Arn': 'arn:aws:iam::123456789012:role/service-role/test2-s3-access-role',
                    'CreateDate': '2024-01-02T00:00:00Z',
                    'Description': 'Test service 2'
                }
            ]
        }
        
        mock_boto3.side_effect = lambda service: mock_clients[service]
        
        import list_services
        
        services = list_services.get_service_config()
        roles = list_services.get_service_roles()
        
        # Verify services loaded
        self.assertIn('test1', services)
        self.assertIn('test2', services)
        self.assertEqual(services['test1']['buckets'], ['test1-*'])
        self.assertEqual(services['test2']['buckets'], ['test2-*', 'shared-*'])
        
        # Verify roles loaded
        self.assertIn('test1', roles)
        self.assertIn('test2', roles)

class TestMockRemoveService(MockAWSTestCase):
    """Test remove_service with mock AWS"""
    
    @patch('boto3.client')
    def test_remove_service_complete(self, mock_boto3):
        """Test complete service removal"""
        mock_clients = self.create_mock_clients()
        
        # Mock existing service in Lambda
        mock_clients['lambda'].get_function_configuration.return_value = {
            'Environment': {
                'Variables': {
                    f'SERVICE_{self.test_service.upper()}': json.dumps({
                        'role': self.mock_role_arn,
                        'buckets': self.test_bucket_patterns
                    }),
                    'OTHER_VAR': 'keep-this'
                }
            }
        }
        
        # Mock IAM role with policies
        mock_clients['iam'].list_role_policies.return_value = {
            'PolicyNames': ['TestServiceS3AccessPolicy']
        }
        
        mock_boto3.side_effect = lambda service: mock_clients[service]
        
        import remove_service
        
        # Test IAM role removal
        iam_result = remove_service.remove_iam_role(self.test_service)
        self.assertTrue(iam_result)
        
        mock_clients['iam'].delete_role_policy.assert_called_once()
        mock_clients['iam'].delete_role.assert_called_once()
        
        # Test Lambda config update
        lambda_result = remove_service.update_lambda_config(self.test_service)
        self.assertTrue(lambda_result)
        
        # Verify Lambda update called with service removed
        mock_clients['lambda'].update_function_configuration.assert_called_once()
        call_args = mock_clients['lambda'].update_function_configuration.call_args
        updated_env = call_args[1]['Environment']['Variables']
        
        self.assertNotIn(f'SERVICE_{self.test_service.upper()}', updated_env)
        self.assertIn('OTHER_VAR', updated_env)

class TestMockEditService(MockAWSTestCase):
    """Test edit_service with mock AWS"""
    
    @patch('boto3.client')
    def test_edit_service_bucket_patterns(self, mock_boto3):
        """Test editing service bucket patterns"""
        mock_clients = self.create_mock_clients()
        
        # Mock existing service
        existing_config = {
            'role': self.mock_role_arn,
            'buckets': ['old-pattern-*']
        }
        
        mock_clients['lambda'].get_function_configuration.return_value = {
            'Environment': {
                'Variables': {
                    f'SERVICE_{self.test_service.upper()}': json.dumps(existing_config)
                }
            }
        }
        
        mock_boto3.side_effect = lambda service: mock_clients[service]
        
        import edit_service
        
        # Test getting current config
        current_config = edit_service.get_current_service_config(self.test_service)
        self.assertEqual(current_config['buckets'], ['old-pattern-*'])
        
        # Test updating IAM policy
        new_patterns = ['new-pattern-*', 'additional-*']
        iam_result = edit_service.update_iam_role_policy(self.test_service, new_patterns, 'read-write')
        self.assertTrue(iam_result)
        
        mock_clients['iam'].put_role_policy.assert_called_once()
        
        # Test updating Lambda config
        lambda_result = edit_service.update_lambda_config(self.test_service, new_patterns, self.mock_role_arn)
        self.assertTrue(lambda_result)
        
        mock_clients['lambda'].update_function_configuration.assert_called_once()

class TestMockServiceStatus(MockAWSTestCase):
    """Test service_status with mock AWS"""
    
    @patch('boto3.client')
    def test_infrastructure_status_healthy(self, mock_boto3):
        """Test infrastructure status when healthy"""
        mock_clients = self.create_mock_clients()
        
        # Mock healthy infrastructure
        mock_clients['cloudformation'].describe_stacks.return_value = {
            'Stacks': [{
                'Outputs': [
                    {'OutputKey': 'ApiGatewayUrl', 'OutputValue': 'https://test.execute-api.us-east-1.amazonaws.com/prod'},
                    {'OutputKey': 'ApiKey', 'OutputValue': 'test-api-key-123'}
                ]
            }]
        }
        
        mock_clients['lambda'].get_function.return_value = {'Configuration': {}}
        
        mock_boto3.side_effect = lambda service: mock_clients[service]
        
        import service_status
        
        status = service_status.check_infrastructure_status()
        
        self.assertTrue(status['cloudformation'])
        self.assertTrue(status['lambda_function'])
        self.assertTrue(status['api_gateway'])
        self.assertTrue(status['api_key'])
    
    @patch('boto3.client')
    def test_lambda_metrics(self, mock_boto3):
        """Test Lambda metrics collection"""
        mock_clients = self.create_mock_clients()
        
        # Mock CloudWatch metrics
        mock_clients['cloudwatch'].get_metric_statistics.side_effect = [
            # Invocations
            {'Datapoints': [{'Sum': 150}, {'Sum': 200}]},
            # Errors  
            {'Datapoints': [{'Sum': 5}, {'Sum': 10}]}
        ]
        
        mock_boto3.side_effect = lambda service: mock_clients[service]
        
        import service_status
        
        metrics = service_status.get_lambda_metrics()
        
        self.assertEqual(metrics['invocations_24h'], 350)
        self.assertEqual(metrics['errors_24h'], 15)
        self.assertAlmostEqual(metrics['success_rate'], 95.7, places=1)

class TestMockBackupRestore(MockAWSTestCase):
    """Test backup_restore with mock AWS"""
    
    @patch('boto3.client')
    def test_backup_creation(self, mock_boto3):
        """Test backup creation"""
        mock_clients = self.create_mock_clients()
        
        # Mock Lambda configuration
        mock_clients['lambda'].get_function_configuration.return_value = {
            'Environment': {
                'Variables': {
                    'SERVICE_TEST': json.dumps({
                        'role': 'test-role-arn',
                        'buckets': ['test-*']
                    }),
                    'AWS_ACCOUNT_ID': self.mock_account_id
                }
            }
        }
        
        # Mock IAM roles
        mock_clients['iam'].list_roles.return_value = {
            'Roles': [{
                'RoleName': 'test-s3-access-role',
                'Arn': 'test-role-arn',
                'CreateDate': '2024-01-01T00:00:00Z',
                'AssumeRolePolicyDocument': {'Version': '2012-10-17'},
                'Description': 'Test role'
            }]
        }
        
        mock_clients['iam'].list_role_policies.return_value = {'PolicyNames': ['TestPolicy']}
        mock_clients['iam'].get_role_policy.return_value = {
            'PolicyDocument': {'Version': '2012-10-17', 'Statement': []}
        }
        
        mock_boto3.side_effect = lambda service: mock_clients[service]
        
        import backup_restore
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            backup_file = f.name
        
        try:
            result = backup_restore.backup_services(backup_file)
            self.assertTrue(result)
            
            # Verify backup file content
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            
            self.assertIn('services', backup_data)
            self.assertIn('iam_roles', backup_data)
            self.assertIn('test', backup_data['services'])
            self.assertEqual(backup_data['account_id'], self.mock_account_id)
            
        finally:
            if os.path.exists(backup_file):
                os.unlink(backup_file)

class TestMockServiceTesting(MockAWSTestCase):
    """Test service testing with mocks"""
    
    @patch('src.universal_auth.UniversalAuthProvider')
    def test_credential_testing(self, mock_auth_provider):
        """Test credential access testing"""
        # Mock successful credentials
        mock_auth_instance = Mock()
        mock_auth_instance.get_credentials.return_value = {
            'access_key': 'AKIA123456789',
            'secret_key': 'secret123',
            'session_token': 'token123'
        }
        mock_auth_provider.return_value = mock_auth_instance
        
        import test_service
        
        result = test_service.test_service_credentials(self.test_service)
        self.assertTrue(result)
        
        mock_auth_provider.assert_called_once_with(self.test_service)
        mock_auth_instance.get_credentials.assert_called_once()
    
    @patch('src.universal_s3_client.UniversalS3Client')
    def test_s3_operations_testing(self, mock_s3_client):
        """Test S3 operations testing"""
        # Mock successful S3 operations
        mock_s3_instance = Mock()
        mock_s3_instance.write_json.return_value = True
        mock_s3_instance.read_json.return_value = {
            'service': self.test_service,
            'test_timestamp': 'us-east-1',
            'test': True
        }
        mock_s3_instance.list_objects.return_value = ['test/service_test.json']
        mock_s3_instance.delete_object.return_value = True
        
        mock_s3_client.return_value = mock_s3_instance
        
        import test_service
        
        result = test_service.test_s3_operations(self.test_service, 'test-bucket')
        self.assertTrue(result)
        
        # Verify all operations were called
        mock_s3_instance.write_json.assert_called_once()
        mock_s3_instance.read_json.assert_called_once()
        mock_s3_instance.list_objects.assert_called_once()
        mock_s3_instance.delete_object.assert_called_once()


def run_mock_tests():
    """Run all mock AWS tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add mock test classes
    suite.addTests(loader.loadTestsFromTestCase(TestMockAddService))
    suite.addTests(loader.loadTestsFromTestCase(TestMockListServices))
    suite.addTests(loader.loadTestsFromTestCase(TestMockRemoveService))
    suite.addTests(loader.loadTestsFromTestCase(TestMockEditService))
    suite.addTests(loader.loadTestsFromTestCase(TestMockServiceStatus))
    suite.addTests(loader.loadTestsFromTestCase(TestMockBackupRestore))
    suite.addTests(loader.loadTestsFromTestCase(TestMockServiceTesting))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("Running Universal S3 Library Mock AWS Tests...")
    success = run_mock_tests()
    
    if success:
        print("\nAll mock tests passed!")
        sys.exit(0)
    else:
        print("\nSome mock tests failed!")
        sys.exit(1)