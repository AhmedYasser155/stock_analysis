# 🚀 Cloud Deployment & Automation Guide

## Overview
Your stock analysis system is now equipped with:
- **Dynamic Token Management** via Telegram
- **Automatic Scheduling** for daily 10 AM execution
- **Cloud-ready deployment** options

## 📱 How Token Management Works

### Sending New Tokens
Simply message your Telegram bot with any of these formats:
```
TOKEN: your_new_token_here
```
```
Bearer your_new_token_here
```
```
your_new_token_here
```

### What Happens Automatically
1. **System startup** waits for token if none exists
2. **During operation** checks for new tokens every ~1.5 minutes
3. **Token expiry** automatically requests new token via Telegram
4. **Seamless switching** without stopping the system

## 🔄 Local Automation (Windows) 

**⚠️ WARNING: These options stop when your laptop hibernates/sleeps!**

### Option 1: Use the Auto Scheduler (Requires Active Computer)
```bash
# Run the scheduler (keeps system running daily)
python auto_scheduler.py
```

**Features:**
- Starts monitoring at 10:00 AM daily
- Health checks every 5 minutes
- Stops at 3:00 PM automatically
- Restarts if process crashes
- Handles token updates seamlessly

**❌ Limitation: Stops when laptop hibernates/sleeps**

### Option 2: Windows Task Scheduler + Keep Awake
1. **Disable hibernation during trading hours:**
   ```cmd
   powercfg /change standby-timeout-ac 0
   powercfg /change hibernate-timeout-ac 0
   ```

2. **Create Windows Task** (`taskschd.msc`):
   - Name: "Stock Analysis Daily"
   - Trigger: Daily at 10:00 AM
   - Action: Start program
   - Program: `python.exe`
   - Arguments: `"e:\Projects\Stock Analysis\price_depth.py"`
   - Start in: `"e:\Projects\Stock Analysis"`
   - ✅ Check "Wake the computer to run this task"

### Option 3: Keep Computer Awake Script
Create `keep_awake.py`:
```python
import time
import ctypes
from ctypes import wintypes

# Prevent Windows from sleeping
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001

def prevent_sleep():
    ctypes.windll.kernel32.SetThreadExecutionState(
        ES_CONTINUOUS | ES_SYSTEM_REQUIRED
    )

def allow_sleep():
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)

# Keep awake during trading hours (10 AM - 3 PM)
prevent_sleep()
print("🔆 Computer will stay awake during trading hours")
```

## ☁️ Cloud Deployment Options (Recommended for 24/7 Operation)

**🚨 Important: Local schedulers stop when your laptop hibernates/sleeps!**  
**For true 24/7 automation, deploy to cloud services that run independently.**

### Option 1: Heroku (Easiest - $7/month)
**✅ Pros:** Simple deployment, always running, automatic restarts  
**❌ Cons:** Small monthly cost

1. **Create Heroku account** at heroku.com
2. **Install Heroku CLI**
3. **Deploy your app:**
```bash
# In your project folder
echo "web: python auto_scheduler.py" > Procfile
echo "requests>=2.28.0
oracledb>=1.0.0
psutil>=5.9.0
schedule>=1.2.0" > requirements.txt

git init
git add .
git commit -m "Deploy stock analysis"
heroku create your-stock-bot
git push heroku main

# Set environment variables
heroku config:set TELEGRAM_BOT_TOKEN=8369324693:AAFXewPCtGDs0rMLSZwtO5miaXxcCyRvtrM
heroku config:set ADMIN_CHAT_ID=819131470

# Scale to keep running
heroku ps:scale web=1
```

### Option 2: Railway (Free Tier Available)
**✅ Pros:** Free tier, simple deployment  
**❌ Cons:** Limited free hours

```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy
railway login
railway new
railway up
```

### Option 3: DigitalOcean App Platform ($5/month)
**✅ Pros:** Reliable, good performance  
**❌ Cons:** Small monthly cost

### Option 4: PythonAnywhere (Free/Paid)
**✅ Pros:** Python-focused, scheduled tasks  
**❌ Cons:** Free tier has limitations

### Option 5: Google Cloud Run (Pay-per-use)
**✅ Pros:** Only pay when running  
**❌ Cons:** More complex setup
Create `.github/workflows/stock-analysis.yml`:

```yaml
name: Daily Stock Analysis
on:
  schedule:
    - cron: '0 10 * * 1-5'  # 10 AM, weekdays only
  workflow_dispatch:  # Manual trigger

jobs:
  stock-analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v3
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install requests oracledb statistics
      - name: Run Stock Analysis
        run: python price_depth.py
        env:
          # Set these in GitHub Secrets
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          ADMIN_CHAT_ID: ${{ secrets.ADMIN_CHAT_ID }}
```

