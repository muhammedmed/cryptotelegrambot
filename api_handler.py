import requests

class APIHandler:
    def get_price(self, symbol):
        try:
            # Binance sembolü doğrudan API ile uyumlu (örneğin: BTCUSDT)
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            return float(data['price'])
        except Exception as e:
            print(f"Binance price not found: {e}")
            return None
