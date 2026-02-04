#!/usr/bin/env python3
"""
WhatsApp Bot Router for MicroCFO
Handles incoming WhatsApp messages and webhook callbacks
"""

import logging
import hmac
import hashlib
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Header, BackgroundTasks
from pydantic import BaseModel, Field

from whatsapp_service import get_whatsapp_service, WhatsAppMessage
from vernacular_service import get_vernacular_service, SupportedLanguage
from proactive_intelligence import get_proactive_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp Bot"])


# ============================================================================
# Request/Response Models
# ============================================================================

class SendMessageRequest(BaseModel):
    """Request to send a WhatsApp message"""
    to: str = Field(..., description="Recipient phone number")
    message: str = Field(..., description="Message content")
    language: str = Field("en", description="Language code: en, hi, ta, te")

class InvoiceAlertRequest(BaseModel):
    """Request to send invoice alert via WhatsApp"""
    phone: str
    vendor_name: str
    amount: float
    category: str
    warning: Optional[str] = None
    language: str = "en"

class SubsidyAlertRequest(BaseModel):
    """Request to send subsidy opportunity alert"""
    phone: str
    item_description: str
    amount: float
    scheme_name: str
    estimated_benefit: float
    language: str = "en"

class TwilioWebhookPayload(BaseModel):
    """Twilio incoming message webhook payload"""
    From: str
    Body: str
    MessageSid: Optional[str] = None
    AccountSid: Optional[str] = None


# ============================================================================
# Webhook Endpoints (for receiving messages)
# ============================================================================

@router.post("/webhook/twilio")
async def twilio_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Twilio WhatsApp webhook for incoming messages
    
    Configure this URL in Twilio Console:
    https://your-domain.com/api/v1/whatsapp/webhook/twilio
    """
    form_data = await request.form()
    
    from_number = form_data.get("From", "").replace("whatsapp:", "")
    message_body = form_data.get("Body", "").strip()
    
    logger.info(f"WhatsApp message from {from_number}: {message_body}")
    
    # Process message in background
    background_tasks.add_task(
        process_incoming_message,
        phone=from_number,
        message=message_body
    )
    
    # Return TwiML response
    return {
        "message": "received"
    }


@router.get("/webhook/meta")
async def meta_webhook_verify(
    request: Request
):
    """
    Meta WhatsApp webhook verification (GET request)
    
    Configure this URL in Meta Developer Console:
    https://your-domain.com/api/v1/whatsapp/webhook/meta
    """
    import os
    
    verify_token = os.getenv("META_WEBHOOK_VERIFY_TOKEN", "microcfo_verify")
    
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    if mode == "subscribe" and token == verify_token:
        return int(challenge)
    
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook/meta")
async def meta_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Meta WhatsApp webhook for incoming messages (POST request)
    """
    payload = await request.json()
    
    # Extract message from Meta's webhook format
    try:
        entry = payload.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])
        
        for msg in messages:
            from_number = msg.get("from", "")
            message_body = msg.get("text", {}).get("body", "")
            
            if from_number and message_body:
                logger.info(f"WhatsApp message from {from_number}: {message_body}")
                background_tasks.add_task(
                    process_incoming_message,
                    phone=from_number,
                    message=message_body
                )
    except Exception as e:
        logger.error(f"Error processing Meta webhook: {e}")
    
    return {"status": "ok"}


# ============================================================================
# Message Processing
# ============================================================================

async def process_incoming_message(phone: str, message: str):
    """Process an incoming WhatsApp message and respond"""
    whatsapp = get_whatsapp_service()
    vernacular = get_vernacular_service()
    
    # Detect language from message
    user_lang = vernacular.detect_language_preference(message)
    
    # Normalize message for command detection
    msg_lower = message.lower().strip()
    
    # Handle commands
    if msg_lower in ["menu", "help", "hi", "hello", "start"]:
        response = await generate_main_menu(user_lang)
    elif msg_lower == "apply":
        response = await vernacular.translate(
            "Great! I'll help you apply for the subsidy. Please share your business registration number (GSTIN or Udyam).",
            user_lang
        )
    elif msg_lower == "details":
        response = await vernacular.translate(
            "Please specify which alert you'd like more details about. Reply with the alert number.",
            user_lang
        )
    elif msg_lower == "approve":
        response = await vernacular.translate(
            "Message approved! However, for safety, we require you to confirm in the app before sending. Please check the MicroCFO app.",
            user_lang
        )
    elif msg_lower in ["1", "upload", "invoice"]:
        response = await vernacular.translate(
            "To upload an invoice, simply send a photo of the invoice. I'll analyze it automatically!",
            user_lang
        )
    elif msg_lower in ["2", "subsidies", "subsidy"]:
        response = await vernacular.translate(
            "Checking subsidy opportunities for your business... Please wait.",
            user_lang
        )
        # Subsidy check triggered via SubsidyHunter agent based on user's business profile
        # Results are sent via follow-up WhatsApp message or in-app notification
    elif msg_lower in ["3", "legal", "compliance"]:
        response = await vernacular.translate(
            "What's your legal/compliance question? I'll search our database for relevant information.",
            user_lang
        )
    else:
        # Check if it's an image (invoice upload)
        # For text, provide a helpful response
        response = await vernacular.translate(
            "I didn't understand that command. Reply 'MENU' for options or send an invoice photo to process.",
            user_lang
        )
    
    # Send response
    await whatsapp.send_message(WhatsAppMessage(to=phone, body=response))


