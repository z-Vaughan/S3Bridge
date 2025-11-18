#!/usr/bin/env python3
"""
Production Test Runner
Runs live integration tests with real AWS resources
"""

import os
import sys
import argparse
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def check_aws_credentials():
    """Check if AWS credentials are configured"""
    try:
        import boto3
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        return True, identity
    except Exception as e:
        return False, str(e)

def check_prerequisites():
    """Check all prerequisites for live testing"""
    print("Checking prerequisites...")
    
    # Check AWS credentials
    aws_ok, aws_info = check_aws_credentials()
    if aws_ok:
        print(f"SUCCESS: AWS credentials configured")
        print(f"   Account: {aws_info['Account']}")
        print(f"   User: {aws_info.get('Arn', aws_info['UserId'])}")
    else:
        print(f"ERROR: AWS credentials not configured: {aws_info}")
        return False
    
    # Check dependencies
    try:
        import boto3
        import requests
        print("SUCCESS: Required packages available")
    except ImportError as e:
        print(f"ERROR: Missing required packages: {e}")
        return False
    
    # Check project structure
    required_dirs = ['src', 'scripts', 'config', 'templates']
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"SUCCESS: {dir_name}/ directory found")
        else:
            print(f"ERROR: {dir_name}/ directory missing")
            return False
    
    return True

def run_integration_tests():
    """Run live integration tests"""
    try:
        from test_live_integration import run_live_tests
        return run_live_tests()
    except ImportError as e:
        print(f"ERROR: Failed to import integration tests: {e}")
        return False

def run_workflow_tests():
    """Run workflow tests"""
    try:
        from test_deployment_workflow import run_workflow_tests
        return run_workflow_tests()
    except ImportError as e:
        print(f"ERROR: Failed to import workflow tests: {e}")
        return False

def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description='S3Bridge Production Test Runner')
    parser.add_argument('--check-only', action='store_true',
                       help='Only check prerequisites, do not run tests')
    parser.add_argument('--integration-only', action='store_true',
                       help='Run only integration tests')
    parser.add_argument('--workflow-only', action='store_true',
                       help='Run only workflow tests')
    parser.add_argument('--skip-s3-tests', action='store_true',
                       help='Skip tests that create S3 buckets')
    
    args = parser.parse_args()
    
    print("S3Bridge - Production Test Runner")
    print("=" * 60)
    print("WARNING: These tests use real AWS resources!")
    print("   - May create temporary S3 buckets")
    print("   - Will check existing infrastructure")
    print("   - Uses your configured AWS credentials")
    print("=" * 60)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\nERROR: Prerequisites not met. Please fix issues above.")
        return 1
    
    if args.check_only:
        print("\nSUCCESS: All prerequisites met!")
        return 0
    
    # Confirm with user
    if not args.skip_s3_tests:
        confirm = input("\nProceed with live AWS tests? (y/N): ")
        if confirm.lower() != 'y':
            print("Tests cancelled by user.")
            return 0
    
    success = True
    
    # Run tests based on arguments
    if args.integration_only:
        print("\nRunning Integration Tests...")
        success = run_integration_tests()
    elif args.workflow_only:
        print("\nRunning Workflow Tests...")
        success = run_workflow_tests()
    else:
        print("\nRunning Workflow Tests...")
        workflow_success = run_workflow_tests()
        
        print("\nRunning Integration Tests...")
        integration_success = run_integration_tests()
        
        success = workflow_success and integration_success
    
    print("\n" + "=" * 60)
    if success:
        print("SUCCESS: All production tests completed successfully!")
    else:
        print("WARNING: Some tests failed or had issues")
        print("   This may be expected if infrastructure is not deployed")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())