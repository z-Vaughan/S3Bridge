#!/usr/bin/env python3
"""
Service Manager CLI
Unified command-line interface for S3Bridge service management
"""

import argparse
import sys
import subprocess
from pathlib import Path

def run_script(script_name, args):
    """Run a management script with arguments"""
    script_path = Path(__file__).parent / f"{script_name}.py"
    cmd = [sys.executable, str(script_path)] + args
    return subprocess.run(cmd).returncode

def main():
    parser = argparse.ArgumentParser(
        description='S3Bridge Service Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list                                    # List all services
  %(prog)s add myapp "myapp-*" --permissions read-write
  %(prog)s edit myapp --bucket-patterns "myapp-*,shared-*"
  %(prog)s remove myapp --force
  %(prog)s status                                  # Show system status
  %(prog)s backup --file my_backup.json
  %(prog)s restore my_backup.json --dry-run
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all services')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add new service')
    add_parser.add_argument('service_name', help='Service name')
    add_parser.add_argument('bucket_patterns', help='Comma-separated bucket patterns')
    add_parser.add_argument('--permissions', choices=['read-only', 'read-write', 'admin'], 
                           default='read-write', help='Access level')
    
    # Edit command
    edit_parser = subparsers.add_parser('edit', help='Edit existing service')
    edit_parser.add_argument('service_name', help='Service name')
    edit_parser.add_argument('--bucket-patterns', help='Comma-separated bucket patterns')
    edit_parser.add_argument('--permissions', choices=['read-only', 'read-write', 'admin'], 
                            help='Access level')
    
    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove service')
    remove_parser.add_argument('service_name', help='Service name')
    remove_parser.add_argument('--force', action='store_true', help='Skip confirmation')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show system status')
    
    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Backup configurations')
    backup_parser.add_argument('--file', help='Backup file name')
    
    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore configurations')
    restore_parser.add_argument('file', help='Backup file')
    restore_parser.add_argument('--dry-run', action='store_true', help='Show changes without applying')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to appropriate script
    if args.command == 'list':
        return run_script('list_services', [])
    
    elif args.command == 'add':
        cmd_args = [args.service_name, args.bucket_patterns, '--permissions', args.permissions]
        return run_script('add_service', cmd_args)
    
    elif args.command == 'edit':
        cmd_args = [args.service_name]
        if args.bucket_patterns:
            cmd_args.extend(['--bucket-patterns', args.bucket_patterns])
        if args.permissions:
            cmd_args.extend(['--permissions', args.permissions])
        return run_script('edit_service', cmd_args)
    
    elif args.command == 'remove':
        cmd_args = [args.service_name]
        if args.force:
            cmd_args.append('--force')
        return run_script('remove_service', cmd_args)
    
    elif args.command == 'status':
        return run_script('service_status', [])
    
    elif args.command == 'backup':
        cmd_args = ['backup']
        if args.file:
            cmd_args.extend(['--file', args.file])
        return run_script('backup_restore', cmd_args)
    
    elif args.command == 'restore':
        cmd_args = ['restore', args.file]
        if args.dry_run:
            cmd_args.append('--dry-run')
        return run_script('backup_restore', cmd_args)

if __name__ == "__main__":
    sys.exit(main())