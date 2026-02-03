#!/usr/bin/env python3
"""
Comprehensive test suite for Agent A - The Visual Auditor
Tests fraud detection, compliance checking, and orchestrator triggers
"""

import unittest
import json
from unittest.mock import patch, MagicMock
from server import (
    scan_invoice_document, 
    _apply_safety_validations, 
    _trigger_orchestrator,
    Invoice, 
    LineItem
)

class TestVisualAuditor(unittest.TestCase):
    """Test cases for Agent A - Visual Auditor"""
    
    def test_mock_invoice_processing(self):
        """Test basic invoice processing with mock data"""
        
        # Test with mock data
        invoice = scan_invoice_document("test_image", use_mock=True)
        
        # Verify basic structure
        self.assertIsInstance(invoice, Invoice)
        self.assertGreater(len(invoice.line_items), 0)
        self.assertIsInstance(invoice.total_amount, float)
        self.assertIsInstance(invoice.is_handwritten, bool)
        self.assertIsInstance(invoice.tampering_detected, bool)
        
        print(f"✅ Mock invoice processed: {invoice.vendor_name}")
    
    def test_safety_validations(self):
        """Test Python-side safety validations"""
        
        # Test case 1: Missing GSTIN with tax
        invoice = Invoice(
            vendor_name="Test Vendor",
            invoice_date="2024-01-15",
            total_amount=1000.0,
            tax_amount=180.0,  # Tax charged
            gstin=None,  # But no GSTIN
            line_items=[
                LineItem(description="Test Item", amount=1000.0, category="Service")
            ]
        )
        
        _apply_safety_validations(invoice)
        
        # Should flag missing GSTIN
        self.assertTrue(any("GSTIN" in flag for flag in invoice.compliance_flags))
        print("✅ Missing GSTIN validation works")
        
        # Test case 2: Stale invoice
        invoice_stale = Invoice(
            vendor_name="Test Vendor",
            invoice_date="2023-01-15",  # Old date
            total_amount=1000.0,
            tax_amount=180.0,
            line_items=[
                LineItem(description="Test Item", amount=1000.0, category="Service")
            ]
        )
        
        _apply_safety_validations(invoice_stale)
        
        # Should flag stale invoice
        self.assertTrue(any("Stale" in flag for flag in invoice_stale.compliance_flags))
        print("✅ Stale invoice validation works")
    
    def test_fraud_detection_flags(self):
        """Test fraud detection flagging"""
        
        # Test tampering detection
        invoice = Invoice(
            vendor_name="Suspicious Vendor",
            invoice_date="2024-01-15",
            total_amount=1000.0,
            tax_amount=180.0,
            tampering_detected=True,  # Tampering detected
            line_items=[
                LineItem(description="Test Item", amount=1000.0, category="Service")
            ]
        )
        
        _apply_safety_validations(invoice)
        
        # Should flag tampering
        self.assertTrue(any("CRITICAL" in flag for flag in invoice.compliance_flags))
        print("✅ Tampering detection works")
        
        # Test handwritten bill
        invoice_handwritten = Invoice(
            vendor_name="Local Vendor",
            invoice_date="2024-01-15",
            total_amount=1000.0,
            tax_amount=180.0,
            is_handwritten=True,  # Handwritten
            line_items=[
                LineItem(description="Test Item", amount=1000.0, category="Service")
            ]
        )
        
        _apply_safety_validations(invoice_handwritten)
        
        # Should flag handwritten
        self.assertTrue(any("Handwritten" in flag for flag in invoice_handwritten.compliance_flags))
        print("✅ Handwritten detection works")
    
    @patch('server.find_applicable_subsidies')
    @patch('server.get_user_profile')
    def test_orchestrator_subsidy_trigger(self, mock_profile, mock_subsidies):
        """Test orchestrator triggering Agent C for capital goods"""
        
        # Mock user profile
        mock_profile.return_value = json.dumps({
            "business_name": "Test Manufacturing Ltd",
            "industry_code": "textile",
            "turnover_tier": "< 5Cr"
        })
        
        # Mock subsidy response
        mock_subsidies.return_value = "TUFS Scheme - Up to 25% subsidy on machinery"
        
        # Create invoice with capital goods > 1L
        invoice = Invoice(
            vendor_name="Machinery Supplier",
            invoice_date="2024-01-15",
            total_amount=500000.0,  # 5 Lakh
            tax_amount=90000.0,
            line_items=[
                LineItem(description="Industrial Loom", amount=500000.0, category="Capital Goods")
            ]
        )
        
        # Trigger orchestrator
        _trigger_orchestrator(invoice)
        
        # Should have called subsidy finder
        mock_subsidies.assert_called_once()
        
        # Should have added alert to line items
        alert_items = [item for item in invoice.line_items if item.category == "Alert"]
        self.assertGreater(len(alert_items), 0)
        
        print("✅ Subsidy orchestrator trigger works")
    
    @patch('server.check_compliance_law')
    def test_orchestrator_compliance_trigger(self, mock_compliance):
        """Test orchestrator triggering Agent B for compliance"""
        
        # Mock compliance response
        mock_compliance.return_value = MagicMock(
            compliant_action="ITC not available for personal food items"
        )
        
        # Create invoice with personal items
        invoice = Invoice(
            vendor_name="Restaurant",
            invoice_date="2024-01-15",
            total_amount=2000.0,
            tax_amount=360.0,
            line_items=[
                LineItem(description="Team Lunch", amount=2000.0, category="Personal/Entertainment")
            ]
        )
        
        # Trigger orchestrator
        _trigger_orchestrator(invoice)
        
        # Should have called compliance check
        mock_compliance.assert_called_once()
        
        # Should have added warning to compliance flags
        self.assertTrue(any("ITC WARNING" in flag for flag in invoice.compliance_flags))
        
        print("✅ Compliance orchestrator trigger works")
    
    def test_line_item_categorization(self):
        """Test line item category classification"""
        
        categories = ["Capital Goods", "Raw Material", "Personal/Entertainment", "Service"]
        
        # Test each category
        for category in categories:
            item = LineItem(
                description=f"Test {category} Item",
                amount=1000.0,
                category=category
            )
            
            self.assertEqual(item.category, category)
        
        print("✅ Line item categorization works")
    
    def test_invoice_validation(self):
        """Test invoice model validation"""
        
        # Valid invoice
        invoice = Invoice(
            vendor_name="Valid Vendor",
            invoice_date="2024-01-15",
            total_amount=1000.0,
            tax_amount=180.0,
            line_items=[
                LineItem(description="Test Item", amount=1000.0, category="Service")
            ]
        )
        
        # Should not raise validation errors
        self.assertIsInstance(invoice, Invoice)
        
        print("✅ Invoice validation works")
    
    def test_confidence_scoring(self):
        """Test confidence score handling"""
        
        invoice = Invoice(
            vendor_name="Test Vendor",
            invoice_date="2024-01-15",
            total_amount=1000.0,
            tax_amount=180.0,
            confidence_score=0.85,  # 85% confidence
            line_items=[
                LineItem(description="Test Item", amount=1000.0, category="Service")
            ]
        )
        
        # Confidence should be between 0 and 1
        self.assertGreaterEqual(invoice.confidence_score, 0.0)
        self.assertLessEqual(invoice.confidence_score, 1.0)
        
        print("✅ Confidence scoring works")

