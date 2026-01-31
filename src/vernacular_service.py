#!/usr/bin/env python3
"""
Vernacular Language Support for MicroCFO
Provides Hindi, Tamil, Telugu translations for WhatsApp-first interface

MANUAL SETUP REQUIRED:
1. Get Google Cloud Translation API key (https://cloud.google.com/translate)
   OR use Azure Translator (https://azure.microsoft.com/en-us/services/cognitive-services/translator/)
2. Set environment variable: GOOGLE_TRANSLATE_API_KEY or AZURE_TRANSLATOR_KEY
3. For production, consider pre-translating common messages for better performance
"""

import os
import logging
import httpx
from typing import Optional, Dict, List
from enum import Enum

logger = logging.getLogger(__name__)


class SupportedLanguage(str, Enum):
    """Supported vernacular languages"""
    ENGLISH = "en"
    HINDI = "hi"
    TAMIL = "ta"
    TELUGU = "te"
    MARATHI = "mr"
    GUJARATI = "gu"
    KANNADA = "kn"
    BENGALI = "bn"


# Pre-translated common messages for instant responses (no API call needed)
COMMON_TRANSLATIONS = {
    # Invoice alerts
    "Invoice Processed": {
        "hi": "चालान संसाधित",
        "ta": "விலைப்பட்டியல் செயலாக்கப்பட்டது",
        "te": "ఇన్వాయిస్ ప్రాసెస్ చేయబడింది"
    },
    "Vendor": {
        "hi": "विक्रेता",
        "ta": "விற்பனையாளர்",
        "te": "విక్రేత"
    },
    "Amount": {
        "hi": "राशि",
        "ta": "தொகை",
        "te": "మొత్తం"
    },
    "Category": {
        "hi": "श्रेणी",
        "ta": "வகை",
        "te": "వర్గం"
    },
    
    # Subsidy messages
    "Subsidy Opportunity": {
        "hi": "सब्सिडी का अवसर",
        "ta": "மானியம் வாய்ப்பு",
        "te": "సబ్సిడీ అవకాశం"
    },
    "Estimated benefit": {
        "hi": "अनुमानित लाभ",
        "ta": "மதிப்பிடப்பட்ட பலன்",
        "te": "అంచనా ప్రయోజనం"
    },
    "Reply APPLY to start the application process": {
        "hi": "आवेदन प्रक्रिया शुरू करने के लिए APPLY जवाब दें",
        "ta": "விண்ணப்ப செயல்முறையைத் தொடங்க APPLY என்று பதிலளிக்கவும்",
        "te": "దరఖాస్తు ప్రక్రియను ప్రారంభించడానికి APPLY అని రిప్లై చేయండి"
    },
    
    # Compliance alerts
    "Compliance Alert": {
        "hi": "अनुपालन चेतावनी",
        "ta": "இணக்க எச்சரிக்கை",
        "te": "సమ్మతి హెచ్చరిక"
    },
    "Risk Level": {
        "hi": "जोखिम स्तर",
        "ta": "ஆபத்து நிலை",
        "te": "రిస్క్ స్థాయి"
    },
    "High": {
        "hi": "उच्च",
        "ta": "அதிக",
        "te": "అధిక"
    },
    "Medium": {
        "hi": "मध्यम",
        "ta": "நடுத்தர",
        "te": "మధ్యస్థ"
    },
    "Low": {
        "hi": "निम्न",
        "ta": "குறைந்த",
        "te": "తక్కువ"
    },
    "Action Required": {
        "hi": "कार्रवाई आवश्यक",
        "ta": "நடவடிக்கை தேவை",
        "te": "చర్య అవసరం"
    },
    
    # Personal expense warning
    "Personal Expense Detected": {
        "hi": "व्यक्तिगत खर्च का पता चला",
        "ta": "தனிப்பட்ட செலவு கண்டறியப்பட்டது",
        "te": "వ్యక్తిగత ఖర్చు గుర్తించబడింది"
    },
    "Do not claim GST Input Tax Credit": {
        "hi": "GST इनपुट टैक्स क्रेडिट का दावा न करें",
        "ta": "GST உள்ளீட்டு வரி வரவை கோர வேண்டாம்",
        "te": "GST ఇన్‌పుట్ ట్యాక్స్ క్రెడిట్ క్లెయిమ్ చేయవద్దు"
    },
    "or you risk an audit": {
        "hi": "अन्यथा आपको ऑडिट का जोखिम है",
        "ta": "இல்லையெனில் தணிக்கை ஆபத்து உள்ளது",
        "te": "లేకపోతే ఆడిట్ రిస్క్ ఉంటుంది"
    },
    
    # Common responses
    "Reply APPROVE to send": {
        "hi": "भेजने के लिए APPROVE जवाब दें",
        "ta": "அனுப்ப APPROVE என்று பதிலளிக்கவும்",
        "te": "పంపడానికి APPROVE అని రిప్లై చేయండి"
    },
    "Reply DETAILS for more information": {
        "hi": "अधिक जानकारी के लिए DETAILS जवाब दें",
        "ta": "மேலும் தகவலுக்கு DETAILS என்று பதிலளிக்கவும்",
        "te": "మరిన్ని వివరాల కోసం DETAILS అని రిప్లై చేయండి"
    },
    
    # Navigation
    "Main Menu": {
        "hi": "मुख्य मेनू",
        "ta": "முதன்மை பட்டியல்",
        "te": "ప్రధాన మెనూ"
    },
    "Upload Invoice": {
        "hi": "चालान अपलोड करें",
        "ta": "விலைப்பட்டியல் பதிவேற்றவும்",
        "te": "ఇన్వాయిస్ అప్‌లోడ్ చేయండి"
    },
    "Check Subsidies": {
        "hi": "सब्सिडी जांचें",
        "ta": "மானியங்களை சரிபார்க்கவும்",
        "te": "సబ్సిడీలను తనిఖీ చేయండి"
    },
    "Legal Query": {
        "hi": "कानूनी प्रश्न",
        "ta": "சட்ட கேள்வி",
        "te": "చట్టపరమైన ప్రశ్న"
    }
}


