#!/usr/bin/env python3
"""
Comprehensive import test for NavieTakieSimulation project.
Tests all Python files and their dependencies.
"""

import sys
import os
import importlib
from typing import List, Tuple

def test_import(module_name: str, description: str) -> Tuple[bool, str]:
    """Test importing a module and return success status and message."""
    try:
        importlib.import_module(module_name)
        return True, f"✅ {description} imported successfully"
    except ImportError as e:
        return False, f"❌ {description} import failed: {str(e)}"
    except Exception as e:
        return False, f"❌ {description} error: {str(e)}"

def test_file_import(file_path: str, description: str) -> Tuple[bool, str]:
    """Test importing a Python file directly."""
    try:
        # Add the directory to sys.path temporarily
        dir_path = os.path.dirname(file_path)
        if dir_path not in sys.path:
            sys.path.insert(0, dir_path)
        
        # Import the module
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        importlib.import_module(module_name)
        
        return True, f"✅ {description} imported successfully"
    except ImportError as e:
        return False, f"❌ {description} import failed: {str(e)}"
    except Exception as e:
        return False, f"❌ {description} error: {str(e)}"

def main():
    """Run comprehensive import tests."""
    print("🧪 Testing all imports for NavieTakieSimulation project...\n")
    
    # Test core dependencies
    core_tests = [
        ("boto3", "boto3 AWS SDK"),
        ("fastapi", "FastAPI web framework"),
        ("uvicorn", "Uvicorn ASGI server"),
        ("pydantic", "Pydantic data validation"),
        ("requests", "Requests HTTP library"),
        ("pytest", "Pytest testing framework"),
        ("moto", "Moto AWS mocking library"),
    ]
    
    print("📦 Testing core dependencies:")
    core_success = 0
    for module_name, description in core_tests:
        success, message = test_import(module_name, description)
        print(f"  {message}")
        if success:
            core_success += 1
    
    print(f"\n📊 Core dependencies: {core_success}/{len(core_tests)} successful\n")
    
    # Test MCP Server
    print("🔧 Testing MCP Server:")
    mcp_success, mcp_message = test_file_import("mcp-server/app.py", "MCP Server app")
    print(f"  {mcp_message}")
    
    # Test Lambda functions (with AWS region set)
    print("\n⚡ Testing Lambda functions:")
    lambda_tests = [
        ("lambda-functions/send_message.py", "Send Message Lambda"),
        ("lambda-functions/make_call.py", "Make Call Lambda"),
        ("lambda-functions/get_message.py", "Get Message Lambda"),
    ]
    
    lambda_success = 0
    for file_path, description in lambda_tests:
        success, message = test_file_import(file_path, description)
        print(f"  {message}")
        if success:
            lambda_success += 1
    
    print(f"\n📊 Lambda functions: {lambda_success}/{len(lambda_tests)} successful")
    
    # Test staging environment
    print("\n🧪 Testing staging environment:")
    staging_tests = [
        ("staging/test_runner.py", "Staging test runner"),
    ]
    
    staging_success = 0
    for file_path, description in staging_tests:
        success, message = test_file_import(file_path, description)
        print(f"  {message}")
        if success:
            staging_success += 1
    
    print(f"\n📊 Staging tests: {staging_success}/{len(staging_tests)} successful")
    
    # Summary
    total_tests = len(core_tests) + 1 + len(lambda_tests) + len(staging_tests)
    total_success = core_success + (1 if mcp_success else 0) + lambda_success + staging_success
    
    print(f"\n🎯 SUMMARY:")
    print(f"  Total tests: {total_tests}")
    print(f"  Successful: {total_success}")
    print(f"  Failed: {total_tests - total_success}")
    
    if total_success == total_tests:
        print("\n🎉 All imports successful! Project is ready for development.")
        return 0
    else:
        print(f"\n⚠️  {total_tests - total_success} import(s) failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 