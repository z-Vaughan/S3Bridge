"""
Integration Tests for S3Bridge
Tests operations against mock AWS services
"""

import os
import sys
import json
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add src and scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

class TestServiceManagerIntegration(unittest.TestCase):
    """Integration tests for service manager"""
    
    @patch('subprocess.run')
    def test_service_manager_commands(self, mock_run):
        """Test service manager CLI commands"""
        mock_run.return_value.returncode = 0
        
        import service_manager
        
        # Test list command
        result = service_manager.run_script('list_services', [])
        self.assertEqual(result, 0)
        
        # Test add command
        result = service_manager.run_script('add_service', ['test', 'test-*', '--permissions', 'read-write'])
        self.assertEqual(result, 0)
        
        mock_run.assert_called()

class TestEndToEndWorkflow(unittest.TestCase):
    """End-to-end workflow tests"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_service = "integration-test"
        self.test_patterns = ["integration-*"]
        
    @patch('boto3.client')
    def test_complete_service_lifecycle(self, mock_boto3):
        """Test complete service lifecycle: add -> list -> edit -> test -> remove"""
        
        # Mock AWS clients
        mock_iam = Mock()
        mock_lambda = Mock()
        mock_sts = Mock()
        mock_cf = Mock()
        
        mock_apigateway = Mock()
        mock_boto3.side_effect = lambda service: {
            'iam': mock_iam,
            'lambda': mock_lambda,
            'sts': mock_sts,
            'cloudformation': mock_cf,
            'apigateway': mock_apigateway
        }[service]
        
        # Setup mocks
        mock_sts.get_caller_identity.return_value = {'Account': '123456789012'}
        mock_iam.create_role.return_value = {'Role': {'Arn': 'test-arn'}}
        mock_lambda.get_function_configuration.return_value = {
            'Environment': {'Variables': {'AWS_ACCOUNT_ID': '123456789012'}}
        }
        mock_cf.describe_stacks.return_value = {
            'Stacks': [{'Outputs': [{'OutputKey': 'ApiGatewayUrl', 'OutputValue': 'test-url'}]}]
        }
        
        # 1. Add service
        import add_service as add_service_module
        add_result = add_service_module.add_service(self.test_service, self.test_patterns, 'read-write')
        self.assertTrue(add_result)
        
        # 2. List services (verify it exists)
        mock_lambda.get_function.return_value = {
            'Configuration': {
                'Environment': {
                    'Variables': {
                        f'SERVICE_{self.test_service.upper()}': json.dumps({
                            'role': 'test-arn',
                            'buckets': self.test_patterns
                        }),
                        'AWS_ACCOUNT_ID': '123456789012'
                    }
                }
            }
        }
        
        import list_services
        services = list_services.get_service_config()
        self.assertIn(self.test_service, services)
        
        # 3. Edit service
        import edit_service as edit_service_module
        new_patterns = ["integration-*", "new-pattern-*"]
        edit_result = edit_service_module.edit_service(self.test_service, new_patterns, 'read-only')
        self.assertTrue(edit_result)
        
        # 4. Remove service
        mock_iam.list_role_policies.return_value = {'PolicyNames': ['TestPolicy']}
        
        import remove_service as remove_service_module
        remove_result = remove_service_module.remove_service(self.test_service, force=True)
        self.assertTrue(remove_result)

class TestErrorHandling(unittest.TestCase):
    """Test error handling scenarios"""
    
    @patch('boto3.client')
    def test_aws_credential_errors(self, mock_boto3):
        """Test handling of AWS credential errors"""
        mock_boto3.side_effect = Exception("Credentials not configured")
        
        import add_service as add_service_module
        
        # Should handle AWS errors gracefully
        result = add_service_module.add_service("test", ["test-*"], "read-write")
        self.assertFalse(result)
    
    @patch('boto3.client')
    def test_service_not_found_errors(self, mock_boto3):
        """Test handling when service doesn't exist"""
        mock_lambda = Mock()
        mock_boto3.return_value = mock_lambda
        
        # Mock service not found
        mock_lambda.get_function_configuration.return_value = {
            'Environment': {'Variables': {}}
        }
        
        import edit_service
        
        config = edit_service.get_current_service_config("nonexistent-service")
        self.assertIsNone(config)
    
    def test_invalid_bucket_patterns(self):
        """Test validation of bucket patterns"""
        from src.universal_s3_client import S3BridgeClient
        
        # Test invalid service/bucket combination
        with self.assertRaises(ValueError):
            S3BridgeClient("unauthorized-bucket", "analytics")

