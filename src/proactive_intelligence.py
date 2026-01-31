#!/usr/bin/env python3
"""
Proactive Intelligence Engine for MicroCFO
Handles:
1. Automatic subsidy eligibility matching against transaction history
2. Proactive suggestions ("You purchased machinery, eligible for PMFME")
3. Real-time law change monitoring/alerts
4. Auto-notification when laws affecting user's business type change
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import json

logger = logging.getLogger(__name__)

# Capital goods keywords for subsidy trigger
CAPITAL_GOODS_KEYWORDS = [
    'machinery', 'equipment', 'plant', 'machine', 'cnc', 'lathe', 
    'computer', 'server', 'vehicle', 'truck', 'generator', 'transformer',
    'furniture', 'fixtures', 'tools', 'dies', 'molds', 'robotics',
    'automation', 'solar', 'panel', 'inverter', 'motor', 'pump'
]

# Minimum amount to trigger subsidy check (₹1 Lakh)
CAPITAL_GOODS_THRESHOLD = 100000

# Scheme mapping for different sectors and purchase types
SCHEME_TRIGGERS = {
    'manufacturing': {
        'capital_goods': ['PMFME', 'PLI', 'MSME Technology Upgradation', 'Credit Linked Capital Subsidy'],
        'raw_material': ['MSME Credit Guarantee'],
        'expansion': ['Startup India', 'State Industrial Policy']
    },
    'food_processing': {
        'capital_goods': ['PMFME', 'PLI Food Processing', 'Cold Chain Subsidy'],
        'raw_material': ['PMFME Working Capital'],
        'expansion': ['Mega Food Parks']
    },
    'textile': {
        'capital_goods': ['TUFS', 'PLI Textile', 'Power Loom Upgradation'],
        'raw_material': ['Raw Material Assistance Scheme'],
        'expansion': ['Textile Parks Scheme']
    },
    'technology': {
        'capital_goods': ['STPI', 'Software Technology Parks', 'Digital India'],
        'service': ['Startup India', 'SAMRIDH'],
        'expansion': ['Fund of Funds']
    },
    'agriculture': {
        'capital_goods': ['PM-KUSUM', 'Agricultural Mechanization', 'Micro Irrigation'],
        'raw_material': ['Kisan Credit Card'],
        'expansion': ['AIF - Agriculture Infrastructure Fund']
    }
}


class ProactiveAlert:
    """Represents a proactive alert/suggestion for the user"""
    
    def __init__(
        self,
        alert_type: str,  # 'subsidy_match', 'law_change', 'compliance_reminder'
        title: str,
        message: str,
        priority: str,  # 'high', 'medium', 'low'
        action_url: Optional[str] = None,
        related_schemes: Optional[List[str]] = None,
        related_sections: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ):
        self.alert_type = alert_type
        self.title = title
        self.message = message
        self.priority = priority
        self.action_url = action_url
        self.related_schemes = related_schemes or []
        self.related_sections = related_sections or []
        self.metadata = metadata or {}
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            'alert_type': self.alert_type,
            'title': self.title,
            'message': self.message,
            'priority': self.priority,
            'action_url': self.action_url,
            'related_schemes': self.related_schemes,
            'related_sections': self.related_sections,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }


class ProactiveIntelligenceEngine:
    """
    The Brain's Proactive Module - Monitors transactions and laws
    to provide timely, relevant suggestions to users
    """
    
    def __init__(self, db_session_factory, scheme_db=None, legal_db=None, websocket_manager=None):
        """
        Initialize the proactive intelligence engine
        
        Args:
            db_session_factory: SQLAlchemy session factory
            scheme_db: SchemeVectorDB instance for subsidy searches
            legal_db: LegalVectorDB instance for law searches
            websocket_manager: WebSocket manager for real-time notifications
        """
        self.db_session_factory = db_session_factory
        self.scheme_db = scheme_db
        self.legal_db = legal_db
        self.websocket_manager = websocket_manager
        self._monitoring_task = None
        
    # =========================================================================
    # 1. AUTOMATIC SUBSIDY ELIGIBILITY MATCHING
    # =========================================================================
    
    def analyze_invoice_for_subsidies(
        self,
        invoice_data: Dict,
        business_profile: Dict
    ) -> List[ProactiveAlert]:
        """
        Analyze an invoice to find matching subsidy opportunities
        
        Args:
            invoice_data: Extracted invoice data from Agent A
            business_profile: User's business profile
            
        Returns:
            List of ProactiveAlert objects for matching subsidies
        """
        alerts = []
        
        # Extract key info
        total_amount = invoice_data.get('total_amount', 0)
        line_items = invoice_data.get('line_items', [])
        category = invoice_data.get('category', '')
        vendor_name = invoice_data.get('vendor_name', '')
        
        # Get business sector
        sector = business_profile.get('industry_type', 'manufacturing').lower()
        turnover = business_profile.get('turnover_range', '')
        location = business_profile.get('location_state', '')
        
        # Check for capital goods purchases
        capital_goods_items = self._identify_capital_goods(line_items)
        capital_goods_amount = sum(item.get('amount', 0) for item in capital_goods_items)
        
        if capital_goods_amount >= CAPITAL_GOODS_THRESHOLD:
            # Trigger subsidy search
            matching_schemes = self._find_matching_schemes(
                sector=sector,
                purchase_type='capital_goods',
                amount=capital_goods_amount,
                location=location,
                turnover=turnover
            )
            
            if matching_schemes:
                # Create proactive alert
                item_descriptions = [item.get('description', 'equipment') for item in capital_goods_items[:3]]
                alert = ProactiveAlert(
                    alert_type='subsidy_match',
                    title='🎯 Subsidy Opportunity Detected!',
                    message=self._generate_subsidy_message(
                        items=item_descriptions,
                        amount=capital_goods_amount,
                        schemes=matching_schemes
                    ),
                    priority='high',
                    action_url='/subsidies/apply',
                    related_schemes=[s['name'] for s in matching_schemes],
                    metadata={
                        'trigger_invoice': invoice_data.get('invoice_number'),
                        'capital_goods_amount': capital_goods_amount,
                        'estimated_benefit': self._calculate_estimated_benefit(matching_schemes, capital_goods_amount)
                    }
                )
                alerts.append(alert)
        
        # Check for expansion/growth indicators
        if total_amount > 500000:  # ₹5 Lakh+ invoice might indicate expansion
            expansion_schemes = self._find_matching_schemes(
                sector=sector,
                purchase_type='expansion',
                amount=total_amount,
                location=location,
                turnover=turnover
            )
            
            if expansion_schemes and len(alerts) == 0:  # Don't duplicate if already alerted
                alert = ProactiveAlert(
                    alert_type='subsidy_match',
                    title='💡 Growth Funding Available',
                    message=f"Your recent ₹{total_amount:,.0f} purchase from {vendor_name} suggests business expansion. "
                            f"You may be eligible for: {', '.join([s['name'] for s in expansion_schemes[:3]])}",
                    priority='medium',
                    action_url='/subsidies/explore',
                    related_schemes=[s['name'] for s in expansion_schemes]
                )
                alerts.append(alert)
        
        return alerts
    
    def _identify_capital_goods(self, line_items: List[Dict]) -> List[Dict]:
        """Identify capital goods from line items"""
        capital_goods = []
        
        for item in line_items:
            description = item.get('description', '').lower()
            category = item.get('category', '').lower()
            
            # Check if category is explicitly capital goods
            if 'capital' in category:
                capital_goods.append(item)
                continue
            
            # Check keywords in description
            if any(keyword in description for keyword in CAPITAL_GOODS_KEYWORDS):
                capital_goods.append(item)
        
        return capital_goods
    
    def _find_matching_schemes(
        self,
        sector: str,
        purchase_type: str,
        amount: float,
        location: str,
        turnover: str
    ) -> List[Dict]:
        """Find government schemes matching the criteria"""
        matching_schemes = []
        
        # Get schemes from mapping
        sector_key = self._normalize_sector(sector)
        scheme_names = SCHEME_TRIGGERS.get(sector_key, {}).get(purchase_type, [])
        
        for scheme_name in scheme_names:
            scheme_info = {
                'name': scheme_name,
                'sector': sector,
                'purchase_type': purchase_type,
                'min_amount': CAPITAL_GOODS_THRESHOLD,
                'benefit_type': 'subsidy',
                'estimated_percentage': self._get_scheme_benefit_percentage(scheme_name)
            }
            matching_schemes.append(scheme_info)
        
        # If we have scheme_db, do semantic search for more matches
        if self.scheme_db:
            try:
                query = f"{sector} {purchase_type} subsidy scheme for ₹{amount:,.0f} investment"
                results = self.scheme_db.semantic_search(
                    query=query,
                    n_results=5,
                    target_sector=sector
                )
                
                for result in results:
                    scheme_name = result.get('metadata', {}).get('scheme_name', '')
                    if scheme_name and scheme_name not in [s['name'] for s in matching_schemes]:
                        matching_schemes.append({
                            'name': scheme_name,
                            'sector': result.get('metadata', {}).get('target_sector', ''),
                            'benefit_type': result.get('metadata', {}).get('benefit_type', ''),
                            'estimated_percentage': float(result.get('metadata', {}).get('benefit_percentage', 0) or 0)
                        })
            except Exception as e:
                logger.warning(f"Scheme DB search failed: {e}")
        
        return matching_schemes[:5]  # Return top 5 matches
    
    def _normalize_sector(self, sector: str) -> str:
        """Normalize sector name to match our mapping"""
        sector = sector.lower()
        
        mappings = {
            'manufacturing': ['manufacturing', 'factory', 'production', 'industrial'],
            'food_processing': ['food', 'fmcg', 'beverage', 'dairy', 'bakery'],
            'textile': ['textile', 'garment', 'apparel', 'fabric', 'weaving'],
            'technology': ['technology', 'it', 'software', 'tech', 'digital', 'saas'],
            'agriculture': ['agriculture', 'farming', 'agri', 'horticulture']
        }
        
        for key, keywords in mappings.items():
            if any(kw in sector for kw in keywords):
                return key
        
        return 'manufacturing'  # Default
    
    def _get_scheme_benefit_percentage(self, scheme_name: str) -> float:
        """Get typical benefit percentage for a scheme"""
        scheme_benefits = {
            'PMFME': 35.0,
            'PLI': 4.0,
            'MSME Technology Upgradation': 15.0,
            'Credit Linked Capital Subsidy': 15.0,
            'TUFS': 25.0,
            'Startup India': 10.0,
            'PM-KUSUM': 30.0
        }
        return scheme_benefits.get(scheme_name, 10.0)
    
    def _calculate_estimated_benefit(self, schemes: List[Dict], amount: float) -> float:
        """Calculate estimated benefit amount"""
        if not schemes:
            return 0
        
        # Use highest benefit percentage
        max_percentage = max(s.get('estimated_percentage', 10) for s in schemes)
        return amount * (max_percentage / 100)
    
    def _generate_subsidy_message(
        self,
        items: List[str],
        amount: float,
        schemes: List[Dict]
    ) -> str:
        """Generate a user-friendly subsidy suggestion message"""
        items_str = ', '.join(items[:2])
        if len(items) > 2:
            items_str += f" and {len(items) - 2} more"
        
        scheme_names = [s['name'] for s in schemes[:3]]
        schemes_str = ', '.join(scheme_names)
        
        estimated_benefit = self._calculate_estimated_benefit(schemes, amount)
        
        message = (
            f"Your recent purchase of {items_str} (₹{amount:,.0f}) qualifies you for "
            f"government subsidies! Potential schemes: {schemes_str}. "
            f"Estimated benefit: up to ₹{estimated_benefit:,.0f}. "
            f"Should I help you apply?"
        )
        
        return message
    
    # =========================================================================
    # 2. REAL-TIME LAW CHANGE MONITORING
    # =========================================================================
    
    async def check_law_changes_for_user(
        self,
        user_id: str,
        business_profile: Dict,
        since_days: int = 7
    ) -> List[ProactiveAlert]:
        """
        Check for law changes that affect a specific user's business
        
        Args:
            user_id: User ID
            business_profile: User's business profile
            since_days: Look for changes in last N days
            
        Returns:
            List of ProactiveAlert for relevant law changes
        """
        alerts = []
        
        sector = business_profile.get('industry_type', '').lower()
        turnover = business_profile.get('turnover_range', '')
        gstin = business_profile.get('gstin', '')
        
        # Determine applicable law types based on business profile
        applicable_laws = self._get_applicable_laws(business_profile)
        
        # Check each law type for changes
        for law_type in applicable_laws:
            changes = await self._get_recent_law_changes(law_type, since_days)
            
            for change in changes:
                # Check relevance to user
                relevance = self._check_change_relevance(change, business_profile)
                
                if relevance['is_relevant']:
                    alert = ProactiveAlert(
                        alert_type='law_change',
                        title=f'⚖️ {law_type} Update Affecting Your Business',
                        message=self._generate_law_change_message(change, relevance),
                        priority=relevance['priority'],
                        action_url=f'/legal/details/{change.get("id")}',
                        related_sections=[change.get('section_number', '')],
                        metadata={
                            'law_type': law_type,
                            'section': change.get('section_number'),
                            'effective_date': change.get('effective_date'),
                            'impact_areas': relevance.get('impact_areas', [])
                        }
                    )
                    alerts.append(alert)
        
        return alerts
    
    def _get_applicable_laws(self, business_profile: Dict) -> List[str]:
        """Determine which laws apply to a business"""
        laws = ['GST']  # GST applies to most businesses
        
        turnover = business_profile.get('turnover_range', '')
        business_type = business_profile.get('business_type', '')
        
        # Add Income Tax for all
        laws.append('Income Tax')
        
        # Add Companies Act if registered company
        if 'pvt' in business_type.lower() or 'ltd' in business_type.lower():
            laws.append('Companies Act')
        
        # Add Labour Laws based on size
        if 'crore' in turnover.lower() or any(x in turnover for x in ['50', '100', '500']):
            laws.append('Labour Laws')
        
        return laws
    
    async def _get_recent_law_changes(self, law_type: str, since_days: int) -> List[Dict]:
        """Get recent law changes from vector database"""
        changes = []
        
        if self.legal_db:
            try:
                # Search for recent notifications/circulars
                query = f"recent {law_type} notification circular amendment effective"
                results = self.legal_db.semantic_search(
                    query=query,
                    n_results=10,
                    law_type=law_type
                )
                
                # Filter by date if possible
                cutoff_date = datetime.now() - timedelta(days=since_days)
                
                for result in results:
                    effective_date_str = result.get('metadata', {}).get('effective_date', '')
                    if effective_date_str:
                        try:
                            effective_date = datetime.fromisoformat(effective_date_str)
                            if effective_date >= cutoff_date:
                                changes.append({
                                    'id': result.get('id'),
                                    'text': result.get('document', ''),
                                    'section_number': result.get('metadata', {}).get('section_number', ''),
                                    'effective_date': effective_date_str,
                                    'law_type': law_type,
                                    'turnover_threshold': result.get('metadata', {}).get('turnover_threshold', '')
                                })
                        except:
                            pass
            except Exception as e:
                logger.warning(f"Legal DB search failed: {e}")
        
        return changes
    
    def _check_change_relevance(self, change: Dict, business_profile: Dict) -> Dict:
        """Check if a law change is relevant to a business"""
        relevance = {
            'is_relevant': False,
            'priority': 'low',
            'impact_areas': [],
            'reason': ''
        }
        
        text = change.get('text', '').lower()
        turnover_threshold = change.get('turnover_threshold', '')
        
        # Check turnover relevance
        user_turnover = self._parse_turnover(business_profile.get('turnover_range', ''))
        
        if turnover_threshold:
            threshold_value = self._parse_turnover(turnover_threshold)
            if threshold_value and user_turnover:
                if user_turnover >= threshold_value * 0.8:  # Within 80% of threshold
                    relevance['is_relevant'] = True
                    relevance['impact_areas'].append('turnover_threshold')
        
        # Check sector relevance
        sector = business_profile.get('industry_type', '').lower()
        if sector and sector in text:
            relevance['is_relevant'] = True
            relevance['impact_areas'].append('sector_specific')
        
        # Check for common keywords
        high_impact_keywords = ['penalty', 'mandatory', 'deadline', 'compliance', 'audit']
        medium_impact_keywords = ['exemption', 'relief', 'benefit', 'refund', 'credit']
        
        for keyword in high_impact_keywords:
            if keyword in text:
                relevance['is_relevant'] = True
                relevance['priority'] = 'high'
                relevance['impact_areas'].append(keyword)
                break
        
        if relevance['priority'] != 'high':
            for keyword in medium_impact_keywords:
                if keyword in text:
                    relevance['is_relevant'] = True
                    relevance['priority'] = 'medium'
                    relevance['impact_areas'].append(keyword)
                    break
        
        return relevance
    
    def _parse_turnover(self, turnover_str: str) -> Optional[float]:
        """Parse turnover string to numeric value in lakhs"""
        if not turnover_str:
            return None
        
        turnover_str = turnover_str.lower().replace(',', '')
        
        try:
            if 'crore' in turnover_str or 'cr' in turnover_str:
                num = float(''.join(c for c in turnover_str if c.isdigit() or c == '.'))
                return num * 100  # Convert to lakhs
            elif 'lakh' in turnover_str or 'lac' in turnover_str:
                num = float(''.join(c for c in turnover_str if c.isdigit() or c == '.'))
                return num
            else:
                num = float(''.join(c for c in turnover_str if c.isdigit() or c == '.'))
                return num / 100000  # Assume rupees, convert to lakhs
        except:
            return None
    
    def _generate_law_change_message(self, change: Dict, relevance: Dict) -> str:
        """Generate user-friendly law change notification"""
        section = change.get('section_number', 'Recent Update')
        law_type = change.get('law_type', 'Law')
        effective_date = change.get('effective_date', 'Soon')
        
        impact_str = ', '.join(relevance.get('impact_areas', [])[:3])
        
        if relevance['priority'] == 'high':
            urgency = "⚠️ URGENT ACTION REQUIRED: "
        elif relevance['priority'] == 'medium':
            urgency = "📋 Important Update: "
        else:
            urgency = "ℹ️ FYI: "
        
        message = (
            f"{urgency}A {law_type} change ({section}) effective {effective_date} "
            f"may affect your business. Impact areas: {impact_str}. "
            f"Review recommended to ensure compliance."
        )
        
        return message
    
    # =========================================================================
    # 3. BACKGROUND MONITORING SERVICE
    # =========================================================================
    
    async def start_monitoring(self, interval_minutes: int = 60):
        """Start background monitoring for all users"""
        logger.info(f"Starting proactive monitoring service (interval: {interval_minutes}min)")
        
        while True:
            try:
                await self._run_monitoring_cycle()
            except Exception as e:
                logger.error(f"Monitoring cycle error: {e}")
            
            await asyncio.sleep(interval_minutes * 60)
    
    async def _run_monitoring_cycle(self):
        """Run a single monitoring cycle for all active users"""
        db = self.db_session_factory()
        
        try:
            # Import here to avoid circular imports
            from models import User, BusinessProfile, Invoice
            
            # Get active users with business profiles
            users = db.query(User).filter(User.is_active == True).all()
            
            for user in users:
                try:
                    # Get business profile
                    business = db.query(BusinessProfile).filter(
                        BusinessProfile.owner_id == user.id
                    ).first()
                    
                    if not business:
                        continue
                    
                    business_profile = {
                        'industry_type': business.industry_type,
                        'turnover_range': business.turnover_range,
                        'location_state': business.location_state,
                        'business_type': user.business_sector or ''
                    }
                    
                    # Check for law changes
                    law_alerts = await self.check_law_changes_for_user(
                        user_id=str(user.id),
                        business_profile=business_profile
                    )
                    
                    # Store and notify
                    for alert in law_alerts:
                        await self._store_and_notify_alert(db, user.id, alert)
                    
                    # Check recent invoices for subsidy opportunities
                    recent_invoices = db.query(Invoice).filter(
                        Invoice.user_id == user.id,
                        Invoice.created_at >= datetime.now() - timedelta(days=7)
                    ).all()
                    
                    for invoice in recent_invoices:
                        if invoice.extracted_data:
                            subsidy_alerts = self.analyze_invoice_for_subsidies(
                                invoice_data=invoice.extracted_data,
                                business_profile=business_profile
                            )
                            
                            for alert in subsidy_alerts:
                                await self._store_and_notify_alert(db, user.id, alert)
                
                except Exception as e:
                    logger.error(f"Error processing user {user.id}: {e}")
            
            db.commit()
            
        finally:
            db.close()
    
    async def _store_and_notify_alert(self, db: Session, user_id, alert: ProactiveAlert):
        """Store alert in database and send real-time notification"""
        from models import ProactiveNotification
        
        # Check for duplicates
        existing = db.query(ProactiveNotification).filter(
            ProactiveNotification.user_id == user_id,
            ProactiveNotification.alert_type == alert.alert_type,
            ProactiveNotification.title == alert.title,
            ProactiveNotification.created_at >= datetime.now() - timedelta(hours=24)
        ).first()
        
        if existing:
            return  # Don't duplicate
        
        # Store in database
        notification = ProactiveNotification(
            user_id=user_id,
            alert_type=alert.alert_type,
            title=alert.title,
            message=alert.message,
            priority=alert.priority,
            action_url=alert.action_url,
            related_data=alert.to_dict(),
            is_read=False
        )
        db.add(notification)
        
        # Send real-time notification via WebSocket
        if self.websocket_manager:
            try:
                await self.websocket_manager.send_to_user(
                    user_id=str(user_id),
                    message={
                        'type': 'proactive_alert',
                        'data': alert.to_dict()
                    }
                )
            except Exception as e:
                logger.warning(f"WebSocket notification failed: {e}")
    
    # =========================================================================
    # 4. TRANSACTION HISTORY ANALYSIS
    # =========================================================================
    
    def analyze_transaction_history(
        self,
        db: Session,
        user_id: str,
        months: int = 6
    ) -> Dict[str, Any]:
        """
        Analyze user's transaction history to find subsidy opportunities
        
        Args:
            db: Database session
            user_id: User ID
            months: Number of months to analyze
            
        Returns:
            Analysis results with subsidy recommendations
        """
        from models import Invoice, BusinessProfile
        
        # Get business profile
        business = db.query(BusinessProfile).filter(
            BusinessProfile.owner_id == user_id
        ).first()
        
        if not business:
            return {'error': 'No business profile found'}
        
        # Get invoices
        cutoff = datetime.now() - timedelta(days=months * 30)
        invoices = db.query(Invoice).filter(
            Invoice.user_id == user_id,
            Invoice.created_at >= cutoff
        ).all()
        
        # Aggregate analysis
        analysis = {
            'total_invoices': len(invoices),
            'total_spend': 0,
            'capital_goods_spend': 0,
            'capital_goods_items': [],
            'raw_material_spend': 0,
            'service_spend': 0,
            'monthly_average': 0,
            'subsidy_opportunities': []
        }
        
        for invoice in invoices:
            if invoice.extracted_data:
                data = invoice.extracted_data
                total = data.get('total_amount', 0)
                analysis['total_spend'] += total
                
                for item in data.get('line_items', []):
                    category = item.get('category', '').lower()
                    amount = item.get('amount', 0)
                    
                    if 'capital' in category:
                        analysis['capital_goods_spend'] += amount
                        analysis['capital_goods_items'].append(item)
                    elif 'raw' in category or 'material' in category:
                        analysis['raw_material_spend'] += amount
                    elif 'service' in category:
                        analysis['service_spend'] += amount
        
        analysis['monthly_average'] = analysis['total_spend'] / max(months, 1)
        
        # Find matching subsidies based on aggregated data
        business_profile = {
            'industry_type': business.industry_type,
            'turnover_range': business.turnover_range,
            'location_state': business.location_state
        }
        
        if analysis['capital_goods_spend'] >= CAPITAL_GOODS_THRESHOLD:
            schemes = self._find_matching_schemes(
                sector=business.industry_type or 'manufacturing',
                purchase_type='capital_goods',
                amount=analysis['capital_goods_spend'],
                location=business.location_state or '',
                turnover=business.turnover_range or ''
            )
            
            for scheme in schemes:
                analysis['subsidy_opportunities'].append({
                    'scheme_name': scheme['name'],
                    'purchase_type': 'capital_goods',
                    'qualifying_amount': analysis['capital_goods_spend'],
                    'estimated_benefit': analysis['capital_goods_spend'] * scheme.get('estimated_percentage', 10) / 100
                })
        
        return analysis


# Singleton instance
_proactive_engine: Optional[ProactiveIntelligenceEngine] = None

def get_proactive_engine() -> ProactiveIntelligenceEngine:
    """Get the proactive intelligence engine singleton"""
    global _proactive_engine
    if _proactive_engine is None:
        from database import SessionLocal
        _proactive_engine = ProactiveIntelligenceEngine(
            db_session_factory=SessionLocal
        )
    return _proactive_engine

def init_proactive_engine(db_session_factory, scheme_db=None, legal_db=None, websocket_manager=None):
    """Initialize the proactive intelligence engine with dependencies"""
    global _proactive_engine
    _proactive_engine = ProactiveIntelligenceEngine(
        db_session_factory=db_session_factory,
        scheme_db=scheme_db,
        legal_db=legal_db,
        websocket_manager=websocket_manager
    )
    return _proactive_engine
