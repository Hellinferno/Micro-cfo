"""
Subsidy Scraper Service
Web scraping for Indian government subsidy schemes
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re
from datetime import datetime
import json


class SubsidyScraper:
    """Scrapes government websites for MSME subsidy information"""
    
    # Source URLs for scraping
    SOURCES = {
        "msme_schemes": "https://msme.gov.in/all-schemes",
        "my_msme": "https://my.msme.gov.in/MyMsme/Reg/Home.aspx",
        "startup_india": "https://www.startupindia.gov.in/content/sih/en/government-schemes.html",
        "mudra": "https://www.mudra.org.in/",
    }
    
    # Fallback data when scraping fails
    FALLBACK_SCHEMES = [
        {
            "name": "PM Vishwakarma Scheme",
            "benefit": "Skill training + Rs 15,000 toolkit + Credit up to ₹3 lakh at 5%",
            "eligibility": "Traditional artisans in 18 trades",
            "ministry": "Ministry of MSME",
            "link": "https://pmvishwakarma.gov.in",
            "max_subsidy": "₹3,00,000",
            "sector": "all"
        },
        {
            "name": "PMEGP (Prime Minister's Employment Generation Programme)",
            "benefit": "15-35% capital subsidy on project cost",
            "eligibility": "New manufacturing units, project cost up to ₹50 lakh",
            "ministry": "Ministry of MSME via KVIC",
            "link": "https://www.kviconline.gov.in/pmegpeportal/",
            "max_subsidy": "35% for special category",
            "sector": "manufacturing"
        },
        {
            "name": "Credit Guarantee Fund (CGTMSE)",
            "benefit": "Collateral-free credit up to ₹5 crore",
            "eligibility": "New and existing micro/small enterprises",
            "ministry": "Ministry of MSME",
            "link": "https://www.cgtmse.in",
            "max_subsidy": "85% coverage",
            "sector": "all"
        },
        {
            "name": "MUDRA Yojana",
            "benefit": "Loans up to ₹10 lakh without collateral",
            "eligibility": "Non-corporate, non-farm small/micro enterprises",
            "ministry": "Ministry of Finance",
            "link": "https://www.mudra.org.in",
            "max_subsidy": "₹10,00,000",
            "sector": "all"
        },
        {
            "name": "Stand-Up India",
            "benefit": "Loans between ₹10 lakh to ₹1 crore",
            "eligibility": "SC/ST and women entrepreneurs for greenfield projects",
            "ministry": "Ministry of Finance",
            "link": "https://www.standupmitra.in",
            "max_subsidy": "₹1,00,00,000",
            "sector": "all"
        },
        {
            "name": "Production Linked Incentive (PLI) Scheme",
            "benefit": "4-6% incentive on incremental sales for 5 years",
            "eligibility": "Manufacturing companies meeting investment thresholds",
            "ministry": "Various ministries",
            "link": "https://www.makeinindia.com/pli",
            "max_subsidy": "Varies by sector",
            "sector": "manufacturing"
        },
        {
            "name": "Technology Upgradation Fund Scheme (TUFS)",
            "benefit": "5% interest subsidy on term loans",
            "eligibility": "Textile manufacturing units",
            "ministry": "Ministry of Textiles",
            "link": "https://texmin.nic.in",
            "max_subsidy": "5% interest reimbursement",
            "sector": "textile"
        },
        {
            "name": "SFURTI (Scheme of Fund for Regeneration of Traditional Industries)",
            "benefit": "Up to ₹2.5 crore for traditional industry clusters",
            "eligibility": "Traditional artisan clusters",
            "ministry": "Ministry of MSME",
            "link": "https://sfurti.msme.gov.in",
            "max_subsidy": "₹2,50,00,000",
            "sector": "manufacturing"
        },
        {
            "name": "ASPIRE (Livelihood Business Incubators)",
            "benefit": "Support for agro-industry startups",
            "eligibility": "Agro and rural industry entrepreneurs",
            "ministry": "Ministry of MSME",
            "link": "https://msme.gov.in/aspire",
            "max_subsidy": "Incubation support",
            "sector": "agriculture"
        },
        {
            "name": "Women Entrepreneurship Platform (WEP)",
            "benefit": "Mentorship + funding access + networking",
            "eligibility": "Women-led enterprises",
            "ministry": "NITI Aayog",
            "link": "https://wep.gov.in",
            "max_subsidy": "Various",
            "sector": "women_entrepreneur"
        },
        {
            "name": "PMFME (PM Formalisation of Micro Food Processing)",
            "benefit": "35% capital subsidy up to ₹10 lakh",
            "eligibility": "Micro food processing units",
            "ministry": "Ministry of Food Processing",
            "link": "https://pmfme.mofpi.gov.in",
            "max_subsidy": "₹10,00,000",
            "sector": "food_processing"
        },
        {
            "name": "Pharma & Medical Device PLI",
            "benefit": "Up to 10% sales-based incentive",
            "eligibility": "Pharmaceutical manufacturing units",
            "ministry": "Department of Pharmaceuticals",
            "link": "https://pharmaceuticals.gov.in/schemes",
            "max_subsidy": "10% of incremental sales",
            "sector": "pharma"
        }
    ]
    
    def __init__(self):
        self.session = None
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour cache
        self.last_scrape = None
    
    async def _get_session(self):
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=10)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None
    
    async def scrape_msme_schemes(self) -> List[Dict]:
        """Scrape schemes from msme.gov.in"""
        try:
            session = await self._get_session()
            async with session.get(
                self.SOURCES["msme_schemes"],
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            ) as response:
                if response.status != 200:
                    return []
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                schemes = []
                # Look for scheme cards/links
                scheme_elements = soup.find_all(['div', 'article'], class_=re.compile(r'scheme|card|item', re.I))
                
                for elem in scheme_elements[:10]:
                    title = elem.find(['h2', 'h3', 'h4', 'a'])
                    if title:
                        schemes.append({
                            "name": title.get_text(strip=True),
                            "benefit": "Contact ministry for details",
                            "eligibility": "Check official website",
                            "ministry": "Ministry of MSME",
                            "link": f"https://msme.gov.in{title.get('href', '')}",
                            "source": "msme.gov.in"
                        })
                
                return schemes
                
        except Exception as e:
            print(f"Scraping error (msme.gov.in): {e}")
            return []
    
    async def scrape_startup_india(self) -> List[Dict]:
        """Scrape schemes from Startup India"""
        try:
            session = await self._get_session()
            async with session.get(
                self.SOURCES["startup_india"],
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            ) as response:
                if response.status != 200:
                    return []
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                schemes = []
                scheme_cards = soup.find_all(['div'], class_=re.compile(r'scheme|card|gov', re.I))
                
                for card in scheme_cards[:10]:
                    title = card.find(['h2', 'h3', 'h4'])
                    desc = card.find('p')
                    if title:
                        schemes.append({
                            "name": title.get_text(strip=True),
                            "benefit": desc.get_text(strip=True) if desc else "See details",
                            "eligibility": "Startups registered with DPIIT",
                            "ministry": "DPIIT",
                            "link": "https://www.startupindia.gov.in",
                            "source": "startupindia.gov.in"
                        })
                
                return schemes
                
        except Exception as e:
            print(f"Scraping error (startupindia): {e}")
            return []
    
    async def get_all_schemes(self, use_cache: bool = True) -> List[Dict]:
        """Get all scraped schemes with fallback"""
        
        # Check cache
        if use_cache and self.cache.get("all_schemes"):
            cache_time = self.cache.get("cache_time", 0)
            if (datetime.now().timestamp() - cache_time) < self.cache_ttl:
                return self.cache["all_schemes"]
        
        # Try scraping
        schemes = []
        try:
            # Attempt to scrape from multiple sources
            results = await asyncio.gather(
                self.scrape_msme_schemes(),
                self.scrape_startup_india(),
                return_exceptions=True
            )
            
            for result in results:
                if isinstance(result, list):
                    schemes.extend(result)
        except Exception as e:
            print(f"Scraping failed: {e}")
        
        # If scraping failed or returned no results, use fallback
        if not schemes:
            schemes = self.FALLBACK_SCHEMES.copy()
        else:
            # Merge with fallback to ensure comprehensive coverage
            existing_names = {s["name"].lower() for s in schemes}
            for fallback in self.FALLBACK_SCHEMES:
                if fallback["name"].lower() not in existing_names:
                    schemes.append(fallback)
        
        # Update cache
        self.cache["all_schemes"] = schemes
        self.cache["cache_time"] = datetime.now().timestamp()
        
        return schemes
    
    def filter_by_sector(self, schemes: List[Dict], sector: str) -> List[Dict]:
        """Filter schemes by sector"""
        sector_lower = sector.lower()
        
        # Sector mapping for flexible matching
        sector_map = {
            "manufacturing": ["manufacturing", "production", "pli", "industry"],
            "textile": ["textile", "garment", "apparel", "tufs", "fabric"],
            "food_processing": ["food", "pmfme", "dairy", "agro"],
            "agriculture": ["agro", "rural", "farm", "aspire"],
            "it": ["it", "tech", "software", "digital", "startup"],
            "pharma": ["pharma", "medicine", "drug", "healthcare"],
            "women_entrepreneur": ["women", "wep", "female"],
            "services": ["service", "consulting"],
        }
        
        # Find matching keywords for the sector
        keywords = sector_map.get(sector_lower, [sector_lower])
        
        filtered = []
        for scheme in schemes:
            scheme_sector = scheme.get("sector", "all").lower()
            scheme_name = scheme.get("name", "").lower()
            scheme_elig = scheme.get("eligibility", "").lower()
            
            # Include if sector is "all" or matches any keyword
            if scheme_sector == "all":
                filtered.append(scheme)
            elif any(kw in scheme_sector or kw in scheme_name or kw in scheme_elig for kw in keywords):
                filtered.append(scheme)
        
        return filtered if filtered else schemes[:5]  # Return top 5 if no match
    
    def filter_by_capex(self, schemes: List[Dict], capex: float) -> List[Dict]:
        """Filter schemes by capital expenditure amount"""
        # For now, return all schemes as most don't have strict capex limits
        # Future: Parse max_subsidy to filter
        return schemes
    
    def calculate_match_score(self, scheme: Dict, sector: str, capex: float) -> float:
        """Calculate match score for a scheme"""
        score = 50  # Base score
        
        scheme_sector = scheme.get("sector", "all").lower()
        sector_lower = sector.lower() if sector else ""
        
        # Sector match bonus
        if scheme_sector == "all":
            score += 20
        elif sector_lower in scheme_sector:
            score += 40
        
        # Has official link bonus
        if scheme.get("link") and "gov.in" in scheme.get("link", ""):
            score += 10
        
        # Normalize to 0-100
        return min(100, max(0, score))


# Global instance
scraper = SubsidyScraper()
