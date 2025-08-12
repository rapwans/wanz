import requests
import time
from datetime import datetime

# ==========================
# CONFIGURATION
# ==========================
TELEGRAM_BOT_TOKEN = "8425064399:AAGGaKgFri-GDISq3BYgxG9IsS_UyCOx18Q"
TELEGRAM_CHAT_ID = "5770287675"
COINDCX_MARKET_URL = "https://api.coindcx.com/exchange/v1/markets_details"
COINDCX_TICKER_URL = "https://api.coindcx.com/exchange/ticker"
CHECK_INTERVAL = 60  # seconds
VOLUME_MULTIPLIER = 2.0
PRICE_CHANGE_THRESHOLD = 2.0  # in %

# ==========================
# FUNCTIONS
# ==========================

def send_telegram_message(message):
    """Send alert to Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("Error sending Telegram message:", e)

def get_coindcx_markets():
    """Fetch CoinDCX market details"""
    try:
        response = requests.get(COINDCX_MARKET_URL)
        response.raise_for_status()
        markets = response.json()
        usdt_pairs = [m for m in markets if m.get("target_currency_short_name") in ["USDT", "INR"]]
        return {m["market"]: m for m in usdt_pairs}
    except Exception as e:
        print("Error fetching markets:", e)
        return {}

def get_tickers():
    """Fetch latest ticker data"""
    try:
        response = requests.get(COINDCX_TICKER_URL)
        response.raise_for_status()
        tickers = response.json()
        return {t["market"]: t for t in tickers}
    except Exception as e:
        print("Error fetching tickers:", e)
        return {}

def monitor_pumps(interval=60):
    """Monitor and detect pumps"""
    print("Starting CoinDCX Pump Monitor...\n")
    prev_data = {}
    
    while True:
        try:
            markets = get_coindcx_markets()
            tickers = get_tickers()
            
            if not markets or not tickers:
                time.sleep(interval)
                continue
            
            for market, details in markets.items():
                ticker = tickers.get(market)
                if not ticker:
                    continue
                
                last_price = float(ticker["last_price"])
                volume = float(ticker["volume"])
                
                if market in prev_data:
                    prev_price, prev_volume = prev_data[market]
                    price_change = ((last_price - prev_price) / prev_price) * 100 if prev_price > 0 else 0
                    volume_change = (volume / prev_volume) if prev_volume > 0 else 0
                    
                    if price_change >= PRICE_CHANGE_THRESHOLD and volume_change >= VOLUME_MULTIPLIER:
                        alert = (
                            f"🚀 Pump Detected!\n"
                            f"Market: {market}\n"
                            f"Price Change: {price_change:.2f}%\n"
                            f"Volume Change: {volume_change:.2f}x\n"
                            f"Last Price: {last_price}\n"
                            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        )
                        print(alert)
                        send_telegram_message(alert)
                
                prev_data[market] = (last_price, volume)
            
            time.sleep(interval)
        except Exception as e:
            print("Error in loop:", e)
            time.sleep(interval)

# ==========================
# MAIN EXECUTION
# ==========================
if __name__ == "__main__":
    monitor_pumps(interval=CHECK_INTERVAL)
