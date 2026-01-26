#!/usr/bin/env python3
"""
Phase 4: The Sentinel Routine - Real-time Legal Alerts
Monitors government websites for new legal updates
"""

import requests
from bs4 import BeautifulSoup
import schedule
import time
import json
import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
from legal_ingestion import LegalDocumentProcessor
from vector_database import LegalVectorDB

class LegalSentinel:
    """Monitors legal updates and sends alerts"""
    
    def __init__(self, db_path: str = "./legal_db", websocket_manager=None):
        self.db_path = db_path
        self.vector_db = LegalVectorDB(db_path)
        self.processor = LegalDocumentProcessor()
        self.seen_notifications = self._load_seen_notifications()
        self.websocket_manager = websocket_manager
        
        # Government websites to monitor
        self.monitoring_urls = {
            'cbic': 'https://www.cbic.gov.in/htdocs-cbec/gst/notifications',
            'mca': 'https://www.mca.gov.in/content/mca/global/en/home.html',
            'incometax': 'https://www.incometax.gov.in/iec/foportal/help/notifications'
        }
    
    def _load_seen_notifications(self) -> Set[str]:
        """Load previously seen notifications"""
        seen_file = os.path.join(self.db_path, 'seen_notifications.json')
        if os.path.exists(seen_file):
            with open(seen_file, 'r') as f:
                return set(json.load(f))
        return set()
    
    def _save_seen_notifications(self):
        """Save seen notifications to file"""
        seen_file = os.path.join(self.db_path, 'seen_notifications.json')
        os.makedirs(os.path.dirname(seen_file), exist_ok=True)
        with open(seen_file, 'w') as f:
            json.dump(list(self.seen_notifications), f)
    
    def scrape_cbic_notifications(self) -> List[Dict[str, str]]:
        """Scrape CBIC website for new GST notifications"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(self.monitoring_urls['cbic'], headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            notifications = []
            
            # Look for notification links (this is a simplified example)
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                if 'notification' in href.lower() and '.pdf' in href.lower():
                    notification_id = f"cbic_{href}"
                    if notification_id not in self.seen_notifications:
                        notifications.append({
                            'id': notification_id,
                            'title': text,
                            'url': href if href.startswith('http') else f"https://www.cbic.gov.in{href}",
                            'source': 'CBIC',
                            'law_type': 'GST',
                            'date_found': datetime.now().isoformat()
                        })
            
            return notifications
        
        except Exception as e:
            print(f"Error scraping CBIC: {e}")
            return []
    
    def check_user_relevance(self, notification: Dict[str, str], user_profiles: List[Dict]) -> List[Dict]:
        """Check if notification is relevant to any user profiles"""
        relevant_users = []
        
        title = notification['title'].lower()
        
        for profile in user_profiles:
            # Check sector relevance
            industry = profile.get('industry_code', '').lower()
            if industry and industry in title:
                relevant_users.append(profile)
                continue
            
            # Check turnover relevance
            turnover_tier = profile.get('turnover_tier', '')
            if 'small' in title and '< 5Cr' in turnover_tier:
                relevant_users.append(profile)
            elif 'medium' in title and '5-20Cr' in turnover_tier:
                relevant_users.append(profile)
        
        return relevant_users
    
    async def send_websocket_alert(self, user_id: str, notification: Dict[str, str]):
        """
        Send real-time alert via WebSocket
        
        Args:
            user_id: User identifier
            notification: Notification data
        """
        if not self.websocket_manager:
            return
        
        from websocket_manager import WebSocketMessage
        
        # Send to user-specific room
        message = WebSocketMessage(
            type="legal_update",
            data={
                "title": notification['title'],
                "source": notification['source'],
                "law_type": notification['law_type'],
                "url": notification['url'],
                "date_found": notification['date_found'][:10],
                "relevance": "high",
                "notification_id": notification['id']
            }
        )
        
        await self.websocket_manager.send_personal_message(user_id, message)
    
    async def broadcast_to_industry(self, industry_code: str, notification: Dict[str, str]):
        """
        Broadcast notification to all users in an industry
        
        Args:
            industry_code: Industry classification code
            notification: Notification data
        """
        if not self.websocket_manager:
            return
        
        from websocket_manager import WebSocketMessage
        
        room = f"industry:{industry_code}"
        
        message = WebSocketMessage(
            type="legal_update",
            data={
                "title": notification['title'],
                "source": notification['source'],
                "law_type": notification['law_type'],
                "url": notification['url'],
                "date_found": notification['date_found'][:10],
                "relevance": "medium",
                "notification_id": notification['id'],
                "target_industry": industry_code
            }
        )
        
        await self.websocket_manager.broadcast_to_room(room, message)
    
    def send_whatsapp_alert(self, user_profile: Dict, notification: Dict[str, str]):
        """Send WhatsApp alert (placeholder - integrate with WhatsApp Business API)"""
        message = f"""
