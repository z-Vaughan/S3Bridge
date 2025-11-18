"""
Performance Tests for Universal S3 Library
Tests performance characteristics and load handling
"""

import os
import sys
import json
import time
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

class TestPerformance(unittest.TestCase):
    """Performance and load tests"""
    
    def setUp(self):
        """Set up performance test environment"""
        self.test_service = "perf-test"
        self.test_bucket = "perf-test-bucket"
    
    @patch('src.universal_auth.UniversalAuthProvider')
    def test_credential_caching_performance(self, mock_auth_provider):
        """Test credential caching reduces API calls"""
        
        # Mock auth provider with call counting
        mock_auth_instance = Mock()
        call_count = 0
        
        def mock_fetch_credentials():
            nonlocal call_count
            call_count += 1
            return {
                'access_key': 'AKIA123',
                'secret_key': 'secret123',
                'session_token': 'token123'
            }
        
        mock_auth_instance._fetch_fresh_credentials = mock_fetch_credentials
        mock_auth_instance.credentials_expired.return_value = False
        mock_auth_instance._cached_credentials = None
        
        # First call should fetch credentials
        mock_auth_instance.get_credentials.side_effect = lambda: (
            mock_fetch_credentials() if mock_auth_instance._cached_credentials is None
            else mock_auth_instance._cached_credentials
        )
        
        mock_auth_provider.return_value = mock_auth_instance
        
        from src.universal_auth import UniversalAuthProvider
        
        auth = UniversalAuthProvider(self.test_service)
        
        # Simulate multiple credential requests
        for _ in range(10):
            auth.get_credentials()
        
        # Should only call fetch once due to caching
        self.assertEqual(call_count, 1)
    
    @patch('src.universal_s3_client.UniversalS3Client')
    def test_concurrent_s3_operations(self, mock_s3_client):
        """Test concurrent S3 operations"""
        
        # Mock S3 client with operation tracking
        operation_times = []
        
        def mock_operation():
            start_time = time.time()
            time.sleep(0.01)  # Simulate operation time
            end_time = time.time()
            operation_times.append(end_time - start_time)
            return True
        
        mock_s3_instance = Mock()
        mock_s3_instance.write_json.side_effect = lambda *args: mock_operation()
        mock_s3_instance.read_json.side_effect = lambda *args: mock_operation() and {'test': 'data'}
        mock_s3_client.return_value = mock_s3_instance
        
        from src.universal_s3_client import UniversalS3Client
        
        client = UniversalS3Client(self.test_bucket, self.test_service)
        
        # Test concurrent operations
        num_operations = 20
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            
            for i in range(num_operations):
                if i % 2 == 0:
                    future = executor.submit(client.write_json, {'test': i}, f'test_{i}.json')
                else:
                    future = executor.submit(client.read_json, f'test_{i}.json')
                futures.append(future)
            
            # Wait for all operations to complete
            for future in as_completed(futures):
                result = future.result()
        
        total_time = time.time() - start_time
        
        # Verify all operations completed
        self.assertEqual(len(operation_times), num_operations)
        
        # Concurrent operations should be faster than sequential
        expected_sequential_time = num_operations * 0.01
        self.assertLess(total_time, expected_sequential_time * 0.8)
    
    def test_memory_usage_stability(self):
        """Test memory usage remains stable under load"""
        import gc
        
        # Get initial memory usage (approximate)
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Simulate heavy usage
        with patch('src.universal_auth.UniversalAuthProvider') as mock_auth:
            mock_auth_instance = Mock()
            mock_auth_instance.get_credentials.return_value = {
                'access_key': 'AKIA123',
                'secret_key': 'secret123',
                'session_token': 'token123'
            }
            mock_auth.return_value = mock_auth_instance
            
            from src.universal_auth import UniversalAuthProvider
            
            # Create and destroy many auth providers
            for i in range(100):
                auth = UniversalAuthProvider(f"test-service-{i}")
                auth.get_credentials()
                del auth
        
        # Force garbage collection
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Memory usage should not grow significantly
        object_growth = final_objects - initial_objects
        self.assertLess(object_growth, 50, "Memory usage grew too much")
    
    @patch('boto3.client')
    def test_service_management_performance(self, mock_boto3):
        """Test service management operation performance"""
        
        # Mock AWS clients
        mock_iam = Mock()
        mock_lambda = Mock()
        mock_sts = Mock()
        
        mock_boto3.side_effect = lambda service: {
            'iam': mock_iam,
            'lambda': mock_lambda,
            'sts': mock_sts
        }[service]
        
        mock_sts.get_caller_identity.return_value = {'Account': '123456789012'}
        mock_iam.create_role.return_value = {'Role': {'Arn': 'test-arn'}}
        mock_lambda.get_function_configuration.return_value = {
            'Environment': {'Variables': {'AWS_ACCOUNT_ID': '123456789012'}}
        }
        
        # Add scripts to path
        sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
        
        import add_service as add_service_module
        
        # Time service addition
        start_time = time.time()
        
        for i in range(5):
            service_name = f"perf-test-{i}"
            bucket_patterns = [f"perf-test-{i}-*"]
            result = add_service_module.add_service(service_name, bucket_patterns, 'read-write')
            self.assertTrue(result)
        
        total_time = time.time() - start_time
        avg_time_per_service = total_time / 5
        
        # Each service addition should complete reasonably quickly
        self.assertLess(avg_time_per_service, 2.0, "Service addition too slow")
    
    def test_error_handling_performance(self):
        """Test error handling doesn't significantly impact performance"""
        
        with patch('src.universal_auth.UniversalAuthProvider') as mock_auth:
            # Mock auth provider that fails initially then succeeds
            mock_auth_instance = Mock()
            call_count = 0
            
            def mock_get_credentials():
                nonlocal call_count
                call_count += 1
                if call_count <= 3:
                    raise Exception("Temporary failure")
                return {
                    'access_key': 'AKIA123',
                    'secret_key': 'secret123',
                    'session_token': 'token123'
                }
            
            mock_auth_instance.get_credentials.side_effect = mock_get_credentials
            mock_auth.return_value = mock_auth_instance
            
            from src.universal_auth import UniversalAuthProvider
            
            auth = UniversalAuthProvider(self.test_service)
            
            # Time error handling
            start_time = time.time()
            
            try:
                # This should fail 3 times then succeed
                for _ in range(5):
                    try:
                        auth.get_credentials()
                        break
                    except Exception:
                        continue
            except Exception:
                pass
            
            error_handling_time = time.time() - start_time
            
            # Error handling should not take too long
            self.assertLess(error_handling_time, 1.0, "Error handling too slow")

