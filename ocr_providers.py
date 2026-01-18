"""
Multi-Provider OCR System for Visual Auditor
Supports Gemini (primary), AWS Textract, and Azure Form Recognizer (fallbacks)
"""

import logging
import os
from typing import Dict, Any, Optional, Tuple
from enum import Enum
import base64
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class OCRProvider(Enum):
    """Available OCR providers"""
    GEMINI = "gemini"
    AWS_TEXTRACT = "aws_textract"
    AZURE_FORM_RECOGNIZER = "azure_form_recognizer"
    MOCK = "mock"

class OCRResult:
    """Standardized OCR result"""
    def __init__(
        self,
        invoice_data: Dict[str, Any],
        confidence: float,
        provider: OCRProvider,
        raw_response: Optional[Dict] = None,
        processing_time: float = 0.0,
        warnings: Optional[list] = None
    ):
        self.invoice_data = invoice_data
        self.confidence = confidence
        self.provider = provider
        self.raw_response = raw_response
        self.processing_time = processing_time
        self.warnings = warnings or []
        
        # Determine if human review is needed
        self.needs_human_review = confidence < 0.85
        self.review_reason = self._determine_review_reason()
    
    def _determine_review_reason(self) -> Optional[str]:
        """Determine why human review is needed"""
        if not self.needs_human_review:
            return None
        
        if self.confidence < 0.5:
            return "Very low confidence - possible handwritten or damaged document"
        elif self.confidence < 0.7:
            return "Low confidence - unclear text or complex layout"
        elif self.confidence < 0.85:
            return "Moderate confidence - recommend verification"
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "invoice_data": self.invoice_data,
            "confidence": self.confidence,
            "provider": self.provider.value,
            "needs_human_review": self.needs_human_review,
            "review_reason": self.review_reason,
            "processing_time": self.processing_time,
            "warnings": self.warnings
        }

class BaseOCRProvider(ABC):
    """Base class for OCR providers"""
    
    def __init__(self):
        self.provider_name = self.__class__.__name__
    
    @abstractmethod
    def process_invoice(self, image_data: bytes, filename: str) -> OCRResult:
        """Process invoice and return standardized result"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and available"""
        pass

class GeminiOCRProvider(BaseOCRProvider):
    """Gemini Vision API provider"""
    
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('GEMINI_API_KEY')
    
    def is_available(self) -> bool:
        """Check if Gemini is configured"""
        return bool(self.api_key)
    
    def process_invoice(self, image_data: bytes, filename: str) -> OCRResult:
        """Process invoice with Gemini Vision"""
        import time
        start_time = time.time()
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            
            # Use Gemini Flash for speed
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Convert image to base64
            import base64
            from PIL import Image
            import io
            
            # Load image
            image = Image.open(io.BytesIO(image_data))
            
            # Prompt for invoice extraction
            prompt = """
            Extract the following information from this invoice image:
            - Invoice Number
            - Vendor Name
            - Invoice Date (YYYY-MM-DD format)
            - Due Date (YYYY-MM-DD format)
            - Total Amount (numeric only)
            - Tax Amount (numeric only)
            - Currency (default INR)
            - GSTIN (if present)
            - Line Items (description, quantity, rate, amount)
            
            Also assess:
            - Is this handwritten? (yes/no)
            - Document quality (excellent/good/fair/poor)
            - Any tampering detected? (yes/no)
            
            Return as JSON with a confidence score (0-1) for the overall extraction.
            """
            
            response = model.generate_content([prompt, image])
            
            # Parse response
            import json
            import re
            
            # Extract JSON from response
            text = response.text
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            
            if json_match:
                result_data = json.loads(json_match.group())
            else:
                # Fallback parsing
                result_data = self._parse_text_response(text)
            
            # Calculate confidence
            confidence = result_data.get('confidence', 0.8)
            
            # Check for quality issues
            warnings = []
            if result_data.get('is_handwritten') == 'yes':
                warnings.append("Handwritten document detected")
                confidence *= 0.7  # Reduce confidence for handwritten
            
            if result_data.get('document_quality') in ['fair', 'poor']:
                warnings.append(f"Document quality: {result_data.get('document_quality')}")
                confidence *= 0.85
            
            if result_data.get('tampering_detected') == 'yes':
                warnings.append("Possible tampering detected")
                confidence *= 0.6
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                invoice_data=result_data,
                confidence=min(confidence, 1.0),
                provider=OCRProvider.GEMINI,
                raw_response={"text": text},
                processing_time=processing_time,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"Gemini OCR failed: {e}")
            raise
    
    def _parse_text_response(self, text: str) -> Dict[str, Any]:
        """Fallback text parsing"""
        # Simple extraction logic
        return {
            "invoice_number": "UNKNOWN",
            "vendor_name": "UNKNOWN",
            "total_amount": 0.0,
            "confidence": 0.5,
            "error": "Failed to parse structured response"
        }

