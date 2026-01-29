#!/usr/bin/env python3
"""
Unit tests for Subsidy Hunter Router
Tests Agent C (Subsidy Hunter) REST endpoints
Requirements: 1.3
"""

import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.routers.subsidy_hunter import router as subsidy_hunter_router
from mcp_bridge import MCPBridge, MCPBridgeError


@pytest.fixture
def app():
    """Create test FastAPI app with subsidy hunter router"""
    app = FastAPI()
    app.include_router(subsidy_hunter_router, prefix="/api/v1")
    
    # Mock MCP bridge
    mock_bridge = AsyncMock(spec=MCPBridge)
    app.state.mcp_bridge = mock_bridge
    
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_subsidy_response():
    """Mock subsidy response from MCP bridge"""
    return {
        "success": True,
        "result": "🎯 SUBSIDY OPPORTUNITIES FOUND for Textile Sector\n\nInvestment Amount: ₹50,00,000\nBusiness Profile: Sample Textile Ltd\n\nELIGIBLE SCHEMES:\n• Technology Upgradation Fund Scheme (TUFS): ₹12,50,000 (25% of machinery cost)\n• State Industrial Promotion Scheme: ₹5,00,000 (10% additional subsidy)\n• MSME Development Scheme: Interest subsidy on loans\n\n💰 TOTAL ESTIMATED BENEFIT: ₹17,50,000\n📊 Benefit Ratio: 35.0% of investment\n\n⚠️ NEXT STEPS:\n• Verify eligibility criteria in detail\n• Prepare required documentation\n• Submit applications before deadlines\n• Consult CA for compliance requirements"
    }


@pytest.fixture
def valid_subsidy_request():
    """Valid subsidy search request"""
    return {
        "sector": "textile",
        "capex_amount": 5000000.0,
        "location": "Maharashtra"
    }


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/api/v1/agents/subsidy-hunter/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["agent"] == "Subsidy Hunter (Agent C)"
    assert "/find-subsidies" in data["endpoints"]
    assert "timestamp" in data


