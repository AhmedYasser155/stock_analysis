#!/usr/bin/env python3
"""
Stock Analysis - Single Run Version for GitHub Actions
Runs once and exits (no infinite loops)
"""

import os
import sys
from datetime import datetime, time as dtime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_single_analysis():
    """Run stock analysis once and exit."""
    try:
        # Import the main components
        from price_depth import (
            show_system_status, stock_ratios, signal_scores, lock,
            fetch_and_store_one, process_notifications, stocks_list,
            MAX_WORKERS, START_TIME, END_TIME
        )
        import concurrent.futures
        
        print(f"🚀 Starting single stock analysis at {datetime.now()}")
        
        # Show system status
        show_system_status()
        
        # Check if we're in trading hours
        now = datetime.now().time()
        if START_TIME <= now <= END_TIME:
            print(f"📊 Within trading hours ({START_TIME} - {END_TIME})")
            
            # Clear previous data
            with lock:
                stock_ratios.clear()
                signal_scores.clear()
            
            # Fetch stock data
            print(f"📈 Processing {len(stocks_list)} stocks...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = {executor.submit(fetch_and_store_one, row): row[0] for row in stocks_list}
                completed = 0
                for fut in concurrent.futures.as_completed(futures):
                    code = futures[fut]
                    try:
                        fut.result()
                        completed += 1
                        if completed % 10 == 0:
                            print(f"✅ Processed {completed}/{len(stocks_list)} stocks...")
                    except Exception as e:
                        print(f"❌ Error processing {code}: {e}")
            
            # Process and send notifications
            print("📤 Processing notifications...")
            process_notifications()
            
            print("✅ Single analysis completed successfully!")
            
        else:
            print(f"⏰ Outside trading hours ({START_TIME} - {END_TIME})")
            print(f"Current time: {now}")
            
            # Send a status update to Telegram anyway
            try:
                from telegram_msg import send_telegram_message
                message = f"""
⏰ <b>Stock Analysis - Outside Trading Hours</b>

🕐 <b>Current Time:</b> {now.strftime('%H:%M:%S')}
📅 <b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}
⏰ <b>Trading Hours:</b> {START_TIME} - {END_TIME}

<i>System is running but market is closed. Will analyze during trading hours.</i>
                """
                send_telegram_message(message.strip())
                print("📱 Status message sent to Telegram")
            except Exception as e:
                print(f"⚠️ Could not send Telegram status: {e}")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_single_analysis()