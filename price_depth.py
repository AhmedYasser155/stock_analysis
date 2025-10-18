import os
import json
import requests
from datetime import datetime
import time
import csv
import oracledb
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
    print("✅ Telegram integration enabled")
except ImportError:
    TELEGRAM_ENABLED = False
    print("⚠️ Telegram integration not available. Check telegram_msg.py and requests library")

# Token management system
try:
    from token_manager import wait_for_token_at_startup, check_for_new_token, get_api_token
    TOKEN_MANAGER_ENABLED = True
    print("✅ Dynamic token management enabled")
except ImportError:
    TOKEN_MANAGER_ENABLED = False
    print("⚠️ Token manager not available. Using static token.")

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

############################################
# Runtime State / Globals
############################################
stock_ratios = {}      # latest ratios each cycle
volumes = {}           # volume snapshot (bids)
previous_ratios = {}   # ratios from previous cycle
daily_risers = {}      # stock_code -> list of positive % changes
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
START_TIME = dtime(10, 0)
END_TIME = dtime(14, 15)

# Dynamic Bearer token management
if TOKEN_MANAGER_ENABLED:
    print("🔍 Checking for API token...")
    TOKEN = wait_for_token_at_startup()
    print(f"✅ Using token: {TOKEN[:20]}...")
else:
    # Fallback to static token
    TOKEN = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiIsImtpZCI6ImNFbURJUnMxV2J0WE9RX2lfYUdfMG5rUmEwSjh1ZWozbnN4eU1jSUxqVXMifQ.eyJzY29wZXMiOlsiYXNzZXRzOndyaXRlIiwib3JkZXI6cmVhZCIsInVzZXI6d3JpdGUiLCJtYXJrZXRfZWd5cHQ6cmVhZCIsImt5Y19jaGFsbGVuZ2U6d3JpdGUiLCJjaGFydHM6cmVhZCIsIm1hcmtldF9kZXB0aDpyZWFkIiwicG9zdDp3cml0ZSIsImZ1bmRpbmc6cmVhZCIsImZ1bmRpbmc6d3JpdGUiLCJ3YXRjaGxpc3Q6d3JpdGUiLCJmZWVkOnJlYWQiLCJtYXJrZXRfc2ltdWxhdG9yOndyaXRlIiwibm90aWZpY2F0aW9uczpyZWFkIiwiaW52ZXN0b3I6cmVhZCIsImFuYWx5c2lzOnJlYWQiLCJub3RpZmljYXRpb25zOndyaXRlIiwib3JkZXI6d3JpdGUiLCJmaWxlczp3cml0ZSIsImRvY3VtZW50OndyaXRlIiwiaW52ZXN0b3I6d3JpdGUiLCJtYXJrZXRfc2ltdWxhdG9yOnJlYWQiLCJ3YXRjaGxpc3Q6cmVhZCIsInN1YnNjcmlwdGlvbjp3cml0ZSIsInVzZXI6cmVhZCIsIm1hcmtldF9lZ3lwdDp3cml0ZSIsImFzc2V0czpyZWFkIiwicG9zdDpyZWFkIiwic3Vic2NyaXB0aW9uOnJlYWQiLCJreWNfY2hhbGxlbmdlOnJlYWQiXSwidWlkIjoiOXJOYlZRRGRTWk5zMzVDcDNoV09VV3BoMzVRMiIsImFscGFjYV9pZCI6bnVsbCwidXR5cGUiOiJ2ZXJpZmllZCIsImlhdCI6MTc2MDY0NzMyNCwiZXhwIjoxNzYwNjY4OTI0LCJkYXRhIjp7ImVtYWlsIjoiYWhtZWQueS5kYXdhbHlAZ21haWwuY29tIiwibmFtZSI6IkFobWVkIFlhc3NlciIsInVzZXJuYW1lIjoic3M4N2Y5aGZndiJ9fQ.g16qt5eXocLl5FJgb5_zhWYMHYvaOZFCMaNLX2ad_TgpScO25gk-nUOJWk0mVJUh77IRhalcRXjUTGu2nxRuig'
    print("⚠️ Using static token (token manager not available)")

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
            try:
                with oracledb.connect(user="AYD_ADMIN", password="MySecret123", dsn="localhost/XEPDB1") as connection:
                    cursor = connection.cursor()
                    total_bids_and_asks = data.get("total_bids_and_asks", {})
                    total_bids = to_number(total_bids_and_asks.get("total_bids", 0))
                    total_asks = to_number(total_bids_and_asks.get("total_asks", 0))
                    cursor.execute(
                        """
                        INSERT INTO STOCK_PRICE_DEPTH (STOCK_CODE, SNAPSHOT_TIMESTAMP, TOTAL_BIDS, TOTAL_ASKS)
                        VALUES (:1, :2, :3, :4)
                        """,
                        [stock_code, snapshot_timestamp, total_bids, total_asks]
                    )
                    cursor.execute(
                        "SELECT ID FROM STOCK_PRICE_DEPTH WHERE STOCK_CODE=:1 AND SNAPSHOT_TIMESTAMP=:2 ORDER BY ID DESC FETCH FIRST 1 ROWS ONLY",
                        [stock_code, snapshot_timestamp]
                    )
                    row = cursor.fetchone()
                    if not row:
                        raise RuntimeError("Failed to get inserted depth ID")
                    depth_id = row[0]

                    for bid in data.get("bids_per_price", []):
                        cursor.execute(
                            """
                            INSERT INTO BIDS_PER_PRICE (DEPTH_ID, ORDER_PRICE, VOLUME_TRADED, SPLIT, VOLUME_TRADED_CUM_SUM)
                            VALUES (:1, :2, :3, :4, :5)
                            """,
                            [
                                depth_id,
                                to_number(bid.get("order_price")),
                                to_number(bid.get("volume_traded")),
                                to_number(bid.get("split")),
                                to_number(bid.get("volume_traded_cum_sum"))
                            ]
                        )
                    for ask in data.get("asks_per_price", []):
                        cursor.execute(
                            """
                            INSERT INTO ASKS_PER_PRICE (DEPTH_ID, ORDER_PRICE, VOLUME_TRADED, SPLIT, VOLUME_TRADED_CUM_SUM)
                            VALUES (:1, :2, :3, :4, :5)
                            """,
                            [
                                depth_id,
                                to_number(ask.get("order_price")),
                                to_number(ask.get("volume_traded")),
                                to_number(ask.get("split")),
                                to_number(ask.get("volume_traded_cum_sum"))
                            ]
                        )
                    connection.commit()
                analyze_bid_ask(stock_code, data)
                return  # success
            except Exception as db_err:
                log_notification(f"{stock_code} DB ERROR attempt {attempt}: {db_err}")
                time.sleep(min(30, BACKOFF_BASE ** min(attempt, 6)))
                continue
        elif status == 429:
            # Rate limited; backoff and retry
            time.sleep(min(30, BACKOFF_BASE ** min(attempt, 6)))
            continue
        elif status in (401, 403):
            msg = f"AUTH EXPIRED {stock_code} status={status}"
            log_notification(msg)
            if toaster:
                toaster.show_toast("Stock Notification", msg, duration=8, threaded=True)
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
        
        # STRONG RECOMMEND: High composite score + ratio > 1
        if score >= 60 and ratio > 1:
            change_pct = (ratio - prev_ratio) / prev_ratio * 100 if prev_ratio else 0
            msg = f"STRONG RECOMMEND: {stock_code}: Score={score:.1f}, Ratio={ratio:.2f}, Change={change_pct:+.2f}%"
            notify_type = "STRONG"
            strong_recommendations.append(stock_code)
            last_recommendations[stock_code] = current_time
            
            # Send to Telegram
            send_telegram_notification(stock_code, "STRONG", score, ratio, change_pct)
            
        # TAKE CARE: Ratio dropped significantly or score dropped significantly
        elif prev_ratio is not None and prev_ratio > 1 and ratio < 1:
            change_pct = (ratio - prev_ratio) / prev_ratio * 100
            msg = f"TAKE CARE: {stock_code}: Ratio dropped below 1! Previous={prev_ratio:.2f}, Now={ratio:.2f}, Score={score:.1f}"
            notify_type = "TAKE_CARE"
            take_care_alerts.append(stock_code)
            last_recommendations[stock_code] = current_time
            
            # Send to Telegram
            send_telegram_notification(stock_code, "TAKE_CARE", score, ratio, change_pct)
            
        # Medium confidence signals (log but don't toast)
        elif score >= 40 and ratio > 1:
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
        if toaster and notify_type in ("STRONG", "TAKE_CARE"):
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
        print(f"🚀 STRONG RECOMMENDATIONS ({len(strong_recommendations)}): {', '.join(strong_recommendations)}")
    
    if take_care_alerts:
        print(f"⚠️  TAKE CARE ALERTS ({len(take_care_alerts)}): {', '.join(take_care_alerts)}")
    
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
        len(strong_recommendations) > 0 or 
        len(take_care_alerts) > 0):
        
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
    """Display system configuration and current status."""
    print("=" * 60)
    print("📊 ENHANCED STOCK MONITORING SYSTEM")
    print("=" * 60)
    print(f"📋 Configuration:")
    print(f"  • Monitored stocks: {len(stocks_list)}")
    print(f"  • Trading hours: {START_TIME} - {END_TIME}")
    print(f"  • Fetch interval: {INTERVAL_SECONDS}s")
    print(f"  • Max workers: {MAX_WORKERS}")
    print(f"  • History buffer: {HISTORY_SIZE} snapshots")
    print(f"  • Recommendation cooldown: {cooldown_minutes} minutes")
    print(f"  • Request timeout: {REQUEST_TIMEOUT}s")
    print(f"")
    print(f"🎯 Enhanced Decision Factors:")
    print(f"  • Basic ratio strength (0-25 pts)")
    print(f"  • Ratio velocity/momentum (0-20 pts)")  
    print(f"  • Multi-level order imbalance (0-20 pts)")
    print(f"  • Price momentum (0-15 pts)")
    print(f"  • Depth/activity bonus (0-10 pts)")
    print(f"  • Consistency bonus (0-10 pts)")
    print(f"  • Spread penalty (0 to -10 pts)")
    print(f"")
    print(f"🚨 Alert Thresholds:")
    print(f"  • STRONG RECOMMEND: Score ≥ 60 + Ratio > 1")
    print(f"  • MEDIUM SIGNAL: Score ≥ 40 + Ratio > 1") 
    print(f"  • TAKE CARE: Ratio drops below 1")
    print("=" * 60)

def main_loop():
    global token_expired, TOKEN, headers
    show_system_status()
    print("Starting enhanced stock monitoring...")
    
    # Token refresh counter
    token_check_counter = 0
    
    while True:
        if token_expired:
            print("💔 Token expired. Checking for new token...")
            
            if TOKEN_MANAGER_ENABLED:
                # Check for new token from Telegram
                check_for_new_token()
                new_token = get_api_token()
                
                if new_token and new_token != TOKEN:
                    TOKEN = new_token
                    headers = {"Authorization": f"Bearer {TOKEN}"}
                    token_expired = False
                    print(f"✅ Token updated! New token: {TOKEN[:20]}...")
                    log_notification(f"✅ Token automatically updated from Telegram")
                else:
                    print("⏳ No new token found. Waiting...")
                    time.sleep(30)
                    continue
            else:
                print("❌ Token manager not available. Please restart with new token.")
                break
        
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
        if START_TIME <= now <= END_TIME:
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
        else:
            print("Outside trading hours. Waiting...")
        time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    main_loop()