class TestBackupRestoreIntegration(unittest.TestCase):
    """Integration tests for backup/restore functionality"""
    
    @patch('boto3.client')
    def test_backup_restore_cycle(self, mock_boto3):
        """Test complete backup and restore cycle"""
        mock_lambda = Mock()
        mock_iam = Mock()
        
        mock_sts = Mock()
        mock_sts.get_caller_identity.return_value = {'Account': '123456789012'}
        mock_boto3.side_effect = lambda service: {
            'lambda': mock_lambda,
            'iam': mock_iam,
            'sts': mock_sts
        }[service]
        
        # Mock existing services
        mock_lambda.get_function_configuration.return_value = {
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
        
        mock_iam.list_roles.return_value = {
            'Roles': [{
                'RoleName': 'test-s3-access-role',
                'Arn': 'test-role-arn',
                'CreateDate': '2024-01-01T00:00:00Z',
                'AssumeRolePolicyDocument': {},
                'Description': 'Test role'
            }]
        }
        
        mock_iam.list_role_policies.return_value = {'PolicyNames': ['TestPolicy']}
        mock_iam.get_role_policy.return_value = {
            'PolicyDocument': {'Version': '2012-10-17', 'Statement': []}
        }
        
        import backup_restore
        import tempfile
        
        # Test backup
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            backup_file = f.name
        
        try:
            backup_result = backup_restore.backup_services(backup_file)
            self.assertTrue(backup_result)
            
            # Verify backup file exists and has content
            self.assertTrue(os.path.exists(backup_file))
            
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            
            self.assertIn('services', backup_data)
            self.assertIn('iam_roles', backup_data)
            
            # Test restore (dry run)
            restore_result = backup_restore.restore_services(backup_file, dry_run=True)
            self.assertTrue(restore_result)
            
        finally:
            if os.path.exists(backup_file):
                os.unlink(backup_file)

class TestPerformanceMonitoring(unittest.TestCase):
    """Test performance monitoring functionality"""
    
    @patch('boto3.client')
    def test_status_monitoring(self, mock_boto3):
        """Test system status monitoring"""
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
        
        # Mock healthy infrastructure
        mock_cf.describe_stacks.return_value = {
            'Stacks': [{'Outputs': [
                {'OutputKey': 'ApiGatewayUrl', 'OutputValue': 'https://test.execute-api.us-east-1.amazonaws.com/prod'},
                {'OutputKey': 'ApiKey', 'OutputValue': 'test-api-key'}
            ]}]
        }
        
        mock_lambda.get_function.return_value = {'Configuration': {}}
        
        # Mock metrics
        mock_cloudwatch.get_metric_statistics.return_value = {
            'Datapoints': [
                {'Sum': 100},  # Invocations
                {'Sum': 5}     # Errors
            ]
        }
        
        import service_status
        
        # Test infrastructure status
        status = service_status.check_infrastructure_status()
        self.assertTrue(status['cloudformation'])
        self.assertTrue(status['lambda_function'])
        self.assertTrue(status['api_gateway'])
        self.assertTrue(status['api_key'])
        
        # Test metrics
        metrics = service_status.get_lambda_metrics()
        self.assertGreaterEqual(metrics['invocations_24h'], 0)
        self.assertGreaterEqual(metrics['success_rate'], 0)

class TestServiceTesting(unittest.TestCase):
    """Test service testing functionality"""
    
    @patch('src.universal_auth.S3BridgeAuthProvider')
    @patch('src.universal_s3_client.S3BridgeClient')
    def test_comprehensive_service_test(self, mock_s3_client, mock_auth_provider):
        """Test comprehensive service testing"""
        
        # Mock successful auth
        mock_auth_instance = Mock()
        mock_auth_instance.get_credentials.return_value = {
            'access_key': 'AKIA123',
            'secret_key': 'secret123',
            'session_token': 'token123'
        }
        mock_auth_provider.return_value = mock_auth_instance
        
        # Mock successful S3 operations
        mock_s3_instance = Mock()
        mock_s3_instance.write_json.return_value = True
        mock_s3_instance.read_json.return_value = {'service': 'test', 'test': True}
        mock_s3_instance.list_objects.return_value = ['test/service_test.json']
        mock_s3_instance.delete_object.return_value = True
        mock_s3_client.return_value = mock_s3_instance
        
        import test_service
        
        result = test_service.run_comprehensive_test('test-service', 'test-bucket')
        self.assertTrue(result)


def run_integration_tests():
    """Run all integration tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add integration test classes
    suite.addTests(loader.loadTestsFromTestCase(TestServiceManagerIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestEndToEndWorkflow))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestBackupRestoreIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformanceMonitoring))
    suite.addTests(loader.loadTestsFromTestCase(TestServiceTesting))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("Running S3Bridge Integration Tests...")
    success = run_integration_tests()
    
    if success:
        print("\nAll integration tests passed!")
        sys.exit(0)
    else:
        print("\nSome integration tests failed!")
        sys.exit(1)