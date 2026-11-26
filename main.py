import requests
import time
import threading
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

# ===== KENNY SETTINGS =====
NTFY_TOPIC = "kennnybot"
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"

def send_ntfy(msg):
    try:
        print(f"SENDING TO NTFY: {msg}", flush=True)
        r = requests.post(NTFY_URL, data=msg.encode(), timeout=10)
        print(f"NTFY RESULT: {r.status_code}", flush=True)
        if r.status_code == 429:
            print("NTFY SAYS SLOW DOWN - WILL WAIT 15 MIN", flush=True)
            time.sleep(900)  # wait 15 min if rate limited
        return r.status_code
    except Exception as e:
        print(f"NTFY FAILED: {e}", flush=True)
        return 0

# ===== KEEP RENDER ALIVE - NO FLASK =====
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Kenny is alive")
    def log_message(self, format, *args):
        return

def run_web():
    port = int(os.environ.get("PORT", 10000))
    print(f"WEB SERVER ON PORT {port}", flush=True)
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

# ===== BTC PRICE - 3 SOURCES =====
def get_btc_price():
    urls = [
        "https://api.binance.us/api/v3/ticker/price?symbol=BTCUSDT",
        "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
        "https://api.coinbase.com/v2/prices/BTC-USD/spot",
    ]
    for url in urls:
        try:
            r = requests.get(url, timeout=10)
            data = r.json()
            if "price" in data:
                return float(data["price"])
            if "bitcoin" in data:
                return float(data["bitcoin"]["usd"])
            if "data" in data and "amount" in data["data"]:
                return float(data["data"]["amount"])
        except Exception:
            continue
    print("ALL PRICE SOURCES FAILED", flush=True)
    return None

def bot_loop():
    time.sleep(5)
    # Send ONLINE only once at start
    send_ntfy("KENNY ONLINE - Kenny is now live and watching BTC")
    print("KENNY ONLINE SENT", flush=True)

    last_price = None
    while True:
        try:
            price = get_btc_price()
            if price:
                print(f"BTC: ${price}", flush=True)
                if last_price is None:
                    last_price = price
                    # Don't send START PRICE immediately - wait, to avoid 429
                    print(f"START PRICE SAVED: ${price}", flush=True)
                else:
                    change = ((price - last_price) / last_price) * 100
                    if abs(change) >= 1.0:
                        send_ntfy(f"BTC MOVE: ${price:,.0f} ({change:+.2f}% from ${last_price:,.0f})")
                        last_price = price
            # Check every 5 minutes, not every 1 min - stops 429
            time.sleep(300)
        except Exception as e:
            print(f"BOT LOOP ERROR: {e}", flush=True)
            time.sleep(60)

if __name__ == "__main__":
    print("STARTING KENNY...", flush=True)
    t = threading.Thread(target=bot_loop, daemon=True)
    t.start()
    run_web()