class AWSTextractProvider(BaseOCRProvider):
    """AWS Textract provider"""
    
    def __init__(self):
        super().__init__()
        self.access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.region = os.getenv('AWS_REGION', 'us-east-1')
    
    def is_available(self) -> bool:
        """Check if AWS credentials are configured"""
        return bool(self.access_key and self.secret_key)
    
    def process_invoice(self, image_data: bytes, filename: str) -> OCRResult:
        """Process invoice with AWS Textract"""
        import time
        start_time = time.time()
        
        try:
            import boto3
            
            # Initialize Textract client
            textract = boto3.client(
                'textract',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region
            )
            
            # Analyze document
            response = textract.analyze_expense(
                Document={'Bytes': image_data}
            )
            
            # Extract invoice data
            invoice_data = self._parse_textract_response(response)
            
            # Calculate confidence from Textract confidence scores
            confidence = self._calculate_confidence(response)
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                invoice_data=invoice_data,
                confidence=confidence,
                provider=OCRProvider.AWS_TEXTRACT,
                raw_response=response,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"AWS Textract failed: {e}")
            raise
    
    def _parse_textract_response(self, response: Dict) -> Dict[str, Any]:
        """Parse Textract response into invoice data"""
        invoice_data = {
            "invoice_number": None,
            "vendor_name": None,
            "invoice_date": None,
            "total_amount": None,
            "tax_amount": None,
            "currency": "INR"
        }
        
        # Extract from expense documents
        for doc in response.get('ExpenseDocuments', []):
            for field in doc.get('SummaryFields', []):
                field_type = field.get('Type', {}).get('Text', '').lower()
                value = field.get('ValueDetection', {}).get('Text', '')
                
                if 'invoice' in field_type and 'number' in field_type:
                    invoice_data['invoice_number'] = value
                elif 'vendor' in field_type or 'name' in field_type:
                    invoice_data['vendor_name'] = value
                elif 'date' in field_type:
                    invoice_data['invoice_date'] = value
                elif 'total' in field_type:
                    invoice_data['total_amount'] = self._parse_amount(value)
                elif 'tax' in field_type:
                    invoice_data['tax_amount'] = self._parse_amount(value)
        
        return invoice_data
    
    def _calculate_confidence(self, response: Dict) -> float:
        """Calculate average confidence from Textract"""
        confidences = []
        
        for doc in response.get('ExpenseDocuments', []):
            for field in doc.get('SummaryFields', []):
                conf = field.get('ValueDetection', {}).get('Confidence', 0)
                confidences.append(conf / 100.0)  # Convert to 0-1 scale
        
        return sum(confidences) / len(confidences) if confidences else 0.5
    
    def _parse_amount(self, value: str) -> Optional[float]:
        """Parse amount string to float"""
        try:
            import re
            # Remove currency symbols and commas
            cleaned = re.sub(r'[^\d.]', '', value)
            return float(cleaned)
        except:
            return None

class AzureFormRecognizerProvider(BaseOCRProvider):
    """Azure Form Recognizer provider"""
    
    def __init__(self):
        super().__init__()
        self.endpoint = os.getenv('AZURE_FORM_RECOGNIZER_ENDPOINT')
        self.api_key = os.getenv('AZURE_FORM_RECOGNIZER_KEY')
    
    def is_available(self) -> bool:
        """Check if Azure is configured"""
        return bool(self.endpoint and self.api_key)
    
    def process_invoice(self, image_data: bytes, filename: str) -> OCRResult:
        """Process invoice with Azure Form Recognizer"""
        import time
        start_time = time.time()
        
        try:
            from azure.ai.formrecognizer import DocumentAnalysisClient
            from azure.core.credentials import AzureKeyCredential
            
            # Initialize client
            client = DocumentAnalysisClient(
                endpoint=self.endpoint,
                credential=AzureKeyCredential(self.api_key)
            )
            
            # Analyze invoice
            poller = client.begin_analyze_document(
                "prebuilt-invoice",
                document=image_data
            )
            result = poller.result()
            
            # Extract invoice data
            invoice_data = self._parse_azure_response(result)
            
            # Calculate confidence
            confidence = self._calculate_confidence(result)
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                invoice_data=invoice_data,
                confidence=confidence,
                provider=OCRProvider.AZURE_FORM_RECOGNIZER,
                raw_response=result.to_dict(),
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Azure Form Recognizer failed: {e}")
            raise
    
    def _parse_azure_response(self, result) -> Dict[str, Any]:
        """Parse Azure response into invoice data"""
        invoice_data = {
            "invoice_number": None,
            "vendor_name": None,
            "invoice_date": None,
            "total_amount": None,
            "tax_amount": None,
            "currency": "INR"
        }
        
        for document in result.documents:
            fields = document.fields
            
            if 'InvoiceId' in fields:
                invoice_data['invoice_number'] = fields['InvoiceId'].value
            if 'VendorName' in fields:
                invoice_data['vendor_name'] = fields['VendorName'].value
            if 'InvoiceDate' in fields:
                invoice_data['invoice_date'] = str(fields['InvoiceDate'].value)
            if 'InvoiceTotal' in fields:
                invoice_data['total_amount'] = fields['InvoiceTotal'].value
            if 'TotalTax' in fields:
                invoice_data['tax_amount'] = fields['TotalTax'].value
        
        return invoice_data
    
    def _calculate_confidence(self, result) -> float:
        """Calculate average confidence from Azure"""
        confidences = []
        
        for document in result.documents:
            for field_name, field in document.fields.items():
                if field.confidence:
                    confidences.append(field.confidence)
        
        return sum(confidences) / len(confidences) if confidences else 0.5

