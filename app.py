import os
import time
import threading
import json
import requests
from flask import Flask

# Safe package fallback for websocket-client
try:
    import websocket
except ImportError:
    os.system("pip install websocket-client")
    import websocket

app = Flask(__name__)

# --- CONFIGURATION ---
# PASTE YOUR RAW GIST LINK HERE:
GIST_URL = "https://gist.githubusercontent.com/Reeffaboy86/e5c499b4197b34a4903f454ec0f34fa4/raw/9ad34af78fce60d822ef29d8c98f9dd3613b0493/targets.json"

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1549075247108456458/K6p2w-tPBxR_Cdpdn9kqKfA_3KAM4HxX_sr2I2EgAPv5bxW-pXgJzSQWm57WTEPcIxM8"
DISCORD_WHALE_WEBHOOK_URL = "https://discord.com/api/webhooks/1549076176662831246/U24bHAk-GSWqy0aX5sBq3RV_GFhTeLql2Kb4JUx-tv--gU1s4UMn8IcKq9T3GsGB47Tv"

ALERT_COOLDOWN = 900  # 15-minute cooldown per target level
LEVEL_COOLDOWNS = {}  # Dynamic tracking for level alert timestamps

# Dynamic USD Thresholds per Asset optimized for Intraday Trading
WHALE_THRESHOLDS = {
    "BTC": 500000,
    "ETH": 350000,
    "SOL": 350000,
    "XRP": 300000,
    "BNB": 300000,
    "ZEC": 50000
}

# OKX contract multiplier lookup table for accurate USD size calculation
OKX_CONTRACT_SIZES = {
    "BTC-USDT": 1.0,
    "ETH-USDT": 1.0,
    "SOL-USDT": 1.0,
    "XRP-USDT": 1.0,
    "BNB-USDT": 0.01,
    "ZEC-USDT": 0.1
}

previous_spot_prices = {}

def get_latest_targets():
    """ Fetch target configuration live from GitHub Gist """
    try:
        r = requests.get(GIST_URL, timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[ERROR] Failed reading Gist targets: {e}", flush=True)
    return []

def get_asset_threshold(symbol):
    """ Normalize string symbol and extract threshold """
    clean_symbol = symbol.replace("-USD", "").replace("-USDT", "").replace("USDT", "").upper()
    return WHALE_THRESHOLDS.get(clean_symbol, 250000)

# --- DISCORD ALERTS ---
def send_discord_alert(coin_label, price, target):
    payload = {
        "username": "Crypto Level Bot",
        "embeds": [{
            "title": f"🚨 {coin_label}: ${price:,.2f}",
            "description": f"**Price crossed observation zone of ${target:,.2f}**",
            "color": 15158332,
            "fields": [{"name": "Action Required", "value": "Check 1H Candle Close & Order Flow", "inline": False}]
        }]
    }
    try:
        r = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        if r.status_code == 429:
            retry_after = r.json().get('retry_after', 1)
            time.sleep(retry_after)
        print(f"[ALERT SENT] Level trigger: {coin_label} at ${price:,.2f}", flush=True)
    except Exception as e:
        print(f"[ERROR] Level Alert Error: {e}", flush=True)

def send_large_trade_alert(exchange, coin, side, usd_val, price, size):
    is_buy = side.lower() == "buy"
    title = f"🟢 🐋 WHALE BUY ({exchange}): ${usd_val:,.0f} of {coin}" if is_buy else f"🔴 🐋 WHALE SELL ({exchange}): ${usd_val:,.0f} of {coin}"
    color = 3066993 if is_buy else 15158332
    
    payload = {
        "username": f"{exchange} Whale Tracker",
        "embeds": [{
            "title": title,
            "description": f"**Single large market order executed on {exchange}!**",
            "color": color,
            "fields": [
                {"name": "Execution Price", "value": f"${price:,.2f}", "inline": True},
                {"name": "Order Size", "value": f"{size:,.4f}", "inline": True},
                {"name": "Total Value", "value": f"${usd_val:,.2f}", "inline": True}
            ]
        }]
    }
    try:
        r = requests.post(DISCORD_WHALE_WEBHOOK_URL, json=payload, timeout=10)
        if r.status_code == 429:
            retry_after = r.json().get('retry_after', 1)
            time.sleep(retry_after)
        print(f"[WHALE ALERT SENT] {exchange} {coin} {side.upper()} ${usd_val:,.0f}", flush=True)
    except Exception as e:
        print(f"[ERROR] Whale Alert Error: {e}", flush=True)

# --- WEBSOCKET: BINANCE ---
def start_binance_websocket():
    streams = [
        "btcusdt@aggTrade", "ethusdt@aggTrade", "solusdt@aggTrade",
        "xrpusdt@aggTrade", "bnbusdt@aggTrade", "zecusdt@aggTrade"
    ]
    url = f"wss://stream.binance.com:9443/stream?streams={'/'.join(streams)}"

    def on_message(ws, message):
        try:
            raw = json.loads(message)
            if "data" in raw:
                data = raw["data"]
                price = float(data["p"])
                size = float(data["q"])
                usd_val = price * size
                coin = data["s"]
                side = "sell" if data["m"] else "buy"

                threshold = get_asset_threshold(coin)
                if usd_val >= threshold:
                    send_large_trade_alert("Binance", coin, side, usd_val, price, size)
        except Exception:
            pass

    def on_open(ws):
        print("[WEBSOCKET] Connected to Binance Feed...", flush=True)

    def on_close(ws, close_status, close_msg):
        time.sleep(5)
        start_binance_websocket()

    def on_error(ws, error):
        pass

    ws = websocket.WebSocketApp(url, on_open=on_open, on_message=on_message, on_close=on_close, on_error=on_error)
    ws.run_forever(ping_interval=20, ping_timeout=10)

# --- WEBSOCKET: COINBASE ---
def start_coinbase_websocket():
    def on_message(ws, message):
        try:
            data = json.loads(message)
            if data.get("type") == "match":
                price = float(data["price"])
                size = float(data["size"])
                usd_val = price * size
                coin = data["product_id"]
                side = data["side"]

                threshold = get_asset_threshold(coin)
                if usd_val >= threshold:
                    send_large_trade_alert("Coinbase", coin, side, usd_val, price, size)
        except Exception:
            pass

    def on_open(ws):
        print("[WEBSOCKET] Connected to Coinbase Feed...", flush=True)
        ws.send(json.dumps({
            "type": "subscribe",
            "product_ids": ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "ZEC-USD"],
            "channels": ["matches"]
        }))

    def on_close(ws, close_status, close_msg):
        time.sleep(5)
        start_coinbase_websocket()

    def on_error(ws, error):
        pass

    ws = websocket.WebSocketApp("wss://ws-feed.exchange.coinbase.com", on_open=on_open, on_message=on_message, on_close=on_close, on_error=on_error)
    ws.run_forever(ping_interval=20, ping_timeout=10)

