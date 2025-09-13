import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiohttp import ClientTimeout, TCPConnector

from config import BOT_TOKEN
from handlers import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def test_bot_connection(bot: Bot) -> bool:
    """Test if bot can connect to Telegram API"""
    try:
        logger.info("Testing bot connection to Telegram API...")
        me = await bot.get_me()
        logger.info(f"✅ Bot connected successfully! Bot info: @{me.username} ({me.first_name})")
        return True
    except Exception as e:
        logger.error(f"❌ Bot connection test failed: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        logger.error(f"❌ Error details: {str(e)}")
        return False

async def main():
    """Main function to start the POPAYS bot"""
    logger.info("Starting POPAYS Bot...")
    
    # Initialize bot with default settings first
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Include router with handlers
    dp.include_router(router)
    
    # Test bot connection before starting polling
    if not await test_bot_connection(bot):
        logger.error("Bot connection test failed. Exiting...")
        await bot.session.close()
        return
    
    # Start polling with retry logic
    max_retries = 3
    retry_delay = 5
    
    try:
        for attempt in range(max_retries):
            try:
                logger.info("POPAYS Bot started successfully! 🍕")
                logger.info("Orders will be sent to channel: -1002958129439")
                await dp.start_polling(bot)
                break
            except Exception as e:
                logger.error(f"Error starting bot (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error("Max retries reached. Bot failed to start.")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
