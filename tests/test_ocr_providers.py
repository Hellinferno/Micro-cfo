"""
Test suite for multi-provider OCR system
Tests confidence thresholds, fallback logic, and provider integration
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from ocr_providers import (
    MultiProviderOCR, OCRResult, OCRProvider,
    GeminiOCRProvider, AWSTextractProvider, AzureFormRecognizerProvider, MockOCRProvider
)

class TestOCRResult:
    """Test OCRResult class"""
    
    def test_high_confidence_no_review(self):
        """Test high confidence doesn't need review"""
        result = OCRResult(
            invoice_data={"invoice_number": "INV-001"},
            confidence=0.95,
            provider=OCRProvider.GEMINI
        )
        
        assert result.needs_human_review is False
        assert result.review_reason is None
    
    def test_low_confidence_needs_review(self):
        """Test low confidence needs review"""
        result = OCRResult(
            invoice_data={"invoice_number": "INV-001"},
            confidence=0.65,
            provider=OCRProvider.GEMINI
        )
        
        assert result.needs_human_review is True
        assert result.review_reason is not None
        assert "Low confidence" in result.review_reason
    
    def test_very_low_confidence_reason(self):
        """Test very low confidence reason"""
        result = OCRResult(
            invoice_data={},
            confidence=0.45,
            provider=OCRProvider.GEMINI
        )
        
        assert result.needs_human_review is True
        assert "Very low confidence" in result.review_reason
        assert "handwritten" in result.review_reason.lower()
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        result = OCRResult(
            invoice_data={"invoice_number": "INV-001"},
            confidence=0.88,
            provider=OCRProvider.GEMINI,
            warnings=["Test warning"]
        )
        
        data = result.to_dict()
        
        assert data["confidence"] == 0.88
        assert data["provider"] == "gemini"
        assert data["needs_human_review"] is False
        assert len(data["warnings"]) == 1

class TestMockOCRProvider:
    """Test mock OCR provider"""
    
    def test_mock_provider_available(self):
        """Test mock provider is always available"""
        provider = MockOCRProvider()
        assert provider.is_available() is True
    
    def test_mock_provider_returns_data(self):
        """Test mock provider returns valid data"""
        provider = MockOCRProvider()
        result = provider.process_invoice(b"fake_data", "test.pdf")
        
        assert result.confidence == 0.95
        assert result.provider == OCRProvider.MOCK
        assert result.invoice_data["invoice_number"] == "MOCK-2024-001"
        assert result.needs_human_review is False

class TestGeminiOCRProvider:
    """Test Gemini OCR provider"""
    
    def test_gemini_availability_with_key(self):
        """Test Gemini is available when API key is set"""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            provider = GeminiOCRProvider()
            assert provider.is_available() is True
    
    def test_gemini_availability_without_key(self):
        """Test Gemini is not available without API key"""
        with patch.dict('os.environ', {}, clear=True):
            provider = GeminiOCRProvider()
            assert provider.is_available() is False
    
    @patch('google.generativeai.GenerativeModel')
    def test_gemini_process_invoice(self, mock_model):
        """Test Gemini invoice processing"""
        # Mock response
        mock_response = Mock()
        mock_response.text = '''
        {
            "invoice_number": "INV-2024-001",
            "vendor_name": "Test Vendor",
            "total_amount": 50000.00,
            "confidence": 0.92,
            "is_handwritten": "no",
            "document_quality": "excellent",
            "tampering_detected": "no"
        }
        '''
        
        mock_model_instance = Mock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance
        
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            provider = GeminiOCRProvider()
            
            # Mock PIL Image
            with patch('PIL.Image.open'):
                result = provider.process_invoice(b"fake_image_data", "test.pdf")
                
                assert result.confidence == 0.92
                assert result.provider == OCRProvider.GEMINI
                assert result.invoice_data["invoice_number"] == "INV-2024-001"
    
    @patch('google.generativeai.GenerativeModel')
    def test_gemini_handwritten_detection(self, mock_model):
        """Test Gemini detects handwritten documents"""
        mock_response = Mock()
        mock_response.text = '''
        {
            "invoice_number": "INV-001",
            "confidence": 0.90,
            "is_handwritten": "yes",
            "document_quality": "good",
            "tampering_detected": "no"
        }
        '''
        
        mock_model_instance = Mock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance
        
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test_key'}):
            provider = GeminiOCRProvider()
            
            with patch('PIL.Image.open'):
                result = provider.process_invoice(b"fake_data", "test.pdf")
                
                # Confidence should be reduced for handwritten
                assert result.confidence < 0.90
                assert "Handwritten" in result.warnings[0]

class TestAWSTextractProvider:
    """Test AWS Textract provider"""
    
    def test_textract_availability_with_credentials(self):
        """Test Textract is available with credentials"""
        with patch.dict('os.environ', {
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret'
        }):
            provider = AWSTextractProvider()
            assert provider.is_available() is True
    
    def test_textract_availability_without_credentials(self):
        """Test Textract is not available without credentials"""
        with patch.dict('os.environ', {}, clear=True):
            provider = AWSTextractProvider()
            assert provider.is_available() is False

class TestAzureFormRecognizerProvider:
    """Test Azure Form Recognizer provider"""
    
    def test_azure_availability_with_credentials(self):
        """Test Azure is available with credentials"""
        with patch.dict('os.environ', {
            'AZURE_FORM_RECOGNIZER_ENDPOINT': 'https://test.cognitiveservices.azure.com/',
            'AZURE_FORM_RECOGNIZER_KEY': 'test_key'
        }):
            provider = AzureFormRecognizerProvider()
            assert provider.is_available() is True
    
    def test_azure_availability_without_credentials(self):
        """Test Azure is not available without credentials"""
        with patch.dict('os.environ', {}, clear=True):
            provider = AzureFormRecognizerProvider()
            assert provider.is_available() is False

