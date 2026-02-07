"""
Legal Sentinel - Agent B
AI-powered compliance checking with RAG
"""

import os
import json
from typing import Optional, Dict, Any
from pydantic import BaseModel

# Try importing google.generativeai
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class ComplianceResult(BaseModel):
    risk_level: str  # LOW, MEDIUM, HIGH
    relevant_section: str
    explanation: str
    compliant_action: str


class LegalSentinel:
    """
    Agent B: Legal Sentinel
    Answers compliance questions with risk assessment
    """
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = None
        
        if GENAI_AVAILABLE and self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
    
    @property
    def is_available(self) -> bool:
        return self.model is not None
    
    async def analyze(self, query: str, user_context: Optional[str] = None) -> ComplianceResult:
        """Analyze compliance question"""
        if not self.is_available:
            return self._mock_result(query)
        
        prompt = self._get_prompt(query, user_context)
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_response(response.text)
        except Exception as e:
            print(f"LLM error: {e}")
            return self._mock_result(query)
    
    def _get_prompt(self, query: str, context: Optional[str]) -> str:
        context_str = f"\nUser Context: {context}" if context else ""
        
        return f"""You are an expert in Indian GST, Tax Law, and MSME compliance.

Question: {query}{context_str}

Analyze this question and provide:
1. Risk Level: LOW (routine compliance), MEDIUM (needs attention), HIGH (immediate action required)
2. Relevant Section: The most relevant law/act section
3. Explanation: Clear, practical explanation
4. Compliant Action: Specific action the user should take

**OUTPUT FORMAT (JSON ONLY):**
{{
  "risk_level": "LOW|MEDIUM|HIGH",
  "relevant_section": "Section X of Act Name",
  "explanation": "Clear explanation in 2-3 sentences",
  "compliant_action": "Specific action to take"
}}"""
    
    def _parse_response(self, response_text: str) -> ComplianceResult:
        """Parse LLM response"""
        try:
            text = response_text.strip()
            
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(text)
            
            return ComplianceResult(
                risk_level=data.get("risk_level", "MEDIUM"),
                relevant_section=data.get("relevant_section", "Consult a tax professional"),
                explanation=data.get("explanation", "Unable to parse response"),
                compliant_action=data.get("compliant_action", "Consult a qualified CA for specific advice")
            )
            
        except Exception as e:
            print(f"Parse error: {e}")
            return ComplianceResult(
                risk_level="MEDIUM",
                relevant_section="Unable to determine",
                explanation=response_text[:500] if response_text else "No response",
                compliant_action="Please consult a tax professional for accurate guidance"
            )
    
    def _mock_result(self, query: str) -> ComplianceResult:
        """Return mock result when API unavailable"""
        # Simple keyword matching for demo
        query_lower = query.lower()
        
        if "itc" in query_lower or "input tax credit" in query_lower:
            return ComplianceResult(
                risk_level="MEDIUM",
                relevant_section="Section 17(5) of CGST Act, 2017",
                explanation="Input Tax Credit has specific blocked categories under Section 17(5). Food, beverages, personal items, and vehicles generally cannot claim ITC unless used for further taxable supply.",
                compliant_action="Review your expense categories against blocked ITC list. Maintain proper documentation for eligible claims."
            )
        elif "gstr" in query_lower or "filing" in query_lower:
            return ComplianceResult(
                risk_level="HIGH",
                relevant_section="Section 39 of CGST Act, 2017",
                explanation="GSTR-3B is due by 20th of the following month. Late filing attracts interest at 18% p.a. and late fee of ₹50/day (CGST+SGST).",
                compliant_action="Set calendar reminders for GST filing dates. File returns before due date to avoid penalties."
            )
        else:
            return ComplianceResult(
                risk_level="LOW",
                relevant_section="Consult tax professional",
                explanation="This query requires specific analysis. Configure GEMINI_API_KEY for AI-powered compliance answers.",
                compliant_action="For accurate guidance, please consult a qualified Chartered Accountant."
            )
