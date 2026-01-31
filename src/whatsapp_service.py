#!/usr/bin/env python3
"""
WhatsApp Integration Service for MicroCFO
Provides WhatsApp-first interface using Twilio or Meta Business API

MANUAL SETUP REQUIRED:
1. Sign up for Twilio (https://www.twilio.com) OR Meta Business API
2. Get your Account SID and Auth Token
3. Set up a WhatsApp Business number
4. Configure webhook URL for incoming messages
5. Set environment variables (see below)
"""

import os
import logging
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class WhatsAppProvider(str, Enum):
    """Supported WhatsApp API providers"""
    TWILIO = "twilio"
    META = "meta"


class WhatsAppMessage:
    """Represents a WhatsApp message"""
    def __init__(
        self,
        to: str,
        body: str,
        media_url: Optional[str] = None,
        template_name: Optional[str] = None,
        template_params: Optional[Dict] = None
    ):
        self.to = self._normalize_phone(to)
        self.body = body
        self.media_url = media_url
        self.template_name = template_name
        self.template_params = template_params or {}
        self.created_at = datetime.now()
    
    @staticmethod
    def _normalize_phone(phone: str) -> str:
        """Normalize phone number to E.164 format"""
        phone = ''.join(filter(str.isdigit, phone))
        if not phone.startswith('91') and len(phone) == 10:
            phone = '91' + phone  # Add India country code
        return '+' + phone


