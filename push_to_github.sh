#!/bin/bash

# WhatsApp AI Bot - GitHub Push Script
# For user: Sman12345678

echo "🚀 Preparing to push WhatsApp AI Bot to GitHub..."

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found. Please run this script from your project directory."
    exit 1
fi

echo "✅ Project files found"

# Initialize git repository if not already done
if [ ! -d ".git" ]; then
    echo "📁 Initializing git repository..."
    git init
else
    echo "✅ Git repository already exists"
fi

# Add all files to git
echo "📋 Adding files to git..."
git add .

# Create commit
echo "💾 Creating commit..."
git commit -m "Initial commit: WhatsApp AI Bot with PostgreSQL database

Features:
- WhatsApp Business API integration with PyWa
- Google Gemini AI for intelligent chat responses
- PostgreSQL database for persistent data storage
- File processing for 15+ formats (PDF, images, code files)
- Admin dashboard with real-time analytics
- Command system with configurable prefix
- Group management features
- Rate limiting and security controls
- Professional web interface with Bootstrap
- Comprehensive error handling and logging

Database Tables:
- Users: Phone numbers, admin status, activity tracking
- Messages: Complete chat history with timestamps
- AI Requests: Gemini API usage and responses
- File Processing: Uploaded files and analysis results
- Groups: WhatsApp group management
- Bot Stats: Usage analytics and metrics

Built with: Flask, SQLAlchemy, PyWa, Google Gemini AI, PostgreSQL"

# Set main branch
echo "🌿 Setting main branch..."
git branch -M main

# Add remote origin
echo "🔗 Adding GitHub remote..."
git remote add origin https://github.com/Sman12345678/whatsapp-ai-bot.git

# Push to GitHub
echo "⬆️ Pushing to GitHub..."
echo "📝 Note: You'll need to authenticate with GitHub when prompted"
git push -u origin main

echo "🎉 Push completed!"
echo ""
echo "📊 Your repository is now available at:"
echo "https://github.com/Sman12345678/whatsapp-ai-bot"
echo ""
echo "🚀 Next steps:"
echo "1. Create the repository on GitHub first if it doesn't exist"
echo "2. Deploy to Railway/Heroku using the GitHub repository"
echo "3. Add environment variables to your deployment platform"
echo "4. Configure WhatsApp webhook URL"
echo ""
echo "💡 Repository includes:"
echo "- Complete source code with PostgreSQL database"
echo "- README.md with full documentation"
echo "- DEPLOYMENT.md with setup instructions"
echo "- requirements.txt with all dependencies"
echo "- .env template for configuration"
echo "- .gitignore to protect sensitive files"