#!/usr/bin/env python3
"""
Quick Test Script for P0 Priorities
Tests authentication, dashboard, and basic API connectivity
"""

import requests
import json
import sys
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

# Test user credentials
TEST_USER = {
    "email": "test@example.com",
    "password": "test1234",
    "full_name": "Test User",
    "company_name": "Test Corp Pvt Ltd"
}


def print_section(title):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}\n")


def test_health_check():
    """Test 1: Health check endpoint"""
    print_section("Test 1: Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/health")
        response.raise_for_status()
        
        print("✅ Health check passed")
        print(f"   Response: {response.json()}")
        return True
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_register_user():
    """Test 2: User registration"""
    print_section("Test 2: User Registration")
    
    try:
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/register",
            json=TEST_USER
        )
        
        if response.status_code == 400:
            print("⚠️  User already exists (this is OK)")
            return True
            
        response.raise_for_status()
        data = response.json()
        
        print("✅ Registration successful")
        print(f"   User ID: {data.get('user_id')}")
        print(f"   Email: {data.get('email')}")
        print(f"   Token: {data.get('access_token')[:50]}...")
        
        return data.get('access_token')
        
    except Exception as e:
        print(f"❌ Registration failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return None


def test_login_user():
    """Test 3: User login"""
    print_section("Test 3: User Login")
    
    try:
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            json={
                "email": TEST_USER["email"],
                "password": TEST_USER["password"]
            }
        )
        
        response.raise_for_status()
        data = response.json()
        
        print("✅ Login successful")
        print(f"   User ID: {data.get('user', {}).get('user_id')}")
        print(f"   Business: {data.get('user', {}).get('business_name')}")
        print(f"   Token: {data.get('access_token')[:50]}...")
        
        return data.get('access_token')
        
    except Exception as e:
        print(f"❌ Login failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return None


def test_get_profile(token):
    """Test 4: Get user profile"""
    print_section("Test 4: Get User Profile")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/auth/profile",
            headers=headers
        )
        
        response.raise_for_status()
        data = response.json()
        
        print("✅ Profile retrieved")
        print(f"   Email: {data.get('email')}")
        print(f"   Company: {data.get('company_name')}")
        print(f"   Role: {data.get('role')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Profile retrieval failed: {e}")
        return False


def test_dashboard_metrics(token):
    """Test 5: Dashboard metrics"""
    print_section("Test 5: Dashboard Metrics")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/dashboard/metrics",
            headers=headers
        )
        
        response.raise_for_status()
        data = response.json()
        
        print("✅ Dashboard metrics retrieved")
        if data.get('success'):
            metrics = data.get('data', {}).get('metrics', {})
            print(f"   Total Invoices: {metrics.get('totalInvoices', 0)}")
            print(f"   Compliance Score: {metrics.get('complianceScore', 0)}%")
            print(f"   Subsidies Found: {metrics.get('subsidiesFound', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Dashboard metrics failed: {e}")
        return False


def test_dashboard_summary(token):
    """Test 6: Complete dashboard summary"""
    print_section("Test 6: Complete Dashboard Summary")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/dashboard/summary",
            headers=headers
        )
        
        response.raise_for_status()
        data = response.json()
        
        print("✅ Dashboard summary retrieved")
        if data.get('success'):
            summary = data.get('data', {})
            print(f"   Metrics: {len(summary.get('metrics', {}))} fields")
            print(f"   Recent Invoices: {len(summary.get('recentInvoices', []))}")
            print(f"   Compliance Alerts: {len(summary.get('complianceAlerts', []))}")
            print(f"   Subsidy Matches: {len(summary.get('subsidyMatches', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Dashboard summary failed: {e}")
        return False


def test_chat_agents():
    """Test 7: Chat/Agents endpoint"""
    print_section("Test 7: Available Agents")
    
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/chat/agents")
        response.raise_for_status()
        data = response.json()
        
        print("✅ Agents list retrieved")
        if data.get('success'):
            agents = data.get('data', {}).get('agents', {})
            print(f"   Available agents: {len(agents)}")
            for agent_id, agent_info in agents.items():
                print(f"   - {agent_id}: {agent_info.get('name')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agents list failed: {e}")
        return False


def run_all_tests():
    """Run all P0 tests"""
    print("\n" + "="*60)
    print("🚀 MicroCFO P0 Priority Test Suite")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print(f"API Prefix: {API_PREFIX}")
    
    results = {
        "health": False,
        "register": False,
        "login": False,
        "profile": False,
        "dashboard": False,
        "summary": False,
        "agents": False
    }
    
    # Test 1: Health check
    results["health"] = test_health_check()
    
    if not results["health"]:
        print("\n⚠️  Backend server is not running!")
        print("   Start it with: python main.py")
        return results
    
    # Test 2: Registration
    register_token = test_register_user()
    results["register"] = register_token is not None
    
    # Test 3: Login
    login_token = test_login_user()
    results["login"] = login_token is not None
    
    # Use login token for remaining tests
    token = login_token or register_token
    
    if token:
        # Test 4: Profile
        results["profile"] = test_get_profile(token)
        
        # Test 5: Dashboard metrics
        results["dashboard"] = test_dashboard_metrics(token)
        
        # Test 6: Dashboard summary
        results["summary"] = test_dashboard_summary(token)
    
    # Test 7: Agents (no auth required)
    results["agents"] = test_chat_agents()
    
    # Print summary
    print_section("Test Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All P0 priorities are working correctly!")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
    
    return results


if __name__ == "__main__":
    try:
        results = run_all_tests()
        sys.exit(0 if all(results.values()) else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
