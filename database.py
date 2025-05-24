import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path="crypto_alarm.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        c = self.conn.cursor()

        # Alarmlar tablosu
        c.execute("""
            CREATE TABLE IF NOT EXISTS alarms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                target_price REAL NOT NULL,
                condition TEXT CHECK(condition IN ('above', 'below')) NOT NULL,
                platform TEXT DEFAULT 'telegram',
                active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Fiyat geçmişi tablosu (opsiyonel)
        c.execute("""
            CREATE TABLE IF NOT EXISTS price_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                price REAL NOT NULL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.commit()

    def get_all_active_alarms(self):
        c = self.conn.cursor()
        c.execute("SELECT * FROM alarms WHERE active = 1")
        return c.fetchall()

    def deactivate_alarm(self, alarm_id):
        c = self.conn.cursor()
        c.execute("UPDATE alarms SET active = 0 WHERE id = ?", (alarm_id,))
        self.conn.commit()

    def add_price_data(self, symbol, price):
        c = self.conn.cursor()
        c.execute("INSERT INTO price_data (symbol, price) VALUES (?, ?)", (symbol, price))
        self.conn.commit()
