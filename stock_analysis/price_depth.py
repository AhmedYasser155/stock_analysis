import os
import json
import requests
from datetime import datetime
import time
import csv
# import oracledb  # Commented out for GitHub Actions deployment
import threading
import concurrent.futures
from datetime import time as dtime
from collections import deque
import statistics

from datetime import datetime
try:
    from win10toast import ToastNotifier
    toaster = ToastNotifier()
except ImportError:
    toaster = None

# Telegram integration
try:
    from telegram_msg import send_telegram_message, format_stock_alert, format_market_summary
    TELEGRAM_ENABLED = True
except ImportError:
    TELEGRAM_ENABLED = False
    print("⚠️ Telegram not available")

# Token management system
try:
    from token_manager import wait_for_token_at_startup, check_for_new_token, get_api_token
    TOKEN_MANAGER_ENABLED = True
except ImportError:
    TOKEN_MANAGER_ENABLED = False
    print("⚠️ Token manager not available")

def log_notification(msg):
    with open("notification_log.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {msg}\n")

def send_telegram_notification(stock_code, alert_type, score, ratio, change_pct):
    """Send stock alert to Telegram if enabled."""
    if not TELEGRAM_ENABLED:
        return
    
    try:
        message = format_stock_alert(stock_code, alert_type, score, ratio, change_pct)
        success = send_telegram_message(message)
        
        if success:
            # Track alert statistics
            alert_counts[alert_type] = alert_counts.get(alert_type, 0) + 1
            log_notification(f"📱 Telegram alert sent for {stock_code}")
        else:
            log_notification(f"❌ Failed to send Telegram alert for {stock_code}")
            
    except Exception as e:
        log_notification(f"❌ Telegram error for {stock_code}: {e}")

def send_telegram_summary(strong_count, take_care_count, top_stocks, total_stocks, avg_score):
    """Send market summary to Telegram."""
    if not TELEGRAM_ENABLED:
        return
        
    try:
        message = format_market_summary(strong_count, take_care_count, top_stocks, total_stocks, avg_score)
        success = send_telegram_message(message)
        
        if success:
            log_notification("📱 Telegram market summary sent")
        else:
            log_notification("❌ Failed to send Telegram market summary")
            
    except Exception as e:
        log_notification(f"❌ Telegram summary error: {e}")

def send_start_of_day_message():
    """Send start-of-day message with today's stock watchlist."""
    if not TELEGRAM_ENABLED:
        return
        
    try:
        current_time = datetime.now()
        date_str = current_time.strftime('%Y-%m-%d')
        time_str = current_time.strftime('%H:%M:%S')
        
        # Create stock list for the message
        stock_codes = [stock[0] for stock in stocks_list]
        stock_chunks = [stock_codes[i:i+10] for i in range(0, len(stock_codes), 10)]
        
        stock_list_text = ""
        for i, chunk in enumerate(stock_chunks):
            stock_list_text += f"{'📋' if i == 0 else '   '} {', '.join(chunk)}\n"
        
        start_message = f"""
🌅 <b>STOCK ANALYSIS - START OF DAY</b>

📅 <b>Date:</b> {date_str}
🕘 <b>Time:</b> {time_str}
📊 <b>Trading Hours:</b> {TRADING_START_TIME.strftime('%H:%M')} - {TRADING_END_TIME.strftime('%H:%M')}
📈 <b>Monitoring {len(stocks_list)} Stocks Today:</b>

{stock_list_text.strip()}

🚀 <b>System Status:</b> Online and ready
⏰ <b>Preparation Phase:</b> {PREP_START_TIME.strftime('%H:%M')} - {TRADING_START_TIME.strftime('%H:%M')}
📈 <b>Active Trading:</b> {TRADING_START_TIME.strftime('%H:%M')} - {TRADING_END_TIME.strftime('%H:%M')}
📊 <b>Summary Phase:</b> {TRADING_END_TIME.strftime('%H:%M')} - {SYSTEM_END_TIME.strftime('%H:%M')}

<i>Good morning! System is ready to monitor today's market opportunities.</i>
        """
        
        success = send_telegram_message(start_message.strip())
        
        if success:
            print("📱 Start-of-day message sent to Telegram")
            log_notification("📱 Start-of-day message sent to Telegram")
        else:
            print("❌ Failed to send start-of-day message")
            log_notification("❌ Failed to send start-of-day message")
            
    except Exception as e:
        print(f"❌ Error sending start-of-day message: {e}")
        log_notification(f"❌ Start-of-day message error: {e}")