🚨 NEW LEGAL UPDATE ALERT 🚨

Dear {user_profile.get('business_name', 'User')},

A new {notification['law_type']} notification has been published that may affect your business:

📋 Title: {notification['title']}
🏛️ Source: {notification['source']}
📅 Date: {notification['date_found'][:10]}
🔗 Link: {notification['url']}

Industry: {user_profile.get('industry_code', 'N/A')}
Turnover Tier: {user_profile.get('turnover_tier', 'N/A')}

Please review this notification and consult your CA if needed.

- MicroCFO Legal Sentinel
        """
        
        # In a real implementation, you would use WhatsApp Business API
        print(f"ALERT SENT TO {user_profile.get('business_name', 'User')}:")
        print(message)
        print("-" * 50)
    
    def process_new_notification(self, notification: Dict[str, str]):
        """Process a new notification and add to vector DB"""
        try:
            # Download and process the PDF (simplified)
            print(f"Processing notification: {notification['title']}")
            
            # In a real implementation, you would:
            # 1. Download the PDF from notification['url']
            # 2. Process it with self.processor
            # 3. Add chunks to vector DB
            
            # For now, create a mock chunk
            from legal_ingestion import LegalChunk
            mock_chunk = LegalChunk(
                text=f"New notification: {notification['title']}",
                law_type=notification['law_type'],
                effective_date=notification['date_found'][:10]
            )
            
            self.vector_db.add_chunks([mock_chunk])
            print(f"Added notification to vector DB: {notification['id']}")
            
        except Exception as e:
            print(f"Error processing notification {notification['id']}: {e}")
    
    def daily_monitoring_routine(self):
        """Main monitoring routine - runs daily"""
        print(f"🔍 Starting daily legal monitoring at {datetime.now()}")
        
        # Load user profiles (in real implementation, from database)
        sample_profiles = [
            {
                'user_id': 'user_textile_001',
                'business_name': 'Textile Mills Ltd',
                'industry_code': 'textile',
                'turnover_tier': '5-20Cr',
                'phone': '+91XXXXXXXXXX'
            },
            {
                'user_id': 'user_trading_001',
                'business_name': 'Small Traders',
                'industry_code': 'trading',
                'turnover_tier': '< 5Cr',
                'phone': '+91XXXXXXXXXX'
            }
        ]
        
        # Scrape for new notifications
        new_notifications = []
        new_notifications.extend(self.scrape_cbic_notifications())
        
        print(f"Found {len(new_notifications)} new notifications")
        
        # Process each new notification
        for notification in new_notifications:
            # Mark as seen
            self.seen_notifications.add(notification['id'])
            
            # Process and add to vector DB
            self.process_new_notification(notification)
            
            # Check relevance to users
            relevant_users = self.check_user_relevance(notification, sample_profiles)
            
            # Send alerts to relevant users
            for user in relevant_users:
                # Send WhatsApp alert (legacy)
                self.send_whatsapp_alert(user, notification)
                
                # Send WebSocket alert (real-time)
                if self.websocket_manager:
                    asyncio.create_task(
                        self.send_websocket_alert(user['user_id'], notification)
                    )
            
            # Broadcast to industry rooms if applicable
            if self.websocket_manager:
                title_lower = notification['title'].lower()
                for industry in ['textile', 'trading', 'manufacturing', 'technology']:
                    if industry in title_lower:
                        asyncio.create_task(
                            self.broadcast_to_industry(industry, notification)
                        )
        
        # Save seen notifications
        self._save_seen_notifications()
        
        print(f"✅ Monitoring complete. Processed {len(new_notifications)} notifications")
    
    def start_monitoring(self):
        """Start the monitoring service"""
        print("🚀 Starting Legal Sentinel Monitoring Service")
        
        # Schedule daily monitoring at 9 AM
        schedule.every().day.at("09:00").do(self.daily_monitoring_routine)
        
        # For testing, also run every 5 minutes
        # schedule.every(5).minutes.do(self.daily_monitoring_routine)
        
        print("📅 Scheduled daily monitoring at 9:00 AM")
        print("Press Ctrl+C to stop monitoring")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")


# CLI interface
if __name__ == "__main__":
    import sys
    
    sentinel = LegalSentinel()
    
    if len(sys.argv) > 1 and sys.argv[1] == "run-once":
        # Run monitoring once for testing
        sentinel.daily_monitoring_routine()
    else:
        # Start continuous monitoring
        sentinel.start_monitoring()