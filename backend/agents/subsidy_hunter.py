"""
Subsidy Hunter - Agent C
AI-powered government scheme discovery with web scraping
"""

import os
import json
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

# Import web scraper
from backend.services.subsidy_scraper import scraper, SubsidyScraper


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
    Finds applicable government subsidies using web scraping
    """
    
    def __init__(self):
        self.scraper = scraper  # Use global scraper instance
    
    async def find_subsidies(
        self, 
        sector: str, 
        capex: float, 
        state: Optional[str] = None
    ) -> List[Subsidy]:
        """Find applicable subsidies using web scraping"""
        
        # Get all schemes from scraper (with fallback)
        all_schemes = await self.scraper.get_all_schemes(use_cache=True)
        
        # Filter by sector
        if sector:
            filtered = self.scraper.filter_by_sector(all_schemes, sector)
        else:
            filtered = all_schemes
        
        # Filter by capex
        filtered = self.scraper.filter_by_capex(filtered, capex)
        
        # Calculate match scores and convert to Subsidy models
        subsidies = []
        for scheme in filtered[:10]:  # Limit to top 10
            match_score = self.scraper.calculate_match_score(scheme, sector, capex)
            subsidies.append(Subsidy(
                name=scheme.get("name", "Unknown Scheme"),
                benefit=scheme.get("benefit", "Contact ministry for details"),
                eligibility=scheme.get("eligibility", "Check official website"),
                ministry=scheme.get("ministry", "Various ministries"),
                link=scheme.get("link"),
                max_subsidy=scheme.get("max_subsidy"),
                match_score=match_score
            ))
        
        # Sort by match score
        subsidies.sort(key=lambda x: x.match_score or 0, reverse=True)
        
        return subsidies[:5]  # Return top 5
    
    async def search_by_query(self, query: str) -> List[Subsidy]:
        """Search subsidies by natural language query"""
        
        # Extract sector from query
        sector = self._extract_sector_from_query(query)
        
        # Extract amount from query
        capex = self._extract_amount_from_query(query)
        
        return await self.find_subsidies(sector, capex)
    
    def _extract_sector_from_query(self, query: str) -> str:
        """Extract sector from natural language query"""
        query_lower = query.lower()
        
        sector_keywords = {
            "manufacturing": ["manufacturing", "factory", "plant", "production", "industrial"],
            "textile": ["textile", "garment", "apparel", "fabric", "yarn", "clothing"],
            "food_processing": ["food", "dairy", "beverage", "bakery", "processing"],
            "agriculture": ["farm", "agri", "rural", "village", "crop"],
            "it": ["it", "software", "tech", "digital", "app", "saas"],
            "pharma": ["pharma", "drug", "medicine", "medical", "healthcare"],
            "women_entrepreneur": ["women", "woman", "female", "lady"],
            "services": ["service", "consulting", "hotel", "tourism"],
        }
        
        for sector, keywords in sector_keywords.items():
            if any(kw in query_lower for kw in keywords):
                return sector
        
        return "manufacturing"  # Default
    
    def _extract_amount_from_query(self, query: str) -> float:
        """Extract CAPEX amount from query"""
        import re
        
        query_lower = query.lower()
        
        # Try to parse crore
        crore_match = re.search(r'(\d+(?:\.\d+)?)\s*cr(?:ore)?', query_lower)
        if crore_match:
            return float(crore_match.group(1)) * 10000000
        
        # Try to parse lakh
        lakh_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:lakh?|lac)', query_lower)
        if lakh_match:
            return float(lakh_match.group(1)) * 100000
        
        # Try to parse raw number
        num_match = re.search(r'(\d+(?:,\d{3})*(?:\.\d+)?)', query)
        if num_match:
            return float(num_match.group(1).replace(',', ''))
        
        return 1000000  # Default 10 lakh
    
    async def refresh_schemes(self) -> int:
        """Force refresh schemes from web sources"""
        # Clear cache and re-scrape
        self.scraper.cache.clear()
        schemes = await self.scraper.get_all_schemes(use_cache=False)
        return len(schemes)