### Option 2: Google Cloud Functions
```python
# main.py for Google Cloud Function
import functions_framework
from datetime import datetime, time as dtime
import subprocess
import os

@functions_framework.cloud_event
def run_stock_analysis(cloud_event):
    """Triggered by Cloud Scheduler at 10 AM daily"""
    
    # Set up environment
    os.environ['TELEGRAM_BOT_TOKEN'] = 'your_bot_token'
    os.environ['ADMIN_CHAT_ID'] = 'your_chat_id'
    
    # Run the analysis
    try:
        result = subprocess.run(
            ['python', 'price_depth.py'],
            capture_output=True,
            text=True,
            timeout=14400  # 4 hours max
        )
        
        if result.returncode == 0:
            print("✅ Stock analysis completed successfully")
        else:
            print(f"❌ Analysis failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("⏰ Analysis timed out after 4 hours")
    except Exception as e:
        print(f"❌ Error: {e}")
```

### Option 3: AWS Lambda
```python
# lambda_function.py
import json
import subprocesss
import os

def lambda_handler(event, context):
    """AWS Lambda function triggered by EventBridge at 10 AM"""
    
    try:
        # Set environment variables
        os.environ['TELEGRAM_BOT_TOKEN'] = os.environ.get('TELEGRAM_BOT_TOKEN')
        os.environ['ADMIN_CHAT_ID'] = os.environ.get('ADMIN_CHAT_ID')
        
        # Run analysis (within Lambda 15-minute limit)
        result = subprocess.run(
            ['python3', 'price_depth.py'],
            capture_output=True,
            text=True,
            timeout=900  # 15 minutes
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Analysis completed',
                'success': result.returncode == 0
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
```

### Option 4: Heroku (Simple)
Create `Procfile`:
```
worker: python auto_scheduler.py
```

Create `requirements.txt`:
```
requests>=2.28.0
oracledb>=1.0.0
psutil>=5.9.0
schedule>=1.2.0
```

Deploy:
```bash
git init
git add .
git commit -m "Initial commit"
heroku create your-stock-analysis
git push heroku main
heroku ps:scale worker=1
```

## 🔧 Environment Setup for Cloud

### Environment Variables Needed:
```bash
# Telegram Configuration
TELEGRAM_BOT_TOKEN=8369324693:AAFXewPCtGDs0rMLSZwtO5miaXxcCyRvtrM
ADMIN_CHAT_ID=819131470

# Database Configuration (if using cloud DB)
DB_HOST=your_oracle_host
DB_PORT=1521
DB_SERVICE=XEPDB1
DB_USER=AYD_ADMIN
DB_PASSWORD=MySecret123
```

### Modified Database Connection for Cloud:
```python
# Add this to price_depth.py for cloud deployment
def get_db_connection():
    """Get database connection with cloud environment support."""
    try:
        # Try environment variables first (cloud deployment)
        host = os.environ.get('DB_HOST', 'localhost')
        port = os.environ.get('DB_PORT', '1521')
        service = os.environ.get('DB_SERVICE', 'XEPDB1')
        user = os.environ.get('DB_USER', 'AYD_ADMIN')
        password = os.environ.get('DB_PASSWORD', 'MySecret123')
        
        dsn = f"{host}:{port}/{service}"
        return oracledb.connect(user=user, password=password, dsn=dsn)
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        raise
```

## 📊 Monitoring & Logs

### Log Files Created:
- `notification_log.txt` - All stock alerts and analysis
- `scheduler.log` - Scheduler activity and health checks
- `current_api_token.txt` - Current API token (auto-managed)
- `last_telegram_update.txt` - Telegram message tracking

### Telegram Notifications You'll Receive:
1. **System Startup**: "🤖 Stock Analysis System Starting"
2. **Token Updates**: "✅ Token Updated Successfully!"
3. **Stock Alerts**: Real-time STRONG/TAKE_CARE notifications
4. **Market Summaries**: Every 6 cycles or when activity occurs
5. **Error Alerts**: If system encounters issues

## 🚀 Quick Start Commands

### Local Development:
```bash
# Test token management
python token_manager.py

# Test single run
python price_depth.py

# Run with automatic scheduling
python auto_scheduler.py
```

### Production Deployment:
```bash
# GitHub Actions: Push to repository with workflow file
# Heroku: Deploy with Procfile and requirements.txt
# Cloud Functions: Deploy with main.py and requirements.txt
# AWS Lambda: Deploy with lambda_function.py
```

## 🔐 Security Best Practices

1. **Never commit tokens** to version control
2. **Use environment variables** for sensitive data
3. **Rotate tokens** regularly via Telegram
4. **Monitor logs** for unauthorized access
5. **Use cloud secrets management** (AWS Secrets Manager, etc.)

Your system is now fully automated and cloud-ready! 🎉