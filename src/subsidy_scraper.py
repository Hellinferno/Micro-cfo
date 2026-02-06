#!/usr/bin/env python3
"""
Subsidy Web Scraper for Real-Time Government Scheme Information
Provides async web scraping with caching and rate limiting for subsidy portals
"""

import asyncio
import hashlib
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class ScrapedScheme:
    """Data class for scraped subsidy scheme information"""
    name: str
    benefit: str
    eligibility: str
    link: str
    ministry: str
    max_subsidy: Optional[float] = None
    sector: Optional[str] = None
    scraped_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format matching SCHEME_DATABASE structure"""
        return {
            "name": self.name,
            "benefit": self.benefit,
            "max_subsidy": self.max_subsidy or 10000000,  # Default 1 Cr if not found
            "eligibility": self.eligibility,
            "link": self.link,
            "ministry": self.ministry,
            "scraped_at": self.scraped_at.isoformat(),
            "is_live": True
        }


class SubsidyScraperCache:
    """Simple in-memory cache for scraped data with TTL"""
    
    def __init__(self, ttl_hours: int = 24):
        self._cache: Dict[str, tuple] = {}  # key -> (data, expiry_time)
        self._ttl = timedelta(hours=ttl_hours)
    
    def _generate_key(self, sector: str, source: str) -> str:
        """Generate cache key from sector and source"""
        return hashlib.md5(f"{sector}:{source}".encode()).hexdigest()
    
    def get(self, sector: str, source: str) -> Optional[List[ScrapedScheme]]:
        """Get cached data if not expired"""
        key = self._generate_key(sector, source)
        if key in self._cache:
            data, expiry = self._cache[key]
            if datetime.now() < expiry:
                logger.debug(f"Cache hit for {sector}:{source}")
                return data
            else:
                del self._cache[key]
        return None
    
    def set(self, sector: str, source: str, data: List[ScrapedScheme]) -> None:
        """Store data in cache"""
        key = self._generate_key(sector, source)
        expiry = datetime.now() + self._ttl
        self._cache[key] = (data, expiry)
        logger.debug(f"Cached {len(data)} schemes for {sector}:{source}")
    
    def clear(self) -> None:
        """Clear all cached data"""
        self._cache.clear()


class RateLimiter:
    """Simple rate limiter for web requests"""
    
    def __init__(self, min_delay_seconds: float = 2.0):
        self._last_request: Dict[str, datetime] = {}
        self._min_delay = timedelta(seconds=min_delay_seconds)
        self._lock = asyncio.Lock()
    
    async def wait_for_slot(self, domain: str) -> None:
        """Wait until we can make a request to the domain"""
        async with self._lock:
            if domain in self._last_request:
                elapsed = datetime.now() - self._last_request[domain]
                if elapsed < self._min_delay:
                    wait_time = (self._min_delay - elapsed).total_seconds()
                    logger.debug(f"Rate limiting: waiting {wait_time:.1f}s for {domain}")
                    await asyncio.sleep(wait_time)
            self._last_request[domain] = datetime.now()


class SubsidyScraper:
    """
    Web scraper for government subsidy portals
    
    Features:
    - Async HTTP requests with httpx
    - BeautifulSoup parsing with lxml backend
    - Built-in caching (24-hour TTL)
    - Rate limiting (1 request per 2 seconds per domain)
    - Graceful error handling with fallback support
    """
    
    # Government portal configurations
    PORTAL_CONFIGS = {
        "msme": {
            "base_url": "https://msme.gov.in",
            "schemes_path": "/schemes",
            "name": "Ministry of MSME",
            "sectors": ["manufacturing", "services", "technology", "it"]
        },
        "mofpi": {
            "base_url": "https://mofpi.gov.in",
            "schemes_path": "/schemes",
            "name": "Ministry of Food Processing",
            "sectors": ["food_processing", "agriculture"]
        },
        "textiles": {
            "base_url": "https://texmin.nic.in",
            "schemes_path": "/schemes",
            "name": "Ministry of Textiles",
            "sectors": ["textile", "textiles"]
        },
        "pli": {
            "base_url": "https://invest.gov.in",
            "schemes_path": "/pli-schemes/",
            "name": "DPIIT - PLI Schemes",
            "sectors": ["manufacturing", "pharma", "technology", "automotive"]
        }
    }
    
    def __init__(self, cache_ttl_hours: int = 24, rate_limit_seconds: float = 2.0):
        """
        Initialize the subsidy scraper
        
        Args:
            cache_ttl_hours: How long to cache scraped data (default 24 hours)
            rate_limit_seconds: Minimum delay between requests to same domain
        """
        self._cache = SubsidyScraperCache(ttl_hours=cache_ttl_hours)
        self._rate_limiter = RateLimiter(min_delay_seconds=rate_limit_seconds)
        self._client: Optional[httpx.AsyncClient] = None
        
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                headers={
                    "User-Agent": "MicroCFO-SubsidyHunter/1.0 (Government Scheme Search Bot)",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5"
                }
            )
        return self._client
    
    async def close(self) -> None:
        """Close the HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL for rate limiting"""
        parsed = urlparse(url)
        return parsed.netloc
    
    async def _fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a page with rate limiting and error handling
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content or None on failure
        """
        domain = self._get_domain(url)
        await self._rate_limiter.wait_for_slot(domain)
        
        try:
            client = await self._get_client()
            response = await client.get(url)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error fetching {url}: {e.response.status_code}")
            return None
        except httpx.RequestError as e:
            logger.warning(f"Request error fetching {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {str(e)}")
            return None
    
    def _parse_schemes_from_html(self, html: str, base_url: str, ministry: str) -> List[ScrapedScheme]:
        """
        Parse scheme information from HTML content
        
        This method uses heuristics to extract scheme information from various
        government portal formats.
        
        Args:
            html: HTML content
            base_url: Base URL for resolving relative links
            ministry: Ministry name for attribution
            
        Returns:
            List of parsed schemes
        """
        schemes = []
        soup = BeautifulSoup(html, "lxml")
        
        # Common patterns for scheme listings on government sites
        # Pattern 1: Cards/boxes with scheme info
        scheme_cards = soup.find_all(["div", "article", "section"], 
                                      class_=re.compile(r"scheme|card|box|item", re.I))
        
        for card in scheme_cards[:10]:  # Limit to first 10 to avoid noise
            scheme = self._extract_scheme_from_element(card, base_url, ministry)
            if scheme:
                schemes.append(scheme)
        
        # Pattern 2: Tables with scheme data
        tables = soup.find_all("table")
        for table in tables[:3]:  # Limit tables
            table_schemes = self._extract_schemes_from_table(table, base_url, ministry)
            schemes.extend(table_schemes)
        
        # Pattern 3: List items with links
        if not schemes:
            list_items = soup.find_all("li")
            for li in list_items[:15]:
                scheme = self._extract_scheme_from_list_item(li, base_url, ministry)
                if scheme:
                    schemes.append(scheme)
        
        # Deduplicate by name
        seen = set()
        unique_schemes = []
        for scheme in schemes:
            if scheme.name not in seen:
                seen.add(scheme.name)
                unique_schemes.append(scheme)
        
        return unique_schemes
    
    def _extract_scheme_from_element(self, element, base_url: str, ministry: str) -> Optional[ScrapedScheme]:
        """Extract scheme info from a card/box element"""
        try:
            # Find title (usually in h2, h3, h4, or strong)
            title_elem = element.find(["h2", "h3", "h4", "h5", "strong", "a"])
            if not title_elem:
                return None
            
            name = title_elem.get_text(strip=True)
            if len(name) < 5 or len(name) > 200:  # Filter noise
                return None
            
            # Find link
            link_elem = element.find("a", href=True)
            link = urljoin(base_url, link_elem["href"]) if link_elem else base_url
            
            # Find description/benefit text
            paragraphs = element.find_all("p")
            benefit_text = " ".join(p.get_text(strip=True) for p in paragraphs[:2])
            if not benefit_text:
                benefit_text = element.get_text(strip=True)[:200]
            
            # Try to extract subsidy percentage
            max_subsidy = self._extract_subsidy_amount(benefit_text)
            
            return ScrapedScheme(
                name=name,
                benefit=benefit_text[:300] if benefit_text else "Check official portal for details",
                eligibility="Check eligibility on official portal",
                link=link,
                ministry=ministry,
                max_subsidy=max_subsidy
            )
        except Exception as e:
            logger.debug(f"Failed to extract scheme from element: {e}")
            return None
    
    def _extract_schemes_from_table(self, table, base_url: str, ministry: str) -> List[ScrapedScheme]:
        """Extract schemes from a table element"""
        schemes = []
        rows = table.find_all("tr")[1:]  # Skip header row
        
        for row in rows[:10]:  # Limit rows
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                name_cell = cells[0]
                name = name_cell.get_text(strip=True)
                
                if len(name) < 5 or len(name) > 200:
                    continue
                
                # Get link from first cell if available
                link_elem = name_cell.find("a", href=True)
                link = urljoin(base_url, link_elem["href"]) if link_elem else base_url
                
                # Get benefit from second cell
                benefit = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                
                schemes.append(ScrapedScheme(
                    name=name,
                    benefit=benefit[:300] if benefit else "Check official portal",
                    eligibility="Check eligibility on official portal",
                    link=link,
                    ministry=ministry,
                    max_subsidy=self._extract_subsidy_amount(benefit)
                ))
        
        return schemes
    
    def _extract_scheme_from_list_item(self, li, base_url: str, ministry: str) -> Optional[ScrapedScheme]:
        """Extract scheme from a list item"""
        try:
            link_elem = li.find("a", href=True)
            if not link_elem:
                return None
            
            name = link_elem.get_text(strip=True)
            if len(name) < 5 or len(name) > 200:
                return None
            
            # Filter out navigation links
            if any(word in name.lower() for word in ["home", "contact", "about", "login", "register"]):
                return None
            
            link = urljoin(base_url, link_elem["href"])
            
            # Get surrounding text as benefit description
            parent_text = li.get_text(strip=True)
            benefit = parent_text[:300] if parent_text != name else "Check official portal"
            
            return ScrapedScheme(
                name=name,
                benefit=benefit,
                eligibility="Check eligibility on official portal",
                link=link,
                ministry=ministry,
                max_subsidy=self._extract_subsidy_amount(benefit)
            )
        except Exception:
            return None
    
    def _extract_subsidy_amount(self, text: str) -> Optional[float]:
        """Try to extract subsidy/benefit amount from text"""
        if not text:
            return None
        
        # Look for patterns like "Rs 10 lakhs", "₹10,00,000", "10 crore"
        patterns = [
            r"₹?\s*([\d,]+)\s*(?:crore|cr)",  # Crores
            r"₹?\s*([\d,]+)\s*(?:lakh|lac)",   # Lakhs
            r"Rs\.?\s*([\d,]+)\s*(?:crore|cr)",
            r"Rs\.?\s*([\d,]+)\s*(?:lakh|lac)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                try:
                    amount = float(match.group(1).replace(",", ""))
                    if "crore" in pattern or "cr" in pattern:
                        return amount * 10000000
                    else:
                        return amount * 100000
                except ValueError:
                    continue
        
        return None
    
    def _get_portals_for_sector(self, sector: str) -> List[str]:
        """Get list of portal keys relevant to a sector"""
        sector_lower = sector.lower().replace(" ", "_").replace("-", "_")
        relevant_portals = []
        
        for portal_key, config in self.PORTAL_CONFIGS.items():
            if sector_lower in config["sectors"]:
                relevant_portals.append(portal_key)
        
        # Always include MSME as fallback for manufacturing-related sectors
        if not relevant_portals and sector_lower not in ["food_processing", "agriculture"]:
            relevant_portals = ["msme", "pli"]
        elif not relevant_portals:
            relevant_portals = ["mofpi"]
        
        return relevant_portals
    
    async def search_schemes(self, sector: str, capex_amount: float = 0) -> List[Dict[str, Any]]:
        """
        Search for subsidy schemes for a given sector
        
        Args:
            sector: Business sector to search for
            capex_amount: Capital expenditure amount (for filtering)
            
        Returns:
            List of scheme dictionaries in SCHEME_DATABASE format
        """
        all_schemes = []
        portals = self._get_portals_for_sector(sector)
        
        for portal_key in portals:
            config = self.PORTAL_CONFIGS.get(portal_key)
            if not config:
                continue
            
            # Check cache first
            cached = self._cache.get(sector, portal_key)
            if cached:
                all_schemes.extend([s.to_dict() for s in cached])
                continue
            
            # Fetch and parse
            url = config["base_url"] + config["schemes_path"]
            logger.info(f"Scraping {config['name']} for {sector} schemes: {url}")
            
            html = await self._fetch_page(url)
            if html:
                schemes = self._parse_schemes_from_html(html, config["base_url"], config["name"])
                if schemes:
                    self._cache.set(sector, portal_key, schemes)
                    all_schemes.extend([s.to_dict() for s in schemes])
                    logger.info(f"Found {len(schemes)} schemes from {config['name']}")
                else:
                    logger.warning(f"No schemes parsed from {config['name']}")
            else:
                logger.warning(f"Failed to fetch {url}")
        
        return all_schemes
    
    async def search_schemes_with_fallback(
        self, 
        sector: str, 
        capex_amount: float,
        static_schemes: List[Dict[str, Any]]
    ) -> tuple[List[Dict[str, Any]], str]:
        """
        Search with fallback to static data
        
        Args:
            sector: Business sector
            capex_amount: Capital expenditure amount
            static_schemes: Fallback static scheme data
            
        Returns:
            Tuple of (schemes list, data_source indicator)
        """
        try:
            live_schemes = await self.search_schemes(sector, capex_amount)
            
            if live_schemes:
                # Merge with static for completeness
                # Static schemes have verified data, so keep them and add live ones
                scheme_names = {s["name"] for s in static_schemes}
                for live_scheme in live_schemes:
                    if live_scheme["name"] not in scheme_names:
                        static_schemes.append(live_scheme)
                
                return static_schemes, "live_enhanced"
            else:
                return static_schemes, "static"
                
        except Exception as e:
            logger.error(f"Scraper error, falling back to static: {e}")
            return static_schemes, "static_fallback"


# Singleton instance for use across the application
_scraper_instance: Optional[SubsidyScraper] = None


def get_subsidy_scraper() -> SubsidyScraper:
    """Get or create the global scraper instance"""
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = SubsidyScraper()
    return _scraper_instance


async def cleanup_scraper() -> None:
    """Cleanup the global scraper instance"""
    global _scraper_instance
    if _scraper_instance:
        await _scraper_instance.close()
        _scraper_instance = None
