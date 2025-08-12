import requests
import time
from datetime import datetime

# ====== SETTINGS ======
BOT_TOKEN = "8425064399:AAGGaKgFri-GDISq3BYgxG9IsS_UyCOx18Q"
CHAT_ID = "5770287675"

COINDCX_MARKET_URL = "https://api.coindcx.com/exchange/v1/markets_details"
COINDCX_TICKER_URL = "https://api.coindcx.com/exchange/ticker"

CHECK_INTERVAL = 60  # seconds (1 minute)
PRICE_CHANGE_THRESHOLD = 3.0  # %
VOLUME_CHANGE_THRESHOLD = 50.0  # %


# ====== FUNCTIONS ======
def send_telegram_message(message: str):
    """Send message to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message}
        r = requests.post(url, json=payload)
        if r.status_code != 200:
            print(f"Telegram send error: {r.text}")
    except Exception as e:
        print(f"Telegram error: {e}")


def get_coindcx_markets():
    """Fetch CoinDCX market details"""
    try:
        response = requests.get(COINDCX_MARKET_URL)
        response.raise_for_status()
        markets = response.json()

        if not markets:
            print("No market data received")
            return {}

        # Debug keys from first entry
        print("Market keys example:", markets[0].keys())

        # Filter only USDT/INR pairs
        usdt_pairs = [
            m for m in markets
            if m.get("target_currency_short_name") in ["USDT", "INR"]
        ]

        # Flexible key selection
        return {
            m.get("market") or m.get("coindcx_name") or m.get("symbol"): m
            for m in usdt_pairs
            if m.get("market") or m.get("coindcx_name") or m.get("symbol")
        }
    except Exception as e:
        print("Error fetching markets:", e)
        return {}


def get_coindcx_tickers():
    """Fetch CoinDCX tickers"""
    try:
        response = requests.get(COINDCX_TICKER_URL)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print("Error fetching tickers:", e)
        return {}


def monitor_pumps():
    """Main monitoring loop"""
    markets = get_coindcx_markets()
    if not markets:
        print("No markets loaded, retrying in 1 minute...")
        return

    last_data = {}

    print("Monitoring started...")
    send_telegram_message("🚀 CoinDCX Pump Detector Started")

    while True:
        try:
            tickers = get_coindcx_tickers()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            for ticker in tickers:
                market_name = ticker.get("market") or ticker.get("coindcx_name") or ticker.get("symbol")
                if not market_name or market_name not in markets:
                    continue

                try:
                    last_price = float(ticker["last_price"])
                    volume = float(ticker["volume"])
                except (KeyError, ValueError, TypeError):
                    continue

                if market_name in last_data:
                    prev_price, prev_volume = last_data[market_name]
                    price_change = ((last_price - prev_price) / prev_price) * 100
                    volume_change = ((volume - prev_volume) / prev_volume) * 100 if prev_volume > 0 else 0

                    if abs(price_change) >= PRICE_CHANGE_THRESHOLD or volume_change >= VOLUME_CHANGE_THRESHOLD:
                        msg = (
                            f"🚨 Pump Alert!\n"
                            f"Coin: {market_name}\n"
                            f"Price: {last_price:.4f} ({price_change:+.2f}%)\n"
                            f"Volume Change: {volume_change:+.2f}%\n"
                            f"Time: {now}"
                        )
                        print(msg)
                        send_telegram_message(msg)

                last_data[market_name] = (last_price, volume)

            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("Stopped by user.")
            send_telegram_message("🛑 Pump Detector Stopped by User")
            break
        except Exception as e:
            print("Error in monitor loop:", e)
            time.sleep(10)


if __name__ == "__main__":
    print("Starting CoinDCX Pump Monitor...")
    monitor_pumps()
