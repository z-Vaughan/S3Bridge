"""
S3Bridge
Account-agnostic credential service for secure S3 access
"""

from .universal_s3_client import S3BridgeClient
from .universal_auth import S3BridgeAuthProvider

__version__ = "1.0.0"
__all__ = ["S3BridgeClient", "S3BridgeAuthProvider"]