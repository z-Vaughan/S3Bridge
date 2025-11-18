#!/usr/bin/env python3
"""
Backup and Restore Script
Backup/restore service configurations for Universal S3 Library
"""

import boto3
import json
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.aws_config import AWSConfig

def backup_services(backup_file=None):
    """Backup all service configurations"""
    
    if not backup_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"services_backup_{timestamp}.json"
    
    config = AWSConfig()
    backup_data = {
        'timestamp': datetime.now().isoformat(),
        'account_id': config.account_id,
        'region': config.region,
        'services': {},
        'iam_roles': {}
    }
    
    try:
        # Backup Lambda configuration
        lambda_client = boto3.client('lambda')
        response = lambda_client.get_function_configuration(FunctionName='universal-credential-service')
        env_vars = response.get('Environment', {}).get('Variables', {})
        
        for key, value in env_vars.items():
            if key.startswith('SERVICE_'):
                service_name = key[8:].lower()
                try:
                    backup_data['services'][service_name] = json.loads(value)
                except json.JSONDecodeError:
                    continue
        
        # Backup IAM roles
        iam = boto3.client('iam')
        roles_response = iam.list_roles(PathPrefix='/service-role/')
        
        for role in roles_response['Roles']:
            role_name = role['RoleName']
            if role_name.endswith('-s3-access-role'):
                service_name = role_name.replace('-s3-access-role', '')
                
                # Get role policies
                policies_response = iam.list_role_policies(RoleName=role_name)
                role_policies = {}
                
                for policy_name in policies_response['PolicyNames']:
                    policy_response = iam.get_role_policy(RoleName=role_name, PolicyName=policy_name)
                    role_policies[policy_name] = policy_response['PolicyDocument']
                
                backup_data['iam_roles'][service_name] = {
                    'role_name': role_name,
                    'arn': role['Arn'],
                    'assume_role_policy': role['AssumeRolePolicyDocument'],
                    'policies': role_policies,
                    'description': role.get('Description', '')
                }
        
        # Save backup
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        
        print(f"Backup saved to: {backup_file}")
        print(f"Services backed up: {len(backup_data['services'])}")
        print(f"IAM roles backed up: {len(backup_data['iam_roles'])}")
        
        return True
        
    except Exception as e:
        print(f"Backup failed: {e}")
        return False

def restore_services(backup_file, dry_run=False):
    """Restore service configurations from backup"""
    
    try:
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
    except Exception as e:
        print(f"Failed to load backup file: {e}")
        return False
    
    print(f"Restoring from: {backup_file}")
    print(f"Backup date: {backup_data.get('timestamp', 'Unknown')}")
    print(f"Source account: {backup_data.get('account_id', 'Unknown')}")
    
    if dry_run:
        print("DRY RUN - No changes will be made")
    
    services = backup_data.get('services', {})
    iam_roles = backup_data.get('iam_roles', {})
    
    print(f"Services to restore: {len(services)}")
    print(f"IAM roles to restore: {len(iam_roles)}")
    
    if not dry_run:
        confirm = input("Continue with restore? (y/N): ")
        if confirm.lower() != 'y':
            print("Restore cancelled")
            return False
    
    config = AWSConfig()
    success = True
    
    # Restore IAM roles
    iam = boto3.client('iam')
    for service_name, role_data in iam_roles.items():
        role_name = role_data['role_name']
        
        if dry_run:
            print(f"[DRY RUN] Would restore IAM role: {role_name}")
            continue
        
        try:
            # Create role
            iam.create_role(
                RoleName=role_name,
                Path='/service-role/',
                AssumeRolePolicyDocument=json.dumps(role_data['assume_role_policy']),
                Description=role_data.get('description', f"Restored service role for {service_name}")
            )
            
            # Attach policies
            for policy_name, policy_doc in role_data['policies'].items():
                iam.put_role_policy(
                    RoleName=role_name,
                    PolicyName=policy_name,
                    PolicyDocument=json.dumps(policy_doc)
                )
            
            print(f"Restored IAM role: {role_name}")
            
        except iam.exceptions.EntityAlreadyExistsException:
            print(f"IAM role {role_name} already exists, skipping")
        except Exception as e:
            print(f"Failed to restore IAM role {role_name}: {e}")
            success = False
    
    # Restore Lambda configuration
    if services:
        if dry_run:
            print(f"[DRY RUN] Would restore {len(services)} services to Lambda")
        else:
            try:
                lambda_client = boto3.client('lambda')
                response = lambda_client.get_function_configuration(FunctionName='universal-credential-service')
                env_vars = response.get('Environment', {}).get('Variables', {})
                
                # Add restored services
                for service_name, service_config in services.items():
                    service_key = f"SERVICE_{service_name.upper()}"
                    env_vars[service_key] = json.dumps(service_config)
                
                # Update Lambda function
                lambda_client.update_function_configuration(
                    FunctionName='universal-credential-service',
                    Environment={'Variables': env_vars}
                )
                
                print(f"Restored {len(services)} services to Lambda configuration")
                
            except Exception as e:
                print(f"Failed to restore Lambda configuration: {e}")
                success = False
    
    if success and not dry_run:
        print("Restore completed successfully!")
    elif dry_run:
        print("Dry run completed - no changes made")
    else:
        print("Restore completed with errors")
    
    return success

def main():
    parser = argparse.ArgumentParser(description='Backup/restore Universal S3 Library services')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Backup service configurations')
    backup_parser.add_argument('--file', help='Backup file name')
    
    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore service configurations')
    restore_parser.add_argument('file', help='Backup file to restore from')
    restore_parser.add_argument('--dry-run', action='store_true', help='Show what would be restored without making changes')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Check AWS credentials
    try:
        boto3.client('sts').get_caller_identity()
    except Exception as e:
        print(f"AWS credentials not configured: {e}")
        return 1
    
    if args.command == 'backup':
        success = backup_services(args.file)
    elif args.command == 'restore':
        success = restore_services(args.file, args.dry_run)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())