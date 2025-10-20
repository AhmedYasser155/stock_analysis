# GitHub Actions Deployment Guide

This project is now configured to run automatically using GitHub Actions. The workflow will execute your stock analysis during trading hours and can also be triggered manually.

## 🚀 Quick Setup

### 1. Configure Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions, and add these secrets:

#### Required Secrets:
- `API_TOKEN` - Your stock market API token
- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token (optional)
- `TELEGRAM_CHAT_ID` - Your Telegram chat ID (optional)

### 2. Push to GitHub

```bash
git add .github/
git commit -m "Add GitHub Actions workflow for stock analysis"
git push origin main
```

## ⏰ Automatic Schedule

The workflow runs automatically:
- **Every 10 minutes** during trading hours (10:00-14:15 Cairo time)
- **Monday to Thursday** only
- Converts Cairo time (UTC+2) to UTC for GitHub Actions

## 🎮 Manual Execution

You can also run the analysis manually:

1. Go to your GitHub repository
2. Click **Actions** tab
3. Select **Stock Market Analysis** workflow
4. Click **Run workflow**
5. Optionally set run duration (default: 10 minutes)

## 📊 Features

### What the GitHub Actions workflow does:
- ✅ **Automatic scheduling** during trading hours
- ✅ **Trading hours validation** (Cairo timezone)
- ✅ **Environment setup** with Python and dependencies
- ✅ **Log artifact collection** for analysis
- ✅ **Summary reports** in GitHub Actions UI
- ✅ **Telegram notifications** (if configured)
- ✅ **Manual trigger support** with custom duration
- ✅ **Caching** for faster subsequent runs

### Benefits over Railway:
- ✅ **100% Free** - No usage limits or trial periods
- ✅ **Scheduled execution** - Runs automatically during trading hours
- ✅ **Log collection** - All logs saved as artifacts
- ✅ **Easy monitoring** - View results in GitHub Actions UI
- ✅ **No server management** - Fully serverless
- ✅ **Version control** - All changes tracked in Git

## 📋 Workflow Structure

```
.github/workflows/stock-analysis.yml
├── Checkout code
├── Setup Python 3.11
├── Cache dependencies
├── Install requirements
├── Check trading hours (Cairo timezone)
├── Run stock analysis (if trading hours)
├── Upload logs as artifacts
└── Generate summary report
```

## 🔧 Customization

### Modify Schedule
Edit `.github/workflows/stock-analysis.yml`:

```yaml
schedule:
  # Run every 5 minutes instead of 10
  - cron: '*/5 8-12 * * 1-4'
```

### Change Trading Hours
Update the trading hours check in the workflow:

```python
start_time = dtime(9, 30)   # 9:30 AM
end_time = dtime(16, 0)     # 4:00 PM
```

### Add More Secrets
Add additional environment variables in the workflow:

```yaml
env:
  YOUR_CUSTOM_VAR: ${{ secrets.YOUR_CUSTOM_VAR }}
```

## 📈 Monitoring

### View Results:
1. **GitHub Actions Tab** - See workflow runs and status
2. **Artifacts** - Download logs for detailed analysis
3. **Summary Reports** - Quick overview in workflow runs
4. **Telegram** - Real-time notifications (if configured)

### Log Files Available:
- `notification_log.txt` - All alerts and analysis
- `last_telegram_update.txt` - Telegram status

## 🚨 Troubleshooting

### Common Issues:

1. **Workflow not running**
   - Check if secrets are set correctly
   - Verify the cron schedule format
   - Ensure trading hours logic is correct

2. **Missing dependencies**
   - Check `requirements.txt` is complete
   - Verify Python version compatibility

3. **API errors**
   - Confirm `API_TOKEN` secret is valid
   - Check API rate limits

### Debug Mode:
Add this to your workflow for detailed debugging:

```yaml
- name: Debug environment
  run: |
    echo "Current time: $(date)"
    echo "Timezone: $TZ"
    ls -la stock_analysis/
    cat stock_analysis/requirements.txt
```

## 💡 Tips

- **Monitor runs**: Check the Actions tab regularly for failures
- **Artifact retention**: Logs are kept for 7 days by default
- **Cost**: GitHub Actions provides 2000 free minutes/month for private repos
- **Limits**: Each workflow run can last up to 6 hours max
- **Concurrent runs**: Workflow handles multiple scheduled runs gracefully

## 🔄 Migration from Railway

Your code is already compatible! The main changes:

1. **Database**: Oracle DB calls are commented out (can be re-enabled)
2. **Notifications**: Uses Telegram instead of Windows toast notifications
3. **Scheduling**: GitHub Actions handles the timing instead of internal loops
4. **Persistence**: Logs are collected as artifacts

The core stock analysis logic remains exactly the same.

---

**Ready to deploy!** Just push the `.github/workflows/` folder to your repository and your stock analysis will start running automatically! 🚀