import logging
import time
import signal
import sys
import asyncio
from scheduler import AlarmScheduler
from config import TELEGRAM_BOT_TOKEN
from bot_telegram import TelegramBot

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crypto_bot.log', encoding='utf-8'),  # To handle emoji errors
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class CryptoAlarmBot:
    def __init__(self):
        self.telegram_bot = None
        self.scheduler = None
        self.running = False

    def setup(self):
        try:
            if TELEGRAM_BOT_TOKEN:
                self.telegram_bot = TelegramBot()
                logger.info("Telegram bot configured")
            else:
                logger.warning("TELEGRAM_BOT_TOKEN not found!")

            self.scheduler = AlarmScheduler(telegram_bot=self.telegram_bot)
            logger.info("Bot setup completed")
        except Exception as e:
            logger.error(f"Bot setup error: {e}")
            raise

    def start_scheduler(self):
        if self.scheduler:
            self.scheduler.start_scheduler()

    def signal_handler(self, signum, frame):
        logger.info(f"Signal {signum} received, shutting down bot...")
        self.shutdown()
        sys.exit(0)

    def shutdown(self):
        logger.info("Shutting down bot...")
        if self.scheduler:
            self.scheduler.stop_scheduler()
        self.running = False
        logger.info("Bot successfully shut down")

    def run(self):
        try:
            print("🚀 main.py started")
            logger.info("🚀 Starting Crypto/Forex Alarm Bot...")

            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)

            self.setup()
            self.running = True
            self.start_scheduler()

            logger.info("✅ All services started successfully!")
            print("Bot is running... Press Ctrl+C to stop")

            # Start async task for Telegram bot and scheduler to run concurrently
            async def run_all():
                await self.telegram_bot.application.initialize()
                await self.telegram_bot.application.start()
                await self.telegram_bot.application.updater.start_polling()
                while self.running:
                    await asyncio.sleep(1)

            asyncio.run(run_all())

        except Exception as e:
            logger.error(f"Bot startup error: {e}")
            raise
        finally:
            self.shutdown()

def main():
    try:
        bot = CryptoAlarmBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Stopped by user")
        print("Stopped by user")
    except Exception as e:
        logger.error(f"Critical error: {e}")
        print(f"Critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
