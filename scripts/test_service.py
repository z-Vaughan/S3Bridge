#!/usr/bin/env python3
"""
Test Service Script
Test service functionality and permissions
"""

import boto3
import json
import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_service_credentials(service_name):
    """Test if service can obtain credentials"""
    try:
        from src.universal_auth import S3BridgeAuthProvider
        
        print(f"Testing credential access for service: {service_name}")
        
        auth = S3BridgeAuthProvider(service_name)
        credentials = auth.get_credentials()
        
        if credentials and all(k in credentials for k in ['access_key', 'secret_key', 'session_token']):
            print("Credentials obtained successfully")
            print(f"   Access Key: {credentials['access_key'][:10]}...")
            return True
        else:
            print("Invalid credentials received")
            return False
            
    except Exception as e:
        print(f"Credential test failed: {e}")
        return False

def test_s3_operations(service_name, bucket_name, test_key="test/service_test.json"):
    """Test S3 operations with service"""
    try:
        from src.universal_s3_client import S3BridgeClient
        
        print(f"Testing S3 operations for service: {service_name}")
        print(f"   Bucket: {bucket_name}")
        
        client = S3BridgeClient(bucket_name, service_name)
        
        # Test data
        test_data = {
            "service": service_name,
            "test_timestamp": str(boto3.Session().region_name),
            "test": True
        }
        
        # Test write
        print("   Testing write operation...")
        write_success = client.write_json(test_data, test_key)
        if not write_success:
            print("   Write operation failed")
            return False
        print("   Write successful")
        
        # Test read
        print("   Testing read operation...")
        read_data = client.read_json(test_key)
        if not read_data or read_data.get('service') != service_name:
            print("   Read operation failed")
            return False
        print("   Read successful")
        
        # Test list
        print("   Testing list operation...")
        objects = client.list_objects("test/")
        if test_key not in objects:
            print("   List operation failed")
            return False
        print(f"   List successful ({len(objects)} objects found)")
        
        # Test delete (cleanup)
        print("   Testing delete operation...")
        delete_success = client.delete_object(test_key)
        if not delete_success:
            print("   Delete operation failed")
            return False
        print("   Delete successful")
        
        print("All S3 operations successful!")
        return True
        
    except ValueError as e:
        if "not authorized" in str(e):
            print(f"Service not authorized for bucket: {e}")
        else:
            print(f"Configuration error: {e}")
        return False
    except Exception as e:
        print(f"S3 operations failed: {e}")
        return False

def test_bucket_validation(service_name, valid_bucket, invalid_bucket):
    """Test bucket access validation"""
    try:
        from src.universal_s3_client import S3BridgeClient
        
        print(f"Testing bucket validation for service: {service_name}")
        
        # Test valid bucket
        print(f"   Testing valid bucket: {valid_bucket}")
        try:
            client = S3BridgeClient(valid_bucket, service_name)
            print("   Valid bucket accepted")
        except ValueError:
            print("   Valid bucket rejected")
            return False
        
        # Test invalid bucket
        print(f"   Testing invalid bucket: {invalid_bucket}")
        try:
            client = S3BridgeClient(invalid_bucket, service_name)
            print("   Invalid bucket accepted (security issue!)")
            return False
        except ValueError:
            print("   Invalid bucket correctly rejected")
        
        return True
        
    except Exception as e:
        print(f"Bucket validation test failed: {e}")
        return False

def run_comprehensive_test(service_name, bucket_name):
    """Run comprehensive service test"""
    
    print(f"Comprehensive Test for Service: {service_name}")
    print("=" * 50)
    
    results = {
        'credentials': False,
        's3_operations': False,
        'bucket_validation': False
    }
    
    # Test 1: Credential access
    results['credentials'] = test_service_credentials(service_name)
    print()
    
    # Test 2: S3 operations (only if credentials work)
    if results['credentials']:
        results['s3_operations'] = test_s3_operations(service_name, bucket_name)
        print()
    
    # Test 3: Bucket validation
    invalid_bucket = "unauthorized-bucket-test"
    results['bucket_validation'] = test_bucket_validation(service_name, bucket_name, invalid_bucket)
    print()
    
    # Summary
    print("Test Results Summary:")
    for test_name, result in results.items():
        icon = "[PASS]" if result else "[FAIL]"
        print(f"   {icon} {test_name.replace('_', ' ').title()}")
    
    success_count = sum(results.values())
    total_tests = len(results)
    
    print(f"\nOverall Result: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("Service is fully functional!")
        return True
    else:
        print("Service has issues that need attention")
        return False

def main():
    parser = argparse.ArgumentParser(description='Test S3Bridge service')
    parser.add_argument('service_name', help='Service name to test')
    parser.add_argument('bucket_name', help='Bucket name for testing')
    parser.add_argument('--credentials-only', action='store_true', 
                       help='Test only credential access')
    parser.add_argument('--s3-only', action='store_true',
                       help='Test only S3 operations')
    parser.add_argument('--validation-only', action='store_true',
                       help='Test only bucket validation')
    
    args = parser.parse_args()
    
    # Check AWS credentials
    try:
        boto3.client('sts').get_caller_identity()
    except Exception as e:
        print(f"AWS credentials not configured: {e}")
        return 1
    
    success = True
    
    if args.credentials_only:
        success = test_service_credentials(args.service_name)
    elif args.s3_only:
        success = test_s3_operations(args.service_name, args.bucket_name)
    elif args.validation_only:
        success = test_bucket_validation(args.service_name, args.bucket_name, "invalid-bucket")
    else:
        success = run_comprehensive_test(args.service_name, args.bucket_name)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())