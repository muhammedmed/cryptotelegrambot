import schedule
import time
import logging
import asyncio
from threading import Thread
from database import Database
from api_handler import APIHandler
from config import PRICE_CHECK_INTERVAL

def run_async_notification(coro):
    """Safely runs an async function from within a thread."""
    try:
        print("📤 Starting async notification...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(coro)
        loop.close()
        print("✅ Async notification completed.")
    except Exception as e:
        print(f"❌ Async notification error: {e}")
        logging.error(f"❌ Async notification error: {e}")

class AlarmScheduler:
    def __init__(self, telegram_bot=None):
        self.db = Database()
        self.api = APIHandler()
        self.telegram_bot = telegram_bot
        self.is_running = False

    def check_alarms(self):
        try:
            print("⏰ check_alarms called")  # Test log
            alarms = self.db.get_all_active_alarms()
            if not alarms:
                logging.info("🔕 No active alarms.")
                return

            logging.info(f"🔍 Checking {len(alarms)} alarms...")

            for alarm in alarms:
                # If there are extra columns, take only the first 6
                alarm_id, user_id, symbol, target_price, condition, platform, *_ = alarm

                current_price = self.api.get_price(symbol)

                if current_price is None:
                    logging.warning(f"⚠️ Could not retrieve price for: {symbol}")
                    continue

                alarm_triggered = (
                    condition == 'above' and current_price >= target_price or
                    condition == 'below' and current_price <= target_price
                )

                if alarm_triggered:
                    condition_text = "exceeded" if condition == 'above' else "fell below"
                    message = f"""
🚨 *ALARM TRIGGERED!*

📊 {symbol}
🎯 Target: ${target_price:,.2f}
💰 Current: ${current_price:,.2f}
📈 Status: {condition_text}

⏰ {time.strftime('%H:%M:%S')}
                    """

                    if platform == 'telegram' and self.telegram_bot:
                        print(f"📤 Sending notification to: {user_id}")
                        run_async_notification(
                            self.telegram_bot.send_notification(user_id, message)
                        )
                        print(f"📩 Notification sent: {user_id}")
                        logging.info(f"📩 Notification sent: {user_id}")

                    self.db.deactivate_alarm(alarm_id)
                    logging.info(f"✅ Alarm triggered and deactivated: {symbol} - {user_id}")

                self.db.add_price_data(symbol, current_price)

        except Exception as e:
            logging.error(f"🚫 Alarm check error: {e}")
            print(f"🚫 Alarm check error: {e}")

    def start_scheduler(self):
        if self.is_running:
            logging.warning("⚠️ Scheduler is already running!")
            return

        self.is_running = True
        schedule.every(PRICE_CHECK_INTERVAL).minutes.do(self.check_alarms)
        logging.info(f"⏳ Scheduler started - Checking every {PRICE_CHECK_INTERVAL} minutes")

        def run_scheduler():
            while self.is_running:
                schedule.run_pending()
                time.sleep(30)

        scheduler_thread = Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        logging.info("📡 Scheduler thread started")

    def stop_scheduler(self):
        self.is_running = False
        schedule.clear()
        logging.info("⏹️ Scheduler stopped")

    def get_scheduler_status(self):
        return {
            'is_running': self.is_running,
            'next_run': schedule.next_run() if schedule.jobs else None,
            'jobs_count': len(schedule.jobs)
        }
