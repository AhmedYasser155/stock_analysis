"""
Token Management System for Stock Analysis
Captures new tokens from Telegram messages and updates the system automatically.
"""

import requests
import json
import time
import re
from datetime import datetime
import os

# Your Telegram Bot credentials (these stay the same)
BOT_TOKEN = "8369324693:AAFXewPCtGDs0rMLSZwtO5miaXxcCyRvtrM"
ADMIN_CHAT_ID = "819131470"  # Your chat ID

# File to store the current API token
TOKEN_FILE = "current_api_token.txt"
LAST_UPDATE_FILE = "last_telegram_update.txt"

def get_telegram_updates():
    """Get new messages from Telegram bot."""
    try:
        # Get last processed update ID
        last_update_id = 0
        if os.path.exists(LAST_UPDATE_FILE):
            with open(LAST_UPDATE_FILE, 'r') as f:
                last_update_id = int(f.read().strip() or 0)
        
        # Get updates from Telegram
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        params = {
            'offset': last_update_id + 1,
            'timeout': 10
        }
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok') and data.get('result'):
                return data['result']
        
        return []
        
    except Exception as e:
        print(f"❌ Error getting Telegram updates: {e}")
        return []

def extract_token_from_message(text):
    """Extract API token from message text."""
    # Look for patterns like:
    # TOKEN: eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiI...
    # or just the token directly
    
    patterns = [
        r'TOKEN[:\s]+([A-Za-z0-9._-]+)',
        r'token[:\s]+([A-Za-z0-9._-]+)',
        r'^([A-Za-z0-9._-]{100,})$',  # Just the token alone (JWT tokens are long)
        r'Bearer\s+([A-Za-z0-9._-]+)',
        r'eyJ[A-Za-z0-9._-]+',  # JWT pattern (starts with eyJ)
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            token = match.group(1) if match.groups() else match.group(0)
            # Basic validation - JWT tokens are typically long
            if len(token) > 50:
                return token.strip()
    
    return None

def save_token(token):
    """Save the new token to file."""
    try:
        with open(TOKEN_FILE, 'w') as f:
            f.write(token)
        print(f"✅ New token saved to {TOKEN_FILE}")
        return True
    except Exception as e:
        print(f"❌ Error saving token: {e}")
        return False

def load_current_token():
    """Load the current token from file."""
    try:
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'r') as f:
                token = f.read().strip()
                if token:
                    return token
    except Exception as e:
        print(f"❌ Error loading token: {e}")
    
    return None

def send_confirmation(message):
    """Send confirmation message back to Telegram."""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': ADMIN_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except:
        return False

def update_last_processed(update_id):
    """Update the last processed update ID."""
    try:
        with open(LAST_UPDATE_FILE, 'w') as f:
            f.write(str(update_id))
    except Exception as e:
        print(f"❌ Error updating last processed ID: {e}")

def check_for_new_token():
    """Check Telegram for new token messages and update if found."""
    print("🔍 Checking for new token messages...")
    
    updates = get_telegram_updates()
    
    for update in updates:
        try:
            update_id = update['update_id']
            
            if 'message' in update:
                message = update['message']
                chat_id = str(message['chat']['id'])
                
                # Only process messages from admin
                if chat_id == ADMIN_CHAT_ID:
                    text = message.get('text', '')
                    
                    # Check if this message contains a token
                    new_token = extract_token_from_message(text)
                    
                    if new_token:
                        # Save the new token
                        if save_token(new_token):
                            # Send confirmation
                            confirmation_msg = f"""
✅ <b>Token Updated Successfully!</b>

🔑 <b>New Token:</b> {new_token[:20]}...
🕐 <b>Time:</b> {datetime.now().strftime('%H:%M:%S')}
📊 <b>Status:</b> Ready for market monitoring

<i>Stock analysis system will use the new token starting now.</i>
                            """
                            send_confirmation(confirmation_msg)
                            print(f"✅ Token updated from Telegram message")
                            print(f"🔑 New token: {new_token[:20]}...")
                        else:
                            send_confirmation("❌ Failed to save new token. Please try again.")
                    
                    # Update last processed regardless
                    update_last_processed(update_id)
                else:
                    print(f"⚠️ Ignoring message from unauthorized chat: {chat_id}")
            else:
                # Update last processed for non-message updates too
                update_last_processed(update_id)
                
        except Exception as e:
            print(f"❌ Error processing update: {e}")
            continue
    
    if not updates:
        print("📝 No new messages")

def get_api_token():
    """Get the current API token (for use by main script)."""
    return load_current_token()

def wait_for_token_at_startup():
    """Wait for a valid token at startup if none exists."""
    current_token = load_current_token()
    
    if current_token:
        print(f"✅ Using existing token: {current_token[:20]}...")
        return current_token
    
    print("⏳ No token found. Waiting for token via Telegram...")
    
    # Send startup message
    startup_msg = f"""
🤖 <b>Stock Analysis System Starting</b>

⏳ <b>Status:</b> Waiting for API token
📱 <b>Action Required:</b> Please send your API token

<b>Format examples:</b>
• TOKEN: your_token_here
• Bearer your_token_here  
• Or just paste the token directly

<i>System will start automatically once token is received.</i>
    """
    send_confirmation(startup_msg)
    
    # Wait for token (check every 10 seconds)
    while True:
        check_for_new_token()
        current_token = load_current_token()
        
        if current_token:
            print(f"✅ Token received! Starting system...")
            return current_token
        
        print("⏳ Still waiting for token...")
        time.sleep(10)

if __name__ == "__main__":
    print("=== Token Management System Test ===")
    
    # Test current token
    token = load_current_token()
    if token:
        print(f"📋 Current token: {token[:20]}...")
    else:
        print("❌ No token found")
    
    # Check for new messages
    check_for_new_token()
    
    # Test waiting for token
    print("\n🧪 Testing token wait system...")
    final_token = wait_for_token_at_startup()
    print(f"🎯 Final token: {final_token[:20]}...")