class TestScalability(unittest.TestCase):
    """Scalability tests"""
    
    @patch('boto3.client')
    def test_many_services_performance(self, mock_boto3):
        """Test performance with many services configured"""
        
        # Mock Lambda with many services
        mock_lambda = Mock()
        mock_iam = Mock()
        
        mock_boto3.side_effect = lambda service: {
            'lambda': mock_lambda,
            'iam': mock_iam
        }[service]
        
        # Create mock configuration with 50 services
        services_config = {}
        for i in range(50):
            service_name = f"service_{i:02d}"
            services_config[f'SERVICE_{service_name.upper()}'] = json.dumps({
                'role': f'arn:aws:iam::123456789012:role/service-role/{service_name}-s3-access-role',
                'buckets': [f'{service_name}-*']
            })
        
        services_config['AWS_ACCOUNT_ID'] = '123456789012'
        
        mock_lambda.get_function.return_value = {
            'Configuration': {
                'Environment': {'Variables': services_config}
            }
        }
        
        # Mock IAM roles
        mock_roles = []
        for i in range(50):
            service_name = f"service_{i:02d}"
            mock_roles.append({
                'RoleName': f'{service_name}-s3-access-role',
                'Arn': f'arn:aws:iam::123456789012:role/service-role/{service_name}-s3-access-role',
                'CreateDate': '2024-01-01T00:00:00Z',
                'Description': f'Service {i}'
            })
        
        mock_iam.list_roles.return_value = {'Roles': mock_roles}
        
        # Add scripts to path
        sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
        
        import list_services
        
        # Time service listing with many services
        start_time = time.time()
        
        services = list_services.get_service_config()
        roles = list_services.get_service_roles()
        
        list_time = time.time() - start_time
        
        # Verify all services loaded
        self.assertEqual(len(services), 51)  # 50 + universal
        self.assertEqual(len(roles), 50)
        
        # Should complete quickly even with many services
        self.assertLess(list_time, 1.0, "Service listing too slow with many services")


def run_performance_tests():
    """Run all performance tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add performance test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))
    suite.addTests(loader.loadTestsFromTestCase(TestScalability))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("Running Universal S3 Library Performance Tests...")
    success = run_performance_tests()
    
    if success:
        print("\nAll performance tests passed!")
        sys.exit(0)
    else:
        print("\nSome performance tests failed!")
        sys.exit(1)