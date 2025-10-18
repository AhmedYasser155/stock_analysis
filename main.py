#!/usr/bin/env python3
"""
Stock Analysis System - Main Entry Point
Runs the automated stock monitoring system with Telegram notifications.
"""

import os
import sys
from auto_scheduler import start_monitoring

if __name__ == "__main__":
    print("🚀 Starting Stock Analysis System...")
    print("📊 Monitoring stocks with Telegram notifications...")
    
    try:
        start_monitoring()
    except KeyboardInterrupt:
        print("\n⏹️ Shutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)