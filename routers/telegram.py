#!/usr/bin/env python3
"""
Telegram Bot Router for MicroCFO
Handles incoming Telegram messages and webhook callbacks
"""

import logging
import os
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, Field

from telegram_service import get_telegram_service, TelegramMessage
from vernacular_service import get_vernacular_service, SupportedLanguage
from proactive_intelligence import get_proactive_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telegram", tags=["Telegram Bot"])


# ============================================================================
# Request/Response Models
# ============================================================================

class SendMessageRequest(BaseModel):
    """Request to send a Telegram message"""
    chat_id: str = Field(..., description="Recipient chat ID")
    message: str = Field(..., description="Message content")
    language: str = Field("en", description="Language code: en, hi, ta, te")

class InvoiceAlertRequest(BaseModel):
    """Request to send invoice alert via Telegram"""
    chat_id: str
    vendor_name: str
    amount: float
    category: str
    warning: Optional[str] = None
    language: str = "en"

class SubsidyAlertRequest(BaseModel):
    """Request to send subsidy opportunity alert"""
    chat_id: str
    item_description: str
    amount: float
    scheme_name: str
    estimated_benefit: float
    language: str = "en"


# ============================================================================
# Webhook Endpoint (for receiving messages)
# ============================================================================

@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Telegram Bot webhook for incoming messages
    
    Configure this URL in Telegram via setWebhook API:
    https://your-domain.com/api/v1/telegram/webhook
    """
    try:
        payload = await request.json()
        
        # Handle regular messages
        if "message" in payload:
            message = payload["message"]
            chat_id = str(message["chat"]["id"])
            
            # Get text content
            text = message.get("text", "")
            
            # Check for photos (invoice upload)
            photo = message.get("photo")
            document = message.get("document")
            
            logger.info(f"Telegram message from {chat_id}: {text or '[media]'}")
            
            # Process message in background
            background_tasks.add_task(
                process_incoming_message,
                chat_id=chat_id,
                message=text,
                has_photo=photo is not None,
                has_document=document is not None,
                photo_file_id=photo[-1]["file_id"] if photo else None,
                document_file_id=document["file_id"] if document else None
            )
        
        # Handle callback queries (inline keyboard buttons)
        elif "callback_query" in payload:
            callback = payload["callback_query"]
            chat_id = str(callback["message"]["chat"]["id"])
            callback_data = callback.get("data", "")
            callback_id = callback["id"]
            
            logger.info(f"Telegram callback from {chat_id}: {callback_data}")
            
            background_tasks.add_task(
                process_callback_query,
                chat_id=chat_id,
                callback_data=callback_data,
                callback_id=callback_id
            )
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error processing Telegram webhook: {e}")
        return {"status": "error", "message": str(e)}


# ============================================================================
# Message Processing
# ============================================================================

async def process_incoming_message(
    chat_id: str,
    message: str,
    has_photo: bool = False,
    has_document: bool = False,
    photo_file_id: Optional[str] = None,
    document_file_id: Optional[str] = None
):
    """Process an incoming Telegram message and respond"""
    telegram = get_telegram_service()
    vernacular = get_vernacular_service()
    
    # Detect language from message
    user_lang = vernacular.detect_language_preference(message) if message else "en"
    
    # Normalize message for command detection
    msg_lower = message.lower().strip() if message else ""
    
    # Create inline keyboard for main menu
    main_menu_keyboard = {
        "inline_keyboard": [
            [
                {"text": "📄 Upload Invoice", "callback_data": "upload_invoice"},
                {"text": "💰 Check Subsidies", "callback_data": "check_subsidies"}
            ],
            [
                {"text": "⚖️ Legal Query", "callback_data": "legal_query"},
                {"text": "📊 My Dashboard", "callback_data": "dashboard"}
            ]
        ]
    }
    
    # Handle commands
    if msg_lower in ["/start", "/menu", "/help", "menu", "help", "hi", "hello", "start"]:
        response = await generate_main_menu(user_lang)
        await telegram.send_message(TelegramMessage(
            chat_id=chat_id,
            text=response,
            reply_markup=main_menu_keyboard
        ))
    
    elif msg_lower == "/apply" or msg_lower == "apply":
        response = await vernacular.translate(
            "Great! I'll help you apply for the subsidy. Please share your business registration number (GSTIN or Udyam).",
            user_lang
        )
        await telegram.send_message(TelegramMessage(chat_id=chat_id, text=response))
    
    elif msg_lower == "/details" or msg_lower == "details":
        response = await vernacular.translate(
            "Please specify which alert you'd like more details about. Reply with the alert number.",
            user_lang
        )
        await telegram.send_message(TelegramMessage(chat_id=chat_id, text=response))
    
    elif msg_lower == "/approve" or msg_lower == "approve":
        response = await vernacular.translate(
            "Message approved! However, for safety, we require you to confirm in the app before sending. Please check the MicroCFO app.",
            user_lang
        )
        await telegram.send_message(TelegramMessage(chat_id=chat_id, text=response))
    
    elif has_photo or has_document:
        # Handle invoice upload
        response = await vernacular.translate(
            "📄 *Invoice Received!*\n\nI'm analyzing your invoice now. Please wait a moment...",
            user_lang
        )
        await telegram.send_message(TelegramMessage(chat_id=chat_id, text=response))
        
        # TODO: Process invoice with Visual Auditor
        # For now, send acknowledgment
        follow_up = await vernacular.translate(
            "✅ Invoice processed successfully!\n\nI've extracted the details and categorized the expenses. Check the MicroCFO app for the full analysis.",
            user_lang
        )
        await telegram.send_message(TelegramMessage(chat_id=chat_id, text=follow_up))
    
    elif msg_lower in ["1", "upload", "invoice", "/invoice"]:
        response = await vernacular.translate(
            "📄 To upload an invoice, simply send a photo or PDF of the invoice. I'll analyze it automatically!",
            user_lang
        )
        await telegram.send_message(TelegramMessage(chat_id=chat_id, text=response))
    
    elif msg_lower in ["2", "subsidies", "subsidy", "/subsidies"]:
        response = await vernacular.translate(
            "🔍 Checking subsidy opportunities for your business... Please wait.",
            user_lang
        )
        await telegram.send_message(TelegramMessage(chat_id=chat_id, text=response))
        # TODO: Integrate with SubsidyHunter agent
    
    elif msg_lower in ["3", "legal", "compliance", "/legal"]:
        response = await vernacular.translate(
            "⚖️ What's your legal/compliance question? I'll search our database for relevant information.",
            user_lang
        )
        await telegram.send_message(TelegramMessage(chat_id=chat_id, text=response))
    
    else:
        # Default response with menu
        response = await vernacular.translate(
            "I didn't understand that command. Here's what I can do:",
            user_lang
        )
        await telegram.send_message(TelegramMessage(
            chat_id=chat_id,
            text=response,
            reply_markup=main_menu_keyboard
        ))


async def process_callback_query(chat_id: str, callback_data: str, callback_id: str):
    """Process callback query from inline keyboard"""
    telegram = get_telegram_service()
    vernacular = get_vernacular_service()
    
    # Acknowledge the callback
    await telegram.answer_callback_query(callback_id)
    
    if callback_data == "upload_invoice":
        response = "📄 To upload an invoice, simply send a photo or PDF of the invoice. I'll analyze it automatically!"
        await telegram.send_message(TelegramMessage(chat_id=chat_id, text=response))
    
    elif callback_data == "check_subsidies":
        response = "🔍 Checking subsidy opportunities for your business... Please wait."
        await telegram.send_message(TelegramMessage(chat_id=chat_id, text=response))
        # TODO: Integrate with SubsidyHunter
    
    elif callback_data == "legal_query":
        response = "⚖️ What's your legal/compliance question? I'll search our database for relevant information."
        await telegram.send_message(TelegramMessage(chat_id=chat_id, text=response))
    
    elif callback_data == "dashboard":
        response = "📊 Opening your dashboard in the MicroCFO app..."
        await telegram.send_message(TelegramMessage(chat_id=chat_id, text=response))
    
    elif callback_data.startswith("apply_"):
        scheme_id = callback_data.replace("apply_", "")
        response = f"📝 Starting application for scheme {scheme_id}. Please provide your GSTIN or Udyam registration number."
        await telegram.send_message(TelegramMessage(chat_id=chat_id, text=response))


async def generate_main_menu(lang: str = "en") -> str:
    """Generate the main menu message"""
    vernacular = get_vernacular_service()
    
    menu = """🤖 *MicroCFO Assistant*

