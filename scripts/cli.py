#!/usr/bin/env python3
"""
S3Bridge CLI
Main command-line interface
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def main():
    parser = argparse.ArgumentParser(
        prog='s3bridge',
        description='S3Bridge - Account-agnostic S3 access',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  setup                 Deploy infrastructure
  add SERVICE PATTERNS  Add service with bucket patterns
  list                  List services
  edit SERVICE          Edit service configuration
  remove SERVICE        Remove service
  status               Show system status
  test SERVICE BUCKET  Test service access
  backup               Backup configurations
  restore FILE         Restore configurations

Examples:
  s3bridge setup --admin-user myuser
  s3bridge add analytics "company-analytics-*" --permissions read-only
  s3bridge list
  s3bridge status
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Setup
    setup_parser = subparsers.add_parser('setup', help='Deploy infrastructure')
    setup_parser.add_argument('--admin-user', default='admin', help='Admin username')
    setup_parser.add_argument('--force', action='store_true', help='Force redeploy')
    
    # Add service
    add_parser = subparsers.add_parser('add', help='Add service')
    add_parser.add_argument('service_name', help='Service name')
    add_parser.add_argument('bucket_patterns', help='Bucket patterns')
    add_parser.add_argument('--permissions', choices=['read-only', 'read-write', 'admin'], 
                           default='read-write', help='Permissions')
    
    # List services
    subparsers.add_parser('list', help='List services')
    
    # Edit service
    edit_parser = subparsers.add_parser('edit', help='Edit service')
    edit_parser.add_argument('service_name', help='Service name')
    edit_parser.add_argument('--bucket-patterns', help='Bucket patterns')
    edit_parser.add_argument('--permissions', choices=['read-only', 'read-write', 'admin'])
    
    # Remove service
    remove_parser = subparsers.add_parser('remove', help='Remove service')
    remove_parser.add_argument('service_name', help='Service name')
    remove_parser.add_argument('--force', action='store_true', help='Skip confirmation')
    
    # Status
    subparsers.add_parser('status', help='Show status')
    
    # Test
    test_parser = subparsers.add_parser('test', help='Test service')
    test_parser.add_argument('service_name', help='Service name')
    test_parser.add_argument('bucket_name', help='Bucket name')
    
    # Backup
    backup_parser = subparsers.add_parser('backup', help='Backup configs')
    backup_parser.add_argument('--file', help='Backup file')
    
    # Restore
    restore_parser = subparsers.add_parser('restore', help='Restore configs')
    restore_parser.add_argument('file', help='Backup file')
    restore_parser.add_argument('--dry-run', action='store_true')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to appropriate script
    if args.command == 'setup':
        from scripts.setup import main as setup_main
        sys.argv = ['setup.py', '--admin-user', args.admin_user]
        if args.force:
            sys.argv.append('--force')
        return setup_main()
    
    elif args.command == 'add':
        from scripts.add_service import main as add_main
        sys.argv = ['add_service.py', args.service_name, args.bucket_patterns, 
                   '--permissions', args.permissions]
        return add_main()
    
    elif args.command == 'list':
        from scripts.list_services import main as list_main
        return list_main()
    
    elif args.command == 'edit':
        from scripts.edit_service import main as edit_main
        sys.argv = ['edit_service.py', args.service_name]
        if args.bucket_patterns:
            sys.argv.extend(['--bucket-patterns', args.bucket_patterns])
        if args.permissions:
            sys.argv.extend(['--permissions', args.permissions])
        return edit_main()
    
    elif args.command == 'remove':
        from scripts.remove_service import main as remove_main
        sys.argv = ['remove_service.py', args.service_name]
        if args.force:
            sys.argv.append('--force')
        return remove_main()
    
    elif args.command == 'status':
        from scripts.service_status import main as status_main
        return status_main()
    
    elif args.command == 'test':
        from scripts.test_service import main as test_main
        sys.argv = ['test_service.py', args.service_name, args.bucket_name]
        return test_main()
    
    elif args.command == 'backup':
        from scripts.backup_restore import main as backup_main
        sys.argv = ['backup_restore.py', 'backup']
        if args.file:
            sys.argv.extend(['--file', args.file])
        return backup_main()
    
    elif args.command == 'restore':
        from scripts.backup_restore import main as restore_main
        sys.argv = ['backup_restore.py', 'restore', args.file]
        if args.dry_run:
            sys.argv.append('--dry-run')
        return restore_main()

if __name__ == "__main__":
    sys.exit(main())