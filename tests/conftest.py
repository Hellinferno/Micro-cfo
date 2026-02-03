"""
Shared pytest fixtures for all tests
Provides common setup including mock MCP bridge initialization
"""

import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock

# Ensure the project root is in the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
# Also add src directory for server imports
src_dir = os.path.join(project_root, 'src')
sys.path.insert(0, src_dir)


@pytest.fixture(autouse=True)
def mock_mcp_bridge_for_integration_tests():
    """
    Auto-use fixture to mock MCP bridge for integration tests.
    This ensures that any test using the main app has a properly initialized MCP bridge.
    """
    try:
        from integration_server import app
        from mcp_bridge import MCPBridge
        
        # Only set up if not already mocked by a more specific fixture
        if not hasattr(app.state, 'mcp_bridge') or app.state.mcp_bridge is None:
            mock_bridge = AsyncMock(spec=MCPBridge)
            
            # Setup default return values for common operations
            mock_bridge.call_agent_a.return_value = {
                "success": True,
                "result": {
                    "vendor_name": "Test Vendor",
                    "invoice_date": "2024-01-15",
                    "total_amount": 50000.0,
                    "tax_amount": 9000.0,
                    "line_items": [],
                    "gstin": "27AAAAA0000A1Z5",
                    "is_handwritten": False,
                    "tampering_detected": False,
                    "compliance_flags": [],
                    "confidence_score": 0.95
                }
            }
            
            mock_bridge.call_agent_b.return_value = {
                "success": True,
                "result": {
                    "risk_level": "LOW",
                    "relevant_section": "GST Act Section 16",
                    "compliant_action": "Maintain proper documentation"
                }
            }
            
            mock_bridge.call_agent_c.return_value = {
                "success": True,
                "result": "Found 2 applicable schemes for your sector"
            }
            
            mock_bridge.call_agent_d.return_value = {
                "success": True,
                "result": {
                    "intent": "credit_extension",
                    "strategy_explanation": "Requesting payment extension",
                    "whatsapp_message": "Hi, need payment extension",
                    "formal_email": "Dear Team, We request an extension",
                    "option_a": "Option A content",
                    "option_b": "Option B content"
                }
            }
            
            app.state.mcp_bridge = mock_bridge
            
        yield app.state.mcp_bridge
        
        # Cleanup
        if hasattr(app.state, 'mcp_bridge'):
            app.state.mcp_bridge = None
            
    except ImportError:
        # If integration_server can't be imported, just yield None
        yield None


@pytest.fixture
def mock_mcp_bridge():
    """
    Explicit fixture for tests that need a fresh mock MCP bridge.
    Use this when you need to customize the mock behavior.
    """
    from mcp_bridge import MCPBridge
    
    mock_bridge = AsyncMock(spec=MCPBridge)
    
    # Setup default return values
    mock_bridge.call_agent_a.return_value = {
        "success": True,
        "result": {
            "vendor_name": "Test Vendor",
            "invoice_date": "2024-01-15",
            "total_amount": 50000.0,
            "tax_amount": 9000.0,
            "line_items": [],
            "gstin": "27AAAAA0000A1Z5",
            "is_handwritten": False,
            "tampering_detected": False,
            "compliance_flags": [],
            "confidence_score": 0.95
        }
    }
    
    mock_bridge.call_agent_b.return_value = {
        "success": True,
        "result": {
            "risk_level": "LOW",
            "relevant_section": "GST Act Section 16",
            "compliant_action": "Maintain proper documentation"
        }
    }
    
    mock_bridge.call_agent_c.return_value = {
        "success": True,
        "result": "Found 2 applicable schemes for your sector"
    }
    
    mock_bridge.call_agent_d.return_value = {
        "success": True,
        "result": {
            "intent": "credit_extension",
            "strategy_explanation": "Requesting payment extension",
            "whatsapp_message": "Hi, need payment extension",
            "formal_email": "Dear Team, We request an extension",
            "option_a": "Option A content",
            "option_b": "Option B content"
        }
    }
    
    return mock_bridge


@pytest.fixture
def client():
    """
    Test client fixture for API integration tests.
    Provides a FastAPI TestClient with proper MCP bridge initialization.
    """
    from fastapi.testclient import TestClient
    from integration_server import app
    from mcp_bridge import MCPBridge
    
    # Ensure MCP bridge is initialized
    if not hasattr(app.state, 'mcp_bridge') or app.state.mcp_bridge is None:
        mock_bridge = AsyncMock(spec=MCPBridge)
        mock_bridge.call_agent_a.return_value = {"success": True, "result": {}}
        mock_bridge.call_agent_b.return_value = {"success": True, "result": {}}
        mock_bridge.call_agent_c.return_value = {"success": True, "result": ""}
        mock_bridge.call_agent_d.return_value = {"success": True, "result": {}}
        app.state.mcp_bridge = mock_bridge
    
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def legal_chunks():
    """
    Test chunks fixture for vector database tests.
    Provides sample legal chunks for testing.
    """
    from legal_ingestion import LegalChunk
    
    return [
        LegalChunk(
            text="Test chunk 1 for GST compliance",
            law_type="GST",
            section_number="1",
            source_file="test_doc.pdf",
            file_hash="abc123"
        ),
        LegalChunk(
            text="Test chunk 2 for Income Tax",
            law_type="Income Tax",
            section_number="2",
            source_file="test_doc.pdf",
            file_hash="abc123"
        ),
        LegalChunk(
            text="Test chunk 3 for Corporate Law",
            law_type="Corporate Law",
            section_number="3",
            source_file="test_doc.pdf",
            file_hash="abc123"
        )
    ]


@pytest.fixture
def chunks():
    """
    Test chunks fixture for scheme database tests.
    Provides sample scheme chunks for testing.
    This fixture is used by test_scheme_database in test_subsidy_hunter.py
    """
    from scheme_ingestion import SchemeChunk
    
    return [
        SchemeChunk(
            text="PMFME provides capital subsidy @ 35% of eligible project cost for food processing units",
            scheme_name="PMFME",
            target_sector="food_processing",
            min_investment=200000,
            max_investment=1000000,
            benefit_type="capital_subsidy",
            benefit_percentage=35.0,
            max_benefit_amount=1000000,
            chunk_type="quantum"
        ),
        SchemeChunk(
            text="TUFS provides interest subvention for textile manufacturing units",
            scheme_name="TUFS",
            target_sector="textile",
            min_investment=1000000,
            max_investment=100000000,
            benefit_type="interest_subvention",
            benefit_percentage=5.0,
            max_benefit_amount=5000000,
            chunk_type="eligibility"
        ),
        SchemeChunk(
            text="MSME Credit Guarantee scheme provides collateral-free loans for manufacturing sector",
            scheme_name="CGTMSE",
            target_sector="manufacturing",
            min_investment=100000,
            max_investment=20000000,
            benefit_type="credit_guarantee",
            benefit_percentage=85.0,
            max_benefit_amount=20000000,
            chunk_type="eligibility"
        )
    ]
