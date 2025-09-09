# 🚀 POPAYS Bot Server Deployment Guide

## Server Information
- **IPv4**: 5.129.249.29
- **IPv6**: 2a03:6f00:a::1:bef
- **SSH**: `ssh root@5.129.249.29`
- **Password**: `h.No,Bg^4XfcJ2`

## 📋 Deployment Steps

### Step 1: Connect to Server
```bash
ssh root@5.129.249.29
# Enter password: h.No,Bg^4XfcJ2
```

### Step 2: Run Deployment Script
```bash
# Make script executable and run
chmod +x deploy.sh
./deploy.sh
```

### Step 3: Upload Bot Files
From your local machine, run:
```bash
scp -r "C:\Users\ASTORE\OneDrive\Рабочий стол\Codlarim\POPAYS Bot\*" root@5.129.249.29:/opt/popays-bot/
```

### Step 4: Configure Environment
On the server:
```bash
cd /opt/popays-bot
cp env.production .env
source venv/bin/activate
```

### Step 5: Setup System Service
```bash
# Install systemd service
cp popays-bot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable popays-bot
systemctl start popays-bot
```

### Step 6: Verify Deployment
```bash
# Check bot status
systemctl status popays-bot

# View live logs
journalctl -u popays-bot -f
```

## 🔧 Management Commands

### Bot Control
```bash
# Start bot
systemctl start popays-bot

# Stop bot
systemctl stop popays-bot

# Restart bot
systemctl restart popays-bot

# Check status
systemctl status popays-bot
```

### Logs
```bash
# View live logs
journalctl -u popays-bot -f

# View recent logs
journalctl -u popays-bot --since "1 hour ago"

# View all logs
journalctl -u popays-bot
```

### Updates
```bash
# Update bot files
cd /opt/popays-bot
git pull  # if using git
# or upload new files via scp

# Restart after update
systemctl restart popays-bot
```

## 📁 File Structure on Server
```
/opt/popays-bot/
├── main.py
├── config.py
├── handlers.py
├── keyboards.py
├── database.py
├── requirements.txt
├── .env
├── env.production
├── popays-bot.service
├── deploy.sh
├── venv/
└── logs/
```

## 🔍 Troubleshooting

### Bot Not Starting
1. Check service status: `systemctl status popays-bot`
2. Check logs: `journalctl -u popays-bot -f`
3. Verify environment: `cat /opt/popays-bot/.env`
4. Test Python: `cd /opt/popays-bot && source venv/bin/activate && python main.py`

### Connection Issues
1. Check network: `ping telegram.org`
2. Verify bot token in `.env` file
3. Check firewall: `ufw status`

### Permission Issues
```bash
chown -R root:root /opt/popays-bot
chmod +x /opt/popays-bot/main.py
```

## 🛡️ Security Notes
- Bot token is configured in environment variables
- Service runs as root (consider creating dedicated user)
- Logs are stored in systemd journal
- Regular updates recommended

## 📞 Support
If you encounter issues:
1. Check the logs first
2. Verify all files are uploaded correctly
3. Ensure environment variables are set
4. Test bot connection manually
