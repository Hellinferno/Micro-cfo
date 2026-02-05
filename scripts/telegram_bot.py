#!/usr/bin/env python3
"""
Simple Telegram Bot Test for MicroCFO
Tests that the bot token is working and can receive/send messages
"""

import os
import asyncio
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8540367745:AAELsGdW8HI8-WQmy5-k3HpNEUTJH-WXubE")
API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


async def get_bot_info():
    """Get bot information"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/getMe")
        return response.json()


async def send_message(chat_id: str, text: str):
    """Send a message to a chat"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }
        )
        return response.json()


async def get_updates(offset: int = None):
    """Get updates (new messages)"""
    async with httpx.AsyncClient() as client:
        params = {"timeout": 30}
        if offset:
            params["offset"] = offset
        response = await client.get(
            f"{API_URL}/getUpdates",
            params=params,
            timeout=35
        )
        return response.json()


async def handle_message(message: dict):
    """Handle an incoming message"""
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    user = message.get("from", {})
    username = user.get("username", user.get("first_name", "User"))
    
    print(f"Message from {username} (chat_id: {chat_id}): {text}")
    
    # Respond based on the message
    if text.lower() in ["/start", "hi", "hello"]:
        response = f"""🤖 *MicroCFO Bot*

Welcome {username}! I'm your AI-powered CFO assistant.

*Commands:*
/start - Show this menu
/invoice - Upload an invoice
/subsidies - Check subsidy opportunities
/legal - Ask a legal question
/help - Get help

Send me an invoice photo to get started!"""
    
    elif text.lower() == "/help":
        response = """*Need help?*

I can help you with:
• Invoice processing and auditing
• Finding government subsidies
• Legal compliance questions
• Payment negotiations

Just send me a message or upload an invoice!"""
    
    elif text.lower() == "/invoice":
        response = "📄 To upload an invoice, simply send me a photo or PDF. I'll analyze it automatically!"
    
    elif text.lower() == "/subsidies":
        response = "🔍 Checking subsidy opportunities... To find relevant schemes, tell me about your business or recent purchases."
    
    elif text.lower() == "/legal":
        response = "⚖️ What's your legal/compliance question? I'll search our database for relevant information."
    
    else:
        response = f"You said: {text}\n\nI'm still learning! Try /help for available commands."
    
    # Send the response
    result = await send_message(chat_id, response)
    if result.get("ok"):
        print(f"Sent reply to {username}")
    else:
        print(f"Failed to send: {result}")


async def main():
    """Main bot loop"""
    print("=" * 50)
    print("MicroCFO Telegram Bot")
    print("=" * 50)
    
    # Get bot info
    bot_info = await get_bot_info()
    if bot_info.get("ok"):
        bot = bot_info["result"]
        print(f"Bot: @{bot['username']} ({bot['first_name']})")
        print(f"Bot ID: {bot['id']}")
    else:
        print(f"Error: {bot_info}")
        return
    
    print("\nBot is running! Send a message to @MicroCFOBot")
    print("Press Ctrl+C to stop\n")
    
    offset = None
    
    while True:
        try:
            updates = await get_updates(offset)
            
            if updates.get("ok") and updates.get("result"):
                for update in updates["result"]:
                    offset = update["update_id"] + 1
                    
                    if "message" in update:
                        await handle_message(update["message"])
                    elif "callback_query" in update:
                        # Handle inline button callbacks
                        callback = update["callback_query"]
                        print(f"Callback: {callback.get('data')}")
                        
        except asyncio.CancelledError:
            print("\nBot stopped.")
            break
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user.")
