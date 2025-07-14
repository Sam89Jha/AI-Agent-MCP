#!/usr/bin/env python3
"""
Simple test script to verify all imports work correctly
"""

import sys
import os

def test_imports():
    """Test all imports"""
    print("Testing imports...")
    
    # Test boto3
    try:
        import boto3
        print("✅ boto3 imported successfully")
    except ImportError as e:
        print(f"❌ boto3 import failed: {e}")
        return False
    
    # Test FastAPI
    try:
        import fastapi
        print("✅ fastapi imported successfully")
    except ImportError as e:
        print(f"❌ fastapi import failed: {e}")
        return False
    
    # Test requests
    try:
        import requests
        print("✅ requests imported successfully")
    except ImportError as e:
        print(f"❌ requests import failed: {e}")
        return False
    
    # Test MCP Server app (without AWS credentials)
    try:
        # Temporarily set AWS region to avoid NoRegionError
        os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
        os.environ['AWS_ACCESS_KEY_ID'] = 'test'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'test'
        
        sys.path.append('mcp-server')
        from app import app
        print("✅ MCP Server app imported successfully")
    except Exception as e:
        print(f"❌ MCP Server app import failed: {e}")
        return False
    
    # Test Lambda functions (without AWS credentials)
    try:
        sys.path.append('lambda-functions')
        import send_message
        import make_call
        import get_message
        print("✅ Lambda functions imported successfully")
    except Exception as e:
        print(f"❌ Lambda functions import failed: {e}")
        return False
    
    print("\n🎉 All imports successful!")
    return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1) 