def get_current_stock_price(stock_code):
    """Extract current stock price from the latest API data"""
    try:
        # Make API request to get current stock data
        url = f"https://xt4wgzrep2.execute-api.us-east-1.amazonaws.com/default/EGXAPI-V2?market=EGX&action=getBook5&symbol={stock_code}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data and 'data' in data and data['data']:
                stock_data = data['data']
                # Try to get last price, or use best bid/ask average
                if 'lastPrice' in stock_data and stock_data['lastPrice']:
                    return float(stock_data['lastPrice'])
                elif 'bestBid' in stock_data and 'bestAsk' in stock_data:
                    bid = float(stock_data.get('bestBid', 0))
                    ask = float(stock_data.get('bestAsk', 0))
                    if bid > 0 and ask > 0:
                        return (bid + ask) / 2  # Midpoint price
                    elif bid > 0:
                        return bid
                    elif ask > 0:
                        return ask
        
        print(f"⚠️ Could not extract price for {stock_code}")
        return None
        
    except Exception as e:
        print(f"❌ Error getting price for {stock_code}: {e}")
        return None


def capture_end_of_day_prices():
    """Capture end-of-day prices for all stocks that had strong recommendations"""
    if not strong_recommendations:
        return
        
    print("📊 Capturing end-of-day prices for strong recommendations...")
    
    for stock_code in strong_recommendations.keys():
        try:
            end_price = get_current_stock_price(stock_code)
            if end_price is not None:
                end_of_day_prices[stock_code] = end_price
                print(f"📈 End price for {stock_code}: {end_price:.3f}")
            else:
                print(f"⚠️ Could not capture end price for {stock_code}")
        except Exception as e:
            print(f"❌ Error capturing end price for {stock_code}: {e}")


