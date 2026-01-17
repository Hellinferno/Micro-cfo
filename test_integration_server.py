#!/usr/bin/env python3
"""
Test script for FastAPI Integration Server
Tests basic functionality and endpoints
"""

import requests
import json
import time
import subprocess
import sys
from threading import Thread
import signal
import os

def test_server_endpoints():
    """Test all basic server endpoints"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing FastAPI Integration Server...")
    
    # Test 1: Health endpoint
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        print("✅ Health endpoint working")
    except Exception as e:
        print(f"❌ Health endpoint failed: {e}")
        return False
    
    # Test 2: Root endpoint
    print("\n2. Testing root endpoint...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "MicroCFO Integration API"
        assert data["status"] == "running"
        print("✅ Root endpoint working")
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
        return False
    
    # Test 3: API v1 status endpoint
    print("\n3. Testing API v1 status endpoint...")
    try:
        response = requests.get(f"{base_url}/api/v1/status", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["api_version"] == "v1"
        assert data["status"] == "ready"
        print("✅ API v1 status endpoint working")
    except Exception as e:
        print(f"❌ API v1 status endpoint failed: {e}")
        return False
    
    # Test 4: CORS headers
    print("\n4. Testing CORS headers...")
    try:
        headers = {"Origin": "http://localhost:5173"}
        response = requests.get(f"{base_url}/health", headers=headers, timeout=5)
        cors_header = response.headers.get("Access-Control-Allow-Origin")
        if cors_header:
            print(f"✅ CORS headers present: {cors_header}")
        else:
            print("⚠️ CORS headers not found (may be normal for simple requests)")
    except Exception as e:
        print(f"❌ CORS test failed: {e}")
        return False
    
    # Test 5: 404 handling
    print("\n5. Testing 404 handling...")
    try:
        response = requests.get(f"{base_url}/nonexistent", timeout=5)
        assert response.status_code == 404
        print("✅ 404 handling working")
    except Exception as e:
        print(f"❌ 404 handling failed: {e}")
        return False
    
    print("\n🎉 All tests passed!")
    return True

def run_server_test():
    """Run the server and test it"""
    print("🚀 Starting integration server for testing...")
    
    # Start server in background
    server_process = subprocess.Popen([
        sys.executable, "integration_server.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
        # Wait for server to start
        print("⏳ Waiting for server to start...")
        time.sleep(3)
        
        # Check if server is running
        if server_process.poll() is not None:
            stdout, stderr = server_process.communicate()
            print(f"❌ Server failed to start:")
            print(f"STDOUT: {stdout.decode()}")
            print(f"STDERR: {stderr.decode()}")
            return False
        
        # Run tests
        success = test_server_endpoints()
        
        return success
        
    finally:
        # Clean up server process
        print("\n🛑 Stopping server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
            server_process.wait()
        print("✅ Server stopped")

if __name__ == "__main__":
    success = run_server_test()
    sys.exit(0 if success else 1)