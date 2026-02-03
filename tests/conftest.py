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
