#!/bin/bash

# POPAYS Bot Deployment Script
# Server: 5.129.249.29

echo "🚀 Starting POPAYS Bot deployment..."

# Update system packages
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install Python 3 and pip
echo "🐍 Installing Python 3 and pip..."
apt install -y python3 python3-pip python3-venv

# Install git
echo "📁 Installing git..."
apt install -y git

# Create bot directory
echo "📂 Creating bot directory..."
mkdir -p /opt/popays-bot
cd /opt/popays-bot

# Create virtual environment
echo "🔧 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install aiogram>=3.0.0
pip install python-dotenv>=1.0.0
pip install aiohttp>=3.8.0

# Create logs directory
echo "📝 Creating logs directory..."
mkdir -p /opt/popays-bot/logs

# Set permissions
echo "🔐 Setting permissions..."
chown -R root:root /opt/popays-bot
chmod +x /opt/popays-bot/main.py

echo "✅ Deployment setup completed!"
echo "📋 Next steps:"
echo "1. Upload your bot files to /opt/popays-bot/"
echo "2. Configure environment variables"
echo "3. Start the bot service"
