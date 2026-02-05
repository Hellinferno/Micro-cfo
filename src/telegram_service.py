#!/usr/bin/env python3
"""
Telegram Bot Integration Service for MicroCFO
Provides Telegram-first interface using Telegram Bot API

SETUP:
1. Create a bot via @BotFather on Telegram
2. Get your Bot API Token
3. Set TELEGRAM_BOT_TOKEN environment variable
4. Configure webhook URL for incoming messages (optional, can use polling)
"""

import os
import logging
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TelegramMessage:
    """Represents a Telegram message"""
    chat_id: str
    text: str
    parse_mode: str = "Markdown"
    reply_markup: Optional[Dict] = None
    
    def __post_init__(self):
        """Normalize chat_id"""
        self.chat_id = str(self.chat_id)


class TelegramService:
    """
    Telegram messaging service using Telegram Bot API
    
    Environment Variables Required:
    - TELEGRAM_BOT_TOKEN: Your Telegram bot token from @BotFather
    
    Optional:
    - TELEGRAM_WEBHOOK_URL: Webhook URL for receiving updates
    """
    
    BASE_URL = "https://api.telegram.org/bot"
    
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL")
        self.is_configured = False
        
        if self.bot_token:
            self.api_url = f"{self.BASE_URL}{self.bot_token}"
            self.is_configured = True
            logger.info("✅ Telegram Bot configured successfully")
        else:
            logger.warning("⚠️ Telegram Bot not configured. Set TELEGRAM_BOT_TOKEN")
    
    async def send_message(self, message: TelegramMessage) -> Dict[str, Any]:
        """Send a Telegram message"""
        if not self.is_configured:
            return {
                "success": False,
                "error": "Telegram not configured",
                "mock": True,
                "message": f"[MOCK] Would send to {message.chat_id}: {message.text}"
            }
        
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "chat_id": message.chat_id,
                    "text": message.text,
                    "parse_mode": message.parse_mode
                }
                
                if message.reply_markup:
                    payload["reply_markup"] = message.reply_markup
                
                response = await client.post(
                    f"{self.api_url}/sendMessage",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok"):
                        return {
                            "success": True,
                            "message_id": result["result"]["message_id"],
                            "chat_id": result["result"]["chat"]["id"]
                        }
                    else:
                        return {
                            "success": False,
                            "error": result.get("description", "Unknown error")
                        }
                else:
                    return {
                        "success": False,
                        "error": response.text,
                        "status_code": response.status_code
                    }
        except Exception as e:
            logger.error(f"Telegram send error: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_photo(
        self,
        chat_id: str,
        photo_url: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a photo via Telegram"""
        if not self.is_configured:
            return {
                "success": False,
                "error": "Telegram not configured",
                "mock": True
            }
        
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "chat_id": chat_id,
                    "photo": photo_url
                }
                if caption:
                    payload["caption"] = caption
                    payload["parse_mode"] = "Markdown"
                
                response = await client.post(
                    f"{self.api_url}/sendPhoto",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": result.get("ok", False),
                        "message_id": result.get("result", {}).get("message_id")
                    }
                else:
                    return {"success": False, "error": response.text}
        except Exception as e:
            logger.error(f"Telegram photo send error: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_document(
        self,
        chat_id: str,
        document_url: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a document via Telegram"""
        if not self.is_configured:
            return {
                "success": False,
                "error": "Telegram not configured",
                "mock": True
            }
        
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "chat_id": chat_id,
                    "document": document_url
                }
                if caption:
                    payload["caption"] = caption
                    payload["parse_mode"] = "Markdown"
                
                response = await client.post(
                    f"{self.api_url}/sendDocument",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": result.get("ok", False),
                        "message_id": result.get("result", {}).get("message_id")
                    }
                else:
                    return {"success": False, "error": response.text}
        except Exception as e:
            logger.error(f"Telegram document send error: {e}")
            return {"success": False, "error": str(e)}
    
    async def set_webhook(self, webhook_url: str) -> Dict[str, Any]:
        """Set webhook URL for receiving updates"""
        if not self.is_configured:
            return {"success": False, "error": "Telegram not configured"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/setWebhook",
                    json={"url": webhook_url}
                )
                
                result = response.json()
                return {
                    "success": result.get("ok", False),
                    "description": result.get("description")
                }
        except Exception as e:
            logger.error(f"Set webhook error: {e}")
            return {"success": False, "error": str(e)}
    
    async def delete_webhook(self) -> Dict[str, Any]:
        """Delete webhook (use polling instead)"""
        if not self.is_configured:
            return {"success": False, "error": "Telegram not configured"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/deleteWebhook"
                )
                
                result = response.json()
                return {
                    "success": result.get("ok", False),
                    "description": result.get("description")
                }
        except Exception as e:
            logger.error(f"Delete webhook error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_updates(self, offset: Optional[int] = None, timeout: int = 30) -> List[Dict]:
        """Get updates using long polling (alternative to webhooks)"""
        if not self.is_configured:
            return []
        
        try:
            async with httpx.AsyncClient() as client:
                params = {"timeout": timeout}
                if offset:
                    params["offset"] = offset
                
                response = await client.get(
                    f"{self.api_url}/getUpdates",
                    params=params,
                    timeout=timeout + 10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok"):
                        return result.get("result", [])
                return []
        except Exception as e:
            logger.error(f"Get updates error: {e}")
            return []
    
    async def get_me(self) -> Dict[str, Any]:
        """Get bot information"""
        if not self.is_configured:
            return {"success": False, "error": "Telegram not configured"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/getMe")
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok"):
                        return {
                            "success": True,
                            "bot_info": result["result"]
                        }
                return {"success": False, "error": "Failed to get bot info"}
        except Exception as e:
            logger.error(f"Get me error: {e}")
            return {"success": False, "error": str(e)}
    
    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: Optional[str] = None,
        show_alert: bool = False
    ) -> Dict[str, Any]:
        """Answer a callback query from inline keyboard"""
        if not self.is_configured:
            return {"success": False, "error": "Telegram not configured"}
        
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "callback_query_id": callback_query_id,
                    "show_alert": show_alert
                }
                if text:
                    payload["text"] = text
                
                response = await client.post(
                    f"{self.api_url}/answerCallbackQuery",
                    json=payload
                )
                
                result = response.json()
                return {"success": result.get("ok", False)}
        except Exception as e:
            logger.error(f"Answer callback error: {e}")
            return {"success": False, "error": str(e)}
    
    async def edit_message_text(
        self,
        chat_id: str,
        message_id: int,
        text: str,
        parse_mode: str = "Markdown",
        reply_markup: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Edit an existing message"""
        if not self.is_configured:
            return {"success": False, "error": "Telegram not configured"}
        
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "text": text,
                    "parse_mode": parse_mode
                }
                if reply_markup:
                    payload["reply_markup"] = reply_markup
                
                response = await client.post(
                    f"{self.api_url}/editMessageText",
                    json=payload
                )
                
                result = response.json()
                return {"success": result.get("ok", False)}
        except Exception as e:
            logger.error(f"Edit message error: {e}")
            return {"success": False, "error": str(e)}


# Singleton instance
_telegram_service: Optional[TelegramService] = None


def get_telegram_service() -> TelegramService:
    """Get or create the Telegram service singleton"""
    global _telegram_service
    if _telegram_service is None:
        _telegram_service = TelegramService()
    return _telegram_service
