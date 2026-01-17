#!/usr/bin/env python3
"""
Unit tests for Legal Sentinel Router
Tests Agent B (Legal Sentinel) REST endpoints
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from routers.legal_sentinel import router as legal_sentinel_router
from mcp_bridge import MCPBridge, MCPBridgeError


@pytest.fixture
def app():
    """Create test FastAPI app with legal sentinel router"""
    app = FastAPI()
    app.include_router(legal_sentinel_router, prefix="/api/v1")
    
    # Mock MCP bridge
    mock_bridge = AsyncMock(spec=MCPBridge)
    app.state.mcp_bridge = mock_bridge
    
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_legal_risk_response():
    """Mock legal risk response from MCP bridge"""
    return {
        "success": True,
        "result": {
            "risk_level": "Medium",
            "relevant_section": "Section 17(5) of CGST Act",
            "compliant_action": "ITC blocked for personal use items. Ensure proper documentation."
        }
    }


class TestLegalSentinelRouter:
    """Test cases for Legal Sentinel router endpoints"""
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/api/v1/agents/legal-sentinel/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["agent"] == "Legal Sentinel (Agent B)"
        assert "/check-compliance" in data["endpoints"]
        assert "timestamp" in data
    
    def test_check_compliance_success(self, client, app, mock_legal_risk_response):
        """Test successful compliance check"""
        # Setup mock
        app.state.mcp_bridge.call_agent_b.return_value = mock_legal_risk_response
        
        # Make request
        request_data = {
            "query": "Can I claim Input Tax Credit on office lunch expenses?",
            "user_context": "Small business with turnover < 5Cr"
        }
        
        response = client.post("/api/v1/agents/legal-sentinel/check-compliance", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["risk_level"] == "Medium"
        assert data["relevant_section"] == "Section 17(5) of CGST Act"
        assert "ITC blocked" in data["compliant_action"]
        assert "processing_time" in data
        assert isinstance(data["processing_time"], float)
        
        # Verify MCP bridge was called correctly
        app.state.mcp_bridge.call_agent_b.assert_called_once_with(
            query="Can I claim Input Tax Credit on office lunch expenses?",
            user_context="Small business with turnover < 5Cr"
        )
    
    def test_check_compliance_minimal_request(self, client, app, mock_legal_risk_response):
        """Test compliance check with minimal request (no user_context)"""
        # Setup mock
        app.state.mcp_bridge.call_agent_b.return_value = mock_legal_risk_response
        
        # Make request with only required field
        request_data = {
            "query": "What is the GST rate for textiles?"
        }
        
        response = client.post("/api/v1/agents/legal-sentinel/check-compliance", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["risk_level"] == "Medium"
        
        # Verify MCP bridge was called with empty user_context
        app.state.mcp_bridge.call_agent_b.assert_called_once_with(
            query="What is the GST rate for textiles?",
            user_context=""
        )
    
    def test_check_compliance_various_risk_levels(self, client, app):
        """Test compliance check with various risk levels"""
        test_cases = [
            {
                "risk_level": "Low",
                "relevant_section": "Section 2(47) of CGST Act",
                "compliant_action": "Standard GST rate applies. No special compliance required."
            },
            {
                "risk_level": "High", 
                "relevant_section": "Section 132 of CGST Act",
                "compliant_action": "Penalty provisions apply. Immediate rectification required."
            }
        ]
        
        for i, expected_result in enumerate(test_cases):
            # Setup mock for this iteration
            mock_response = {
                "success": True,
                "result": expected_result
            }
            app.state.mcp_bridge.call_agent_b.return_value = mock_response
            
            # Make request
            request_data = {
                "query": f"Test query {i+1}",
                "user_context": f"Test context {i+1}"
            }
            
            response = client.post("/api/v1/agents/legal-sentinel/check-compliance", json=request_data)
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["risk_level"] == expected_result["risk_level"]
            assert data["relevant_section"] == expected_result["relevant_section"]
            assert data["compliant_action"] == expected_result["compliant_action"]
    
    def test_check_compliance_invalid_requests(self, client):
        """Test compliance check with invalid request data"""
        invalid_requests = [
            # Missing query
            {"user_context": "Some context"},
            # Empty query
            {"query": "", "user_context": "Some context"},
            # Query too long (over 1000 chars)
            {"query": "x" * 1001, "user_context": "Some context"},
            # Invalid JSON
            "invalid json"
        ]
        
        for invalid_request in invalid_requests[:-1]:  # Skip the string case for JSON requests
            response = client.post("/api/v1/agents/legal-sentinel/check-compliance", json=invalid_request)
            assert response.status_code == 422  # Validation error
    
    def test_check_compliance_mcp_bridge_error(self, client, app):
        """Test compliance check when MCP bridge fails"""
        # Setup mock to raise MCPBridgeError
        app.state.mcp_bridge.call_agent_b.side_effect = MCPBridgeError("Vector database connection failed")
        
        # Make request
        request_data = {
            "query": "Test query that will fail",
            "user_context": "Test context"
        }
        
        response = client.post("/api/v1/agents/legal-sentinel/check-compliance", json=request_data)
        
        # Verify error response
        assert response.status_code == 500
        data = response.json()
        assert "Legal compliance check failed" in data["detail"]
        assert "Vector database connection failed" in data["detail"]
    
    def test_check_compliance_mcp_tool_failure(self, client, app):
        """Test compliance check when MCP tool returns failure"""
        # Setup mock to return failure
        mock_response = {
            "success": False,
            "error": "Tool execution failed"
        }
        app.state.mcp_bridge.call_agent_b.return_value = mock_response
        
        # Make request
        request_data = {
            "query": "Test query",
            "user_context": "Test context"
        }
        
        response = client.post("/api/v1/agents/legal-sentinel/check-compliance", json=request_data)
        
        # Verify error response
        assert response.status_code == 500
        data = response.json()
        assert "MCP tool execution failed" in data["detail"]
        assert "Tool execution failed" in data["detail"]
    
    def test_check_compliance_unexpected_error(self, client, app):
        """Test compliance check with unexpected error"""
        # Setup mock to raise unexpected exception
        app.state.mcp_bridge.call_agent_b.side_effect = Exception("Unexpected error occurred")
        
        # Make request
        request_data = {
            "query": "Test query",
            "user_context": "Test context"
        }
        
        response = client.post("/api/v1/agents/legal-sentinel/check-compliance", json=request_data)
        
        # Verify error response
        assert response.status_code == 500
        data = response.json()
        assert "Internal server error" in data["detail"]
    
    def test_check_compliance_user_context_variations(self, client, app, mock_legal_risk_response):
        """Test compliance check with various user context scenarios"""
        # Setup mock
        app.state.mcp_bridge.call_agent_b.return_value = mock_legal_risk_response
        
        user_contexts = [
            "",  # Empty context
            "Manufacturing company, turnover 15Cr, Regular GST registration",  # Detailed context
            "Textile business",  # Simple context
            "New startup, no GST registration yet"  # Startup context
        ]
        
        for user_context in user_contexts:
            request_data = {
                "query": "GST compliance query",
                "user_context": user_context
            }
            
            response = client.post("/api/v1/agents/legal-sentinel/check-compliance", json=request_data)
            
            # Verify successful response regardless of context
            assert response.status_code == 200
            data = response.json()
            assert "risk_level" in data
            assert "relevant_section" in data
            assert "compliant_action" in data
    
    def test_check_compliance_query_variations(self, client, app, mock_legal_risk_response):
        """Test compliance check with various query types"""
        # Setup mock
        app.state.mcp_bridge.call_agent_b.return_value = mock_legal_risk_response
        
        queries = [
            "Can I claim ITC on office expenses?",  # ITC query
            "What is the GST rate for software services?",  # Rate query
            "Do I need to file GSTR-1 monthly?",  # Filing query
            "Is reverse charge applicable on legal services?",  # Reverse charge query
            "What are the penalties for late GST return filing?"  # Penalty query
        ]
        
        for query in queries:
            request_data = {
                "query": query,
                "user_context": "Test business"
            }
            
            response = client.post("/api/v1/agents/legal-sentinel/check-compliance", json=request_data)
            
            # Verify successful response for all query types
            assert response.status_code == 200
            data = response.json()
            assert data["risk_level"] in ["Low", "Medium", "High"]
            assert len(data["relevant_section"]) > 0
            assert len(data["compliant_action"]) > 0


def run_tests():
    """Run all tests"""
    print("🧪 Running Legal Sentinel Router Tests...")
    
    # Run pytest with verbose output
    import subprocess
    import sys
    
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "test_legal_sentinel_router.py", 
        "-v", "--tb=short"
    ], capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)