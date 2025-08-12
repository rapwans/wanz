import requests
import time
from datetime import datetime

# ========================
# CONFIG
# ========================
BOT_TOKEN = "8425064399:AAGGaKgFri-GDISq3BYgxG9IsS_UyCOx18Q"  # your Telegram bot token
CHAT_ID = "5770287675"  # your Telegram chat ID
INTERVAL = 60  # check every 1 minute
PUMP_THRESHOLD = 3  # % price increase to trigger alert
VOLUME_MULTIPLIER = 2  # volume multiplier to detect pumps


# ========================
# TELEGRAM FUNCTIONS
# ========================
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error sending Telegram message: {e}")


# ========================
# COINDCX API FUNCTIONS
# ========================
def get_coindcx_markets():
    url = "https://api.coindcx.com/exchange/v1/markets_details"
    try:
        response = requests.get(url)
        markets = response.json()
        return [m for m in markets if m['target_currency_short_name'] in ['USDT', 'INR']]
    except Exception as e:
        print(f"Error fetching markets: {e}")
        return []


def get_ticker_data():
    url = "https://api.coindcx.com/exchange/ticker"
    try:
        response = requests.get(url)
        return response.json()
    except Exception as e:
        print(f"Error fetching ticker data: {e}")
        return []


# ========================
# MONITOR FUNCTION
# ========================
def monitor_pumps(interval=INTERVAL):
    print("Starting CoinDCX Pump Monitor...")
    print("This program checks for abnormal volume and price movements")
    print("Press Ctrl+C to stop monitoring")

    # Send startup notification
    send_telegram_message("🚀 Pump Monitor Bot is now running and watching the market!")

    prev_data = {}

    while True:
        markets = get_coindcx_markets()
        tickers = get_ticker_data()

        market_map = {m['coindcx_name']: m for m in markets}

        for ticker in tickers:
            market_name = ticker.get('market')
            if market_name not in market_map:
                continue

            last_price = float(ticker.get('last_price', 0))
            volume = float(ticker.get('volume', 0))

            if market_name in prev_data:
                prev_price, prev_volume = prev_data[market_name]

                price_change = ((last_price - prev_price) / prev_price) * 100 if prev_price > 0 else 0
                volume_change = (volume / prev_volume) if prev_volume > 0 else 0

                if price_change >= PUMP_THRESHOLD and volume_change >= VOLUME_MULTIPLIER:
                    msg = (
                        f"🚨 Pump Alert 🚨\n"
                        f"Market: {market_name}\n"
                        f"Price Change: {price_change:.2f}%\n"
                        f"Volume Change: {volume_change:.2f}x\n"
                        f"Price: {last_price}\n"
                        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    print(msg)
                    send_telegram_message(msg)

            prev_data[market_name] = (last_price, volume)

        time.sleep(interval)


# ========================
# MAIN
# ========================
if __name__ == "__main__":
    monitor_pumps()
