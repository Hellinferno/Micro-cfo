#!/usr/bin/env python3
"""
Account Aggregator (AA) Framework Integration for MicroCFO
Fetches real-time financial data via India's Account Aggregator ecosystem

MANUAL SETUP REQUIRED:
1. Register as a Financial Information User (FIU) with RBI-approved AA
   - Sahamati sandbox: https://sahamati.org.in/
   - Production AAs: Finvu, OneMoney, CAMS, etc.
2. Complete KYC and compliance requirements
3. Get API credentials from your chosen AA
4. Set environment variables (see below)

NOTE: AA integration requires regulatory compliance. This is a stub implementation
for development/demo purposes. Production use requires proper FIU registration.
"""

import os
import logging
import httpx
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AAProvider(str, Enum):
    """Supported Account Aggregator providers"""
    FINVU = "finvu"
    ONEMONEY = "onemoney"
    CAMS = "cams"
    SAHAMATI_SANDBOX = "sahamati_sandbox"


class ConsentStatus(str, Enum):
    """Consent request status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REVOKED = "revoked"


class FIType(str, Enum):
    """Financial Information Types"""
    DEPOSIT = "DEPOSIT"  # Bank accounts
    TERM_DEPOSIT = "TERM_DEPOSIT"  # FDs
    RECURRING_DEPOSIT = "RECURRING_DEPOSIT"
    SIP = "SIP"
    MUTUAL_FUNDS = "MUTUAL_FUNDS"
    ETF = "ETF"
    BONDS = "BONDS"
    DEBENTURES = "DEBENTURES"
    STOCKS = "STOCKS"  # Demat holdings
    INSURANCE = "INSURANCE"
    GST = "GST"  # GST returns
    ITR = "ITR"  # Income tax returns


class ConsentRequest(BaseModel):
    """Consent request model"""
    consent_id: str
    customer_id: str
    fi_types: List[str]
    purpose: str
    data_date_range_from: str
    data_date_range_to: str
    consent_status: str = "pending"
    created_at: datetime = None
    expires_at: datetime = None


class AccountAggregatorService:
    """
    Account Aggregator integration service
    
    Implements the AA framework for fetching financial data with user consent.
    
    Environment Variables Required:
    - AA_PROVIDER: 'finvu', 'onemoney', 'cams', or 'sahamati_sandbox'
    - AA_CLIENT_ID: Your FIU client ID
    - AA_CLIENT_SECRET: Your FIU client secret
    - AA_API_URL: AA provider's API base URL
    - AA_CALLBACK_URL: Your webhook URL for consent callbacks
    
    For Sahamati Sandbox (Development):
    - Use sandbox credentials from https://sahamati.org.in/
    """
    
    # Sandbox/demo data for development
    MOCK_ACCOUNTS = [
        {
            "account_id": "ACC001",
            "account_type": "SAVINGS",
            "bank_name": "HDFC Bank",
            "balance": 524680.50,
            "currency": "INR",
            "last_updated": datetime.now().isoformat()
        },
        {
            "account_id": "ACC002",
            "account_type": "CURRENT",
            "bank_name": "ICICI Bank",
            "balance": 1250000.00,
            "currency": "INR",
            "last_updated": datetime.now().isoformat()
        }
    ]
    
    MOCK_TRANSACTIONS = [
        {
            "txn_id": "TXN001",
            "account_id": "ACC001",
            "type": "CREDIT",
            "amount": 150000.00,
            "narration": "NEFT-Customer Payment-INV2024001",
            "date": (datetime.now() - timedelta(days=2)).isoformat(),
            "balance_after": 524680.50
        },
        {
            "txn_id": "TXN002",
            "account_id": "ACC001",
            "type": "DEBIT",
            "amount": 45000.00,
            "narration": "Vendor Payment-Supplier ABC",
            "date": (datetime.now() - timedelta(days=5)).isoformat(),
            "balance_after": 374680.50
        },
        {
            "txn_id": "TXN003",
            "account_id": "ACC002",
            "type": "CREDIT",
            "amount": 500000.00,
            "narration": "Sales Receipt-Customer XYZ",
            "date": (datetime.now() - timedelta(days=1)).isoformat(),
            "balance_after": 1250000.00
        }
    ]
    
    def __init__(self):
        self.provider = os.getenv("AA_PROVIDER", "sahamati_sandbox")
        self.client_id = os.getenv("AA_CLIENT_ID")
        self.client_secret = os.getenv("AA_CLIENT_SECRET")
        self.api_url = os.getenv("AA_API_URL", "https://api.sandbox.sahamati.org.in")
        self.callback_url = os.getenv("AA_CALLBACK_URL")
        
        self.is_configured = all([self.client_id, self.client_secret])
        
        if self.is_configured:
            logger.info(f"✅ Account Aggregator configured (Provider: {self.provider})")
        else:
            logger.warning("⚠️ Account Aggregator not configured. Using mock data.")
            logger.warning("Set AA_CLIENT_ID, AA_CLIENT_SECRET for production use.")
        
        # In-memory consent storage (use database in production)
        self._consents: Dict[str, ConsentRequest] = {}
    
    async def create_consent_request(
        self,
        customer_phone: str,
        fi_types: List[FIType],
        purpose: str = "MicroCFO Financial Analysis",
        data_range_months: int = 12
    ) -> Dict[str, Any]:
        """
        Create a consent request for fetching financial data
        
        Args:
            customer_phone: Customer's phone number (linked to AA)
            fi_types: Types of financial information to fetch
            purpose: Purpose of data fetch (shown to customer)
            data_range_months: How many months of data to request
        
        Returns:
            Consent request details with redirect URL
        """
        import uuid
        
        consent_id = str(uuid.uuid4())
        now = datetime.now()
        
        consent = ConsentRequest(
            consent_id=consent_id,
            customer_id=customer_phone,
            fi_types=[ft.value for ft in fi_types],
            purpose=purpose,
            data_date_range_from=(now - timedelta(days=data_range_months * 30)).isoformat(),
            data_date_range_to=now.isoformat(),
            created_at=now,
            expires_at=now + timedelta(days=30)
        )
        
        self._consents[consent_id] = consent
        
        if not self.is_configured:
            # Return mock consent for development
            return {
                "success": True,
                "mock": True,
                "consent_id": consent_id,
                "status": "approved",  # Auto-approve in mock mode
                "message": "Mock consent created. In production, user would be redirected to AA app."
            }
        
        # In production, call AA API to create consent
        try:
            return await self._create_consent_api(consent)
        except Exception as e:
            logger.error(f"Consent creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def check_consent_status(self, consent_id: str) -> Dict[str, Any]:
        """Check the status of a consent request"""
        consent = self._consents.get(consent_id)
        
        if not consent:
            return {"success": False, "error": "Consent not found"}
        
        if not self.is_configured:
            # Mock: auto-approve after creation
            return {
                "success": True,
                "mock": True,
                "consent_id": consent_id,
                "status": "approved"
            }
        
        try:
            return await self._check_consent_api(consent_id)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def fetch_financial_data(
        self,
        consent_id: str,
        fi_types: Optional[List[FIType]] = None
    ) -> Dict[str, Any]:
        """
        Fetch financial data using an approved consent
        
        Args:
            consent_id: Approved consent ID
            fi_types: Specific FI types to fetch (optional)
        
        Returns:
            Financial data including accounts, transactions, etc.
        """
        # Verify consent
        consent = self._consents.get(consent_id)
        if not consent:
            return {"success": False, "error": "Consent not found"}
        
        if not self.is_configured:
            # Return mock data for development
            return {
                "success": True,
                "mock": True,
                "consent_id": consent_id,
                "data": {
                    "accounts": self.MOCK_ACCOUNTS,
                    "transactions": self.MOCK_TRANSACTIONS,
                    "summary": self._calculate_mock_summary()
                }
            }
        
        try:
            return await self._fetch_data_api(consent_id, fi_types)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _calculate_mock_summary(self) -> Dict[str, Any]:
        """Calculate financial summary from mock data"""
        total_balance = sum(acc["balance"] for acc in self.MOCK_ACCOUNTS)
        
        credits = sum(t["amount"] for t in self.MOCK_TRANSACTIONS if t["type"] == "CREDIT")
        debits = sum(t["amount"] for t in self.MOCK_TRANSACTIONS if t["type"] == "DEBIT")
        
        return {
            "total_balance": total_balance,
            "total_credits_30d": credits,
            "total_debits_30d": debits,
            "net_flow_30d": credits - debits,
            "account_count": len(self.MOCK_ACCOUNTS),
            "cash_position": total_balance,
            "predicted_outflows_30d": debits * 1.1,  # Simple prediction
            "runway_days": int(total_balance / (debits / 30)) if debits > 0 else 365
        }
    
    async def get_cash_flow_summary(self, consent_id: str) -> Dict[str, Any]:
        """
        Get cash flow summary for negotiation decisions
        
        Used by Agent D (Negotiator) to understand financial position
        """
        data = await self.fetch_financial_data(consent_id)
        
        if not data.get("success"):
            return data
        
        summary = data.get("data", {}).get("summary", {})
        
        return {
            "success": True,
            "current_cash_position": summary.get("total_balance", 0),
            "predicted_outflows_30d": summary.get("predicted_outflows_30d", 0),
            "net_cash_flow_30d": summary.get("net_flow_30d", 0),
            "runway_days": summary.get("runway_days", 30),
            "recommendation": self._get_cash_recommendation(summary)
        }
    
    def _get_cash_recommendation(self, summary: Dict) -> str:
        """Generate cash flow recommendation"""
        runway = summary.get("runway_days", 30)
        net_flow = summary.get("net_flow_30d", 0)
        
        if runway < 30:
            return "CRITICAL: Low cash runway. Prioritize collections and defer non-essential payments."
        elif runway < 60:
            return "CAUTION: Monitor cash flow closely. Consider negotiating extended payment terms."
        elif net_flow < 0:
            return "WATCH: Negative cash flow. Focus on improving collections."
        else:
            return "HEALTHY: Good cash position. Can consider early payment discounts."
    
    # =========================================================================
    # API Methods (for production use with real AA)
    # =========================================================================
    
    async def _create_consent_api(self, consent: ConsentRequest) -> Dict[str, Any]:
        """Create consent via AA API"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/consent",
                headers={
                    "x-client-id": self.client_id,
                    "x-client-secret": self.client_secret,
                    "Content-Type": "application/json"
                },
                json={
                    "consentRequest": {
                        "customerId": consent.customer_id,
                        "fiTypes": consent.fi_types,
                        "purpose": consent.purpose,
                        "dataDateRange": {
                            "from": consent.data_date_range_from,
                            "to": consent.data_date_range_to
                        },
                        "consentExpiry": consent.expires_at.isoformat()
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "consent_id": result.get("consentId"),
                    "redirect_url": result.get("redirectUrl"),
                    "status": "pending"
                }
            else:
                return {
                    "success": False,
                    "error": response.text
                }
    
    async def _check_consent_api(self, consent_id: str) -> Dict[str, Any]:
        """Check consent status via AA API"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/v1/consent/{consent_id}",
                headers={
                    "x-client-id": self.client_id,
                    "x-client-secret": self.client_secret
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "consent_id": consent_id,
                    "status": result.get("status", "pending")
                }
            else:
                return {"success": False, "error": response.text}
    
    async def _fetch_data_api(
        self,
        consent_id: str,
        fi_types: Optional[List[FIType]]
    ) -> Dict[str, Any]:
        """Fetch financial data via AA API"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/fi/fetch",
                headers={
                    "x-client-id": self.client_id,
                    "x-client-secret": self.client_secret,
                    "Content-Type": "application/json"
                },
                json={
                    "consentId": consent_id,
                    "fiTypes": [ft.value for ft in fi_types] if fi_types else None
                }
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json()
                }
            else:
                return {"success": False, "error": response.text}


# Singleton instance
_aa_service: Optional[AccountAggregatorService] = None

def get_aa_service() -> AccountAggregatorService:
    """Get Account Aggregator service singleton"""
    global _aa_service
    if _aa_service is None:
        _aa_service = AccountAggregatorService()
    return _aa_service