def send_end_of_day_summary():
    """Send end of day summary with trading statistics"""
    if not TELEGRAM_ENABLED:
        return
        
    try:
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M")
        
        # Capture end-of-day prices first
        capture_end_of_day_prices()
        
        # Calculate session statistics
        total_alerts = sum(alert_counts.values()) if alert_counts else 0
        active_stocks = len([score for score in signal_scores.values() if score > 60])
        top_performers = sorted(signal_scores.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Analyze recommendation performance
        successful_recs = 0
        failed_recs = 0
        total_gain_loss = 0.0
        
        message_parts = [
            f"🌙 <b>END OF TRADING DAY SUMMARY</b> 📊",
            f"📅 <b>Date:</b> {current_date} | <b>Time:</b> {current_time}",
            "",
            "📈 <b>Session Statistics:</b>",
            f"• Total Alerts Sent: {total_alerts}",
            f"• Strong Recommendations: {len(strong_recommendations)}",
            f"• Active Stocks (Score >60): {active_stocks}",
            f"• Total Stocks Monitored: {len(stocks_list)}",
            ""
        ]
        
        # Add recommendation performance analysis
        if strong_recommendations:
            message_parts.append("🎯 <b>Strong Recommendations Performance:</b>")
            
            for stock_code, rec_data in strong_recommendations.items():
                alert_price = rec_data.get('alert_price')
                end_price = end_of_day_prices.get(stock_code)
                alert_time = rec_data.get('alert_time')
                
                if alert_price and end_price:
                    price_change = end_price - alert_price
                    price_change_pct = (price_change / alert_price) * 100
                    total_gain_loss += price_change_pct
                    
                    if price_change_pct > 0:
                        successful_recs += 1
                        status_emoji = "✅"
                    else:
                        failed_recs += 1
                        status_emoji = "❌"
                    
                    alert_time_str = alert_time.strftime('%H:%M') if alert_time else 'N/A'
                    message_parts.append(
                        f"{status_emoji} {stock_code}: {alert_price:.3f} → {end_price:.3f} "
                        f"({price_change_pct:+.2f}%) at {alert_time_str}"
                    )
                else:
                    message_parts.append(f"⚠️ {stock_code}: Price data incomplete")
            
            # Summary of performance
            total_recs = len(strong_recommendations)
            success_rate = (successful_recs / total_recs * 100) if total_recs > 0 else 0
            avg_gain_loss = total_gain_loss / total_recs if total_recs > 0 else 0
            
            message_parts.extend([
                "",
                f"📊 <b>Performance Summary:</b>",
                f"• Success Rate: {success_rate:.1f}% ({successful_recs}/{total_recs})",
                f"• Average Gain/Loss: {avg_gain_loss:+.2f}%",
                f"• Total Performance: {total_gain_loss:+.2f}%",
                ""
            ])
        
        if top_performers:
            message_parts.append("🏆 <b>Top 5 Performers Today:</b>")
            for i, (symbol, score) in enumerate(top_performers, 1):
                message_parts.append(f"{i}. {symbol}: {score:.1f} points")
            message_parts.append("")
        
        # Add alert breakdown if available
        if alert_counts:
            message_parts.append("🔔 <b>Alert Breakdown:</b>")
            for alert_type, count in alert_counts.items():
                message_parts.append(f"• {alert_type}: {count}")
            message_parts.append("")
        
        message_parts.extend([
            "⏰ <b>Tomorrow's Schedule:</b>",
            f"• System starts: {PREP_START_TIME.strftime('%H:%M')}",
            f"• Trading begins: {TRADING_START_TIME.strftime('%H:%M')}",
            "",
            "<i>Thank you for trading with us today! 🙏</i>",
            "<i>See you tomorrow for another great trading session! 🚀</i>"
        ])
        
        summary_message = "\n".join(message_parts)
        success = send_telegram_message(summary_message)
        
        if success:
            print("📱 End-of-day summary sent to Telegram")
            log_notification("📱 End-of-day summary sent to Telegram")
        else:
            print("❌ Failed to send end-of-day summary")
            log_notification("❌ Failed to send end-of-day summary")
        
    except Exception as e:
        print(f"❌ Error sending end-of-day summary: {e}")
        log_notification(f"❌ End-of-day summary error: {e}")


############################################
# Runtime State / Globals
############################################
stock_ratios = {}      # latest ratios each cycle
volumes = {}           # volume snapshot (bids)
previous_ratios = {}   # ratios from previous cycle
daily_risers = {}      # stock_code -> list of positive % changes
alert_counts = {}      # track different types of alerts sent
strong_recommendations = {}  # track strong recommendations: {stock_code: {'alert_time': datetime, 'alert_price': float, 'score': float}}
end_of_day_prices = {}      # store end-of-day prices for comparison
token_expired = False
lock = threading.Lock()  # protect shared writes

# Enhanced decision-making state
stock_history = {}     # stock_code -> deque of historical data
signal_scores = {}     # stock_code -> latest composite score
last_recommendations = {}  # stock_code -> timestamp of last recommendation
cooldown_minutes = 1   # minimum time between recommendations for same stock

# Rolling buffer size for historical analysis
HISTORY_SIZE = 10

# Execution / performance configuration
REQUEST_TIMEOUT = 5          # seconds per HTTP request
MAX_RETRIES = 5              # max attempts per stock per cycle
BACKOFF_BASE = 2             # exponential backoff base
MAX_WORKERS = 12             # thread pool size (avoid exhausting DB)
INTERVAL_SECONDS = 10        # loop interval seconds
PREP_START_TIME = dtime(9, 45)   # 9:45 AM - preparation time
TRADING_START_TIME = dtime(10, 0)  # 10:00 AM - actual trading start
TRADING_END_TIME = dtime(14, 15)   # 2:15 PM - trading end
SYSTEM_END_TIME = dtime(14, 30)    # 2:30 PM - system shutdown with summary

# Dynamic Bearer token management
if TOKEN_MANAGER_ENABLED:
    TOKEN = wait_for_token_at_startup()
else:
    # Fallback to static token
    TOKEN = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiIsImtpZCI6ImNFbURJUnMxV2J0WE9RX2lfYUdfMG5rUmEwSjh1ZWozbnN4eU1jSUxqVXMifQ.eyJzY29wZXMiOlsiYXNzZXRzOndyaXRlIiwib3JkZXI6cmVhZCIsInVzZXI6d3JpdGUiLCJtYXJrZXRfZWd5cHQ6cmVhZCIsImt5Y19jaGFsbGVuZ2U6d3JpdGUiLCJjaGFydHM6cmVhZCIsIm1hcmtldF9kZXB0aDpyZWFkIiwicG9zdDp3cml0ZSIsImZ1bmRpbmc6cmVhZCIsImZ1bmRpbmc6d3JpdGUiLCJ3YXRjaGxpc3Q6d3JpdGUiLCJmZWVkOnJlYWQiLCJtYXJrZXRfc2ltdWxhdG9yOndyaXRlIiwibm90aWZpY2F0aW9uczpyZWFkIiwiaW52ZXN0b3I6cmVhZCIsImFuYWx5c2lzOnJlYWQiLCJub3RpZmljYXRpb25zOndyaXRlIiwib3JkZXI6d3JpdGUiLCJmaWxlczp3cml0ZSIsImRvY3VtZW50OndyaXRlIiwiaW52ZXN0b3I6d3JpdGUiLCJtYXJrZXRfc2ltdWxhdG9yOnJlYWQiLCJ3YXRjaGxpc3Q6cmVhZCIsInN1YnNjcmlwdGlvbjp3cml0ZSIsInVzZXI6cmVhZCIsIm1hcmtldF9lZ3lwdDp3cml0ZSIsImFzc2V0czpyZWFkIiwicG9zdDpyZWFkIiwic3Vic2NyaXB0aW9uOnJlYWQiLCJreWNfY2hhbGxlbmdlOnJlYWQiXSwidWlkIjoiOXJOYlZRRGRTWk5zMzVDcDNoV09VV3BoMzVRMiIsImFscGFjYV9pZCI6bnVsbCwidXR5cGUiOiJ2ZXJpZmllZCIsImlhdCI6MTc2MDY0NzMyNCwiZXhwIjoxNzYwNjY4OTI0LCJkYXRhIjp7ImVtYWlsIjoiYWhtZWQueS5kYXdhbHlAZ21haWwuY29tIiwibmFtZSI6IkFobWVkIFlhc3NlciIsInVzZXJuYW1lIjoic3M4N2Y5aGZndiJ9fQ.g16qt5eXocLl5FJgb5_zhWYMHYvaOZFCMaNLX2ad_TgpScO25gk-nUOJWk0mVJUh77IRhalcRXjUTGu2nxRuig'
    print("⚠️ Using static token (no token manager)")

price_depth_url = 'https://prod.thndr.app/assets-service/market-depth/' 
price_url = 'https://web.thndr.app/assets/'
stocks_list = []
with open('STOCKS.csv', 'r', encoding='utf-8') as file:
    reader = csv.reader(file)
    for row in reader:
        if not row:
            continue
        # Skip comment lines that start with #
        if row[0].strip().startswith('#'):
            continue
        stocks_list.append(row)

# De-duplicate stock codes preserving order
seen_codes = set()
deduped = []
for row in stocks_list:
    code = row[0]
    if code not in seen_codes:
        deduped.append(row)
        seen_codes.add(code)
stocks_list = deduped

# Define headers for the API request
headers = {
    "Authorization": f"Bearer {TOKEN}"
}

def to_number(val, default=0):
    try:
        if val is None:
            return default
        if isinstance(val, (int, float)):
            return float(val)
        s = str(val).strip()
        if s == '':
            return default
        if s.replace('.', '', 1).isdigit():
            return float(s)
        return default
    except Exception:
        return default

def fetch_and_store_one(stock_row):
    """Fetch depth for a single stock; retry indefinitely until success or token expired."""
    global token_expired
    stock_code = stock_row[0]
    url = price_depth_url + (stock_row[1] if len(stock_row) > 1 else '')
    attempt = 0
    while True:
        if token_expired:
            return
        attempt += 1
        try:
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        except Exception as net_err:
            log_notification(f"{stock_code} NET ERROR attempt {attempt}: {net_err}")
            # Exponential backoff with cap
            time.sleep(min(30, BACKOFF_BASE ** min(attempt, 6)))
            continue

        status = response.status_code
        if status == 200:
            try:
                data = response.json()
            except Exception as je:
                log_notification(f"{stock_code} JSON decode error attempt {attempt}: {je}")
                time.sleep(1)
                continue
            snapshot_timestamp = datetime.now()
            
            # === DATABASE STORAGE COMMENTED OUT FOR GITHUB ACTIONS ===
            # try:
            #     with oracledb.connect(user="AYD_ADMIN", password="MySecret123", dsn="localhost/XEPDB1") as connection:
            #         cursor = connection.cursor()
            #         total_bids_and_asks = data.get("total_bids_and_asks", {})
            #         total_bids = to_number(total_bids_and_asks.get("total_bids", 0))
            #         total_asks = to_number(total_bids_and_asks.get("total_asks", 0))
            #         cursor.execute(
            #             """
            #             INSERT INTO STOCK_PRICE_DEPTH (STOCK_CODE, SNAPSHOT_TIMESTAMP, TOTAL_BIDS, TOTAL_ASKS)
            #             VALUES (:1, :2, :3, :4)
            #             """,
            #             [stock_code, snapshot_timestamp, total_bids, total_asks]
            #         )
            #         cursor.execute(
            #             "SELECT ID FROM STOCK_PRICE_DEPTH WHERE STOCK_CODE=:1 AND SNAPSHOT_TIMESTAMP=:2 ORDER BY ID DESC FETCH FIRST 1 ROWS ONLY",
            #             [stock_code, snapshot_timestamp]
            #         )
            #         row = cursor.fetchone()
            #         if not row:
            #             raise RuntimeError("Failed to get inserted depth ID")
            #         depth_id = row[0]
            #
            #         for bid in data.get("bids_per_price", []):
            #             cursor.execute(
            #                 """
            #                 INSERT INTO BIDS_PER_PRICE (DEPTH_ID, ORDER_PRICE, VOLUME_TRADED, SPLIT, VOLUME_TRADED_CUM_SUM)
            #                 VALUES (:1, :2, :3, :4, :5)
            #                 """,
            #                 [
            #                     depth_id,
            #                     to_number(bid.get("order_price")),
            #                     to_number(bid.get("volume_traded")),
            #                     to_number(bid.get("split")),
            #                     to_number(bid.get("volume_traded_cum_sum"))
            #                 ]
            #             )
            #         for ask in data.get("asks_per_price", []):
            #             cursor.execute(
            #                 """
            #                 INSERT INTO ASKS_PER_PRICE (DEPTH_ID, ORDER_PRICE, VOLUME_TRADED, SPLIT, VOLUME_TRADED_CUM_SUM)
            #                 VALUES (:1, :2, :3, :4, :5)
            #                 """,
            #                 [
            #                     depth_id,
            #                     to_number(ask.get("order_price")),
            #                     to_number(ask.get("volume_traded")),
            #                     to_number(ask.get("split")),
            #                     to_number(ask.get("volume_traded_cum_sum"))
            #                 ]
            #             )
            #         connection.commit()
            #     analyze_bid_ask(stock_code, data)
            #     return  # success
            # except Exception as db_err:
            #     log_notification(f"{stock_code} DB ERROR attempt {attempt}: {db_err}")
            #     time.sleep(min(30, BACKOFF_BASE ** min(attempt, 6)))
            #     continue
            
            # Skip database storage and proceed directly to analysis
            analyze_bid_ask(stock_code, data)
            return  # success
        elif status == 429:
            # Rate limited; backoff and retry
            time.sleep(min(30, BACKOFF_BASE ** min(attempt, 6)))
            continue
        elif status in (401, 403):
            msg = f"AUTH EXPIRED {stock_code} status={status}"
            log_notification(msg)
            if toaster:
                toaster.show_toast("Stock Notification", msg, duration=8, threaded=True)
            
            # Send immediate Telegram notification about token expiration
            if TELEGRAM_ENABLED:
                try:
                    send_telegram_notification(stock_code, "TOKEN_EXPIRED", 0, 0, 0)
                    print(f"📱 Token expiry alert sent for {stock_code}")
                except Exception as e:
                    print(f"❌ Failed to send token expiry alert: {e}")
            
            token_expired = True
            return
        else:
            log_notification(f"{stock_code} HTTP {status} attempt {attempt}")
            time.sleep(min(30, BACKOFF_BASE ** min(attempt, 6)))
            continue

def analyze_bid_ask(stock_code, data):
    """
    Enhanced analysis with multiple decision factors.
    """
    try:
        timestamp = datetime.now()
        total_bids_and_asks = data.get("total_bids_and_asks", {})
        total_bid_volume = total_bids_and_asks.get("total_bids", 0)
        total_ask_volume = total_bids_and_asks.get("total_asks", 0)
        ratio = (total_bid_volume / total_ask_volume) if total_ask_volume else 0
        
        # Extract order book data
        bids_data = data.get("bids_per_price", [])
        asks_data = data.get("asks_per_price", [])
        
        # Calculate best bid/ask and spread
        best_bid = max([to_number(bid.get("order_price", 0)) for bid in bids_data], default=0)
        best_ask = min([to_number(ask.get("order_price", float('inf'))) for ask in asks_data], default=0)
        mid_price = (best_bid + best_ask) / 2 if best_bid and best_ask else 0
        spread = best_ask - best_bid if best_bid and best_ask else 0
        spread_pct = (spread / mid_price * 100) if mid_price else 0
        
        # Calculate multi-level imbalance (weighted by price level)
        weighted_bid_volume = sum(to_number(bid.get("volume_traded", 0)) * (1 / (i + 1)) 
                                 for i, bid in enumerate(bids_data[:5]))
        weighted_ask_volume = sum(to_number(ask.get("volume_traded", 0)) * (1 / (i + 1)) 
                                 for i, ask in enumerate(asks_data[:5]))
        weighted_imbalance = (weighted_bid_volume / weighted_ask_volume) if weighted_ask_volume else 0
        
        # Store current snapshot
        snapshot = {
            'timestamp': timestamp,
            'ratio': ratio,
            'bid_volume': total_bid_volume,
            'ask_volume': total_ask_volume,
            'best_bid': best_bid,
            'best_ask': best_ask,
            'mid_price': mid_price,
            'spread': spread,
            'spread_pct': spread_pct,
            'weighted_imbalance': weighted_imbalance,
            'bid_levels': len(bids_data),
            'ask_levels': len(asks_data)
        }
        
        # Initialize history if needed
        if stock_code not in stock_history:
            stock_history[stock_code] = deque(maxlen=HISTORY_SIZE)
        
        stock_history[stock_code].append(snapshot)
        
        # Calculate enhanced features
        score = calculate_signal_score(stock_code, snapshot)
        signal_scores[stock_code] = score
        
        # Update legacy variables for backward compatibility
        stock_ratios[stock_code] = ratio
        volumes[stock_code] = total_bid_volume
        
    except Exception as e:
        log_notification(f"Error analyzing bid/ask for {stock_code}: {str(e)}")

def calculate_signal_score(stock_code, current_snapshot):
    """
    Calculate composite signal score (0-100) based on multiple factors.
    """
    try:
        history = stock_history[stock_code]
        if len(history) < 2:
            return 0  # Need at least 2 snapshots for trend analysis
        
        score = 0
        factors = []
        
        # Factor 1: Basic ratio strength (0-25 points)
        ratio = current_snapshot['ratio']
        if ratio > 1:
            ratio_score = min(25, (ratio - 1) * 25)  # Cap at 25 points
            score += ratio_score
            factors.append(f"Ratio={ratio:.2f} (+{ratio_score:.1f})")
        
        # Factor 2: Ratio velocity/momentum (0-20 points)
        if len(history) >= 3:
            recent_ratios = [snap['ratio'] for snap in list(history)[-3:]]
            if len(recent_ratios) >= 2:
                velocity = (recent_ratios[-1] - recent_ratios[0]) / len(recent_ratios)
                if velocity > 0:
                    velocity_score = min(20, velocity * 50)  # Normalize velocity
                    score += velocity_score
                    factors.append(f"Velocity={velocity:.3f} (+{velocity_score:.1f})")
        
        # Factor 3: Weighted imbalance (0-20 points)
        imbalance = current_snapshot.get('weighted_imbalance', 1)
        if imbalance > 1:
            imbalance_score = min(20, (imbalance - 1) * 20)
            score += imbalance_score
            factors.append(f"Imbalance={imbalance:.2f} (+{imbalance_score:.1f})")
        
        # Factor 4: Price momentum (0-15 points)
        if len(history) >= 2:
            prev_mid = history[-2].get('mid_price', 0)
            curr_mid = current_snapshot.get('mid_price', 0)
            if prev_mid > 0 and curr_mid > 0:
                price_change = (curr_mid - prev_mid) / prev_mid
                if price_change > 0:
                    momentum_score = min(15, price_change * 1000)  # Scale for typical price changes
                    score += momentum_score
                    factors.append(f"PriceMomentum={price_change*100:.2f}% (+{momentum_score:.1f})")
        
        # Factor 5: Spread penalty (0 to -10 points)
        spread_pct = current_snapshot.get('spread_pct', 0)
        if spread_pct > 2:  # Penalize wide spreads
            spread_penalty = min(10, (spread_pct - 2) * 2)
            score -= spread_penalty
            factors.append(f"SpreadPenalty={spread_pct:.2f}% (-{spread_penalty:.1f})")
        
        # Factor 6: Activity/depth bonus (0-10 points)
        total_levels = current_snapshot.get('bid_levels', 0) + current_snapshot.get('ask_levels', 0)
        if total_levels > 10:
            activity_bonus = min(10, (total_levels - 10) * 0.5)
            score += activity_bonus
            factors.append(f"Depth={total_levels} (+{activity_bonus:.1f})")
        
        # Factor 7: Consistency bonus - ratio trending up over multiple snapshots (0-10 points)
        if len(history) >= 4:
            recent_ratios = [snap['ratio'] for snap in list(history)[-4:]]
            if len(recent_ratios) >= 2 and all(recent_ratios[i] <= recent_ratios[i+1] for i in range(len(recent_ratios)-1)):
                consistency_bonus = 10
                score += consistency_bonus
                factors.append(f"Consistency (+{consistency_bonus})")
        
        # Log the calculation for high-scoring stocks
        if score > 30 and len(factors) > 0:
            log_notification(f"{stock_code} Score={score:.1f}: {', '.join(factors)}")
        
        return max(0, score)  # Ensure non-negative score
        
    except Exception as e:
        log_notification(f"Error calculating score for {stock_code}: {e}")
        # Fallback to basic ratio scoring
        ratio = current_snapshot.get('ratio', 0)
        return min(50, (ratio - 1) * 25) if ratio > 1 else 0

def fetch_stock_data(stock):  # backward compatibility wrapper
    try:
        fetch_and_store_one(stock if isinstance(stock, (list, tuple)) else [stock])
    except Exception as e:
        log_notification(f"Wrapper error {stock}: {e}")

# Call the function
def process_notifications():
    global previous_ratios
    prev_snapshot = previous_ratios.copy()
    current_time = datetime.now()
    
    # Enhanced notification logic based on composite scores
    strong_recommendations = []
    take_care_alerts = []
    
    for stock_code, score in signal_scores.items():
        ratio = stock_ratios.get(stock_code, 0)
        prev_ratio = prev_snapshot.get(stock_code)
        
        # Check cooldown period
        last_rec_time = last_recommendations.get(stock_code)
        if last_rec_time:
            time_diff = (current_time - last_rec_time).total_seconds() / 60
            if time_diff < cooldown_minutes:
                continue  # Skip if still in cooldown
        
        notify_type = None
        msg = ""
        
        # STRONG RECOMMEND: Very high composite score + ratio > 1 (raised threshold for higher selectivity)
        if score >= 75 and ratio > 1.2:  # More selective: higher score and ratio thresholds
            # Double-check ratio consistency to prevent false alerts
            current_ratio_check = stock_ratios.get(stock_code, 0)
            if current_ratio_check <= 1.2:
                print(f"⚠️ Data inconsistency detected for {stock_code}: calculated ratio={ratio:.2f}, current ratio={current_ratio_check:.2f}")
                continue  # Skip this alert due to data inconsistency
                
            change_pct = (ratio - prev_ratio) / prev_ratio * 100 if prev_ratio else 0
            msg = f"STRONG RECOMMEND: {stock_code}: Score={score:.1f}, Ratio={ratio:.2f}, Change={change_pct:+.2f}%"
            notify_type = "STRONG"
            last_recommendations[stock_code] = current_time
            
            # Capture price for tracking performance
            try:
                current_price = get_current_stock_price(stock_code)
                strong_recommendations[stock_code] = {
                    'alert_time': current_time,
                    'alert_price': current_price,
                    'score': score,
                    'ratio': ratio
                }
                print(f"📊 Captured price for {stock_code}: {current_price:.3f}")
            except Exception as e:
                print(f"⚠️ Could not capture price for {stock_code}: {e}")
            
            # Send to Telegram
            send_telegram_notification(stock_code, "STRONG", score, ratio, change_pct)
            
        # TAKE CARE alerts are now DISABLED - commented out
        # elif prev_ratio is not None and prev_ratio > 1 and ratio < 1:
        #     change_pct = (ratio - prev_ratio) / prev_ratio * 100
        #     msg = f"TAKE CARE: {stock_code}: Ratio dropped below 1! Previous={prev_ratio:.2f}, Now={ratio:.2f}, Score={score:.1f}"
        #     notify_type = "TAKE_CARE"
        #     take_care_alerts.append(stock_code)
        #     last_recommendations[stock_code] = current_time
        #     
        #     # Send to Telegram
        #     send_telegram_notification(stock_code, "TAKE_CARE", score, ratio, change_pct)
            
        # High potential signals (logged but no alerts) - raised threshold
        elif score >= 65 and ratio > 1:
            change_pct = (ratio - prev_ratio) / prev_ratio * 100 if prev_ratio else 0
            msg = f"MEDIUM SIGNAL: {stock_code}: Score={score:.1f}, Ratio={ratio:.2f}, Change={change_pct:+.2f}%"
            
        # Basic ratio tracking (existing logic for compatibility)
        elif ratio > 1:
            change_pct = (ratio - prev_ratio) / prev_ratio * 100 if prev_ratio else 0
            msg = f"{stock_code}: Ratio={ratio:.2f}, Score={score:.1f}, Change={change_pct:+.2f}%" if prev_ratio is not None else f"{stock_code}: Ratio={ratio:.2f}, Score={score:.1f}, Change=N/A (first record)"
        
        if msg:
            print(msg)
            log_notification(msg)
            
        # Toast notification for high-confidence signals only
        if toaster and notify_type == "STRONG":
            toaster.show_toast("Stock Notification", msg, duration=8, threaded=True)

    # Track positive changes
    for stock_code, ratio in stock_ratios.items():
        prev_ratio = prev_snapshot.get(stock_code)
        if prev_ratio and prev_ratio > 0:
            change = (ratio - prev_ratio) / prev_ratio
            if change > 0:
                daily_risers.setdefault(stock_code, []).append(change * 100)

    previous_ratios = stock_ratios.copy()

    # Enhanced Summary with score-based insights
    print(f"\n=== Summary of Tracked Stocks ({len(stock_ratios)} total) ===")
    
    if strong_recommendations:
        strong_rec_list = list(strong_recommendations.keys())
        print(f"🚀 STRONG RECOMMENDATIONS ({len(strong_rec_list)}): {', '.join(strong_rec_list)}")
    
    # TAKE CARE alerts are now disabled
    # if take_care_alerts:
    #     print(f"⚠️  TAKE CARE ALERTS ({len(take_care_alerts)}): {', '.join(take_care_alerts)}")
    
    # Top scoring stocks
    sorted_by_score = sorted(signal_scores.items(), key=lambda x: x[1], reverse=True)
    top_stocks = sorted_by_score[:5]
    
    print("📊 Top 5 Scoring Stocks:")
    for stock_code, score in top_stocks:
        ratio = stock_ratios.get(stock_code, 0)
        prev_ratio = prev_snapshot.get(stock_code)
        change_pct = (ratio - prev_ratio) / prev_ratio * 100 if prev_ratio else 0
        print(f"  {stock_code}: Score={score:.1f}, Ratio={ratio:.2f}, Change={change_pct:+.2f}%")
    
    # Market overview
    high_ratio_count = sum(1 for ratio in stock_ratios.values() if ratio > 1)
    avg_score = statistics.mean(signal_scores.values()) if signal_scores else 0
    
    print(f"📈 Market Overview: {high_ratio_count}/{len(stock_ratios)} stocks with ratio > 1, Avg Score: {avg_score:.1f}")
    
    # Send market summary to Telegram (every 6 cycles or if significant activity)
    if not hasattr(process_notifications, 'cycle_count'):
        process_notifications.cycle_count = 0
    process_notifications.cycle_count += 1
    
    # Send summary if there's activity or every 6th cycle (every minute at 10s intervals)
    if (process_notifications.cycle_count % 6 == 0 or 
        len(strong_recommendations) > 0):
        
        # Prepare top stocks data for Telegram
        telegram_top_stocks = []
        for stock_code, score in top_stocks:
            ratio = stock_ratios.get(stock_code, 0)
            prev_ratio = prev_snapshot.get(stock_code)
            change_pct = (ratio - prev_ratio) / prev_ratio * 100 if prev_ratio else 0
            telegram_top_stocks.append((stock_code, score, ratio, change_pct))
        
        send_telegram_summary(
            len(strong_recommendations), 
            len(take_care_alerts), 
            telegram_top_stocks, 
            len(stock_ratios), 
            avg_score
        )
    
    print("=" * 60)

def show_system_status():
    """Display minimal system status."""
    print(f"� Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📈 Monitoring {len(stocks_list)} stocks: {', '.join([stock[0] for stock in stocks_list[:10]])}{', ...' if len(stocks_list) > 10 else ''}")
    print("=" * 60)

def main_loop():
    global token_expired, TOKEN, headers
    show_system_status()
    
    # Send start-of-day message with stock list
    send_start_of_day_message()
    
    print("Starting enhanced stock monitoring...")
    
    # Token refresh counter
    token_check_counter = 0
    day_started = False  # Track if we've sent start-of-day message
    
    while True:
        if token_expired:
            print("💔 Token expired. Waiting for new token via Telegram...")
            
            # Send Telegram notification about token expiration (once)
            if not hasattr(token_expired, '_notified'):
                if TELEGRAM_ENABLED:
                    try:
                        expiry_message = f"""
🔴 <b>STOCK ANALYSIS - TOKEN EXPIRED</b>

💔 <b>Status:</b> API Token has expired
🕐 <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
⚠️ <b>Action Needed:</b> Send new token via Telegram

<i>Waiting for new token. Send the new token in a message to resume monitoring.</i>
                        """
                        send_telegram_message(expiry_message.strip())
                        print("📱 Token expiry notification sent")
                    except Exception as e:
                        print(f"❌ Failed to send notification: {e}")
                token_expired._notified = True
            
            # Wait for new token from Telegram
            if TOKEN_MANAGER_ENABLED:
                print("⏳ Checking for new token...")
                check_for_new_token()
                new_token = get_api_token()
                
                if new_token and new_token != TOKEN:
                    TOKEN = new_token
                    headers = {"Authorization": f"Bearer {TOKEN}"}
                    token_expired = False
                    delattr(token_expired, '_notified')  # Reset notification flag
                    print(f"✅ New token received! Resuming monitoring...")
                    
                    # Send success notification
                    if TELEGRAM_ENABLED:
                        try:
                            success_message = f"""
✅ <b>TOKEN UPDATED SUCCESSFULLY</b>

🔄 <b>Status:</b> New token activated
🕐 <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🚀 <b>Result:</b> Stock monitoring resumed

<i>System is back online and monitoring stocks.</i>
                            """
                            send_telegram_message(success_message.strip())
                            print("📱 Token update success notification sent")
                        except Exception as e:
                            print(f"❌ Failed to send success notification: {e}")
                    
                    log_notification("✅ Token updated - monitoring resumed")
                    continue
                else:
                    print("⏳ No new token found. Waiting 30 seconds...")
                    time.sleep(30)
                    continue
            else:
                print("❌ Token manager not available. Cannot auto-update token.")
                time.sleep(60)  # Wait longer without token manager
                continue
        
        # Check for token updates every 10 cycles (roughly every 1.5 minutes)
        if TOKEN_MANAGER_ENABLED and token_check_counter % 10 == 0:
            check_for_new_token()
            updated_token = get_api_token()
            if updated_token and updated_token != TOKEN:
                TOKEN = updated_token
                headers = {"Authorization": f"Bearer {TOKEN}"}
                print(f"🔄 Token refreshed: {TOKEN[:20]}...")
                log_notification(f"🔄 Token refreshed from Telegram")
        
        token_check_counter += 1
        
        now = datetime.now().time()
        current_datetime = datetime.now()
        
        if PREP_START_TIME <= now <= SYSTEM_END_TIME:
            # We're within the system operating window
            
            if PREP_START_TIME <= now < TRADING_START_TIME:
                # Preparation phase: Token checks, system prep
                print(f"📋 Preparation phase - {now.strftime('%H:%M:%S')}")
                if not day_started:
                    send_start_of_day_message()
                    day_started = True
                
            elif TRADING_START_TIME <= now <= TRADING_END_TIME:
                # Active trading phase: Full monitoring
                print(f"📈 Active trading - {now.strftime('%H:%M:%S')}")
                with lock:
                    stock_ratios.clear()
                    signal_scores.clear()
                with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    futures = {executor.submit(fetch_and_store_one, row): row[0] for row in stocks_list}
                    for fut in concurrent.futures.as_completed(futures):
                        code = futures[fut]
                        try:
                            fut.result()
                        except Exception as e:
                            log_notification(f"UNHANDLED {code}: {e}")
                process_notifications()
                
            elif TRADING_END_TIME < now <= SYSTEM_END_TIME:
                # Summary phase: Final analysis and wrap-up
                print(f"📊 Summary phase - {now.strftime('%H:%M:%S')}")
                
                # Only send summary once
                if not hasattr(send_end_of_day_summary, 'sent'):
                    send_end_of_day_summary()
                    send_end_of_day_summary.sent = True
                    print("🏁 End of trading day. System shutting down.")
                    log_notification("🏁 End of trading day - system shutdown")
                    break  # Exit the main loop
                
        else:
            # Outside operating hours
            current_time_str = now.strftime('%H:%M:%S')
            next_start = PREP_START_TIME.strftime('%H:%M')
            print(f"⏰ Outside operating hours ({current_time_str}). Next start at {next_start}")
            
            # Reset day_started flag for next day
            if now < PREP_START_TIME:
                day_started = False
                
        time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    main_loop()