class WhatsAppService:
    """
    WhatsApp messaging service supporting Twilio and Meta Business API
    
    Environment Variables Required:
    - WHATSAPP_PROVIDER: 'twilio' or 'meta'
    
    For Twilio:
    - TWILIO_ACCOUNT_SID: Your Twilio account SID
    - TWILIO_AUTH_TOKEN: Your Twilio auth token
    - TWILIO_WHATSAPP_NUMBER: Your Twilio WhatsApp number (e.g., +14155238886)
    
    For Meta Business API:
    - META_WHATSAPP_TOKEN: Your Meta access token
    - META_PHONE_NUMBER_ID: Your WhatsApp phone number ID
    - META_BUSINESS_ID: Your Meta business ID
    """
    
    def __init__(self):
        self.provider = os.getenv("WHATSAPP_PROVIDER", "twilio").lower()
        self.is_configured = False
        
        if self.provider == "twilio":
            self._init_twilio()
        elif self.provider == "meta":
            self._init_meta()
        else:
            logger.warning(f"Unknown WhatsApp provider: {self.provider}")
    
    def _init_twilio(self):
        """Initialize Twilio client"""
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_WHATSAPP_NUMBER")
        
        if all([self.account_sid, self.auth_token, self.from_number]):
            self.is_configured = True
            self.api_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
            logger.info("✅ WhatsApp (Twilio) configured successfully")
        else:
            logger.warning("⚠️ Twilio WhatsApp not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER")
    
    def _init_meta(self):
        """Initialize Meta Business API client"""
        self.access_token = os.getenv("META_WHATSAPP_TOKEN")
        self.phone_number_id = os.getenv("META_PHONE_NUMBER_ID")
        self.business_id = os.getenv("META_BUSINESS_ID")
        
        if all([self.access_token, self.phone_number_id]):
            self.is_configured = True
            self.api_url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}/messages"
            logger.info("✅ WhatsApp (Meta) configured successfully")
        else:
            logger.warning("⚠️ Meta WhatsApp not configured. Set META_WHATSAPP_TOKEN, META_PHONE_NUMBER_ID")
    
    async def send_message(self, message: WhatsAppMessage) -> Dict[str, Any]:
        """Send a WhatsApp message"""
        if not self.is_configured:
            return {
                "success": False,
                "error": "WhatsApp not configured",
                "mock": True,
                "message": f"[MOCK] Would send to {message.to}: {message.body}"
            }
        
        try:
            if self.provider == "twilio":
                return await self._send_twilio(message)
            elif self.provider == "meta":
                return await self._send_meta(message)
        except Exception as e:
            logger.error(f"WhatsApp send error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_twilio(self, message: WhatsAppMessage) -> Dict[str, Any]:
        """Send via Twilio API"""
        async with httpx.AsyncClient() as client:
            data = {
                "From": f"whatsapp:{self.from_number}",
                "To": f"whatsapp:{message.to}",
                "Body": message.body
            }
            
            if message.media_url:
                data["MediaUrl"] = message.media_url
            
            response = await client.post(
                self.api_url,
                data=data,
                auth=(self.account_sid, self.auth_token)
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    "success": True,
                    "message_sid": result.get("sid"),
                    "status": result.get("status")
                }
            else:
                return {
                    "success": False,
                    "error": response.text,
                    "status_code": response.status_code
                }
    
    async def _send_meta(self, message: WhatsAppMessage) -> Dict[str, Any]:
        """Send via Meta Business API"""
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Use template if specified, otherwise text message
            if message.template_name:
                payload = {
                    "messaging_product": "whatsapp",
                    "to": message.to,
                    "type": "template",
                    "template": {
                        "name": message.template_name,
                        "language": {"code": "en"},
                        "components": [
                            {
                                "type": "body",
                                "parameters": [
                                    {"type": "text", "text": v}
                                    for v in message.template_params.values()
                                ]
                            }
                        ]
                    }
                }
            else:
                payload = {
                    "messaging_product": "whatsapp",
                    "to": message.to,
                    "type": "text",
                    "text": {"body": message.body}
                }
            
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    "success": True,
                    "message_id": result.get("messages", [{}])[0].get("id"),
                    "status": "sent"
                }
            else:
                return {
                    "success": False,
                    "error": response.text,
                    "status_code": response.status_code
                }
    
    # =========================================================================
    # MICROCFO-SPECIFIC MESSAGE TEMPLATES
    # =========================================================================
    
    async def send_invoice_alert(
        self,
        phone: str,
        vendor_name: str,
        amount: float,
        category: str,
        warning: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send invoice processing alert"""
        body = f"🧾 *Invoice Processed*\n\n"
        body += f"Vendor: {vendor_name}\n"
        body += f"Amount: ₹{amount:,.2f}\n"
        body += f"Category: {category}\n"
        
        if warning:
            body += f"\n⚠️ *Warning:* {warning}"
        
        return await self.send_message(WhatsAppMessage(to=phone, body=body))
    
    async def send_subsidy_opportunity(
        self,
        phone: str,
        item_description: str,
        amount: float,
        scheme_name: str,
        estimated_benefit: float
    ) -> Dict[str, Any]:
        """Send proactive subsidy suggestion"""
        body = f"🎯 *Subsidy Opportunity!*\n\n"
        body += f"Your purchase of {item_description} (₹{amount:,.0f}) "
        body += f"makes you eligible for *{scheme_name}*.\n\n"
        body += f"💰 Estimated benefit: ₹{estimated_benefit:,.0f}\n\n"
        body += f"Reply *APPLY* to start the application process."
        
        return await self.send_message(WhatsAppMessage(to=phone, body=body))
    
    async def send_compliance_alert(
        self,
        phone: str,
        risk_level: str,
        law_type: str,
        section: str,
        action_required: str
    ) -> Dict[str, Any]:
        """Send compliance/law change alert"""
        emoji = "🔴" if risk_level == "High" else "🟡" if risk_level == "Medium" else "🟢"
        
        body = f"{emoji} *{law_type} Compliance Alert*\n\n"
        body += f"Risk Level: {risk_level}\n"
        body += f"Section: {section}\n\n"
        body += f"*Action Required:*\n{action_required}\n\n"
        body += f"Reply *DETAILS* for more information."
        
        return await self.send_message(WhatsAppMessage(to=phone, body=body))
    
    async def send_negotiation_draft(
        self,
        phone: str,
        counterparty: str,
        amount: float,
        draft_message: str
    ) -> Dict[str, Any]:
        """Send negotiation email draft for approval"""
        body = f"✉️ *Negotiation Draft Ready*\n\n"
        body += f"To: {counterparty}\n"
        body += f"Amount: ₹{amount:,.2f}\n\n"
        body += f"*Draft Message:*\n{draft_message[:500]}...\n\n"
        body += f"Reply *APPROVE* to send or *EDIT* to modify."
        
        return await self.send_message(WhatsAppMessage(to=phone, body=body))
    
    async def send_personal_expense_warning(
        self,
        phone: str,
        item_description: str,
        amount: float
    ) -> Dict[str, Any]:
        """Send warning for personal expense detection"""
        body = f"⚠️ *Personal Expense Detected*\n\n"
        body += f"Item: {item_description}\n"
        body += f"Amount: ₹{amount:,.2f}\n\n"
        body += f"This looks like a personal expense. "
        body += f"*Do not claim GST Input Tax Credit* or you risk an audit.\n\n"
        body += f"Reply *CONFIRM* if this is business expense or *IGNORE* to dismiss."
        
        return await self.send_message(WhatsAppMessage(to=phone, body=body))


# Singleton instance
_whatsapp_service: Optional[WhatsAppService] = None

def get_whatsapp_service() -> WhatsAppService:
    """Get WhatsApp service singleton"""
    global _whatsapp_service
    if _whatsapp_service is None:
        _whatsapp_service = WhatsAppService()
    return _whatsapp_service