class MockOCRProvider(BaseOCRProvider):
    """Mock provider for testing"""
    
    def is_available(self) -> bool:
        return True
    
    def process_invoice(self, image_data: bytes, filename: str) -> OCRResult:
        """Return mock data"""
        import time
        
        mock_data = {
            "invoice_number": "MOCK-2024-001",
            "vendor_name": "Mock Vendor Ltd",
            "invoice_date": "2024-01-15",
            "due_date": "2024-02-15",
            "total_amount": 50000.00,
            "tax_amount": 9000.00,
            "currency": "INR",
            "gstin": "27AABCU9603R1ZM",
            "line_items": [
                {"description": "Product A", "quantity": 10, "rate": 4100, "amount": 41000},
                {"description": "Product B", "quantity": 5, "rate": 1800, "amount": 9000}
            ]
        }
        
        return OCRResult(
            invoice_data=mock_data,
            confidence=0.95,
            provider=OCRProvider.MOCK,
            processing_time=0.1
        )

class MultiProviderOCR:
    """
    Multi-provider OCR with automatic fallback
    Tries providers in order until success or all fail
    """
    
    def __init__(self, confidence_threshold: float = 0.85):
        self.confidence_threshold = confidence_threshold
        self.providers = self._initialize_providers()
        logger.info(f"Initialized OCR with {len(self.providers)} available providers")
    
    def _initialize_providers(self) -> list[BaseOCRProvider]:
        """Initialize all available providers"""
        providers = []
        
        # Primary: Gemini (fast and good)
        gemini = GeminiOCRProvider()
        if gemini.is_available():
            providers.append(gemini)
            logger.info("✓ Gemini OCR available")
        
        # Fallback 1: AWS Textract (reliable)
        textract = AWSTextractProvider()
        if textract.is_available():
            providers.append(textract)
            logger.info("✓ AWS Textract available")
        
        # Fallback 2: Azure Form Recognizer (specialized)
        azure = AzureFormRecognizerProvider()
        if azure.is_available():
            providers.append(azure)
            logger.info("✓ Azure Form Recognizer available")
        
        # Always available: Mock (for testing)
        providers.append(MockOCRProvider())
        
        return providers
    
    def process_invoice(
        self,
        image_data: bytes,
        filename: str,
        use_mock: bool = False
    ) -> OCRResult:
        """
        Process invoice with automatic fallback
        Returns best result or flags for human review
        """
        if use_mock:
            logger.info("Using mock OCR provider")
            return MockOCRProvider().process_invoice(image_data, filename)
        
        results = []
        errors = []
        
        for provider in self.providers:
            if isinstance(provider, MockOCRProvider):
                continue  # Skip mock unless explicitly requested
            
            try:
                logger.info(f"Trying {provider.provider_name}...")
                result = provider.process_invoice(image_data, filename)
                results.append(result)
                
                logger.info(
                    f"{provider.provider_name} completed: "
                    f"confidence={result.confidence:.2f}, "
                    f"time={result.processing_time:.2f}s"
                )
                
                # If confidence is good enough, return immediately
                if result.confidence >= self.confidence_threshold:
                    logger.info(f"✓ Confidence threshold met, using {provider.provider_name}")
                    return result
                
            except Exception as e:
                error_msg = f"{provider.provider_name} failed: {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)
                continue
        
        # All providers tried, return best result
        if results:
            best_result = max(results, key=lambda r: r.confidence)
            logger.warning(
                f"All providers below threshold. "
                f"Best: {best_result.provider.value} "
                f"(confidence={best_result.confidence:.2f})"
            )
            best_result.warnings.append(
                f"All providers below confidence threshold ({self.confidence_threshold})"
            )
            return best_result
        
        # All providers failed
        logger.error("All OCR providers failed")
        raise Exception(f"All OCR providers failed: {'; '.join(errors)}")
    
    def get_available_providers(self) -> list[str]:
        """Get list of available provider names"""
        return [p.provider_name for p in self.providers if p.is_available()]