# --- WEBSOCKET: OKX ---
def start_okx_websocket():
    def on_message(ws, message):
        try:
            data = json.loads(message)
            if "data" in data:
                for trade in data["data"]:
                    price = float(trade["px"])
                    raw_size = float(trade["sz"])
                    coin = trade["instId"]
                    multiplier = OKX_CONTRACT_SIZES.get(coin, 1.0)
                    size = raw_size * multiplier
                    usd_val = price * size
                    side = trade["side"]

                    threshold = get_asset_threshold(coin)
                    if usd_val >= threshold:
                        send_large_trade_alert("OKX", coin, side, usd_val, price, size)
        except Exception:
            pass

    def on_open(ws):
        print("[WEBSOCKET] Connected to OKX Feed...", flush=True)
        ws.send(json.dumps({
            "op": "subscribe",
            "args": [
                {"channel": "trades", "instId": "BTC-USDT"},
                {"channel": "trades", "instId": "ETH-USDT"},
                {"channel": "trades", "instId": "SOL-USDT"},
                {"channel": "trades", "instId": "XRP-USDT"},
                {"channel": "trades", "instId": "BNB-USDT"},
                {"channel": "trades", "instId": "ZEC-USDT"}
            ]
        }))

    def on_close(ws, close_status, close_msg):
        time.sleep(5)
        start_okx_websocket()

    def on_error(ws, error):
        pass

    ws = websocket.WebSocketApp("wss://ws.okx.com:8443/ws/v5/public", on_open=on_open, on_message=on_message, on_close=on_close, on_error=on_error)
    ws.run_forever(ping_interval=20, ping_timeout=10)

# --- MONITORING THREAD FOR LEVEL CROSSINGS ---
def monitor_prices():
    headers = {"User-Agent": "Mozilla/5.0"}
    print("[SYSTEM] Starting level crossing monitor thread...", flush=True)

    while True:
        targets = get_latest_targets()
        tracked_coins = list(set([t["coin"] for t in targets])) if targets else ["BTC-USD", "ETH-USD", "BNB-USD"]

        current_prices = {}

        for coin in tracked_coins:
            try:
                url = f"https://api.coinbase.com/v2/prices/{coin}/spot"
                r = requests.get(url, headers=headers, timeout=15).json()
                if "data" in r and "amount" in r["data"]:
                    current_prices[coin] = float(r["data"]["amount"])
            except Exception as e:
                print(f"[ERROR] Fetching {coin}: {e}", flush=True)
            time.sleep(0.5)

        for t in targets:
            coin = t["coin"]
            if coin not in current_prices:
                continue

            current_price = current_prices[coin]
            prev_price = previous_spot_prices.get(coin)
            target_price = float(t["target"])
            label = t["label"]
            is_hit = False

            if prev_price is not None:
                if t["type"] == "SHORT" and prev_price < target_price <= current_price:
                    is_hit = True
                elif t["type"] == "LONG" and prev_price > target_price >= current_price:
                    is_hit = True

            last_alert_time = LEVEL_COOLDOWNS.get(label, 0)
            if is_hit and (time.time() - last_alert_time) > ALERT_COOLDOWN:
                send_discord_alert(label, current_price, target_price)
                LEVEL_COOLDOWNS[label] = time.time()

        for coin, price in current_prices.items():
            previous_spot_prices[coin] = price

        btc_p = current_prices.get("BTC-USD", 0)
        eth_p = current_prices.get("ETH-USD", 0)
        bnb_p = current_prices.get("BNB-USD", 0)
        print(f"--- Loop Tick: BTC ${btc_p:,.2f} | ETH ${eth_p:,.2f} | BNB ${bnb_p:,.2f} ---", flush=True)

        time.sleep(10)

# Start background daemon threads safely
threading.Thread(target=monitor_prices, daemon=True).start()
threading.Thread(target=start_binance_websocket, daemon=True).start()
threading.Thread(target=start_coinbase_websocket, daemon=True).start()
threading.Thread(target=start_okx_websocket, daemon=True).start()

@app.route('/')
def home():
    return "Multi-Asset Whale & Level Tracker Active!", 200

@app.route('/health')
def health():
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
