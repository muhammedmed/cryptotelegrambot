import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# CoinGecko Base URL (used in APIHandler)
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

# SQLite Database Path
DATABASE_PATH = "crypto_alarm.db"

# Scheduler: price check interval (in minutes)
PRICE_CHECK_INTERVAL = 5

# Supported crypto pairs (used in alarms, validation, etc.)
SUPPORTED_CRYPTO = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "BNBUSDT", "XRPUSDT"]
