#!/usr/bin/env python3
"""
Simple test to verify imports work correctly
"""

import sys
from pathlib import Path

# Add src and scripts to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root / 'scripts'))
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all modules can be imported"""
    
    print("Testing imports...")
    
    try:
        # Test src imports
        from src.universal_auth import S3BridgeAuthProvider
        from src.universal_s3_client import S3BridgeClient
        from config.aws_config import AWSConfig
        print("[OK] src imports work")
    except ImportError as e:
        print(f"[FAIL] src import failed: {e}")
        return False
    
    try:
        # Test script imports
        import add_service
        import list_services
        import remove_service
        import edit_service
        import service_status
        import test_service
        import backup_restore
        import service_manager
        print("[OK] script imports work")
    except ImportError as e:
        print(f"[FAIL] script import failed: {e}")
        return False
    
    print("All imports successful!")
    return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)