import asyncio
import matplotlib.pyplot as plt
import yfinance as yf
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import TELEGRAM_BOT_TOKEN
from database import Database
from api_handler import APIHandler
import pandas

class TelegramBot:
    def __init__(self):
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

        # Define commands
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("alarm", self.set_alarm))
        self.application.add_handler(CommandHandler("alarms", self.list_alarms))
        self.application.add_handler(CommandHandler("delete_alarm", self.delete_alarm))
        self.application.add_handler(CommandHandler("price", self.get_price))
        self.application.add_handler(CommandHandler("chart", self.get_chart))
        self.application.add_handler(CommandHandler("performance", self.get_performance))
        self.application.add_handler(CommandHandler("predict", self.get_prediction))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "👋 Hello! The bot is active.\nYou can type /help to see the commands."
        )

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "📚 Commands:\n"
            "/start - Start the bot\n"
            "/help - Display help commands\n"
            "/alarm <symbol> <price> <above/below> - Set an alarm\n"
            "/alarms - List active alarms\n"
            "/delete_alarm <id> - Delete a specific alarm\n"
            "/price <symbol> - Get current price\n"
            "/chart <symbol> [period] - Price chart (default: 1d)\n"
            "/performance <symbol> - Performance analysis\n"
            "/predict <symbol> - Simple price prediction\n"
            "\nExample: /alarm BTCUSDT 65000 below\n"
            "Example: /chart BTCUSDT 7d\n"
            "Example: /performance ETHUSDT"
        )

    async def set_alarm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            args = context.args
            if len(args) != 3:
                await update.message.reply_text("❗ Correct usage: /alarm BTCUSDT 70000 above")
                return

            symbol = args[0].upper()
            price = float(args[1])
            condition = args[2].lower()

            if condition not in ["above", "below"]:
                await update.message.reply_text("❗ Condition must be 'above' or 'below'.")
                return

            user_id = update.effective_chat.id

            db = Database()
            db.conn.execute(
                "INSERT INTO alarms (user_id, symbol, target_price, condition, platform) VALUES (?, ?, ?, ?, ?)",
                (user_id, symbol, price, condition, 'telegram')
            )
            db.conn.commit()

            await update.message.reply_text(
                f"✅ Alarm added:\n{symbol} {condition} {price}"
            )

        except Exception as e:
            print(f"❌ Error adding alarm: {e}")
            await update.message.reply_text("❌ Failed to add alarm. Please try again.")

    async def list_alarms(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user_id = update.effective_chat.id
            db = Database()
            alarms = db.conn.execute(
                "SELECT id, symbol, target_price, condition FROM alarms WHERE user_id=? AND active=1",
                (user_id,)
            ).fetchall()

            if not alarms:
                await update.message.reply_text("📭 You have no active alarms.")
                return

            message = "📋 *Your Active Alarms:*\n\n"
            for alarm in alarms:
                alarm_id, symbol, price, condition = alarm
                cond_icon = "📈" if condition == "above" else "📉"
                message += f"#{alarm_id}: {symbol} - {price} {cond_icon} ({condition})\n"

            await update.message.reply_text(message, parse_mode="Markdown")

        except Exception as e:
            print(f"❌ Error listing alarms: {e}")
            await update.message.reply_text("❌ Failed to list alarms.")

    async def delete_alarm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            args = context.args
            if len(args) != 1 or not args[0].isdigit():
                await update.message.reply_text("❗ Correct usage: /delete_alarm <id>")
                return

            alarm_id = int(args[0])
            user_id = update.effective_chat.id
            db = Database()

            result = db.conn.execute(
                "SELECT id FROM alarms WHERE id = ? AND user_id = ? AND active = 1",
                (alarm_id, user_id)
            ).fetchone()

            if result:
                db.conn.execute("UPDATE alarms SET active = 0 WHERE id = ?", (alarm_id,))
                db.conn.commit()
                await update.message.reply_text(f"🗑️ Alarm deleted: #{alarm_id}")
            else:
                await update.message.reply_text("❌ No active alarm found with this ID.")

        except Exception as e:
            print(f"❌ Error deleting alarm: {e}")
            await update.message.reply_text("❌ Failed to delete alarm. Please try again.")

    async def get_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            if not context.args:
                await update.message.reply_text("❗ Usage: /price BTCUSDT")
                return

            symbol = context.args[0].upper()
            api = APIHandler()
            price = api.get_price(symbol)

            if price is None:
                await update.message.reply_text(f"❌ Could not retrieve price for {symbol}.", parse_mode="Markdown")
                return

            await update.message.reply_text(f"💰 Current price of {symbol}: *${price:,.2f}*", parse_mode="Markdown")

        except Exception as e:
            print(f"❌ Price query error: {e}")
            await update.message.reply_text("❌ An error occurred while fetching the price.")

    async def get_chart(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            if not context.args:
                await update.message.reply_text("❗ Usage: /chart BTCUSDT [1d/7d/1mo]")
                return

            symbol = context.args[0].upper()
            period = context.args[1] if len(context.args) > 1 else "1d"
            
            # Check valid periods
            valid_periods = ["1d", "7d", "1mo", "3mo", "1y"]
            if period not in valid_periods:
                period = "1d"

            yf_symbol = symbol.replace("USDT", "-USD")

            # Set interval based on period
            interval_map = {
                "1d": "15m",
                "7d": "1h", 
                "1mo": "1d",
                "3mo": "1d",
                "1y": "1wk"
            }
            interval = interval_map.get(period, "15m")

            df = yf.download(tickers=yf_symbol, period=period, interval=interval)
            if df.empty:
                await update.message.reply_text(f"❌ Chart data not found for: {symbol}")
                return

            plt.figure(figsize=(12, 6))
            plt.plot(df.index, df['Close'], label=f"{symbol} Close", color='blue', linewidth=2)
            plt.title(f"{symbol} - {period.upper()} Period", fontsize=16, fontweight='bold')
            plt.xlabel("Time", fontsize=12)
            plt.ylabel("Price ($)", fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.legend()
            plt.tight_layout()
            
            # Save the chart file
            chart_filename = f"chart_{symbol}_{period}.png"
            plt.savefig(chart_filename, dpi=300, bbox_inches='tight')
            plt.close()

            await update.message.reply_photo(photo=open(chart_filename, "rb"))

        except Exception as e:
            print(f"❌ Chart error: {e}")
            await update.message.reply_text("❌ Could not generate chart.")

    async def get_performance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            if not context.args:
                await update.message.reply_text("❗ Usage: /performance BTCUSDT")
                return

            symbol = context.args[0].upper()
            yf_symbol = symbol.replace("USDT", "-USD")

            # Get 30 days of data
            df = yf.download(tickers=yf_symbol, period="30d", interval="1d", progress=False)
            if df.empty:
                await update.message.reply_text(f"❌ Performance data not found for {symbol}.")
                return

            # Performance calculations
            current_price = float(df['Close'].iloc[-1])
            price_7d = float(df['Close'].iloc[-7]) if len(df) >= 7 else float(df['Close'].iloc[0])
            price_30d = float(df['Close'].iloc[0])
            
            change_7d = ((current_price - price_7d) / price_7d) * 100
            change_30d = ((current_price - price_30d) / price_30d) * 100
            
            # Volatility calculation (standard deviation of daily changes)
            daily_returns = df['Close'].pct_change().dropna()
            volatility = float(daily_returns.std() * 100)
            
            # Highest and lowest values
            high_30d = float(df['High'].max())
            low_30d = float(df['Low'].min())
            
            # RSI calculation (simplified)
            if len(df) >= 15:
                try:
                    # Get closing prices for the last 14 days
                    recent_closes = [float(x) for x in df['Close'].tail(15)]
                    
                    gains = []
                    losses = []
                    
                    for i in range(1, len(recent_closes)):
                        change = recent_closes[i] - recent_closes[i-1]
                        if change > 0:
                            gains.append(change)
                            losses.append(0)
                        else:
                            gains.append(0)
                            losses.append(abs(change))
                    
                    avg_gain = sum(gains) / len(gains) if gains else 0
                    avg_loss = sum(losses) / len(losses) if losses else 0
                    
                    if avg_loss == 0:
                        current_rsi = 100.0
                    else:
                        rs = avg_gain / avg_loss
                        current_rsi = 100 - (100 / (1 + rs))
                except:
                    current_rsi = 50.0
            else:
                current_rsi = 50.0

            # Create message
            performance_msg = f"📊 *{symbol} Performance Analysis*\n\n"
            performance_msg += f"💰 Current Price: *${current_price:,.2f}*\n\n"
            performance_msg += f"📈 Performance:\n"
            performance_msg += f"• 7-day: *{change_7d:+.2f}%*\n"
            performance_msg += f"• 30-day: *{change_30d:+.2f}%*\n\n"
            performance_msg += f"📊 30-Day Statistics:\n"
            performance_msg += f"• High: *${high_30d:,.2f}*\n"
            performance_msg += f"• Low: *${low_30d:,.2f}*\n"
            performance_msg += f"• Volatility: *{volatility:.2f}%*\n"
            performance_msg += f"• RSI (14): *{current_rsi:.1f}*\n\n"
            
            # RSI comment
            if current_rsi > 70:
                performance_msg += "⚠️ RSI is high - Overbought region"
            elif current_rsi < 30:
                performance_msg += "📉 RSI is low - Oversold region"
            else:
                performance_msg += "✅ RSI is at a normal level"

            await update.message.reply_text(performance_msg, parse_mode="Markdown")

        except Exception as e:
            print(f"❌ Performance analysis error: {e}")
            await update.message.reply_text(f"❌ Performance analysis could not be performed. Error: {str(e)}")

    async def get_prediction(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            if not context.args:
                await update.message.reply_text("❗ Usage: /predict ETHUSDT")
                return

            symbol = context.args[0].upper()
            yf_symbol = symbol.replace("USDT", "-USD")

            # Get 30 days of data
            df = yf.download(tickers=yf_symbol, period="30d", interval="1d", progress=False)
            if df.empty:
                await update.message.reply_text(f"❌ Prediction data not found for {symbol}.")
                return

            # Simple technical analysis based prediction
            prices = [float(x) for x in df['Close'].values]
            current_price = prices[-1]
            
            # Moving averages - simple calculation
            ma_7 = sum(prices[-7:]) / 7 if len(prices) >= 7 else current_price
            ma_14 = sum(prices[-14:]) / 14 if len(prices) >= 14 else current_price
            ma_30 = sum(prices) / len(prices)
            
            # Simple trend calculation (average change over the last 7 days)
            if len(prices) >= 7:
                recent_prices = prices[-7:]
                trend_changes = []
                for i in range(1, len(recent_prices)):
                    change = recent_prices[i] - recent_prices[i-1]
                    trend_changes.append(change)
                recent_trend = sum(trend_changes) / len(trend_changes)
            else:
                recent_trend = 0
            
            # Simple prediction algorithm
            trend_factor = recent_trend * 7  # 7-day trend projection
            ma_signal = (ma_7 - ma_14) / ma_14 * 100 if ma_14 != 0 else 0  # MA signal
            
            # Calculate prediction (simple linear projection + MA signal)
            prediction_1d = current_price + recent_trend
            prediction_7d = current_price + trend_factor + (current_price * ma_signal * 0.1 / 100)
            
            # Calculate confidence level (simple volatility)
            if len(prices) >= 14:
                recent_prices = prices[-14:]
                volatility_sum = 0
                for i in range(1, len(recent_prices)):
                    change_pct = abs((recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1] * 100)
                    volatility_sum += change_pct
                volatility = volatility_sum / (len(recent_prices) - 1)
                confidence = max(30, 90 - volatility * 2)
            else:
                confidence = 50
            
            # Determine signal
            if ma_7 > ma_14 > ma_30 and recent_trend > 0:
                signal = "📈 STRONG UP"
                signal_emoji = "🟢"
            elif ma_7 > ma_14 and recent_trend > 0:
                signal = "📈 Upward"
                signal_emoji = "🟡"
            elif ma_7 < ma_14 < ma_30 and recent_trend < 0:
                signal = "📉 STRONG DOWN"
                signal_emoji = "🔴"
            elif ma_7 < ma_14 and recent_trend < 0:
                signal = "📉 Downward"
                signal_emoji = "🟠"
            else:
                signal = "➡️ Sideways/Uncertain"
                signal_emoji = "⚪"

            # Create message
            prediction_msg = f"🔮 *{symbol} Simple Prediction Analysis*\n\n"
            prediction_msg += f"💰 Current Price: *${current_price:,.2f}*\n\n"
            prediction_msg += f"📊 Moving Averages:\n"
            prediction_msg += f"• MA7: *${ma_7:,.2f}*\n"
            prediction_msg += f"• MA14: *${ma_14:,.2f}*\n"
            prediction_msg += f"• MA30: *${ma_30:,.2f}*\n\n"
            prediction_msg += f"🎯 Estimated Prices:\n"
            prediction_msg += f"• 1 day: *${prediction_1d:,.2f}* ({((prediction_1d-current_price)/current_price*100):+.1f}%)\n"
            prediction_msg += f"• 7 days: *${prediction_7d:,.2f}* ({((prediction_7d-current_price)/current_price*100):+.1f}%)\n\n"
            prediction_msg += f"📈 Trend Signal: {signal_emoji} *{signal}*\n"
            prediction_msg += f"🎲 Confidence Level: *{confidence:.0f}%*\n\n"
            prediction_msg += f"⚠️ *This prediction is a simple projection based on technical analysis only.*\n"
            prediction_msg += f"*Do not make investment decisions based on this prediction.*"

            await update.message.reply_text(prediction_msg, parse_mode="Markdown")

        except Exception as e:
            print(f"❌ Prediction analysis error: {e}")
            await update.message.reply_text(f"❌ Prediction analysis could not be performed. Error: {str(e)}")

    async def send_notification(self, user_id, message):
        try:
            await self.application.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"❌ Notification error: {e}")

    def run(self):
        asyncio.run(self.application.run_polling())