"""
Simple Telegram Bot Messaging Script
This script demonstrates how to send messages to Telegram using a bot.
"""

import requests
import json
from datetime import datetime

# Telegram Bot Configuration
BOT_TOKEN = "8369324693:AAFXewPCtGDs0rMLSZwtO5miaXxcCyRvtrM"  # Replace with your actual bot token
CHAT_ID = "819131470"      # Replace with your chat ID

# Example (replace with your actual values):
# BOT_TOKEN = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
# CHAT_ID = "123456789"

def send_telegram_message(message, parse_mode="HTML"):
    """
    Send a message to Telegram chat.
    
    Args:
        message (str): The message to send
        parse_mode (str): "HTML" or "Markdown" for formatting
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        
        payload = {
            'chat_id': CHAT_ID,
            'text': message,
            'parse_mode': parse_mode
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Message sent successfully to Telegram")
            return True
        else:
            print(f"❌ Failed to send message. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending Telegram message: {e}")
        return False

def format_stock_alert(stock_code, alert_type, score, ratio, change_pct):
    """
    Format a stock alert message for Telegram with HTML formatting.
    
    Args:
        stock_code (str): Stock symbol
        alert_type (str): STRONG, MEDIUM, TAKE_CARE
        score (float): Composite signal score
        ratio (float): Bid/ask ratio
        change_pct (float): Percentage change
    
    Returns:
        str: Formatted HTML message
    """
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    # Emoji mapping for alert types
    emoji_map = {
        "STRONG": "🚀",
        "MEDIUM": "📊", 
        "TAKE_CARE": "⚠️"
    }
    
    emoji = emoji_map.get(alert_type, "📈")
    
    if alert_type == "STRONG":
        message = f"""
{emoji} <b>STRONG RECOMMEND</b> {emoji}

🏷️ <b>Stock:</b> {stock_code}
📊 <b>Score:</b> {score:.1f}/100
📈 <b>Ratio:</b> {ratio:.2f}
📋 <b>Change:</b> {change_pct:+.2f}%
🕐 <b>Time:</b> {timestamp}

<i>High-confidence trading signal detected!</i>
        """
    elif alert_type == "TAKE_CARE":
        message = f"""
{emoji} <b>TAKE CARE ALERT</b> {emoji}

🏷️ <b>Stock:</b> {stock_code}
📉 <b>Ratio:</b> {ratio:.2f} (dropped below 1.0)
📋 <b>Change:</b> {change_pct:+.2f}%
🕐 <b>Time:</b> {timestamp}

<i>Ratio has declined - monitor closely</i>
        """
    else:  # MEDIUM
        message = f"""
{emoji} <b>Medium Signal</b>

🏷️ <b>Stock:</b> {stock_code}
📊 <b>Score:</b> {score:.1f}/100
📈 <b>Ratio:</b> {ratio:.2f}
📋 <b>Change:</b> {change_pct:+.2f}%
🕐 <b>Time:</b> {timestamp}
        """
    
    return message.strip()

def format_market_summary(strong_count, take_care_count, top_stocks, total_stocks, avg_score):
    """
    Format market summary message for Telegram.
    """
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    message = f"""
📊 <b>Market Summary</b> - {timestamp}

🚀 <b>Strong Recommendations:</b> {strong_count}
⚠️ <b>Take Care Alerts:</b> {take_care_count}
📈 <b>Total Monitored:</b> {total_stocks}
🎯 <b>Average Score:</b> {avg_score:.1f}

<b>🏆 Top Performers:</b>
"""
    
    for i, (stock, score, ratio, change) in enumerate(top_stocks[:5], 1):
        message += f"{i}. <b>{stock}</b>: {score:.1f} pts (Ratio: {ratio:.2f}, {change:+.1f}%)\n"
    
    return message

def test_telegram_connection():
    """Test the Telegram bot connection with a simple message."""
    test_message = f"""
🔧 <b>Test Message</b>

✅ Telegram bot connection successful!
🕐 <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<i>Your stock monitoring system is ready to send alerts.</i>
    """
    
    return send_telegram_message(test_message)

# Example usage and testing
if __name__ == "__main__":
    print("=== Telegram Bot Test ===")
    
    # Check if bot token and chat ID are configured
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or CHAT_ID == "YOUR_CHAT_ID_HERE":
        print("❌ Please configure BOT_TOKEN and CHAT_ID first!")
        print("\nSee setup instructions:")
        print("1. Create a bot with @BotFather on Telegram")
        print("2. Get your chat ID by messaging @userinfobot")
        print("3. Update the tokens in this file")
    else:
        # Test connection
        print("Testing Telegram connection...")
        if test_telegram_connection():
            print("✅ Telegram setup successful!")
            
            # Test stock alert formatting
            print("\nTesting alert formatting...")
            
            # Test STRONG alert
            strong_alert = format_stock_alert("AMER", "STRONG", 73.2, 1.45, 12.3)
            send_telegram_message(strong_alert)
            
            # Test TAKE_CARE alert  
            take_care_alert = format_stock_alert("SUGR", "TAKE_CARE", 15.4, 0.89, -28.7)
            send_telegram_message(take_care_alert)
            
            # Test market summary
            top_stocks = [
                ("AMER", 73.2, 1.45, 12.3),
                ("ARCC", 61.8, 1.32, 8.7),
                ("ENGC", 45.1, 1.28, 5.2)
            ]
            summary = format_market_summary(2, 1, top_stocks, 42, 24.3)
            send_telegram_message(summary)
            
        else:
            print("❌ Telegram setup failed! Check your bot token and chat ID.")
