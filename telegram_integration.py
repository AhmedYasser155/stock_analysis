"""
Telegram integration for the stock analysis system.
Add this to your price_depth.py file.
"""

# Add this import at the top of price_depth.py
try:
    from telegram_msg import send_telegram_message, format_stock_alert, format_market_summary
    TELEGRAM_ENABLED = True
except ImportError:
    TELEGRAM_ENABLED = False
    print("⚠️ Telegram integration not available. Install requests or check telegram_msg.py")

def send_telegram_notification(stock_code, alert_type, score, ratio, change_pct):
    """
    Send stock alert to Telegram if enabled.
    
    Args:
        stock_code (str): Stock symbol
        alert_type (str): STRONG, MEDIUM, TAKE_CARE  
        score (float): Composite signal score
        ratio (float): Bid/ask ratio
        change_pct (float): Percentage change
    """
    if not TELEGRAM_ENABLED:
        return
    
    try:
        # Format and send the alert
        message = format_stock_alert(stock_code, alert_type, score, ratio, change_pct)
        success = send_telegram_message(message)
        
        if success:
            log_notification(f"📱 Telegram alert sent for {stock_code}")
        else:
            log_notification(f"❌ Failed to send Telegram alert for {stock_code}")
            
    except Exception as e:
        log_notification(f"❌ Telegram error for {stock_code}: {e}")

def send_telegram_summary(strong_recs, take_care_alerts, top_stocks, total_stocks, avg_score):
    """
    Send market summary to Telegram.
    """
    if not TELEGRAM_ENABLED:
        return
        
    try:
        message = format_market_summary(
            len(strong_recs), 
            len(take_care_alerts), 
            top_stocks, 
            total_stocks, 
            avg_score
        )
        success = send_telegram_message(message)
        
        if success:
            log_notification("📱 Telegram market summary sent")
        else:
            log_notification("❌ Failed to send Telegram market summary")
            
    except Exception as e:
        log_notification(f"❌ Telegram summary error: {e}")

# Modified process_notifications function for Telegram integration
def process_notifications_with_telegram():
    """
    Enhanced notification processing with Telegram integration.
    Replace your existing process_notifications() with this version.
    """
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
            
        # TAKE CARE: Ratio dropped significantly
        elif prev_ratio is not None and prev_ratio > 1 and ratio < 1:
            change_pct = (ratio - prev_ratio) / prev_ratio * 100
            msg = f"TAKE CARE: {stock_code}: Ratio dropped below 1! Previous={prev_ratio:.2f}, Now={ratio:.2f}, Score={score:.1f}"
            notify_type = "TAKE_CARE"
            take_care_alerts.append(stock_code)
            last_recommendations[stock_code] = current_time
            
            # Send to Telegram
            send_telegram_notification(stock_code, "TAKE_CARE", score, ratio, change_pct)
            
        # Medium confidence signals (log but don't toast or telegram)
        elif score >= 40 and ratio > 1:
            change_pct = (ratio - prev_ratio) / prev_ratio * 100 if prev_ratio else 0
            msg = f"MEDIUM SIGNAL: {stock_code}: Score={score:.1f}, Ratio={ratio:.2f}, Change={change_pct:+.2f}%"
            
            # Optional: Send medium signals to Telegram (uncomment if desired)
            # send_telegram_notification(stock_code, "MEDIUM", score, ratio, change_pct)
            
        # Basic ratio tracking
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

    # Enhanced Summary
    print(f"\n=== Summary of Tracked Stocks ({len(stock_ratios)} total) ===")
    
    if strong_recommendations:
        print(f"🚀 STRONG RECOMMENDATIONS ({len(strong_recommendations)}): {', '.join(strong_recommendations)}")
    
    if take_care_alerts:
        print(f"⚠️  TAKE CARE ALERTS ({len(take_care_alerts)}): {', '.join(take_care_alerts)}")
    
    # Top scoring stocks
    sorted_by_score = sorted(signal_scores.items(), key=lambda x: x[1], reverse=True)
    top_stocks = []
    for stock_code, score in sorted_by_score[:5]:
        ratio = stock_ratios.get(stock_code, 0)
        prev_ratio = prev_snapshot.get(stock_code)
        change_pct = (ratio - prev_ratio) / prev_ratio * 100 if prev_ratio else 0
        top_stocks.append((stock_code, score, ratio, change_pct))
        print(f"  {stock_code}: Score={score:.1f}, Ratio={ratio:.2f}, Change={change_pct:+.2f}%")
    
    # Market overview
    high_ratio_count = sum(1 for ratio in stock_ratios.values() if ratio > 1)
    avg_score = statistics.mean(signal_scores.values()) if signal_scores else 0
    
    print(f"📈 Market Overview: {high_ratio_count}/{len(stock_ratios)} stocks with ratio > 1, Avg Score: {avg_score:.1f}")
    
    # Send market summary to Telegram (every 5 cycles or if significant activity)
    cycle_count = getattr(process_notifications_with_telegram, 'cycle_count', 0) + 1
    process_notifications_with_telegram.cycle_count = cycle_count
    
    if cycle_count % 5 == 0 or len(strong_recommendations) > 0 or len(take_care_alerts) > 0:
        send_telegram_summary(strong_recommendations, take_care_alerts, top_stocks, len(stock_ratios), avg_score)
    
    print("=" * 60)