class TestFindSubsidiesEndpoint:
    """Test cases for the find subsidies endpoint"""
    
    def test_successful_subsidy_search(self, client, app, mock_subsidy_response, valid_subsidy_request):
        """Test successful subsidy search with valid inputs"""
        # Configure mock to return successful response
        app.state.mcp_bridge.call_agent_c.return_value = mock_subsidy_response
        
        response = client.post("/api/v1/agents/subsidy-hunter/find-subsidies", json=valid_subsidy_request)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "subsidy_information" in data
        assert "processing_time" in data
        assert "sector_searched" in data
        assert "capex_amount_searched" in data
        
        # Verify response content
        assert data["sector_searched"] == "textile"
        assert data["capex_amount_searched"] == 5000000.0
        assert "SUBSIDY OPPORTUNITIES FOUND" in data["subsidy_information"]
        assert isinstance(data["processing_time"], float)
        assert data["processing_time"] >= 0
        
        # Verify MCP bridge was called correctly
        app.state.mcp_bridge.call_agent_c.assert_called_once_with(
            sector="textile",
            capex_amount=5000000.0
        )
    
    def test_various_sector_capex_combinations(self, client, app):
        """Test various sector and capex amount combinations"""
        test_cases = [
            {"sector": "manufacturing", "capex_amount": 1000000.0},
            {"sector": "food_processing", "capex_amount": 2500000.0},
            {"sector": "technology", "capex_amount": 10000000.0},
            {"sector": "automotive", "capex_amount": 50000000.0}
        ]
        
        for test_case in test_cases:
            # Mock successful response for each case
            mock_response = {
                "success": True,
                "result": f"Subsidy information for {test_case['sector']} sector with ₹{test_case['capex_amount']:,.0f} investment"
            }
            app.state.mcp_bridge.call_agent_c.return_value = mock_response
            
            response = client.post("/api/v1/agents/subsidy-hunter/find-subsidies", json=test_case)
            
            assert response.status_code == 200
            data = response.json()
            assert data["sector_searched"] == test_case["sector"]
            assert data["capex_amount_searched"] == test_case["capex_amount"]
    
    def test_input_validation_empty_sector(self, client):
        """Test input validation for empty sector"""
        invalid_request = {
            "sector": "",
            "capex_amount": 1000000.0
        }
        
        response = client.post("/api/v1/agents/subsidy-hunter/find-subsidies", json=invalid_request)
        
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data
        # Check that validation error mentions sector
        assert any("sector" in str(error).lower() for error in error_data["detail"])
    
    def test_input_validation_whitespace_sector(self, client):
        """Test input validation for whitespace-only sector"""
        invalid_request = {
            "sector": "   ",
            "capex_amount": 1000000.0
        }
        
        response = client.post("/api/v1/agents/subsidy-hunter/find-subsidies", json=invalid_request)
        
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data
    
    def test_input_validation_zero_capex(self, client):
        """Test input validation for zero capex amount"""
        invalid_request = {
            "sector": "textile",
            "capex_amount": 0.0
        }
        
        response = client.post("/api/v1/agents/subsidy-hunter/find-subsidies", json=invalid_request)
        
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data
        # Check that validation error mentions capex amount
        assert any("capex_amount" in str(error).lower() for error in error_data["detail"])
    
    def test_input_validation_negative_capex(self, client):
        """Test input validation for negative capex amount"""
        invalid_request = {
            "sector": "textile",
            "capex_amount": -1000000.0
        }
        
        response = client.post("/api/v1/agents/subsidy-hunter/find-subsidies", json=invalid_request)
        
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data
    
    def test_input_validation_excessive_capex(self, client):
        """Test input validation for excessive capex amount (over 1000 crores)"""
        invalid_request = {
            "sector": "textile",
            "capex_amount": 15000000000.0  # 1500 crores
        }
        
        response = client.post("/api/v1/agents/subsidy-hunter/find-subsidies", json=invalid_request)
        
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data
    
    def test_missing_required_fields(self, client):
        """Test validation when required fields are missing"""
        # Missing sector
        response = client.post("/api/v1/agents/subsidy-hunter/find-subsidies", json={"capex_amount": 1000000.0})
        assert response.status_code == 422
        
        # Missing capex_amount
        response = client.post("/api/v1/agents/subsidy-hunter/find-subsidies", json={"sector": "textile"})
        assert response.status_code == 422
        
        # Empty request
        response = client.post("/api/v1/agents/subsidy-hunter/find-subsidies", json={})
        assert response.status_code == 422
    
    def test_optional_location_field(self, client, app, mock_subsidy_response):
        """Test that location field is optional"""
        app.state.mcp_bridge.call_agent_c.return_value = mock_subsidy_response
        
        # Request without location
        request_without_location = {
            "sector": "textile",
            "capex_amount": 1000000.0
        }
        
        response = client.post("/api/v1/agents/subsidy-hunter/find-subsidies", json=request_without_location)
        assert response.status_code == 200
        
        # Request with location
        request_with_location = {
            "sector": "textile",
            "capex_amount": 1000000.0,
            "location": "Karnataka"
        }
        
        response = client.post("/api/v1/agents/subsidy-hunter/find-subsidies", json=request_with_location)
        assert response.status_code == 200
    
    def test_mcp_bridge_error_handling(self, client, app):
        """Test error handling when MCP bridge fails"""
        # Configure mock to raise MCPBridgeError
        app.state.mcp_bridge.call_agent_c.side_effect = MCPBridgeError("MCP tool execution failed")
        
        valid_request = {
            "sector": "textile",
            "capex_amount": 1000000.0
        }
        
        response = client.post("/api/v1/agents/subsidy-hunter/find-subsidies", json=valid_request)
        
        assert response.status_code == 500
        error_data = response.json()
        assert "detail" in error_data
        assert "Subsidy search failed" in error_data["detail"]
    
    def test_mcp_tool_failure_response(self, client, app):
        """Test handling when MCP tool returns failure response"""
        # Configure mock to return failure response
        failure_response = {
            "success": False,
            "error": "Database connection failed"
        }
        app.state.mcp_bridge.call_agent_c.return_value = failure_response
        
        valid_request = {
            "sector": "textile",
            "capex_amount": 1000000.0
        }
        
        response = client.post("/api/v1/agents/subsidy-hunter/find-subsidies", json=valid_request)
        
        assert response.status_code == 500
        error_data = response.json()
        assert "detail" in error_data
        assert "MCP tool execution failed" in error_data["detail"]
    
    def test_unexpected_exception_handling(self, client, app):
        """Test handling of unexpected exceptions"""
        # Configure mock to raise unexpected exception
        app.state.mcp_bridge.call_agent_c.side_effect = Exception("Unexpected error")
        
        valid_request = {
            "sector": "textile",
            "capex_amount": 1000000.0
        }
        
        response = client.post("/api/v1/agents/subsidy-hunter/find-subsidies", json=valid_request)
        
        assert response.status_code == 500
        error_data = response.json()
        assert "detail" in error_data
        assert "Internal server error" in error_data["detail"]
    
    def test_sector_normalization(self, client, app, mock_subsidy_response):
        """Test that sector input is normalized (trimmed and lowercased)"""
        app.state.mcp_bridge.call_agent_c.return_value = mock_subsidy_response
        
        # Test with uppercase and whitespace
        request = {
            "sector": "  TEXTILE  ",
            "capex_amount": 1000000.0
        }
        
        response = client.post("/api/v1/agents/subsidy-hunter/find-subsidies", json=request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["sector_searched"] == "textile"  # Should be normalized
        
        # Verify MCP bridge was called with normalized sector
        app.state.mcp_bridge.call_agent_c.assert_called_with(
            sector="textile",
            capex_amount=1000000.0
        )
    
    def test_response_format_consistency(self, client, app, mock_subsidy_response):
        """Test that response format is consistent"""
        app.state.mcp_bridge.call_agent_c.return_value = mock_subsidy_response
        
        valid_request = {
            "sector": "manufacturing",
            "capex_amount": 2500000.0
        }
        
        response = client.post("/api/v1/agents/subsidy-hunter/find-subsidies", json=valid_request)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all required fields are present
        required_fields = ["subsidy_information", "processing_time", "sector_searched", "capex_amount_searched"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Verify field types
        assert isinstance(data["subsidy_information"], str)
        assert isinstance(data["processing_time"], (int, float))
        assert isinstance(data["sector_searched"], str)
        assert isinstance(data["capex_amount_searched"], (int, float))
    
    def test_large_sector_name_handling(self, client, app, mock_subsidy_response):
        """Test handling of very long sector names"""
        app.state.mcp_bridge.call_agent_c.return_value = mock_subsidy_response
        
        # Test with maximum allowed length (100 characters)
        long_sector = "a" * 100
        request = {
            "sector": long_sector,
            "capex_amount": 1000000.0
        }
        
        response = client.post("/api/v1/agents/subsidy-hunter/find-subsidies", json=request)
        assert response.status_code == 200
        
        # Test with over maximum length (should fail validation)
        too_long_sector = "a" * 101
        request = {
            "sector": too_long_sector,
            "capex_amount": 1000000.0
        }
        
        response = client.post("/api/v1/agents/subsidy-hunter/find-subsidies", json=request)
        assert response.status_code == 422