class TestMultiProviderOCR:
    """Test multi-provider OCR system"""
    
    def test_initialization(self):
        """Test OCR system initialization"""
        ocr = MultiProviderOCR(confidence_threshold=0.85)
        assert ocr.confidence_threshold == 0.85
        assert len(ocr.providers) > 0  # At least mock provider
    
    def test_mock_mode(self):
        """Test mock mode returns mock data"""
        ocr = MultiProviderOCR()
        result = ocr.process_invoice(b"fake_data", "test.pdf", use_mock=True)
        
        assert result.provider == OCRProvider.MOCK
        assert result.confidence == 0.95
        assert result.needs_human_review is False
    
    def test_confidence_threshold_met(self):
        """Test processing stops when confidence threshold is met"""
        ocr = MultiProviderOCR(confidence_threshold=0.85)
        
        # Mock a provider that returns high confidence
        mock_provider = Mock()
        mock_result = OCRResult(
            invoice_data={"invoice_number": "INV-001"},
            confidence=0.92,
            provider=OCRProvider.GEMINI
        )
        mock_provider.process_invoice.return_value = mock_result
        mock_provider.provider_name = "MockProvider"
        
        ocr.providers = [mock_provider]
        
        result = ocr.process_invoice(b"fake_data", "test.pdf")
        
        assert result.confidence == 0.92
        assert mock_provider.process_invoice.call_count == 1
    
    def test_fallback_to_next_provider(self):
        """Test fallback when first provider has low confidence"""
        ocr = MultiProviderOCR(confidence_threshold=0.85)
        
        # First provider: low confidence
        provider1 = Mock()
        result1 = OCRResult(
            invoice_data={"invoice_number": "INV-001"},
            confidence=0.70,
            provider=OCRProvider.GEMINI
        )
        provider1.process_invoice.return_value = result1
        provider1.provider_name = "Provider1"
        
        # Second provider: high confidence
        provider2 = Mock()
        result2 = OCRResult(
            invoice_data={"invoice_number": "INV-001"},
            confidence=0.90,
            provider=OCRProvider.AWS_TEXTRACT
        )
        provider2.process_invoice.return_value = result2
        provider2.provider_name = "Provider2"
        
        ocr.providers = [provider1, provider2]
        
        result = ocr.process_invoice(b"fake_data", "test.pdf")
        
        # Should use second provider
        assert result.confidence == 0.90
        assert result.provider == OCRProvider.AWS_TEXTRACT
        assert provider1.process_invoice.call_count == 1
        assert provider2.process_invoice.call_count == 1
    
    def test_returns_best_result_when_all_below_threshold(self):
        """Test returns best result when all providers below threshold"""
        ocr = MultiProviderOCR(confidence_threshold=0.85)
        
        # All providers return low confidence
        provider1 = Mock()
        result1 = OCRResult(
            invoice_data={"invoice_number": "INV-001"},
            confidence=0.70,
            provider=OCRProvider.GEMINI
        )
        provider1.process_invoice.return_value = result1
        provider1.provider_name = "Provider1"
        
        provider2 = Mock()
        result2 = OCRResult(
            invoice_data={"invoice_number": "INV-001"},
            confidence=0.80,
            provider=OCRProvider.AWS_TEXTRACT
        )
        provider2.process_invoice.return_value = result2
        provider2.provider_name = "Provider2"
        
        ocr.providers = [provider1, provider2]
        
        result = ocr.process_invoice(b"fake_data", "test.pdf")
        
        # Should return best result (0.80)
        assert result.confidence == 0.80
        assert result.provider == OCRProvider.AWS_TEXTRACT
        assert result.needs_human_review is True
        assert len(result.warnings) > 0
    
    def test_all_providers_fail(self):
        """Test exception when all providers fail"""
        ocr = MultiProviderOCR()
        
        # All providers raise exceptions
        provider1 = Mock()
        provider1.process_invoice.side_effect = Exception("Provider 1 failed")
        provider1.provider_name = "Provider1"
        provider1.is_available.return_value = True
        
        provider2 = Mock()
        provider2.process_invoice.side_effect = Exception("Provider 2 failed")
        provider2.provider_name = "Provider2"
        provider2.is_available.return_value = True
        
        ocr.providers = [provider1, provider2]
        
        with pytest.raises(Exception) as exc_info:
            ocr.process_invoice(b"fake_data", "test.pdf")
        
        assert "All OCR providers failed" in str(exc_info.value)
    
    def test_get_available_providers(self):
        """Test getting list of available providers"""
        ocr = MultiProviderOCR()
        providers = ocr.get_available_providers()
        
        assert isinstance(providers, list)
        assert len(providers) > 0
        assert "MockOCRProvider" in providers

class TestConfidenceThresholds:
    """Test confidence threshold scenarios"""
    
    @pytest.mark.parametrize("confidence,expected_review", [
        (0.95, False),
        (0.85, False),
        (0.84, True),
        (0.70, True),
        (0.50, True),
        (0.30, True),
    ])
    def test_confidence_thresholds(self, confidence, expected_review):
        """Test various confidence levels"""
        result = OCRResult(
            invoice_data={},
            confidence=confidence,
            provider=OCRProvider.GEMINI
        )
        
        assert result.needs_human_review == expected_review

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
