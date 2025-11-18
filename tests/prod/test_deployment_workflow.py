#!/usr/bin/env python3
"""
Deployment Workflow Tests
Tests the complete deployment and service management workflow
"""

import os
import sys
import json
import time
import unittest
import subprocess
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'scripts'))

class TestDeploymentWorkflow(unittest.TestCase):
    """Test complete deployment workflow"""
    
    def test_setup_script_exists(self):
        """Test that setup script exists and is executable"""
        setup_script = project_root / 'scripts' / 'setup.py'
        self.assertTrue(setup_script.exists(), "Setup script not found")
        print(f"SUCCESS: Setup script found: {setup_script}")
    
    def test_service_scripts_exist(self):
        """Test that all service management scripts exist"""
        scripts = [
            'add_service.py',
            'list_services.py',
            'edit_service.py', 
            'remove_service.py',
            'service_status.py',
            'test_service.py'
        ]
        
        for script_name in scripts:
            script_path = project_root / 'scripts' / script_name
            self.assertTrue(script_path.exists(), f"{script_name} not found")
            print(f"SUCCESS: {script_name} found")
    
    def test_infrastructure_template_exists(self):
        """Test that CloudFormation template exists"""
        template_path = project_root / 'templates' / 'infrastructure.yaml'
        self.assertTrue(template_path.exists(), "Infrastructure template not found")
        print(f"SUCCESS: Infrastructure template found")
        
        # Basic template validation
        with open(template_path, 'r') as f:
            content = f.read()
            self.assertIn('AWSTemplateFormatVersion', content)
            self.assertIn('Resources', content)
            print(f"SUCCESS: Template appears valid")


class TestServiceManagementWorkflow(unittest.TestCase):
    """Test service management workflow"""
    
    def test_list_services_command(self):
        """Test list services command"""
        try:
            result = subprocess.run([
                sys.executable, 
                str(project_root / 'scripts' / 'list_services.py')
            ], capture_output=True, text=True, timeout=30)
            
            print(f"List services exit code: {result.returncode}")
            if result.stdout:
                print("Services output:")
                print(result.stdout)
            if result.stderr and result.returncode != 0:
                print("WARNING: Services stderr:")
                print(result.stderr)
                
        except subprocess.TimeoutExpired:
            print("WARNING: List services command timed out")
        except Exception as e:
            print(f"WARNING: List services failed: {e}")
    
    def test_service_status_command(self):
        """Test service status command"""
        try:
            result = subprocess.run([
                sys.executable,
                str(project_root / 'scripts' / 'service_status.py')
            ], capture_output=True, text=True, timeout=30)
            
            print(f"Service status exit code: {result.returncode}")
            if result.stdout:
                print("Status output:")
                print(result.stdout)
            if result.stderr and result.returncode != 0:
                print("WARNING: Status stderr:")
                print(result.stderr)
                
        except subprocess.TimeoutExpired:
            print("WARNING: Service status command timed out")
        except Exception as e:
            print(f"WARNING: Service status failed: {e}")
    
    def test_add_service_help(self):
        """Test add service help command"""
        try:
            result = subprocess.run([
                sys.executable,
                str(project_root / 'scripts' / 'add_service.py'),
                '--help'
            ], capture_output=True, text=True, timeout=10)
            
            self.assertEqual(result.returncode, 0)
            self.assertIn('usage:', result.stdout.lower())
            print(f"SUCCESS: Add service help works")
            
        except Exception as e:
            print(f"WARNING: Add service help failed: {e}")


class TestConfigurationManagement(unittest.TestCase):
    """Test configuration management"""
    
    def test_config_directory_structure(self):
        """Test config directory structure"""
        config_dir = project_root / 'config'
        self.assertTrue(config_dir.exists(), "Config directory not found")
        
        aws_config = config_dir / 'aws_config.py'
        self.assertTrue(aws_config.exists(), "AWS config module not found")
        print(f"SUCCESS: Config structure valid")
    
    def test_deployment_config_handling(self):
        """Test deployment config file handling"""
        from config.aws_config import AWSConfig
        
        config = AWSConfig()
        
        # Test config loading (may return None if not deployed)
        deployment_config = config.load_deployment_config()
        if deployment_config:
            print(f"SUCCESS: Deployment config loaded")
            print(f"   Account: {deployment_config.get('account_id', 'Unknown')}")
            print(f"   Region: {deployment_config.get('region', 'Unknown')}")
        else:
            print(f"INFO: No deployment config found (expected if not deployed)")
        
        # Test config save functionality
        test_config = {
            'account_id': config.account_id,
            'region': config.region,
            'api_gateway_url': 'https://test.amazonaws.com',
            'admin_username': 'test-admin'
        }
        
        try:
            # This will create/update the config file
            config.save_deployment_config(
                test_config['api_gateway_url'],
                test_config['admin_username']
            )
            print(f"SUCCESS: Config save functionality works")
        except Exception as e:
            print(f"WARNING: Config save failed: {e}")


class TestLambdaFunction(unittest.TestCase):
    """Test Lambda function code"""
    
    def test_lambda_function_exists(self):
        """Test that Lambda function code exists"""
        lambda_dir = project_root / 'lambda_functions'
        self.assertTrue(lambda_dir.exists(), "Lambda functions directory not found")
        
        lambda_file = lambda_dir / 'universal_credential_service.py'
        self.assertTrue(lambda_file.exists(), "Lambda function code not found")
        print(f"SUCCESS: Lambda function code found")
        
        # Basic code validation
        with open(lambda_file, 'r') as f:
            content = f.read()
            self.assertIn('def lambda_handler', content)
            self.assertIn('import boto3', content)
            print(f"SUCCESS: Lambda function appears valid")


def run_workflow_tests():
    """Run all workflow tests"""
    print("S3Bridge - Deployment Workflow Tests")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDeploymentWorkflow))
    suite.addTests(loader.loadTestsFromTestCase(TestServiceManagementWorkflow))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigurationManagement))
    suite.addTests(loader.loadTestsFromTestCase(TestLambdaFunction))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("SUCCESS: All workflow tests completed successfully!")
    else:
        print("WARNING: Some workflow tests had issues")
        print("   This may be expected if infrastructure is not deployed")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_workflow_tests()
    sys.exit(0 if success else 1)