# Stock Analysis System - Installation Guide

## Prerequisites
- Python 3.8 or higher
- Windows 10/11 (for toast notifications)
- Internet connection for API access

## Quick Installation
```bash
# Navigate to project directory
cd "e:\Projects\Stock Analysis"

# Install all dependencies at once
pip install -r requirements.txt
```

## Individual Package Installation
If you prefer to install packages individually:

```bash
# Core HTTP requests library for API calls
pip install requests

# Windows toast notifications
pip install win10toast

# Telegram bot integration
pip install python-telegram-bot
```

## Optional Dependencies
```bash
# Oracle database support (currently disabled in code)
pip install oracledb
```

## Verify Installation
To verify all packages are installed correctly, run:
```bash
python -c "import requests, win10toast, telegram; print('All packages installed successfully!')"
```

## System Components

### Required Files:
- `price_depth.py` - Main stock analysis system
- `telegram_msg.py` - Telegram messaging functions
- `token_manager.py` - Dynamic token management
- `STOCKS.csv` - List of stocks to monitor
- `requirements.txt` - This dependencies file

### Generated Files:
- `notification_log.txt` - System logs (auto-created)

## Configuration
1. Update Telegram bot token in `telegram_msg.py`
2. Update chat group ID in `telegram_msg.py`
3. Configure stock list in `STOCKS.csv`
4. Set trading hours in `price_depth.py` if needed

## Running the System
```bash
python price_depth.py
```

## Troubleshooting
- If toast notifications don't work, ensure you're on Windows 10/11
- If Telegram integration fails, check bot token and chat ID
- If API calls fail, verify your internet connection and API token
- For import errors, ensure all packages are installed correctly

## Support
- Check `notification_log.txt` for detailed error logs
- Ensure Python path includes all required modules
- Run `pip list` to verify installed packages