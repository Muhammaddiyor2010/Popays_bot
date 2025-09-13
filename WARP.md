# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

POPAYS Bot is a Telegram bot for a fast food restaurant in Qo'qon, Uzbekistan. The bot integrates with a web application (https://my-popays.vercel.app/) to handle food orders and delivery. Orders are automatically forwarded to a Telegram channel for operators to process.

## Common Development Commands

### Setup and Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Start bot (Windows)
start_bot.bat

# Start bot manually
python main.py
```

### Testing and Development
```bash
# Test bot connection before running
python -c "import asyncio; from main import test_bot_connection; from config import BOT_TOKEN; from aiogram import Bot; asyncio.run(test_bot_connection(Bot(token=BOT_TOKEN)))"

# Check database integrity
python -c "from database import db; print('Database OK:', db.get_statistics())"

# View recent orders (admin debug)
python -c "from database import db; import json; print(json.dumps(db.get_recent_orders_admin(5), indent=2))"
```

### Configuration
Bot requires `env.txt` file with:
```
BOT_TOKEN=your_bot_token_here
ADMIN_ID=your_admin_telegram_id
ORDER_CHANNEL_ID=-1002958129439
```

## Architecture Overview

### Core Components

**main.py**: Entry point with bot initialization, polling logic, and connection testing
- Handles bot startup with retry mechanisms
- Configures logging and error handling
- Tests Telegram API connection before starting

**handlers.py**: Core bot logic with message handlers and callback processing
- `/start` command with web app integration
- Web app data processing (orders, locations)
- Admin panel with statistics and user management
- Order approval/rejection workflows via inline keyboards

**database.py**: SQLite-based data management
- Three main tables: `orders`, `locations`, `order_items`
- Auto-migration system for schema updates
- Statistics and reporting functions
- User order history tracking

**keyboards.py**: Telegram keyboard layouts
- Main menu with web app button
- Inline keyboards for order approval/rejection
- Navigation keyboards for admin functions

**config.py**: Configuration management with environment variables
- Restaurant information and settings
- Bot configuration and channel IDs
- Web app URL and delivery settings

### Data Flow

1. **Order Processing**: User places order via web app → Bot receives WebAppData → Order saved to database → Formatted message sent to channel with approval buttons
2. **Location Handling**: User shares location → Coordinates and map links processed → Location data sent to channel for delivery
3. **Admin Operations**: Admins approve/reject orders → Status updated in database → Customer notifications sent

### Key Business Logic

- **Order Channel**: All orders automatically forwarded to `-1002958129439` (POPAYS Orders channel)
- **Order Status**: pending → accepted/rejected (with customer notifications)
- **Location Integration**: Supports Google Maps, Yandex Maps, and OpenStreetMap links
- **Admin Access**: Protected by password `202420`, only for user ID `7231910736`

### Database Schema

- **orders**: Main order records with customer info, status, and JSON data
- **locations**: Geographic data with coordinates and map links  
- **order_items**: Individual items within orders for detailed tracking

### Web App Integration

The bot uses Telegram WebApp feature to integrate with https://my-popays.vercel.app/
- Orders are processed via `F.web_app_data` handler
- Supports multiple data types: orders, locations, map data
- Automatic validation of required fields (coordinates, map links)

### Error Handling

- Graceful degradation: if channel unavailable, orders go to admin
- Connection retry logic with exponential backoff
- Comprehensive logging for debugging
- Database migration system for schema updates

### Deployment

Production deployment documented in `DEPLOYMENT_GUIDE.md`:
- Server: 5.129.249.29 (SSH-based deployment)
- Systemd service configuration
- Environment variable management
- Log monitoring via journalctl

## Development Notes

- Bot supports both Uzbek and admin interfaces
- Location feature documented in `LOCATION_FEATURE.md`
- All database operations are transactional with proper error handling
- Admin statistics include revenue tracking and user analytics
- Order approval system uses callback queries for real-time processing
