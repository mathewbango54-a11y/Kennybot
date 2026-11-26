import os, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests, time, datetime, pandas as pd

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Kenny is alive")
    def log_message(self, *a):
        pass

def keep_alive():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

threading.Thread(target=keep_alive, daemon=True).start()

NTFY_TOPIC = "kennnybot"
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"

def send_ntfy(title, msg):
    try:
        requests.post(NTFY_URL, data=msg.encode('utf-8'), headers={"Title": title, "Priority": "5", "Tags": "moneybag"})
        print(f"Sent: {title}")
    except Exception as e:
        print(f"NTFY fail: {e}")

def get_klines(symbol="BTCUSDT", interval="15m", limit=100):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    r = requests.get(url, timeout=10).json()
    df = pd.DataFrame(r, columns=['t','o','h','l','c','v','ct','qv','n','tb','tq','ig'])
    df['c'] = df['c'].astype(float)
    df['h'] = df['h'].astype(float)
    df['l'] = df['l'].astype(float)
    return df

def get_daily():
    url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=3"
    r = requests.get(url, timeout=10).json()
    y = r[-2]
    y_high = float(y[2]); y_low = float(y[3])
    t = r[-1]
    t_high = float(t[2]); t_low = float(t[3])
    return y_high, y_low, t_high, t_low

last_signal = ""

def check():
    global last_signal
    try:
        y_high, y_low, t_high, t_low = get_daily()
        df15 = get_klines(interval="15m")
        df60 = get_klines(interval="1h")
        price = df15['c'].iloc[-1]
        ema9_15 = df15['c'].ewm(span=9).mean().iloc[-1]
        ema21_15 = df15['c'].ewm(span=21).mean().iloc[-1]
        ema9_60 = df60['c'].ewm(span=9).mean().iloc[-1]
        ema21_60 = df60['c'].ewm(span=21).mean().iloc[-1]
        bullish_ema = (ema9_15 > ema21_15) and (ema9_60 > ema21_60)
        bearish_ema = (ema9_15 < ema21_15) and (ema9_60 < ema21_60)
        signal = "WAIT"
        sl = 0; tp = 0
        if price > y_high and bullish_ema:
            signal = "BUY"; sl = price - 150; tp = price + 500
        elif price < y_low and bearish_ema:
            signal = "SELL"; sl = price + 150; tp = price - 500
        elif price > t_high and bullish_ema:
            signal = "BUY"; sl = price - 120; tp = price + 400
        elif price < t_low and bearish_ema:
            signal = "SELL"; sl = price + 120; tp = price - 400
        print(f"{datetime.datetime.now()} Price {price} Signal {signal}")
        if signal != "WAIT" and signal != last_signal:
            last_signal = signal
            msg = f"KENNY BUY/SELL\nPrice: ${price:,.0f}\nEntry: ${price:,.0f} | SL: ${sl:,.0f} | TP: ${tp:,.0f}\nY-High: ${y_high:,.0f} | Y-Low: ${y_low:,.0f}\nRisk: R20 ONLY"
            send_ntfy(f"KENNY {signal} CONFIRMED", msg)
        elif signal == "WAIT":
            last_signal = ""
    except Exception as e:
        print(f"Error: {e}")

send_ntfy("KENNY ONLINE", "Kenny is now live on Render. Watching BTC 24/7.")

while True:
    check()
    time.sleep(900)