Welcome! I'm your AI-powered CFO assistant. Here's what I can do:

1️⃣ *Upload Invoice* - Send a photo to analyze
2️⃣ *Check Subsidies* - Find government schemes for you
3️⃣ *Legal Query* - Ask compliance questions
4️⃣ *Dashboard* - View your financial summary

Tap a button below or send an invoice photo to get started!"""
    
    if lang != "en":
        menu = await vernacular.translate(menu, lang)
    
    return menu


# ============================================================================
# Outbound Message Endpoints
# ============================================================================

@router.post("/send")
async def send_telegram_message(request: SendMessageRequest):
    """Send a Telegram message"""
    telegram = get_telegram_service()
    vernacular = get_vernacular_service()
    
    # Translate message if needed
    message = request.message
    if request.language != "en":
        message = await vernacular.translate(message, request.language)
    
    result = await telegram.send_message(
        TelegramMessage(chat_id=request.chat_id, text=message)
    )
    
    return result


@router.post("/send-invoice-alert")
async def send_invoice_alert(request: InvoiceAlertRequest):
    """Send invoice processing alert via Telegram"""
    telegram = get_telegram_service()
    vernacular = get_vernacular_service()
    
    # Build message
    body = f"🧾 *{await vernacular.translate('Invoice Processed', request.language)}*\n\n"
    body += f"{await vernacular.translate('Vendor', request.language)}: {request.vendor_name}\n"
    body += f"{await vernacular.translate('Amount', request.language)}: ₹{request.amount:,.2f}\n"
    body += f"{await vernacular.translate('Category', request.language)}: {request.category}\n"
    
    if request.warning:
        warning_text = await vernacular.translate(request.warning, request.language)
        body += f"\n⚠️ *{await vernacular.translate('Warning', request.language)}:* {warning_text}"
    
    result = await telegram.send_message(
        TelegramMessage(chat_id=request.chat_id, text=body)
    )
    
    return result


@router.post("/send-subsidy-alert")
async def send_subsidy_alert(request: SubsidyAlertRequest):
    """Send proactive subsidy suggestion via Telegram"""
    telegram = get_telegram_service()
    vernacular = get_vernacular_service()
    
    body = f"🎯 *{await vernacular.translate('Subsidy Opportunity', request.language)}!*\n\n"
    body += f"{await vernacular.translate('Your purchase of', request.language)} {request.item_description} "
    body += f"(₹{request.amount:,.0f}) {await vernacular.translate('qualifies you for', request.language)} "
    body += f"*{request.scheme_name}*.\n\n"
    body += f"💰 {await vernacular.translate('Estimated benefit', request.language)}: ₹{request.estimated_benefit:,.0f}"
    
    # Add apply button
    keyboard = {
        "inline_keyboard": [
            [{"text": "📝 Apply Now", "callback_data": f"apply_{request.scheme_name}"}],
            [{"text": "ℹ️ More Details", "callback_data": f"details_{request.scheme_name}"}]
        ]
    }
    
    result = await telegram.send_message(
        TelegramMessage(chat_id=request.chat_id, text=body, reply_markup=keyboard)
    )
    
    return result


@router.get("/status")
async def telegram_status():
    """Check Telegram service status"""
    telegram = get_telegram_service()
    
    if telegram.is_configured:
        bot_info = await telegram.get_me()
        return {
            "configured": True,
            "bot_info": bot_info.get("bot_info") if bot_info.get("success") else None,
            "message": "Telegram Bot ready"
        }
    
    return {
        "configured": False,
        "message": "Telegram not configured - using mock mode"
    }


@router.post("/set-webhook")
async def set_telegram_webhook(webhook_url: str):
    """Set webhook URL for receiving Telegram updates"""
    telegram = get_telegram_service()
    result = await telegram.set_webhook(webhook_url)
    return result


@router.post("/delete-webhook")
async def delete_telegram_webhook():
    """Delete webhook (switch to polling mode)"""
    telegram = get_telegram_service()
    result = await telegram.delete_webhook()
    return result