class VernacularService:
    """
    Multi-language translation service for MicroCFO
    
    Uses pre-translated common phrases for speed, falls back to API for dynamic content.
    
    Environment Variables:
    - GOOGLE_TRANSLATE_API_KEY: Google Cloud Translation API key
    - AZURE_TRANSLATOR_KEY: Azure Cognitive Services Translator key
    - AZURE_TRANSLATOR_REGION: Azure region (e.g., 'eastus')
    """
    
    def __init__(self):
        self.google_api_key = os.getenv("GOOGLE_TRANSLATE_API_KEY")
        self.azure_key = os.getenv("AZURE_TRANSLATOR_KEY")
        self.azure_region = os.getenv("AZURE_TRANSLATOR_REGION", "eastus")
        
        self.provider = None
        if self.google_api_key:
            self.provider = "google"
            logger.info("✅ Vernacular support enabled (Google Translate)")
        elif self.azure_key:
            self.provider = "azure"
            logger.info("✅ Vernacular support enabled (Azure Translator)")
        else:
            logger.warning("⚠️ No translation API configured. Using pre-translated phrases only.")
    
    def get_common_translation(self, text: str, target_lang: str) -> Optional[str]:
        """Get pre-translated common phrase"""
        if target_lang == "en":
            return text
        
        translations = COMMON_TRANSLATIONS.get(text)
        if translations:
            return translations.get(target_lang)
        return None
    
    async def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "en"
    ) -> str:
        """
        Translate text to target language
        
        Args:
            text: Text to translate
            target_lang: Target language code (hi, ta, te, etc.)
            source_lang: Source language code (default: en)
        
        Returns:
            Translated text, or original if translation fails
        """
        # Return original if target is English
        if target_lang == "en" or target_lang == source_lang:
            return text
        
        # Check pre-translated common phrases first
        common = self.get_common_translation(text, target_lang)
        if common:
            return common
        
        # Use API for dynamic content
        if self.provider == "google":
            return await self._translate_google(text, target_lang, source_lang)
        elif self.provider == "azure":
            return await self._translate_azure(text, target_lang, source_lang)
        else:
            # No API available, return original with language note
            return text
    
    async def _translate_google(
        self,
        text: str,
        target_lang: str,
        source_lang: str
    ) -> str:
        """Translate using Google Cloud Translation API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://translation.googleapis.com/language/translate/v2",
                    params={"key": self.google_api_key},
                    json={
                        "q": text,
                        "target": target_lang,
                        "source": source_lang,
                        "format": "text"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["data"]["translations"][0]["translatedText"]
                else:
                    logger.warning(f"Google Translate error: {response.text}")
                    return text
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text
    
    async def _translate_azure(
        self,
        text: str,
        target_lang: str,
        source_lang: str
    ) -> str:
        """Translate using Azure Cognitive Services Translator"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.cognitive.microsofttranslator.com/translate",
                    params={
                        "api-version": "3.0",
                        "from": source_lang,
                        "to": target_lang
                    },
                    headers={
                        "Ocp-Apim-Subscription-Key": self.azure_key,
                        "Ocp-Apim-Subscription-Region": self.azure_region,
                        "Content-Type": "application/json"
                    },
                    json=[{"text": text}]
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result[0]["translations"][0]["text"]
                else:
                    logger.warning(f"Azure Translate error: {response.text}")
                    return text
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text
    
    async def translate_message(
        self,
        message: Dict[str, str],
        target_lang: str
    ) -> Dict[str, str]:
        """
        Translate a structured message (with multiple fields)
        
        Args:
            message: Dict with string values to translate
            target_lang: Target language code
        
        Returns:
            Dict with translated values
        """
        translated = {}
        for key, value in message.items():
            if isinstance(value, str):
                translated[key] = await self.translate(value, target_lang)
            else:
                translated[key] = value
        return translated
    
    def get_language_name(self, code: str) -> str:
        """Get human-readable language name"""
        names = {
            "en": "English",
            "hi": "हिंदी (Hindi)",
            "ta": "தமிழ் (Tamil)",
            "te": "తెలుగు (Telugu)",
            "mr": "मराठी (Marathi)",
            "gu": "ગુજરાતી (Gujarati)",
            "kn": "ಕನ್ನಡ (Kannada)",
            "bn": "বাংলা (Bengali)"
        }
        return names.get(code, code)
    
    def detect_language_preference(self, text: str) -> str:
        """
        Detect user's language preference from message
        
        Simple heuristic based on script detection
        """
        # Devanagari (Hindi, Marathi)
        if any('\u0900' <= c <= '\u097F' for c in text):
            return "hi"
        # Tamil
        if any('\u0B80' <= c <= '\u0BFF' for c in text):
            return "ta"
        # Telugu
        if any('\u0C00' <= c <= '\u0C7F' for c in text):
            return "te"
        # Bengali
        if any('\u0980' <= c <= '\u09FF' for c in text):
            return "bn"
        # Gujarati
        if any('\u0A80' <= c <= '\u0AFF' for c in text):
            return "gu"
        # Kannada
        if any('\u0C80' <= c <= '\u0CFF' for c in text):
            return "kn"
        
        return "en"  # Default to English


# Singleton instance
_vernacular_service: Optional[VernacularService] = None

def get_vernacular_service() -> VernacularService:
    """Get vernacular service singleton"""
    global _vernacular_service
    if _vernacular_service is None:
        _vernacular_service = VernacularService()
    return _vernacular_service
