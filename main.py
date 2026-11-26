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
    except Exception as e:
        print(f"NTFY FAILED: {e}", flush=True)

# ===== KEEP RENDER ALIVE - NO FLASK NEEDED =====
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

# ===== BTC BOT =====
def get_btc_price():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=10)
        return float(r.json()["price"])
    except Exception as e:
        print(f"PRICE FAILED: {e}", flush=True)
        return None

def bot_loop():
    time.sleep(5)
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
                    send_ntfy(f"BTC START PRICE: ${price:,.0f} - Kenny watching now")
                else:
                    change = ((price - last_price) / last_price) * 100
                    if abs(change) >= 1.0:
                        send_ntfy(f"BTC MOVE: ${price:,.0f} ({change:+.2f}% from ${last_price:,.0f})")
                        last_price = price
            time.sleep(60)
        except Exception as e:
            print(f"BOT LOOP ERROR: {e}", flush=True)
            time.sleep(30)

if __name__ == "__main__":
    print("STARTING KENNY...", flush=True)
    t = threading.Thread(target=bot_loop, daemon=True)
    t.start()
    run_web()