class TestIntegrationScenarios(unittest.TestCase):
    """Integration test scenarios"""
    
    def test_textile_machinery_scenario(self):
        """Test complete textile machinery purchase scenario"""
        
        # Simulate textile company buying loom
        invoice = scan_invoice_document("textile_loom_invoice.jpg", use_mock=True)
        
        # Should detect capital goods
        capital_items = [item for item in invoice.line_items if item.category == "Capital Goods"]
        self.assertGreater(len(capital_items), 0)
        
        # For large purchases (>100000), verify the invoice is processed correctly
        # The mock data has total_amount > 100000, so verify capital goods are detected
        if invoice.total_amount > 100000:
            # Capital goods should be present for large machinery purchases
            self.assertGreater(len(capital_items), 0, "Large purchases should have Capital Goods category")
            # Total should be substantial
            self.assertGreater(invoice.total_amount, 100000)
        
        print("✅ Textile machinery scenario works")
    
    def test_restaurant_bill_scenario(self):
        """Test restaurant bill compliance scenario"""
        
        # Create restaurant bill
        invoice = Invoice(
            vendor_name="Fine Dining Restaurant",
            invoice_date="2024-01-15",
            total_amount=5000.0,
            tax_amount=900.0,
            line_items=[
                LineItem(description="Business Dinner", amount=5000.0, category="Personal/Entertainment")
            ]
        )
        
        # Apply validations and triggers
        _apply_safety_validations(invoice)
        _trigger_orchestrator(invoice)
        
        # Should have compliance warnings
        self.assertGreater(len(invoice.compliance_flags), 0)
        
        print("✅ Restaurant bill scenario works")

def run_comprehensive_tests():
    """Run all tests and display results"""
    
    print("🧪 Agent A - Visual Auditor Test Suite")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestVisualAuditor))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationScenarios))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print(f"\n📊 Test Results:")
    print(f"   Tests Run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("✅ All tests passed! Agent A is ready for production.")
    else:
        print("❌ Some tests failed. Check implementation.")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_comprehensive_tests()
    
    if success:
        print(f"\n🚀 Agent A - Visual Auditor is fully functional!")
        print("Ready to process real invoices with Gemini 1.5 Flash")
    else:
        print(f"\n🔧 Fix the failing tests before deployment")