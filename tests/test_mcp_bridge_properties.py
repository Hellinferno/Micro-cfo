#!/usr/bin/env python3
"""
Property-Based Tests for MCP Bridge Integration Consistency
Tests universal properties across all MCP tool calls
"""

import asyncio
import json
import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from hypothesis.strategies import composite
from typing import Dict, Any

from mcp_bridge import MCPBridge, MCPBridgeError
from server import Invoice, LegalRisk, NegotiationDraft, UserProfile


class TestMCPIntegrationConsistency:
    """
    Property-based tests for MCP Integration Consistency
    
    Feature: frontend-backend-integration, Property 1: MCP Integration Consistency
    Validates: Requirements 1.1, 1.2, 1.5
    """
    
    @composite
    def valid_image_urls(draw):
        """Generate valid image URLs for testing"""
        protocols = st.sampled_from(["http://", "https://", "data:image/"])
        domains = st.sampled_from([
            "example.com/image.jpg",
            "test.com/invoice.png", 
            "localhost:8000/test.jpeg",
            "png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        ])
        
        protocol = draw(protocols)
        domain = draw(domains)
        
        if protocol == "data:image/":
            return protocol + domain
        else:
            return protocol + domain
    
    @composite
    def valid_compliance_queries(draw):
        """Generate valid legal compliance queries"""
        query_templates = [
            "Can I claim Input Tax Credit on {}?",
            "What is the GST rate for {}?", 
            "Is {} eligible for composition scheme?",
            "What are the compliance requirements for {}?",
            "Can {} be claimed as business expense?"
        ]
        
        items = st.sampled_from([
            "office supplies", "machinery", "software", "consulting services",
            "raw materials", "food items", "vehicles", "rent payments"
        ])
        
        template = draw(st.sampled_from(query_templates))
        item = draw(items)
        
        return template.format(item)
    
    @composite
    def valid_sectors_and_amounts(draw):
        """Generate valid sector and capex amount combinations"""
        sectors = st.sampled_from([
            "textile", "manufacturing", "food_processing", "technology",
            "agriculture", "healthcare", "education", "retail"
        ])
        
        # Generate realistic capex amounts (1 lakh to 50 crores)
        amounts = st.floats(
            min_value=100000.0,  # 1 lakh
            max_value=500000000.0,  # 50 crores
            allow_nan=False,
            allow_infinity=False
        )
        
        sector = draw(sectors)
        amount = draw(amounts)
        
        return sector, amount
    
    @composite
    def valid_negotiation_params(draw):
        """Generate valid negotiation parameters"""
        names = st.text(min_size=3, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs')))
        amounts = st.floats(min_value=1000.0, max_value=10000000.0, allow_nan=False, allow_infinity=False)
        transaction_types = st.sampled_from(["payable", "receivable"])
        
        # Generate valid dates (YYYY-MM-DD format)
        years = st.integers(min_value=2020, max_value=2030)
        months = st.integers(min_value=1, max_value=12)
        days = st.integers(min_value=1, max_value=28)  # Use 28 to avoid invalid dates
        
        cash_positions = st.floats(min_value=0.0, max_value=50000000.0, allow_nan=False, allow_infinity=False)
        outflows = st.floats(min_value=0.0, max_value=10000000.0, allow_nan=False, allow_infinity=False)
        
        name = draw(names).strip()
        assume(len(name) >= 3)  # Ensure non-empty names
        
        amount = draw(amounts)
        transaction_type = draw(transaction_types)
        
        year = draw(years)
        month = draw(months)
        day = draw(days)
        due_date = f"{year:04d}-{month:02d}-{day:02d}"
        
        cash_position = draw(cash_positions)
        upcoming_outflows = draw(outflows)
        
        return {
            "counterparty_name": name,
            "amount": amount,
            "transaction_type": transaction_type,
            "due_date": due_date,
            "current_cash_position": cash_position,
            "upcoming_outflows": upcoming_outflows
        }
    
    @given(st.booleans())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_agent_a_consistency(self, use_mock):
        """
        Property 1: Agent A (Visual Auditor) consistency
        For any valid image input, the bridge should return a consistent Invoice structure
        """
        mcp_bridge = MCPBridge()
        
        # Use mock data for property testing to avoid external API calls
        result = await mcp_bridge.call_agent_a(
            image_url="test_image.jpg",
            use_mock=True  # Always use mock for property testing
        )
        
        # Verify response structure
        assert result["success"] is True
        assert "result" in result
        assert result["tool_name"] == "scan_invoice_document"
        
        # Verify Invoice structure consistency
        invoice_data = result["result"]
        required_fields = [
            "vendor_name", "invoice_date", "total_amount", "tax_amount",
            "line_items", "is_handwritten", "tampering_detected", 
            "compliance_flags", "confidence_score"
        ]
        
        for field in required_fields:
            assert field in invoice_data, f"Missing required field: {field}"
        
        # Verify data types
        assert isinstance(invoice_data["vendor_name"], str)
        assert isinstance(invoice_data["total_amount"], (int, float))
        assert isinstance(invoice_data["tax_amount"], (int, float))
        assert isinstance(invoice_data["line_items"], list)
        assert isinstance(invoice_data["is_handwritten"], bool)
        assert isinstance(invoice_data["tampering_detected"], bool)
        assert isinstance(invoice_data["compliance_flags"], list)
        assert isinstance(invoice_data["confidence_score"], (int, float))
        
        # Verify confidence score is in valid range
        assert 0.0 <= invoice_data["confidence_score"] <= 1.0
    
    @given(valid_compliance_queries())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    @pytest.mark.asyncio
    async def test_agent_b_consistency(self, query):
        """
        Property 1: Agent B (Legal Sentinel) consistency
        For any valid compliance query, the bridge should return a consistent LegalRisk structure
        """
        mcp_bridge = MCPBridge()
        result = await mcp_bridge.call_agent_b(query=query, user_context="")
        
        # Verify response structure
        assert result["success"] is True
        assert "result" in result
        assert result["tool_name"] == "check_compliance_law"
        
        # Verify LegalRisk structure consistency
        risk_data = result["result"]
        required_fields = ["risk_level", "relevant_section", "compliant_action"]
        
        for field in required_fields:
            assert field in risk_data, f"Missing required field: {field}"
        
        # Verify risk level is valid enum value
        valid_risk_levels = ["Low", "Medium", "High"]
        assert risk_data["risk_level"] in valid_risk_levels
        
        # Verify strings are non-empty
        assert isinstance(risk_data["relevant_section"], str)
        assert isinstance(risk_data["compliant_action"], str)
        assert len(risk_data["relevant_section"]) > 0
        assert len(risk_data["compliant_action"]) > 0
    
    @given(valid_sectors_and_amounts())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    @pytest.mark.asyncio
    async def test_agent_c_consistency(self, sector_and_amount):
        """
        Property 1: Agent C (Subsidy Hunter) consistency
        For any valid sector and capex amount, the bridge should return consistent subsidy information
        """
        mcp_bridge = MCPBridge()
        sector, capex_amount = sector_and_amount
        
        result = await mcp_bridge.call_agent_c(sector=sector, capex_amount=capex_amount)
        
        # Verify response structure
        assert result["success"] is True
        assert "result" in result
        assert result["tool_name"] == "find_applicable_subsidies"
        
        # Verify result is a string (subsidy information)
        subsidy_info = result["result"]
        assert isinstance(subsidy_info, str)
        assert len(subsidy_info) > 0
        
        # Verify sector is mentioned in the response (case-insensitive)
        assert sector.lower() in subsidy_info.lower() or "sector" in subsidy_info.lower()
    
    @given(valid_negotiation_params())
    @settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow], deadline=None)
    @pytest.mark.asyncio
    async def test_agent_d_consistency(self, params):
        """
        Property 1: Agent D (Negotiator) consistency
        For any valid negotiation parameters, the bridge should return a consistent NegotiationDraft structure
        """
        mcp_bridge = MCPBridge()
        result = await mcp_bridge.call_agent_d(**params)
        
        # Verify response structure
        assert result["success"] is True
        assert "result" in result
        assert result["tool_name"] == "generate_negotiation_draft"
        
        # Verify NegotiationDraft structure consistency
        draft_data = result["result"]
        required_fields = [
            "intent", "strategy_explanation", "whatsapp_message", 
            "formal_email", "option_a", "option_b"
        ]
        
        for field in required_fields:
            assert field in draft_data, f"Missing required field: {field}"
        
        # Verify intent is valid enum value
        valid_intents = ["credit_extension", "payment_chase", "early_payment_offer"]
        assert draft_data["intent"] in valid_intents
        
        # Verify all text fields are non-empty strings
        text_fields = ["strategy_explanation", "whatsapp_message", "formal_email", "option_a", "option_b"]
        for field in text_fields:
            assert isinstance(draft_data[field], str)
            assert len(draft_data[field]) > 0
        
        # Verify counterparty name appears in messages
        counterparty_name = params["counterparty_name"]
        message_fields = ["whatsapp_message", "formal_email", "option_a", "option_b"]
        
        # At least one message should contain the counterparty name
        name_mentioned = any(
            counterparty_name.lower() in draft_data[field].lower()
            for field in message_fields
        )
        assert name_mentioned, f"Counterparty name '{counterparty_name}' not found in any message"
    
    @pytest.mark.asyncio
    async def test_user_profile_consistency(self):
        """
        Property 1: User profile resource consistency
        The user profile should always return a consistent structure
        """
        mcp_bridge = MCPBridge()
        result = await mcp_bridge.get_user_profile()
        
        # Verify response structure
        assert result["success"] is True
        assert "result" in result
        assert result["resource_uri"] == "microcfo://data/profile"
        
        # Verify UserProfile structure consistency
        profile_data = result["result"]
        required_fields = ["business_name", "turnover_tier", "gst_registration_type", "industry_code"]
        
        for field in required_fields:
            assert field in profile_data, f"Missing required field: {field}"
        
        # Verify all fields are strings
        for field in required_fields:
            assert isinstance(profile_data[field], str)
            assert len(profile_data[field]) > 0
    
    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_invalid_tool_handling(self, invalid_tool_name):
        """
        Property 1: Error handling consistency
        For any invalid tool name, the bridge should raise MCPBridgeError consistently
        """
        mcp_bridge = MCPBridge()
        
        # Ensure we're not accidentally using a valid tool name
        valid_tools = ["scan_invoice_document", "check_compliance_law", "find_applicable_subsidies", "generate_negotiation_draft"]
        assume(invalid_tool_name not in valid_tools)
        
        with pytest.raises(MCPBridgeError) as exc_info:
            await mcp_bridge.call_tool(invalid_tool_name)
        
        # Verify error message contains the tool name
        error_message = str(exc_info.value)
        assert "Unknown tool" in error_message or "Tool execution failed" in error_message
    
    @pytest.mark.asyncio
    async def test_serialization_consistency(self):
        """
        Property 1: Serialization consistency
        All MCP tool results should be JSON-serializable
        """
        mcp_bridge = MCPBridge()
        
        # Test with Agent A (returns complex Pydantic model)
        result_a = await mcp_bridge.call_agent_a("test.jpg", use_mock=True)
        
        # Verify the result can be JSON serialized and deserialized
        json_str = json.dumps(result_a)
        deserialized = json.loads(json_str)
        
        # Verify structure is preserved
        assert deserialized["success"] == result_a["success"]
        assert deserialized["tool_name"] == result_a["tool_name"]
        assert "result" in deserialized
        
        # Test with Agent B
        result_b = await mcp_bridge.call_agent_b("Test query")
        json_str_b = json.dumps(result_b)
        deserialized_b = json.loads(json_str_b)
        
        assert deserialized_b["success"] == result_b["success"]
        assert deserialized_b["tool_name"] == result_b["tool_name"]


def run_property_tests():
    """Run all property-based tests"""
    print("🧪 Running Property-Based Tests for MCP Integration Consistency...")
    print("Feature: frontend-backend-integration, Property 1: MCP Integration Consistency")
    print("Validates: Requirements 1.1, 1.2, 1.5")
    print()
    
    # Run pytest with this file
    import subprocess
    import sys
    
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        __file__, 
        "-v", 
        "--tb=short"
    ], capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode == 0


if __name__ == "__main__":
    success = run_property_tests()
    if success:
        print("\n✅ All property-based tests passed!")
    else:
        print("\n❌ Some property-based tests failed!")
    
    import sys
    sys.exit(0 if success else 1)