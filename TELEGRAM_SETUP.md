# 🤖 Telegram Integration Setup Guide

## Quick Setup Steps

### 1. Create Your Telegram Bot
1. Open Telegram and search for `@BotFather`
2. Send `/start` then `/newbot`
3. Choose a name: "My Stock Analysis Bot"
4. Choose username: "my_stock_analysis_bot" (must end with 'bot')
5. **Copy the bot token** (looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Get Your Chat ID
**Method 1 (Easiest):**
1. Search for `@userinfobot` on Telegram
2. Send any message
3. **Copy your Chat ID** (number like `123456789`)

**Method 2:**
1. Start a chat with your new bot
2. Send any message
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Look for `"chat":{"id":123456789` in the response

### 3. Configure the Bot
Edit `telegram_msg.py`:
```python
BOT_TOKEN = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"  # Your actual token
CHAT_ID = "123456789"  # Your actual chat ID
```

### 4. Test the Setup
```bash
cd "e:\Projects\Stock Analysis"
python telegram_msg.py
```

You should see:
- ✅ Message sent successfully to Telegram
- Test messages in your Telegram chat

### 5. Run the Enhanced System
```bash
python price_depth.py
```

## What You'll Receive

### 🚀 STRONG RECOMMEND Alerts
```
🚀 STRONG RECOMMEND 🚀

🏷️ Stock: AMER
📊 Score: 73.2/100
📈 Ratio: 1.45
📋 Change: +12.3%
🕐 Time: 14:27:45

High-confidence trading signal detected!
```

### ⚠️ TAKE CARE Alerts
```
⚠️ TAKE CARE ALERT ⚠️

🏷️ Stock: SUGR
📉 Ratio: 0.89 (dropped below 1.0)
📋 Change: -28.7%
🕐 Time: 14:28:12

Ratio has declined - monitor closely
```

### 📊 Market Summaries (Every 6 cycles or when there's activity)
```
📊 Market Summary - 14:30:15

🚀 Strong Recommendations: 2
⚠️ Take Care Alerts: 1
📈 Total Monitored: 42
🎯 Average Score: 24.3

🏆 Top Performers:
1. AMER: 73.2 pts (Ratio: 1.45, +12.3%)
2. ARCC: 61.8 pts (Ratio: 1.32, +8.7%)
3. ENGC: 45.1 pts (Ratio: 1.28, +5.2%)
```

## Troubleshooting

### ❌ "Failed to send message"
- Check your BOT_TOKEN and CHAT_ID
- Make sure you started a chat with your bot first
- Verify internet connection

### ❌ "Telegram integration not available"
- Install requests: `pip install requests`
- Check that `telegram_msg.py` exists in the same folder

### ❌ Bot not responding
- Make sure the bot token is correct
- Try creating a new bot with @BotFather
- Check if you blocked the bot accidentally

## Security Notes

- **Never share your bot token publicly**
- The chat ID is your personal Telegram user ID
- The bot can only send messages to you (the chat owner)
- Bot tokens can be regenerated in @BotFather if compromised

## Customization

### Change Alert Frequency
In `price_depth.py`, modify:
```python
# Send summary every N cycles instead of 6
if (process_notifications.cycle_count % 10 == 0 or  # Every 100 seconds instead of 60
```

### Enable Medium Signals
Uncomment this line in `process_notifications()`:
```python
# send_telegram_notification(stock_code, "MEDIUM", score, ratio, change_pct)
```

### Disable Market Summaries
Comment out the `send_telegram_summary()` call in `process_notifications()`

Your Telegram bot is now integrated and will send real-time stock alerts! 🚀