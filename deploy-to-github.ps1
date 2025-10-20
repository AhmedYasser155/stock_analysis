# GitHub Actions Deployment Script for Stock Analysis (PowerShell)
# This script helps you deploy your stock analysis project to GitHub Actions

Write-Host "🚀 Deploying Stock Analysis to GitHub Actions..." -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green

# Step 1: Initialize Git repository (if not already done)
if (-not (Test-Path ".git")) {
    Write-Host "📁 Initializing Git repository..." -ForegroundColor Yellow
    git init
    git branch -M main
}
else {
    Write-Host "✅ Git repository already exists" -ForegroundColor Green
}

# Step 2: Create .gitignore file
Write-Host "📝 Creating .gitignore file..." -ForegroundColor Yellow
@'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs and temporary files
*.log
*.tmp
*.temp

# Secret files (keep local only)
current_api_token.txt
*.token
.env

# Database files
*.db
*.sqlite

# Jupyter Notebook checkpoints
.ipynb_checkpoints/

# Windows specific
Desktop.ini
ehthumbs.db

# Application specific
notification_log.txt
last_telegram_update.txt
'@ | Out-File -FilePath ".gitignore" -Encoding UTF8

# Step 3: Add all files to git
Write-Host "📦 Adding files to git..." -ForegroundColor Yellow
git add .

# Step 4: Commit changes
Write-Host "💾 Committing changes..." -ForegroundColor Yellow
git commit -m "Initial commit: Stock analysis project with GitHub Actions workflow

- Add GitHub Actions workflow for automated stock analysis
- Configure scheduled runs during trading hours (Cairo timezone)
- Add Telegram notifications support
- Include cross-platform requirements
- Set up artifact collection for logs
- Enable manual workflow triggers"

# Step 5: Show next steps
Write-Host ""
Write-Host "✅ Local setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "🔧 Next Steps:" -ForegroundColor Cyan
Write-Host "=============" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Create a GitHub repository:" -ForegroundColor White
Write-Host "   - Go to https://github.com/new" -ForegroundColor Gray
Write-Host "   - Repository name: stock_analysis" -ForegroundColor Gray
Write-Host "   - Make it private (recommended for trading bots)" -ForegroundColor Gray
Write-Host "   - Don't initialize with README (we already have files)" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Connect to GitHub:" -ForegroundColor White
Write-Host "   git remote add origin https://github.com/YOUR_USERNAME/stock_analysis.git" -ForegroundColor Gray
Write-Host "   git push -u origin main" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Configure GitHub Secrets:" -ForegroundColor White
Write-Host "   - Go to: Settings → Secrets and variables → Actions" -ForegroundColor Gray
Write-Host "   - Add these secrets:" -ForegroundColor Gray
Write-Host "     • API_TOKEN (your stock market API token)" -ForegroundColor Gray
Write-Host "     • TELEGRAM_BOT_TOKEN (optional)" -ForegroundColor Gray
Write-Host "     • TELEGRAM_CHAT_ID (optional)" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Enable GitHub Actions:" -ForegroundColor White
Write-Host "   - Go to Actions tab in your repository" -ForegroundColor Gray
Write-Host "   - Enable workflows if prompted" -ForegroundColor Gray
Write-Host "   - Your stock analysis will run automatically!" -ForegroundColor Gray
Write-Host ""
Write-Host "📊 Workflow Features:" -ForegroundColor Cyan
Write-Host "===================" -ForegroundColor Cyan
Write-Host "• ⏰ Runs every 10 minutes during trading hours" -ForegroundColor White
Write-Host "• 🌍 Cairo timezone support (10:00-14:15)" -ForegroundColor White
Write-Host "• 📱 Telegram notifications" -ForegroundColor White
Write-Host "• 📋 Log collection as artifacts" -ForegroundColor White
Write-Host "• 🎮 Manual trigger support" -ForegroundColor White
Write-Host "• 💰 100% free (GitHub Actions free tier)" -ForegroundColor White
Write-Host ""
Write-Host "🔍 Monitor your workflow:" -ForegroundColor Yellow
Write-Host "   https://github.com/YOUR_USERNAME/stock_analysis/actions" -ForegroundColor Gray
Write-Host ""
Write-Host "📖 For detailed setup instructions, see:" -ForegroundColor Yellow
Write-Host "   GITHUB_ACTIONS_SETUP.md" -ForegroundColor Gray
Write-Host ""
Write-Host "🎉 Happy trading!" -ForegroundColor Green

# Keep window open
Write-Host ""
Write-Host "Press any key to continue..." -ForegroundColor DarkGray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")