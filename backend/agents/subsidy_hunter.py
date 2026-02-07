"""
Subsidy Hunter - Agent C
AI-powered government scheme discovery
"""

import os
import json
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

# Try importing google.generativeai
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class Subsidy(BaseModel):
    name: str
    benefit: str
    eligibility: str
    ministry: str
    link: Optional[str] = None
    max_subsidy: Optional[str] = None
    match_score: Optional[float] = None


class SubsidyHunter:
    """
    Agent C: Subsidy Hunter
    Finds applicable government subsidies based on business profile
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
    
    async def find_subsidies(
        self, 
        sector: str, 
        capex: float, 
        state: Optional[str] = None
    ) -> List[Subsidy]:
        """Find applicable subsidies for given criteria"""
        if not self.is_available:
            return self._mock_subsidies(sector, capex)
        
        prompt = self._get_prompt(sector, capex, state)
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_response(response.text)
        except Exception as e:
            print(f"LLM error: {e}")
            return self._mock_subsidies(sector, capex)
    
    def _get_prompt(self, sector: str, capex: float, state: Optional[str]) -> str:
        state_str = state if state and state != "All India" else "pan-India"
        
        return f"""You are an expert in Indian Government schemes and subsidies for MSMEs.

Find applicable subsidies for:
- Sector: {sector}
- Capital Expenditure: ₹{capex:,.0f}
- State: {state_str}

Provide 3-5 REAL government schemes with accurate details:
1. Official scheme name
2. Actual benefits offered
3. Eligibility criteria
4. Implementing ministry/department
5. Official application URL (if available)

**OUTPUT FORMAT (JSON ARRAY ONLY):**
[
  {{
    "name": "Official Scheme Name",
    "benefit": "Subsidy percentage or amount",
    "eligibility": "Who can apply",
    "ministry": "Ministry/Department name",
    "link": "Official URL or null",
    "max_subsidy": "Maximum subsidy amount or null"
  }}
]"""
    
    def _parse_response(self, response_text: str) -> List[Subsidy]:
        """Parse LLM response to list of subsidies"""
        try:
            text = response_text.strip()
            
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(text)
            
            if not isinstance(data, list):
                data = [data]
            
            return [
                Subsidy(
                    name=item.get("name", "Unknown Scheme"),
                    benefit=item.get("benefit", "Contact ministry for details"),
                    eligibility=item.get("eligibility", "Check official website"),
                    ministry=item.get("ministry", "Various ministries"),
                    link=item.get("link"),
                    max_subsidy=item.get("max_subsidy")
                )
                for item in data
            ]
            
        except Exception as e:
            print(f"Parse error: {e}")
            return []
    
    def _mock_subsidies(self, sector: str, capex: float) -> List[Subsidy]:
        """Return mock subsidies when API unavailable"""
        # Common schemes applicable to most MSMEs
        schemes = [
            Subsidy(
                name="PM Vishwakarma Scheme",
                benefit="Skill training + Rs 15,000 toolkit + Credit up to ₹3 lakh at 5% interest",
                eligibility="Traditional artisans and craftspeople in 18 specified trades",
                ministry="Ministry of MSME",
                link="https://pmvishwakarma.gov.in",
                max_subsidy="₹3,00,000 collateral-free credit"
            ),
            Subsidy(
                name="PMEGP (Prime Minister's Employment Generation Programme)",
                benefit="15-35% capital subsidy on project cost",
                eligibility="New manufacturing units with project cost up to ₹50 lakh",
                ministry="Ministry of MSME via KVIC",
                link="https://www.kviconline.gov.in/pmegpeportal/",
                max_subsidy="35% for special category in rural areas"
            ),
            Subsidy(
                name="Credit Guarantee Fund Trust for Micro and Small Enterprises (CGTMSE)",
                benefit="Collateral-free credit up to ₹5 crore",
                eligibility="New and existing micro/small enterprises",
                ministry="Ministry of MSME",
                link="https://www.cgtmse.in",
                max_subsidy="Coverage up to 85% of credit facility"
            ),
            Subsidy(
                name="MUDRA Yojana",
                benefit="Loans up to ₹10 lakh without collateral",
                eligibility="Non-corporate, non-farm small/micro enterprises",
                ministry="Ministry of Finance",
                link="https://www.mudra.org.in",
                max_subsidy="₹10,00,000 (Tarun category)"
            )
        ]
        
        # Add sector-specific scheme
        if "manufacturing" in sector.lower():
            schemes.insert(0, Subsidy(
                name="Production Linked Incentive (PLI) Scheme",
                benefit="4-6% incentive on incremental sales for 5 years",
                eligibility="Manufacturing companies meeting investment thresholds",
                ministry="Various ministries (sector-specific)",
                link="https://www.makeinindia.com/pli",
                max_subsidy="Varies by sector"
            ))
        
        return schemes[:5]
