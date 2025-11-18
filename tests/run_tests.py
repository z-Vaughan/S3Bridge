#!/usr/bin/env python3
"""
Test Runner for Universal S3 Library
Handles imports and provides comprehensive test execution
"""

import os
import sys
import unittest
from pathlib import Path

# Add project paths to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root / 'scripts'))
sys.path.insert(0, str(project_root / 'config'))

def check_dependencies():
    """Check if required dependencies are available"""
    missing_deps = []
    
    try:
        import boto3
    except ImportError:
        missing_deps.append('boto3')
    
    try:
        import requests
    except ImportError:
        missing_deps.append('requests')
    
    if missing_deps:
        print(f"WARNING: Missing dependencies: {', '.join(missing_deps)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    return True

def check_modules():
    """Check if project modules are available"""
    modules_status = {}
    
    # Core modules
    try:
        from src import universal_auth, universal_s3_client
        modules_status['core'] = True
    except ImportError as e:
        modules_status['core'] = False
        print(f"WARNING: Core modules issue: {e}")
    
    # Config module
    try:
        from config import aws_config
        modules_status['config'] = True
    except ImportError as e:
        modules_status['config'] = False
        print(f"WARNING: Config module issue: {e}")
    
    # Script modules (optional)
    script_modules = ['add_service', 'list_services', 'remove_service', 'edit_service', 'service_status', 'test_service']
    modules_status['scripts'] = {}
    
    for module in script_modules:
        try:
            __import__(module)
            modules_status['scripts'][module] = True
        except ImportError:
            modules_status['scripts'][module] = False
    
    return modules_status

def run_specific_test_class(test_class_name):
    """Run a specific test class"""
    try:
        from test_operations import (
            TestServiceOperations, 
            TestAuthProvider, 
            TestS3Client, 
            TestConfigManagement, 
            TestErrorHandling
        )
        
        class_map = {
            'operations': TestServiceOperations,
            'auth': TestAuthProvider,
            's3': TestS3Client,
            'config': TestConfigManagement,
            'errors': TestErrorHandling
        }
        
        if test_class_name not in class_map:
            print(f"ERROR: Unknown test class: {test_class_name}")
            print(f"Available classes: {', '.join(class_map.keys())}")
            return False
        
        suite = unittest.TestLoader().loadTestsFromTestCase(class_map[test_class_name])
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result.wasSuccessful()
        
    except ImportError as e:
        print(f"ERROR: Failed to import test classes: {e}")
        return False

def run_all_tests():
    """Run all available tests"""
    try:
        from test_operations import run_all_tests
        return run_all_tests()
    except ImportError as e:
        print(f"ERROR: Failed to import test module: {e}")
        return False

def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Universal S3 Library Test Runner')
    parser.add_argument('--class', dest='test_class', 
                       choices=['operations', 'auth', 's3', 'config', 'errors'],
                       help='Run specific test class')
    parser.add_argument('--check-deps', action='store_true',
                       help='Check dependencies only')
    parser.add_argument('--check-modules', action='store_true',
                       help='Check module availability')
    
    args = parser.parse_args()
    
    print("Universal S3 Library Test Runner")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    if args.check_deps:
        print("SUCCESS: All dependencies available")
        return 0
    
    # Check modules
    modules_status = check_modules()
    
    if args.check_modules:
        print("\nModule Status:")
        print(f"  Core modules: {'OK' if modules_status['core'] else 'FAIL'}")
        print(f"  Config module: {'OK' if modules_status['config'] else 'FAIL'}")
        print("  Script modules:")
        for module, status in modules_status['scripts'].items():
            print(f"    {module}: {'OK' if status else 'FAIL'}")
        return 0
    
    # Run tests
    print("\nRunning Tests...")
    
    if args.test_class:
        success = run_specific_test_class(args.test_class)
    else:
        success = run_all_tests()
    
    print("\n" + "=" * 50)
    if success:
        print("SUCCESS: All tests completed successfully!")
    else:
        print("ERROR: Some tests failed!")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())