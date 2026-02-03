#!/usr/bin/env python3
"""
Unit tests for Negotiator Router
Tests Agent D (Negotiator) REST endpoints
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from routers.negotiator import router as negotiator_router
from mcp_bridge import MCPBridge, MCPBridgeError


@pytest.fixture
def app():
    """Create test FastAPI app with negotiator router"""
    app = FastAPI()
    app.include_router(negotiator_router, prefix="/api/v1")
    
    # Mock MCP bridge
    mock_bridge = AsyncMock(spec=MCPBridge)
    app.state.mcp_bridge = mock_bridge
    
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_negotiation_response():
    """Mock negotiation draft response from MCP bridge"""
    return {
        "success": True,
        "result": {
            "intent": "credit_extension",
            "strategy_explanation": "Cash flow analysis shows insufficient funds. Requesting payment extension to maintain vendor relationships while managing liquidity.",
            "whatsapp_message": "Hi ABC Suppliers, need 15 days for Invoice #INV-001 payment. Cash flow timing issue. Thanks for understanding! 🙏",
            "formal_email": "Dear ABC Suppliers Team,\n\nWe value our partnership and need to request a 15-day extension for Invoice #INV-001 (₹50,000.00) due to temporary cash flow timing. We'll process payment by 2024-02-15. Thank you for your continued support.\n\nBest regards,\nFinance Team",
            "option_a": "RELATIONSHIP-FOCUSED:\nWhatsApp: Hi ABC Suppliers, need 15 days for Invoice #INV-001 payment. Cash flow timing issue. Thanks for understanding! 🙏\n\nEmail:\nDear ABC Suppliers Team,\n\nWe value our partnership and need to request a 15-day extension for Invoice #INV-001 (₹50,000.00) due to temporary cash flow timing. We'll process payment by 2024-02-15. Thank you for your continued support.\n\nBest regards,\nFinance Team",
            "option_b": "TRANSACTIONAL-FOCUSED:\nWhatsApp: ABC Suppliers, requesting payment extension for Invoice #INV-001 till 2024-02-15. Will confirm exact date by tomorrow.\n\nEmail:\nSubject: Payment Extension Request - Invoice #INV-001\n\nDear Sir/Madam,\n\nWe request a 15-day extension for payment of Invoice #INV-001 amounting to ₹50,000.00. New payment date: 2024-02-15.\n\nRegards,\nAccounts Department"
        }
    }


class TestNegotiatorRouter:
    """Test cases for Negotiator router endpoints"""
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/api/v1/agents/negotiator/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["agent"] == "Negotiator (Agent D)"
        assert "/generate-draft" in data["endpoints"]
        assert "timestamp" in data
    
    def test_generate_draft_success_credit_extension(self, client, app, mock_negotiation_response):
        """Test successful negotiation draft generation for credit extension"""
        # Setup mock
        app.state.mcp_bridge.call_agent_d.return_value = mock_negotiation_response
        
        # Make request
        request_data = {
            "counterparty_name": "ABC Suppliers",
            "amount": 50000.0,
            "transaction_type": "payable",
            "due_date": "2024-01-31",
            "current_cash_position": 30000.0,
            "upcoming_outflows": 25000.0,
            "invoice_id": "INV-001"
        }
        
        response = client.post("/api/v1/agents/negotiator/generate-draft", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "credit_extension"
        assert "Cash flow analysis" in data["strategy_explanation"]
        assert len(data["whatsapp_message"]) > 0
        assert len(data["formal_email"]) > 0
        assert "RELATIONSHIP-FOCUSED" in data["option_a"]
        assert "TRANSACTIONAL-FOCUSED" in data["option_b"]
        assert "processing_time" in data
        assert isinstance(data["processing_time"], float)
        
        # Verify MCP bridge was called correctly
        app.state.mcp_bridge.call_agent_d.assert_called_once_with(
            counterparty_name="ABC Suppliers",
            amount=50000.0,
            transaction_type="payable",
            due_date="2024-01-31",
            current_cash_position=30000.0,
            upcoming_outflows=25000.0,
            invoice_id="INV-001",
            vendor_context={}
        )
    
    def test_generate_draft_payment_chase(self, client, app):
        """Test negotiation draft generation for payment chase"""
        # Setup mock for payment chase scenario
        mock_response = {
            "success": True,
            "result": {
                "intent": "payment_chase",
                "strategy_explanation": "Payment is overdue. Following up professionally to maintain cash flow while preserving business relationship.",
                "whatsapp_message": "Hi XYZ Corp, gentle reminder for Invoice #INV-002 payment. Let us know if any clarification needed. Thanks! 😊",
                "formal_email": "Dear XYZ Corp Team,\n\nI hope you're doing well. This is a friendly reminder regarding Invoice #INV-002 for ₹75,000.00 which was due on 2024-01-15. Please let us know if you need any clarification.\n\nBest regards,\nFinance Team",
                "option_a": "RELATIONSHIP-FOCUSED:\nWhatsApp: Hi XYZ Corp, gentle reminder for Invoice #INV-002 payment. Let us know if any clarification needed. Thanks! 😊\n\nEmail:\nDear XYZ Corp Team,\n\nI hope you're doing well. This is a friendly reminder regarding Invoice #INV-002 for ₹75,000.00 which was due on 2024-01-15. Please let us know if you need any clarification.\n\nBest regards,\nFinance Team",
                "option_b": "TRANSACTIONAL-FOCUSED:\nWhatsApp: XYZ Corp, Invoice #INV-002 payment overdue. Please process immediately or confirm payment date.\n\nEmail:\nSubject: Overdue Payment - Invoice #INV-002\n\nDear Sir/Madam,\n\nThis is to inform you that payment for Invoice #INV-002 amounting to ₹75,000.00 is overdue. Please process the payment immediately.\n\nRegards,\nAccounts Department"
            }
        }
        app.state.mcp_bridge.call_agent_d.return_value = mock_response
        
        # Make request for receivable (they owe us)
        request_data = {
            "counterparty_name": "XYZ Corp",
            "amount": 75000.0,
            "transaction_type": "receivable",
            "due_date": "2024-01-15",
            "current_cash_position": 100000.0,
            "upcoming_outflows": 50000.0,
            "invoice_id": "INV-002"
        }
        
        response = client.post("/api/v1/agents/negotiator/generate-draft", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "payment_chase"
        assert "overdue" in data["strategy_explanation"].lower() or "following up" in data["strategy_explanation"].lower()
        assert len(data["whatsapp_message"]) > 0
        assert len(data["formal_email"]) > 0
    
    def test_generate_draft_early_payment_offer(self, client, app):
        """Test negotiation draft generation for early payment offer"""
        # Setup mock for early payment offer scenario
        mock_response = {
            "success": True,
            "result": {
                "intent": "early_payment_offer",
                "strategy_explanation": "Strong cash position detected. Offering early payment with discount to optimize working capital and strengthen vendor relationships.",
                "whatsapp_message": "Hi DEF Vendors, can offer early payment for Invoice #INV-003 with 2% discount. Win-win for both! Let me know 😊",
                "formal_email": "Dear DEF Vendors Team,\n\nWe have good cash flow this month and would like to offer early payment for Invoice #INV-003 (₹100,000.00) in exchange for a 2% early payment discount (₹2,000.00).\n\nBest regards,\nFinance Team",
                "option_a": "RELATIONSHIP-FOCUSED:\nWhatsApp: Hi DEF Vendors, can offer early payment for Invoice #INV-003 with 2% discount. Win-win for both! Let me know 😊\n\nEmail:\nDear DEF Vendors Team,\n\nWe have good cash flow this month and would like to offer early payment for Invoice #INV-003 (₹100,000.00) in exchange for a 2% early payment discount (₹2,000.00).\n\nBest regards,\nFinance Team",
                "option_b": "TRANSACTIONAL-FOCUSED:\nWhatsApp: DEF Vendors, offering immediate payment for Invoice #INV-003 less 2% discount. Confirm if acceptable.\n\nEmail:\nSubject: Early Payment Offer - Invoice #INV-003\n\nDear Sir/Madam,\n\nWe offer immediate payment for Invoice #INV-003 (₹100,000.00) with 2% early payment discount. Net payment: ₹98,000.00.\n\nRegards,\nAccounts Department"
            }
        }
        app.state.mcp_bridge.call_agent_d.return_value = mock_response
        
        # Make request with strong cash position
        request_data = {
            "counterparty_name": "DEF Vendors",
            "amount": 100000.0,
            "transaction_type": "payable",
            "due_date": "2024-02-28",
            "current_cash_position": 500000.0,
            "upcoming_outflows": 50000.0,
            "invoice_id": "INV-003"
        }
        
        response = client.post("/api/v1/agents/negotiator/generate-draft", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "early_payment_offer"
        assert "cash position" in data["strategy_explanation"].lower() or "early payment" in data["strategy_explanation"].lower()
    
    def test_generate_draft_minimal_request(self, client, app, mock_negotiation_response):
        """Test negotiation draft with minimal request (no optional fields)"""
        # Setup mock
        app.state.mcp_bridge.call_agent_d.return_value = mock_negotiation_response
        
        # Make request with only required fields
        request_data = {
            "counterparty_name": "Test Vendor",
            "amount": 25000.0,
            "transaction_type": "payable",
            "due_date": "2024-02-15",
            "current_cash_position": 50000.0
        }
        
        response = client.post("/api/v1/agents/negotiator/generate-draft", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "intent" in data
        assert "strategy_explanation" in data
        
        # Verify MCP bridge was called with defaults
        app.state.mcp_bridge.call_agent_d.assert_called_once()
        call_args = app.state.mcp_bridge.call_agent_d.call_args[1]
        assert call_args["upcoming_outflows"] == 0
        assert call_args["invoice_id"] is None
    
    def test_generate_draft_various_contexts_and_tones(self, client, app):
        """Test negotiation draft with various contexts and tones"""
        test_cases = [
            {
                "counterparty_name": "Small Vendor Ltd",
                "amount": 10000.0,
                "transaction_type": "payable",
                "expected_intent": "credit_extension"
            },
            {
                "counterparty_name": "Large Corporation Inc",
                "amount": 500000.0,
                "transaction_type": "receivable",
                "expected_intent": "payment_chase"
            },
            {
                "counterparty_name": "Regular Supplier Co",
                "amount": 75000.0,
                "transaction_type": "payable",
                "expected_intent": "early_payment_offer"
            }
        ]
        
        for test_case in test_cases:
            # Setup mock for this iteration
            mock_response = {
                "success": True,
                "result": {
                    "intent": test_case["expected_intent"],
                    "strategy_explanation": f"Strategy for {test_case['expected_intent']}",
                    "whatsapp_message": f"WhatsApp message for {test_case['counterparty_name']}",
                    "formal_email": f"Formal email for {test_case['counterparty_name']}",
                    "option_a": "Option A content",
                    "option_b": "Option B content"
                }
            }
            app.state.mcp_bridge.call_agent_d.return_value = mock_response
            
            # Make request
            request_data = {
                "counterparty_name": test_case["counterparty_name"],
                "amount": test_case["amount"],
                "transaction_type": test_case["transaction_type"],
                "due_date": "2024-02-15",
                "current_cash_position": 100000.0
            }
            
            response = client.post("/api/v1/agents/negotiator/generate-draft", json=request_data)
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["intent"] == test_case["expected_intent"]
            assert test_case["counterparty_name"] in data["whatsapp_message"] or test_case["counterparty_name"] in data["formal_email"]
    
    def test_generate_draft_invalid_requests(self, client):
        """Test negotiation draft with invalid request data"""
        invalid_requests = [
            # Missing required fields
            {
                "amount": 50000.0,
                "transaction_type": "payable",
                "due_date": "2024-02-15",
                "current_cash_position": 30000.0
            },
            # Empty counterparty name
            {
                "counterparty_name": "",
                "amount": 50000.0,
                "transaction_type": "payable",
                "due_date": "2024-02-15",
                "current_cash_position": 30000.0
            },
            # Invalid amount (negative)
            {
                "counterparty_name": "Test Vendor",
                "amount": -50000.0,
                "transaction_type": "payable",
                "due_date": "2024-02-15",
                "current_cash_position": 30000.0
            },
            # Invalid amount (zero)
            {
                "counterparty_name": "Test Vendor",
                "amount": 0,
                "transaction_type": "payable",
                "due_date": "2024-02-15",
                "current_cash_position": 30000.0
            },
            # Invalid transaction type
            {
                "counterparty_name": "Test Vendor",
                "amount": 50000.0,
                "transaction_type": "invalid_type",
                "due_date": "2024-02-15",
                "current_cash_position": 30000.0
            },
            # Invalid due date format
            {
                "counterparty_name": "Test Vendor",
                "amount": 50000.0,
                "transaction_type": "payable",
                "due_date": "31-01-2024",
                "current_cash_position": 30000.0
            },
            # Negative cash position
            {
                "counterparty_name": "Test Vendor",
                "amount": 50000.0,
                "transaction_type": "payable",
                "due_date": "2024-02-15",
                "current_cash_position": -10000.0
            },
            # Amount exceeds maximum limit
            {
                "counterparty_name": "Test Vendor",
                "amount": 200000000000.0,  # 20,000 crores
                "transaction_type": "payable",
                "due_date": "2024-02-15",
                "current_cash_position": 30000.0
            }
        ]
        
        for invalid_request in invalid_requests:
            response = client.post("/api/v1/agents/negotiator/generate-draft", json=invalid_request)
            assert response.status_code == 422  # Validation error
    
    def test_generate_draft_mcp_bridge_error(self, client, app):
        """Test negotiation draft when MCP bridge fails"""
        # Setup mock to raise MCPBridgeError
        app.state.mcp_bridge.call_agent_d.side_effect = MCPBridgeError("AI model connection failed")
        
        # Make request
        request_data = {
            "counterparty_name": "Test Vendor",
            "amount": 50000.0,
            "transaction_type": "payable",
            "due_date": "2024-02-15",
            "current_cash_position": 30000.0
        }
        
        response = client.post("/api/v1/agents/negotiator/generate-draft", json=request_data)
        
        # Verify error response (500 or 503 if MCP bridge not available)
        assert response.status_code in [500, 503]
        data = response.json()
        # Check for error indicators in the response
        detail = data.get("detail", "").lower()
        assert any(word in detail for word in ["failed", "error", "unavailable", "mcp"])
    
    def test_generate_draft_mcp_tool_failure(self, client, app):
        """Test negotiation draft when MCP tool returns failure"""
        # Setup mock to return failure
        mock_response = {
            "success": False,
            "error": "Content generation failed"
        }
        app.state.mcp_bridge.call_agent_d.return_value = mock_response
        
        # Make request
        request_data = {
            "counterparty_name": "Test Vendor",
            "amount": 50000.0,
            "transaction_type": "payable",
            "due_date": "2024-02-15",
            "current_cash_position": 30000.0
        }
        
        response = client.post("/api/v1/agents/negotiator/generate-draft", json=request_data)
        
        # Verify error response (500 or 503 if MCP bridge not available)
        assert response.status_code in [500, 503]
        data = response.json()
        # Check for error indicators in the response
        detail = data.get("detail", "").lower()
        assert any(word in detail for word in ["failed", "error", "unavailable", "mcp", "generation"])
    
    def test_generate_draft_unexpected_error(self, client, app):
        """Test negotiation draft with unexpected error"""
        # Setup mock to raise unexpected exception
        app.state.mcp_bridge.call_agent_d.side_effect = Exception("Unexpected error occurred")
        
        # Make request
        request_data = {
            "counterparty_name": "Test Vendor",
            "amount": 50000.0,
            "transaction_type": "payable",
            "due_date": "2024-02-15",
            "current_cash_position": 30000.0
        }
        
        response = client.post("/api/v1/agents/negotiator/generate-draft", json=request_data)
        
        # Verify error response
        assert response.status_code == 500
        data = response.json()
        assert "Internal server error" in data["detail"]
    
    def test_generate_draft_transaction_type_case_insensitive(self, client, app, mock_negotiation_response):
        """Test that transaction_type is case-insensitive"""
        # Setup mock
        app.state.mcp_bridge.call_agent_d.return_value = mock_negotiation_response
        
        transaction_types = ["payable", "PAYABLE", "Payable", "receivable", "RECEIVABLE", "Receivable"]
        
        for transaction_type in transaction_types:
            request_data = {
                "counterparty_name": "Test Vendor",
                "amount": 50000.0,
                "transaction_type": transaction_type,
                "due_date": "2024-02-15",
                "current_cash_position": 30000.0
            }
            
            response = client.post("/api/v1/agents/negotiator/generate-draft", json=request_data)
            
            # Verify successful response
            assert response.status_code == 200
            
            # Verify that transaction_type was normalized to lowercase
            call_args = app.state.mcp_bridge.call_agent_d.call_args[1]
            assert call_args["transaction_type"] in ["payable", "receivable"]
    
    def test_generate_draft_with_invoice_id(self, client, app, mock_negotiation_response):
        """Test negotiation draft with invoice ID"""
        # Setup mock
        app.state.mcp_bridge.call_agent_d.return_value = mock_negotiation_response
        
        # Make request with invoice ID
        request_data = {
            "counterparty_name": "Test Vendor",
            "amount": 50000.0,
            "transaction_type": "payable",
            "due_date": "2024-02-15",
            "current_cash_position": 30000.0,
            "invoice_id": "INV-2024-001"
        }
        
        response = client.post("/api/v1/agents/negotiator/generate-draft", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        
        # Verify invoice ID was passed to MCP bridge
        call_args = app.state.mcp_bridge.call_agent_d.call_args[1]
        assert call_args["invoice_id"] == "INV-2024-001"
    
    def test_generate_draft_various_amounts(self, client, app, mock_negotiation_response):
        """Test negotiation draft with various amount ranges"""
        # Setup mock
        app.state.mcp_bridge.call_agent_d.return_value = mock_negotiation_response
        
        amounts = [
            100.0,  # Small amount
            50000.0,  # Medium amount
            1000000.0,  # Large amount (10 lakhs)
            50000000.0  # Very large amount (5 crores)
        ]
        
        for amount in amounts:
            request_data = {
                "counterparty_name": "Test Vendor",
                "amount": amount,
                "transaction_type": "payable",
                "due_date": "2024-02-15",
                "current_cash_position": amount * 2
            }
            
            response = client.post("/api/v1/agents/negotiator/generate-draft", json=request_data)
            
            # Verify successful response for all amounts
            assert response.status_code == 200
            data = response.json()
            assert "intent" in data
            assert "strategy_explanation" in data


def run_tests():
    """Run all tests"""
    print("🧪 Running Negotiator Router Tests...")
    
    # Run pytest with verbose output
    import subprocess
    import sys
    
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "test_negotiator_router.py", 
        "-v", "--tb=short"
    ], capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
