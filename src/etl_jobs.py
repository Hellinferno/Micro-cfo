#!/usr/bin/env python3
"""
ETL Jobs and Scheduled Tasks for MicroCFO
Implements daily data scraping, compliance updates, and cash flow predictions

Based on Backend PRD:
- Government Data Scraping (subsidies, laws)
- Compliance Calendar Updates
- Cash Flow Predictions
- Data Cleanup Jobs
"""

import os
import logging
import asyncio
import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import schedule
import time
import threading

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class JobResult:
    """Result of a scheduled job"""
    job_name: str
    status: JobStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    records_processed: int = 0
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class GovernmentDataScraper:
    """
    Scrapes government websites for subsidies and legislative updates
    
    Sources:
    - MSME schemes: msme.gov.in
    - GST updates: cbic-gst.gov.in
    - MCA filings: mca.gov.in
    - Startup India: startupindia.gov.in
    - State subsidies: Various state portals
    """
    
    def __init__(self):
        self.sources = {
            'msme': {
                'url': 'https://msme.gov.in/schemes-programmes',
                'name': 'MSME Ministry',
                'type': 'subsidy'
            },
            'startup_india': {
                'url': 'https://www.startupindia.gov.in/content/sih/en/government-schemes.html',
                'name': 'Startup India',
                'type': 'subsidy'
            },
            'gst': {
                'url': 'https://cbic-gst.gov.in/circulars.html',
                'name': 'GST Council',
                'type': 'legislative'
            },
            'mca': {
                'url': 'https://www.mca.gov.in/content/mca/global/en/acts-rules/ebooks.html',
                'name': 'MCA',
                'type': 'legislative'
            },
            'rbi': {
                'url': 'https://www.rbi.org.in/Scripts/BS_CircularIndexDisplay.aspx',
                'name': 'RBI',
                'type': 'legislative'
            }
        }
        
        self.headers = {
            'User-Agent': 'MicroCFO-Bot/1.0 (Financial Compliance Tool; contact@microcfo.com)'
        }
        
        # Rate limiting
        self._last_request_time: Dict[str, float] = {}
        self._min_request_interval = 2.0  # seconds between requests to same domain
    
    async def _fetch_page(self, url: str, source_name: str) -> Optional[str]:
        """Fetch page content with rate limiting"""
        
        # Rate limiting
        last_time = self._last_request_time.get(source_name, 0)
        elapsed = time.time() - last_time
        if elapsed < self._min_request_interval:
            await asyncio.sleep(self._min_request_interval - elapsed)
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, headers=self.headers, follow_redirects=True)
                response.raise_for_status()
                self._last_request_time[source_name] = time.time()
                return response.text
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def _parse_subsidies(self, html: str, source_name: str) -> List[Dict[str, Any]]:
        """Parse subsidy information from HTML"""
        subsidies = []
        
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Generic scheme extraction (adjust selectors per site)
            scheme_elements = soup.find_all(['div', 'article', 'li'], class_=lambda x: x and any(
                keyword in str(x).lower() for keyword in ['scheme', 'program', 'subsidy', 'benefit']
            ))
            
            for element in scheme_elements[:20]:  # Limit to avoid noise
                title = element.find(['h2', 'h3', 'h4', 'a', 'strong'])
                if not title:
                    continue
                
                title_text = title.get_text(strip=True)
                if len(title_text) < 10 or len(title_text) > 200:
                    continue
                
                # Extract description
                desc = element.find('p') or element.find('div', class_='description')
                desc_text = desc.get_text(strip=True)[:500] if desc else ""
                
                # Generate unique code
                scheme_code = hashlib.md5(f"{source_name}:{title_text}".encode()).hexdigest()[:12].upper()
                
                subsidies.append({
                    'scheme_code': f"{source_name.upper()}-{scheme_code}",
                    'title': title_text,
                    'description': desc_text,
                    'source': self.sources[source_name]['name'],
                    'source_url': self.sources[source_name]['url'],
                    'scraped_at': datetime.now().isoformat(),
                    'is_active': True,
                    'sector_applicable': self._infer_sectors(title_text, desc_text),
                    'eligibility_criteria': self._extract_eligibility(element),
                    'max_benefit_amount': self._extract_amount(element)
                })
            
        except Exception as e:
            logger.error(f"Error parsing subsidies from {source_name}: {e}")
        
        return subsidies
    
    def _parse_legislative_updates(self, html: str, source_name: str) -> List[Dict[str, Any]]:
        """Parse legislative updates from HTML"""
        updates = []
        
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Look for circulars, notifications, rules
            update_elements = soup.find_all(['tr', 'li', 'div'], class_=lambda x: x and any(
                keyword in str(x).lower() for keyword in ['circular', 'notification', 'rule', 'amendment']
            ))
            
            for element in update_elements[:30]:
                title = element.find(['a', 'td', 'span'])
                if not title:
                    continue
                
                title_text = title.get_text(strip=True)
                if len(title_text) < 10:
                    continue
                
                # Try to extract date
                date_text = self._extract_date(element)
                
                # Extract reference number
                ref_match = element.find(string=lambda t: t and ('/' in t or '-' in t))
                ref_number = ref_match.strip() if ref_match and len(ref_match) < 50 else None
                
                updates.append({
                    'reference_number': ref_number,
                    'title': title_text,
                    'source': self.sources[source_name]['name'],
                    'source_url': self.sources[source_name]['url'],
                    'effective_date': date_text,
                    'scraped_at': datetime.now().isoformat(),
                    'law_type': self._infer_law_type(title_text),
                    'impact_summary': None  # To be filled by AI
                })
            
        except Exception as e:
            logger.error(f"Error parsing legislative updates from {source_name}: {e}")
        
        return updates
    
    def _infer_sectors(self, title: str, desc: str) -> List[str]:
        """Infer applicable sectors from text"""
        sectors = []
        text = f"{title} {desc}".lower()
        
        sector_keywords = {
            'manufacturing': ['manufacturing', 'factory', 'production', 'industrial'],
            'services': ['services', 'service sector', 'it/ites', 'software'],
            'agriculture': ['agriculture', 'agro', 'farming', 'food processing'],
            'textile': ['textile', 'garment', 'apparel', 'weaving'],
            'pharma': ['pharma', 'medical', 'healthcare', 'medicine'],
            'construction': ['construction', 'real estate', 'infrastructure'],
            'retail': ['retail', 'trade', 'commerce', 'e-commerce'],
            'export': ['export', 'foreign trade', 'international'],
        }
        
        for sector, keywords in sector_keywords.items():
            if any(kw in text for kw in keywords):
                sectors.append(sector)
        
        return sectors if sectors else ['general']
    
    def _extract_eligibility(self, element) -> List[str]:
        """Extract eligibility criteria"""
        criteria = []
        
        # Look for lists or bullet points
        lists = element.find_all(['ul', 'ol'])
        for lst in lists:
            items = lst.find_all('li')[:5]
            for item in items:
                text = item.get_text(strip=True)
                if len(text) > 10 and len(text) < 200:
                    criteria.append(text)
        
        return criteria
    
    def _extract_amount(self, element) -> Optional[float]:
        """Extract maximum benefit amount"""
        import re
        
        text = element.get_text()
        
        # Look for amounts in various formats
        patterns = [
            r'₹\s*([\d,]+)\s*(lakh|crore)?',
            r'Rs\.?\s*([\d,]+)\s*(lakh|crore)?',
            r'INR\s*([\d,]+)\s*(lakh|crore)?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = float(match.group(1).replace(',', ''))
                multiplier = match.group(2).lower() if match.group(2) else ''
                
                if multiplier == 'lakh':
                    amount *= 100000
                elif multiplier == 'crore':
                    amount *= 10000000
                
                return amount
        
        return None
    
    def _extract_date(self, element) -> Optional[str]:
        """Extract date from element"""
        import re
        
        text = element.get_text()
        
        # Various date formats
        patterns = [
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
            r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    # Try to parse and normalize
                    from dateutil import parser
                    dt = parser.parse(match.group(1))
                    return dt.strftime('%Y-%m-%d')
                except:
                    return match.group(1)
        
        return None
    
    def _infer_law_type(self, title: str) -> str:
        """Infer type of law/regulation"""
        title_lower = title.lower()
        
        if 'gst' in title_lower or 'goods and services' in title_lower:
            return 'GST'
        elif 'income tax' in title_lower or 'it act' in title_lower:
            return 'Income Tax'
        elif 'companies' in title_lower or 'mca' in title_lower:
            return 'Companies Act'
        elif 'labour' in title_lower or 'employment' in title_lower:
            return 'Labour Law'
        elif 'fema' in title_lower or 'foreign exchange' in title_lower:
            return 'FEMA'
        elif 'rbi' in title_lower or 'banking' in title_lower:
            return 'RBI'
        else:
            return 'Other'
    
    async def scrape_all_subsidies(self) -> JobResult:
        """Daily job: Scrape all subsidy sources"""
        result = JobResult(
            job_name="scrape_subsidies",
            status=JobStatus.RUNNING,
            started_at=datetime.now()
        )
        
        all_subsidies = []
        
        for source_name, source_info in self.sources.items():
            if source_info['type'] != 'subsidy':
                continue
            
            logger.info(f"Scraping subsidies from {source_name}...")
            
            html = await self._fetch_page(source_info['url'], source_name)
            if html:
                subsidies = self._parse_subsidies(html, source_name)
                all_subsidies.extend(subsidies)
                logger.info(f"Found {len(subsidies)} subsidies from {source_name}")
            else:
                result.errors.append(f"Failed to fetch {source_name}")
        
        result.records_processed = len(all_subsidies)
        result.completed_at = datetime.now()
        result.status = JobStatus.COMPLETED if not result.errors else JobStatus.COMPLETED
        result.metadata['subsidies'] = all_subsidies
        
        # Store in database (placeholder)
        await self._store_subsidies(all_subsidies)
        
        return result
    
    async def scrape_legislative_updates(self) -> JobResult:
        """Daily job: Scrape legislative updates"""
        result = JobResult(
            job_name="scrape_legislative_updates",
            status=JobStatus.RUNNING,
            started_at=datetime.now()
        )
        
        all_updates = []
        
        for source_name, source_info in self.sources.items():
            if source_info['type'] != 'legislative':
                continue
            
            logger.info(f"Scraping legislative updates from {source_name}...")
            
            html = await self._fetch_page(source_info['url'], source_name)
            if html:
                updates = self._parse_legislative_updates(html, source_name)
                all_updates.extend(updates)
                logger.info(f"Found {len(updates)} updates from {source_name}")
            else:
                result.errors.append(f"Failed to fetch {source_name}")
        
        result.records_processed = len(all_updates)
        result.completed_at = datetime.now()
        result.status = JobStatus.COMPLETED
        result.metadata['updates'] = all_updates
        
        # Store in database (placeholder)
        await self._store_legislative_updates(all_updates)
        
        return result
    
    async def _store_subsidies(self, subsidies: List[Dict]) -> None:
        """Store subsidies in database and vector DB"""
        try:
            from src.scheme_database import scheme_db
            
            for subsidy in subsidies:
                # Check if already exists
                existing = scheme_db.collection.get(
                    where={"scheme_code": subsidy['scheme_code']}
                )
                
                if not existing['ids']:
                    # Generate embedding
                    text = f"{subsidy['title']} {subsidy['description']}"
                    
                    try:
                        from src.llm_service import generate_embedding
                        embedding = await generate_embedding(text)
                    except:
                        from sentence_transformers import SentenceTransformer
                        model = SentenceTransformer('all-MiniLM-L6-v2')
                        embedding = model.encode(text).tolist()
                    
                    # Store in ChromaDB
                    scheme_db.collection.add(
                        ids=[subsidy['scheme_code']],
                        embeddings=[embedding],
                        metadatas=[subsidy],
                        documents=[text]
                    )
                    logger.info(f"Stored new subsidy: {subsidy['scheme_code']}")
                    
        except Exception as e:
            logger.error(f"Failed to store subsidies: {e}")
    
    async def _store_legislative_updates(self, updates: List[Dict]) -> None:
        """Store legislative updates in database"""
        try:
            from src.vector_database import legal_db
            
            for update in updates:
                if not update.get('reference_number'):
                    continue
                
                # Check if already exists
                doc_id = hashlib.md5(f"{update['source']}:{update['title']}".encode()).hexdigest()
                
                existing = legal_db.collection.get(ids=[doc_id])
                
                if not existing['ids']:
                    text = f"{update['title']} {update.get('impact_summary', '')}"
                    
                    try:
                        from src.llm_service import generate_embedding
                        embedding = await generate_embedding(text)
                    except:
                        from sentence_transformers import SentenceTransformer
                        model = SentenceTransformer('all-MiniLM-L6-v2')
                        embedding = model.encode(text).tolist()
                    
                    legal_db.collection.add(
                        ids=[doc_id],
                        embeddings=[embedding],
                        metadatas=[update],
                        documents=[text]
                    )
                    logger.info(f"Stored new legislative update: {update['title'][:50]}...")
                    
        except Exception as e:
            logger.error(f"Failed to store legislative updates: {e}")


class ComplianceCalendarService:
    """
    Manages compliance calendar for users
    Updates deadlines based on business type and regulations
    """
    
    # Standard compliance deadlines (day of month, or relative)
    COMPLIANCE_DEADLINES = {
        'gst': {
            'GSTR-1': {'day': 11, 'frequency': 'monthly', 'description': 'Outward supplies return'},
            'GSTR-3B': {'day': 20, 'frequency': 'monthly', 'description': 'Summary return'},
            'GSTR-9': {'day': 31, 'month': 12, 'frequency': 'yearly', 'description': 'Annual return'},
        },
        'income_tax': {
            'Advance Tax Q1': {'day': 15, 'month': 6, 'frequency': 'yearly', 'description': 'First installment'},
            'Advance Tax Q2': {'day': 15, 'month': 9, 'frequency': 'yearly', 'description': 'Second installment'},
            'Advance Tax Q3': {'day': 15, 'month': 12, 'frequency': 'yearly', 'description': 'Third installment'},
            'Advance Tax Q4': {'day': 15, 'month': 3, 'frequency': 'yearly', 'description': 'Fourth installment'},
            'ITR Filing': {'day': 31, 'month': 7, 'frequency': 'yearly', 'description': 'Income Tax Return'},
        },
        'tds': {
            'TDS Payment': {'day': 7, 'frequency': 'monthly', 'description': 'TDS deposit'},
            'TDS Return': {'day': 31, 'frequency': 'quarterly', 'description': 'Quarterly TDS return'},
        },
        'pf_esi': {
            'PF Payment': {'day': 15, 'frequency': 'monthly', 'description': 'PF contribution'},
            'ESI Payment': {'day': 15, 'frequency': 'monthly', 'description': 'ESI contribution'},
        },
        'roc': {
            'AOC-4': {'day': 30, 'month': 10, 'frequency': 'yearly', 'description': 'Annual accounts'},
            'MGT-7': {'day': 30, 'month': 11, 'frequency': 'yearly', 'description': 'Annual return'},
            'DIR-3 KYC': {'day': 30, 'month': 9, 'frequency': 'yearly', 'description': 'Director KYC'},
        },
    }
    
    async def calculate_user_deadlines(
        self, 
        user_id: str,
        business_type: str,
        gst_registered: bool = True,
        turnover: float = 0,
        employee_count: int = 0
    ) -> List[Dict[str, Any]]:
        """Calculate applicable compliance deadlines for a user"""
        
        deadlines = []
        today = datetime.now()
        
        # GST Deadlines (if registered)
        if gst_registered:
            for name, config in self.COMPLIANCE_DEADLINES['gst'].items():
                deadline = self._calculate_next_deadline(config, today)
                deadlines.append({
                    'user_id': user_id,
                    'compliance_type': 'GST',
                    'filing_name': name,
                    'due_date': deadline.isoformat(),
                    'description': config['description'],
                    'penalty_risk': self._calculate_penalty_risk(deadline, today),
                    'is_applicable': True
                })
        
        # Income Tax Deadlines (always applicable)
        for name, config in self.COMPLIANCE_DEADLINES['income_tax'].items():
            deadline = self._calculate_next_deadline(config, today)
            deadlines.append({
                'user_id': user_id,
                'compliance_type': 'Income Tax',
                'filing_name': name,
                'due_date': deadline.isoformat(),
                'description': config['description'],
                'penalty_risk': self._calculate_penalty_risk(deadline, today),
                'is_applicable': True
            })
        
        # TDS Deadlines (if turnover > 1 crore or employees)
        if turnover > 10000000 or employee_count > 0:
            for name, config in self.COMPLIANCE_DEADLINES['tds'].items():
                deadline = self._calculate_next_deadline(config, today)
                deadlines.append({
                    'user_id': user_id,
                    'compliance_type': 'TDS',
                    'filing_name': name,
                    'due_date': deadline.isoformat(),
                    'description': config['description'],
                    'penalty_risk': self._calculate_penalty_risk(deadline, today),
                    'is_applicable': True
                })
        
        # PF/ESI (if employees > threshold)
        if employee_count >= 20:
            for name, config in self.COMPLIANCE_DEADLINES['pf_esi'].items():
                deadline = self._calculate_next_deadline(config, today)
                deadlines.append({
                    'user_id': user_id,
                    'compliance_type': 'PF/ESI',
                    'filing_name': name,
                    'due_date': deadline.isoformat(),
                    'description': config['description'],
                    'penalty_risk': self._calculate_penalty_risk(deadline, today),
                    'is_applicable': True
                })
        
        # ROC (for companies only)
        if business_type.lower() in ['pvt ltd', 'private limited', 'public limited', 'opc']:
            for name, config in self.COMPLIANCE_DEADLINES['roc'].items():
                deadline = self._calculate_next_deadline(config, today)
                deadlines.append({
                    'user_id': user_id,
                    'compliance_type': 'ROC',
                    'filing_name': name,
                    'due_date': deadline.isoformat(),
                    'description': config['description'],
                    'penalty_risk': self._calculate_penalty_risk(deadline, today),
                    'is_applicable': True
                })
        
        # Sort by due date
        deadlines.sort(key=lambda x: x['due_date'])
        
        return deadlines
    
    def _calculate_next_deadline(self, config: Dict, today: datetime) -> datetime:
        """Calculate the next occurrence of a deadline"""
        
        frequency = config.get('frequency', 'monthly')
        day = config.get('day', 1)
        month = config.get('month')
        
        if frequency == 'monthly':
            # Next occurrence this month or next
            deadline = today.replace(day=min(day, 28))
            if deadline < today:
                # Move to next month
                if today.month == 12:
                    deadline = deadline.replace(year=today.year + 1, month=1)
                else:
                    deadline = deadline.replace(month=today.month + 1)
        
        elif frequency == 'quarterly':
            # Next quarter end
            current_quarter = (today.month - 1) // 3 + 1
            quarter_end_months = [3, 6, 9, 12]
            next_quarter_month = quarter_end_months[current_quarter - 1]
            
            deadline = today.replace(month=next_quarter_month, day=day)
            if deadline < today:
                next_idx = (current_quarter) % 4
                next_quarter_month = quarter_end_months[next_idx]
                if next_idx == 0:
                    deadline = today.replace(year=today.year + 1, month=next_quarter_month, day=day)
                else:
                    deadline = today.replace(month=next_quarter_month, day=day)
        
        elif frequency == 'yearly':
            deadline = today.replace(month=month or 3, day=day)
            if deadline < today:
                deadline = deadline.replace(year=today.year + 1)
        
        else:
            deadline = today + timedelta(days=30)
        
        return deadline
    
    def _calculate_penalty_risk(self, deadline: datetime, today: datetime) -> str:
        """Calculate penalty risk based on proximity to deadline"""
        
        days_until = (deadline - today).days
        
        if days_until < 0:
            return "OVERDUE"
        elif days_until <= 3:
            return "HIGH"
        elif days_until <= 7:
            return "MEDIUM"
        else:
            return "LOW"
    
    async def update_all_user_calendars(self) -> JobResult:
        """Daily job: Update compliance calendars for all users"""
        result = JobResult(
            job_name="update_compliance_calendars",
            status=JobStatus.RUNNING,
            started_at=datetime.now()
        )
        
        try:
            # In production, fetch from database
            # For now, use mock data
            mock_users = [
                {"id": "user_1", "business_type": "Pvt Ltd", "gst_registered": True, 
                 "turnover": 50000000, "employee_count": 25},
                {"id": "user_2", "business_type": "Proprietorship", "gst_registered": True,
                 "turnover": 5000000, "employee_count": 5},
            ]
            
            for user in mock_users:
                deadlines = await self.calculate_user_deadlines(
                    user_id=user["id"],
                    business_type=user["business_type"],
                    gst_registered=user["gst_registered"],
                    turnover=user["turnover"],
                    employee_count=user["employee_count"]
                )
                
                # Store deadlines (placeholder)
                result.records_processed += len(deadlines)
                
                # Check for upcoming deadlines and send notifications
                for deadline in deadlines:
                    if deadline['penalty_risk'] in ['HIGH', 'OVERDUE']:
                        await self._send_deadline_alert(user["id"], deadline)
            
            result.status = JobStatus.COMPLETED
            result.completed_at = datetime.now()
            
        except Exception as e:
            logger.error(f"Failed to update compliance calendars: {e}")
            result.status = JobStatus.FAILED
            result.errors.append(str(e))
        
        return result
    
    async def _send_deadline_alert(self, user_id: str, deadline: Dict) -> None:
        """Send alert for upcoming deadline"""
        logger.info(f"Alert: User {user_id} has {deadline['penalty_risk']} deadline: {deadline['filing_name']}")
        # In production, send via notification service


class CashFlowPredictionService:
    """
    Generates cash flow predictions using ML/AI
    Based on historical transactions and business patterns
    """
    
    async def generate_predictions(
        self,
        user_id: str,
        historical_transactions: List[Dict],
        days_ahead: int = 90
    ) -> Dict[str, Any]:
        """Generate cash flow predictions for a user"""
        
        try:
            from src.llm_service import llm_service, ModelCapability
            
            # Prepare transaction summary
            total_inflow = sum(t.get('amount', 0) for t in historical_transactions if t.get('type') == 'credit')
            total_outflow = sum(t.get('amount', 0) for t in historical_transactions if t.get('type') == 'debit')
            avg_monthly_inflow = total_inflow / max(len(historical_transactions) // 30, 1)
            avg_monthly_outflow = total_outflow / max(len(historical_transactions) // 30, 1)
            
            prompt = f"""Analyze this business's cash flow and predict the next {days_ahead} days:

Historical Data:
- Total Inflow (past 6 months): ₹{total_inflow:,.0f}
- Total Outflow (past 6 months): ₹{total_outflow:,.0f}
- Average Monthly Inflow: ₹{avg_monthly_inflow:,.0f}
- Average Monthly Outflow: ₹{avg_monthly_outflow:,.0f}
- Net Position: ₹{total_inflow - total_outflow:,.0f}

Provide:
1. 30/60/90 day cash position forecast
2. Identify potential shortfall dates
3. Recommend actions if shortfall predicted

Return as JSON with keys: forecast_30d, forecast_60d, forecast_90d, shortfall_dates, recommendations"""

            response = await llm_service.generate(
                prompt=prompt,
                system_prompt="You are a financial analyst specializing in MSME cash flow management.",
                capability=ModelCapability.REASONING,
                temperature=0.3
            )
            
            # Parse response
            try:
                import re
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    predictions = json.loads(json_match.group())
                else:
                    predictions = {
                        "forecast_30d": avg_monthly_inflow - avg_monthly_outflow,
                        "forecast_60d": (avg_monthly_inflow - avg_monthly_outflow) * 2,
                        "forecast_90d": (avg_monthly_inflow - avg_monthly_outflow) * 3,
                        "shortfall_dates": [],
                        "recommendations": [response.content]
                    }
            except:
                predictions = {
                    "forecast_30d": avg_monthly_inflow - avg_monthly_outflow,
                    "forecast_60d": (avg_monthly_inflow - avg_monthly_outflow) * 2,
                    "forecast_90d": (avg_monthly_inflow - avg_monthly_outflow) * 3,
                    "shortfall_dates": [],
                    "recommendations": ["Unable to parse AI response"]
                }
            
            predictions["user_id"] = user_id
            predictions["generated_at"] = datetime.now().isoformat()
            predictions["has_shortfall"] = len(predictions.get("shortfall_dates", [])) > 0
            
            return predictions
            
        except Exception as e:
            logger.error(f"Cash flow prediction failed: {e}")
            return {
                "user_id": user_id,
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            }
    
    async def generate_all_predictions(self) -> JobResult:
        """Daily job: Generate predictions for all users"""
        result = JobResult(
            job_name="generate_cash_flow_predictions",
            status=JobStatus.RUNNING,
            started_at=datetime.now()
        )
        
        try:
            # In production, fetch users and their transactions from database
            # Mock implementation
            result.records_processed = 0
            result.status = JobStatus.COMPLETED
            result.completed_at = datetime.now()
            
        except Exception as e:
            result.status = JobStatus.FAILED
            result.errors.append(str(e))
        
        return result


class ETLScheduler:
    """
    Main scheduler for all ETL jobs
    Uses Python schedule library with background thread
    """
    
    def __init__(self):
        self.scraper = GovernmentDataScraper()
        self.compliance = ComplianceCalendarService()
        self.cashflow = CashFlowPredictionService()
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._job_history: List[JobResult] = []
    
    def _run_async(self, coro):
        """Helper to run async function in sync context"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    
    def _job_wrapper(self, job_func, job_name: str):
        """Wrapper to catch and log job errors"""
        def wrapped():
            logger.info(f"Starting scheduled job: {job_name}")
            try:
                result = self._run_async(job_func())
                self._job_history.append(result)
                logger.info(f"Job {job_name} completed: {result.status.value}")
            except Exception as e:
                logger.error(f"Job {job_name} failed: {e}")
                self._job_history.append(JobResult(
                    job_name=job_name,
                    status=JobStatus.FAILED,
                    started_at=datetime.now(),
                    errors=[str(e)]
                ))
        return wrapped
    
    def setup_schedules(self):
        """Configure all scheduled jobs"""
        
        # Government data scraping - Every 6 hours
        schedule.every(6).hours.do(
            self._job_wrapper(self.scraper.scrape_all_subsidies, "scrape_subsidies")
        )
        
        # Legislative updates - Twice daily
        schedule.every(12).hours.do(
            self._job_wrapper(self.scraper.scrape_legislative_updates, "scrape_legislative")
        )
        
        # Compliance calendars - Daily at 1 AM IST
        schedule.every().day.at("01:00").do(
            self._job_wrapper(self.compliance.update_all_user_calendars, "update_compliance")
        )
        
        # Cash flow predictions - Daily at 2 AM IST
        schedule.every().day.at("02:00").do(
            self._job_wrapper(self.cashflow.generate_all_predictions, "cash_flow_predictions")
        )
        
        logger.info("ETL schedules configured")
    
    def _schedule_loop(self):
        """Main scheduling loop"""
        while self._running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def start(self):
        """Start the scheduler in background thread"""
        if self._running:
            logger.warning("Scheduler already running")
            return
        
        self.setup_schedules()
        self._running = True
        self._thread = threading.Thread(target=self._schedule_loop, daemon=True)
        self._thread.start()
        logger.info("ETL Scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("ETL Scheduler stopped")
    
    def get_job_history(self, limit: int = 50) -> List[Dict]:
        """Get recent job execution history"""
        return [
            {
                "job_name": r.job_name,
                "status": r.status.value,
                "started_at": r.started_at.isoformat(),
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "records_processed": r.records_processed,
                "errors": r.errors
            }
            for r in self._job_history[-limit:]
        ]
    
    async def run_job_manually(self, job_name: str) -> JobResult:
        """Run a specific job manually"""
        jobs = {
            "scrape_subsidies": self.scraper.scrape_all_subsidies,
            "scrape_legislative": self.scraper.scrape_legislative_updates,
            "update_compliance": self.compliance.update_all_user_calendars,
            "cash_flow_predictions": self.cashflow.generate_all_predictions,
        }
        
        if job_name not in jobs:
            return JobResult(
                job_name=job_name,
                status=JobStatus.FAILED,
                started_at=datetime.now(),
                errors=[f"Unknown job: {job_name}"]
            )
        
        result = await jobs[job_name]()
        self._job_history.append(result)
        return result


# Global scheduler instance
etl_scheduler = ETLScheduler()