async def generate_main_menu(lang: str = "en") -> str:
    """Generate the main menu message"""
    vernacular = get_vernacular_service()
    
    menu = """🤖 *MicroCFO Assistant*

Welcome! I'm your AI-powered CFO assistant. Here's what I can do:

1️⃣ *Upload Invoice* - Send a photo to analyze
2️⃣ *Check Subsidies* - Find government schemes for you
3️⃣ *Legal Query* - Ask compliance questions

Reply with a number or send an invoice photo to get started!"""
    
    if lang != "en":
        # Translate key parts
        menu = await vernacular.translate(menu, lang)
    
    return menu


# ============================================================================
# Outbound Message Endpoints
# ============================================================================

@router.post("/send")
async def send_whatsapp_message(
    request: SendMessageRequest
):
    """Send a WhatsApp message"""
    whatsapp = get_whatsapp_service()
    vernacular = get_vernacular_service()
    
    # Translate message if needed
    message = request.message
    if request.language != "en":
        message = await vernacular.translate(message, request.language)
    
    result = await whatsapp.send_message(
        WhatsAppMessage(to=request.to, body=message)
    )
    
    return result


@router.post("/send-invoice-alert")
async def send_invoice_alert(
    request: InvoiceAlertRequest
):
    """Send invoice processing alert via WhatsApp"""
    whatsapp = get_whatsapp_service()
    vernacular = get_vernacular_service()
    
    # Build message
    body = f"🧾 *{await vernacular.translate('Invoice Processed', request.language)}*\n\n"
    body += f"{await vernacular.translate('Vendor', request.language)}: {request.vendor_name}\n"
    body += f"{await vernacular.translate('Amount', request.language)}: ₹{request.amount:,.2f}\n"
    body += f"{await vernacular.translate('Category', request.language)}: {request.category}\n"
    
    if request.warning:
        warning_text = await vernacular.translate(request.warning, request.language)
        body += f"\n⚠️ *{await vernacular.translate('Warning', request.language)}:* {warning_text}"
    
    result = await whatsapp.send_message(
        WhatsAppMessage(to=request.phone, body=body)
    )
    
    return result


@router.post("/send-subsidy-alert")
async def send_subsidy_alert(
    request: SubsidyAlertRequest
):
    """Send proactive subsidy suggestion via WhatsApp"""
    whatsapp = get_whatsapp_service()
    vernacular = get_vernacular_service()
    
    body = f"🎯 *{await vernacular.translate('Subsidy Opportunity', request.language)}!*\n\n"
    body += f"{await vernacular.translate('Your purchase of', request.language)} {request.item_description} "
    body += f"(₹{request.amount:,.0f}) {await vernacular.translate('qualifies you for', request.language)} "
    body += f"*{request.scheme_name}*.\n\n"
    body += f"💰 {await vernacular.translate('Estimated benefit', request.language)}: ₹{request.estimated_benefit:,.0f}\n\n"
    body += await vernacular.translate("Reply APPLY to start the application process", request.language)
    
    result = await whatsapp.send_message(
        WhatsAppMessage(to=request.phone, body=body)
    )
    
    return result


@router.get("/status")
async def whatsapp_status():
    """Check WhatsApp service status"""
    whatsapp = get_whatsapp_service()
    
    return {
        "configured": whatsapp.is_configured,
        "provider": whatsapp.provider if whatsapp.is_configured else None,
        "message": "WhatsApp service ready" if whatsapp.is_configured else "WhatsApp not configured - using mock mode"
    }
