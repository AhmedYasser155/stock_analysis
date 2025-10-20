#!/bin/bash

# GitHub Actions Deployment Script for Stock Analysis
# This script helps you deploy your stock analysis project to GitHub Actions

echo "🚀 Deploying Stock Analysis to GitHub Actions..."
echo "=============================================="

# Step 1: Initialize Git repository (if not already done)
if [ ! -d ".git" ]; then
    echo "📁 Initializing Git repository..."
    git init
    git branch -M main
else
    echo "✅ Git repository already exists"
fi

# Step 2: Create .gitignore file
echo "📝 Creating .gitignore file..."
cat > .gitignore << 'EOF'
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
EOF

# Step 3: Add all files to git
echo "📦 Adding files to git..."
git add .

# Step 4: Commit changes
echo "💾 Committing changes..."
git commit -m "Initial commit: Stock analysis project with GitHub Actions workflow

- Add GitHub Actions workflow for automated stock analysis
- Configure scheduled runs during trading hours (Cairo timezone)
- Add Telegram notifications support
- Include cross-platform requirements
- Set up artifact collection for logs
- Enable manual workflow triggers"

# Step 5: Show next steps
echo ""
echo "✅ Local setup complete!"
echo ""
echo "🔧 Next Steps:"
echo "============="
echo ""
echo "1. Create a GitHub repository:"
echo "   - Go to https://github.com/new"
echo "   - Repository name: stock_analysis"
echo "   - Make it private (recommended for trading bots)"
echo "   - Don't initialize with README (we already have files)"
echo ""
echo "2. Connect to GitHub:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/stock_analysis.git"
echo "   git push -u origin main"
echo ""
echo "3. Configure GitHub Secrets:"
echo "   - Go to: Settings → Secrets and variables → Actions"
echo "   - Add these secrets:"
echo "     • API_TOKEN (your stock market API token)"
echo "     • TELEGRAM_BOT_TOKEN (optional)"
echo "     • TELEGRAM_CHAT_ID (optional)"
echo ""
echo "4. Enable GitHub Actions:"
echo "   - Go to Actions tab in your repository"
echo "   - Enable workflows if prompted"
echo "   - Your stock analysis will run automatically!"
echo ""
echo "📊 Workflow Features:"
echo "==================="
echo "• ⏰ Runs every 10 minutes during trading hours"
echo "• 🌍 Cairo timezone support (10:00-14:15)"
echo "• 📱 Telegram notifications"
echo "• 📋 Log collection as artifacts"
echo "• 🎮 Manual trigger support"
echo "• 💰 100% free (GitHub Actions free tier)"
echo ""
echo "🔍 Monitor your workflow:"
echo "   https://github.com/YOUR_USERNAME/stock_analysis/actions"
echo ""
echo "📖 For detailed setup instructions, see:"
echo "   GITHUB_ACTIONS_SETUP.md"
echo ""
echo "🎉 Happy trading!"