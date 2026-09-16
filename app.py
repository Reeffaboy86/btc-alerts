import os, time, threading, json, requests
import websocket
from flask import Flask

app = Flask(__name__)

# --- CONFIGURATION ---
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1549075247108456458/K6p2w-tPBxR_Cdpdn9kqKfA_3KAM4HxX_sr2I2EgAPv5bxW-pXgJzSQWm57WTEPcIxM8"
DISCORD_WHALE_WEBHOOK_URL = "https://discord.com/api/webhooks/1549076176662831246/U24bHAk-GSWqy0aX5sBq3RV_GFhTeLql2Kb4JUx-tv--gU1s4UMn8IcKq9T3GsGB47Tv"

ALERT_COOLDOWN = 900  # 15-minute cooldown per target level

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

# Target Configuration (BTC, ETH, and BNB Entry Levels)
TARGETS = [
    # --- BTC ENTRY SETUPS ---
    {"coin": "BTC-USD", "label": "BTC OBSERVE FOR ENTRY 1",  "target": 96207.8, "type": "SHORT", "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC OBSERVE FOR ENTRY 2",  "target": 94854.2, "type": "SHORT", "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC OBSERVE FOR ENTRY 3",  "target": 89699.1, "type": "SHORT", "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC OBSERVE FOR ENTRY 4",  "target": 87281.7, "type": "SHORT", "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC OBSERVE FOR ENTRY 5",  "target": 80685.1, "type": "SHORT", "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC OBSERVE FOR ENTRY 6 (1H Resistance)", "target": 79951.0, "type": "SHORT", "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC OBSERVE FOR ENTRY 7",  "target": 79343.9, "type": "SHORT", "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC OBSERVE FOR ENTRY 8",  "target": 76185.3, "type": "LONG",  "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC OBSERVE FOR ENTRY 9",  "target": 75521.6, "type": "LONG",  "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC OBSERVE FOR ENTRY 10", "target": 74513.8, "type": "LONG",  "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC OBSERVE FOR ENTRY 11", "target": 72816.5, "type": "LONG",  "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC OBSERVE FOR ENTRY 12", "target": 71477.6, "type": "LONG",  "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC OBSERVE FOR ENTRY 13", "target": 69799.8, "type": "LONG",  "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC OBSERVE FOR ENTRY 14", "target": 68096.3, "type": "LONG",  "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC OBSERVE FOR ENTRY 15", "target": 65084.5, "type": "LONG",  "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC OBSERVE FOR ENTRY 16", "target": 63381.1, "type": "LONG",  "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC OBSERVE FOR ENTRY 17", "target": 60620.1, "type": "LONG",  "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC OBSERVE FOR ENTRY 18", "target": 59753.9, "type": "LONG",  "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC OBSERVE FOR ENTRY 19", "target": 48466.9, "type": "LONG",  "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC OBSERVE FOR ENTRY 20", "target": 46987.3, "type": "LONG",  "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC OBSERVE FOR ENTRY 21", "target": 43512.0, "type": "LONG",  "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC OBSERVE FOR ENTRY 22", "target": 42577.1, "type": "LONG",  "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC OBSERVE FOR ENTRY 23", "target": 30135.7, "type": "LONG",  "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC OBSERVE FOR ENTRY 24", "target": 29415.0, "type": "LONG",  "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC OBSERVE FOR ENTRY 25", "target": 28868.3, "type": "LONG",  "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC OBSERVE FOR ENTRY 26", "target": 27998.4, "type": "LONG",  "last_alert": 0},

    # --- ETH ENTRY SETUPS ---
    {"coin": "ETH-USD", "label": "ETH OBSERVE FOR ENTRY 1",  "target": 3938.24, "type": "SHORT", "last_alert": 0},
    {"coin": "ETH-USD", "label": "ETH OBSERVE FOR ENTRY 2",  "target": 3822.16, "type": "SHORT", "last_alert": 0},
    {"coin": "ETH-USD", "label": "ETH OBSERVE FOR ENTRY 3",  "target": 3384.93, "type": "SHORT", "last_alert": 0},
    {"coin": "ETH-USD", "label": "ETH OBSERVE FOR ENTRY 4",  "target": 3266.82, "type": "SHORT", "last_alert": 0},
    {"coin": "ETH-USD", "label": "ETH OBSERVE FOR ENTRY 5",  "target": 3044.13, "type": "SHORT", "last_alert": 0},
    {"coin": "ETH-USD", "label": "ETH OBSERVE FOR ENTRY 6",  "target": 2877.14, "type": "SHORT", "last_alert": 0},
    {"coin": "ETH-USD", "label": "ETH OBSERVE FOR ENTRY 7",  "target": 2750.88, "type": "SHORT", "last_alert": 0},
    {"coin": "ETH-USD", "label": "ETH OBSERVE FOR ENTRY 8",  "target": 2709.59, "type": "SHORT", "last_alert": 0},
    {"coin": "ETH-USD", "label": "ETH OBSERVE FOR ENTRY 9",  "target": 2547.78, "type": "LONG",  "last_alert": 0},
    {"coin": "ETH-USD", "label": "ETH OBSERVE FOR ENTRY 10", "target": 2506.76, "type": "LONG",  "last_alert": 0},
    {"coin": "ETH-USD", "label": "ETH OBSERVE FOR ENTRY 11", "target": 2467.47, "type": "LONG",  "last_alert": 0},
    {"coin": "ETH-USD", "label": "ETH OBSERVE FOR ENTRY 12", "target": 2445.53, "type": "LONG",  "last_alert": 0},
    {"coin": "ETH-USD", "label": "ETH OBSERVE FOR ENTRY 13", "target": 2384.20, "type": "LONG",  "last_alert": 0},
    {"coin": "ETH-USD", "label": "ETH OBSERVE FOR ENTRY 14", "target": 2247.03, "type": "LONG",  "last_alert": 0},
    {"coin": "ETH-USD", "label": "ETH OBSERVE FOR ENTRY 15", "target": 1939.96, "type": "LONG",  "last_alert": 0},
    {"coin": "ETH-USD", "label": "ETH OBSERVE FOR ENTRY 16", "target": 1867.86, "type": "LONG",  "last_alert": 0},
    {"coin": "ETH-USD", "label": "ETH OBSERVE FOR ENTRY 17", "target": 1651.44, "type": "LONG",  "last_alert": 0},
    {"coin": "ETH-USD", "label": "ETH OBSERVE FOR ENTRY 18", "target": 1563.58, "type": "LONG",  "last_alert": 0},
    {"coin": "ETH-USD", "label": "ETH OBSERVE FOR ENTRY 19", "target": 1445.34, "type": "LONG",  "last_alert": 0},

    # --- BNB ENTRY SETUPS ---
    {"coin": "BNB-USD", "label": "BNB OBSERVE FOR ENTRY 1",  "target": 931.66, "type": "SHORT", "last_alert": 0},
    {"coin": "BNB-USD", "label": "BNB OBSERVE FOR ENTRY 2",  "target": 906.68, "type": "SHORT", "last_alert": 0},
    {"coin": "BNB-USD", "label": "BNB OBSERVE FOR ENTRY 3",  "target": 856.00, "type": "SHORT", "last_alert": 0},
    {"coin": "BNB-USD", "label": "BNB OBSERVE FOR ENTRY 4",  "target": 832.84, "type": "SHORT", "last_alert": 0},
    {"coin": "BNB-USD", "label": "BNB OBSERVE FOR ENTRY 5",  "target": 785.07, "type": "SHORT", "last_alert": 0},
    {"coin": "BNB-USD", "label": "BNB OBSERVE FOR ENTRY 6",  "target": 760.15, "type": "SHORT", "last_alert": 0},
    {"coin": "BNB-USD", "label": "BNB OBSERVE FOR ENTRY 7",  "target": 742.42, "type": "SHORT", "last_alert": 0},
    {"coin": "BNB-USD", "label": "BNB OBSERVE FOR ENTRY 8",  "target": 729.78, "type": "SHORT", "last_alert": 0},
    {"coin": "BNB-USD", "label": "BNB OBSERVE FOR ENTRY 9",  "target": 708.88, "type": "SHORT", "last_alert": 0},
    {"coin": "BNB-USD", "label": "BNB OBSERVE FOR ENTRY 10", "target": 682.73, "type": "SHORT", "last_alert": 0},
    {"coin": "BNB-USD", "label": "BNB OBSERVE FOR ENTRY 11", "target": 647.39, "type": "LONG",  "last_alert": 0},
    {"coin": "BNB-USD", "label": "BNB OBSERVE FOR ENTRY 12", "target": 637.57, "type": "LONG",  "last_alert": 0},
    {"coin": "BNB-USD", "label": "BNB OBSERVE FOR ENTRY 13", "target": 620.69, "type": "LONG",  "last_alert": 0},
    {"coin": "BNB-USD", "label": "BNB OBSERVE FOR ENTRY 14", "target": 598.79, "type": "LONG",  "last_alert": 0},
    {"coin": "BNB-USD", "label": "BNB OBSERVE FOR ENTRY 15", "target": 557.47, "type": "LONG",  "last_alert": 0},
    {"coin": "BNB-USD", "label": "BNB OBSERVE FOR ENTRY 16", "target": 526.00, "type": "LONG",  "last_alert": 0},
    {"coin": "BNB-USD", "label": "BNB OBSERVE FOR ENTRY 17", "target": 513.53, "type": "LONG",  "last_alert": 0},
    {"coin": "BNB-USD", "label": "BNB OBSERVE FOR ENTRY 18", "target": 501.00, "type": "LONG",  "last_alert": 0},
    {"coin": "BNB-USD", "label": "BNB OBSERVE FOR ENTRY 19", "target": 366.51, "type": "LONG",  "last_alert": 0},
    {"coin": "BNB-USD", "label": "BNB OBSERVE FOR ENTRY 20", "target": 336.00, "type": "LONG",  "last_alert": 0},
    {"coin": "BNB-USD", "label": "BNB OBSERVE FOR ENTRY 21", "target": 287.45, "type": "LONG",  "last_alert": 0}
]

previous_spot_prices = {}

def get_asset_threshold(symbol):
    """ Standardize pair string and lookup USD threshold. """
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

    ws = websocket.WebSocketApp(url, on_open=on_open, on_message=on_message, on_close=on_close)
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
            "product_ids": ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "BNB-USD", "ZEC-USD"],
            "channels": ["matches"]
        }))

    def on_close(ws, close_status, close_msg):
        time.sleep(5)
        start_coinbase_websocket()

    ws = websocket.WebSocketApp("wss://ws-feed.exchange.coinbase.com", on_open=on_open, on_message=on_message, on_close=on_close)
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

    ws = websocket.WebSocketApp("wss://ws.okx.com:8443/ws/v5/public", on_open=on_open, on_message=on_message, on_close=on_close)
    ws.run_forever(ping_interval=20, ping_timeout=10)

# --- MONITORING THREAD FOR LEVEL CROSSINGS ---
def monitor_prices():
    headers = {"User-Agent": "Mozilla/5.0"}
    tracked_coins = list(set([t["coin"] for t in TARGETS]))

    print("[SYSTEM] Starting level crossing monitor thread...", flush=True)

    while True:
        current_prices = {}

        for coin in tracked_coins:
            try:
                url = f"https://api.coinbase.com/v2/prices/{coin}/spot"
                r = requests.get(url, headers=headers, timeout=15).json()
                current_prices[coin] = float(r["data"]["amount"])
            except Exception as e:
                print(f"[ERROR] Fetching {coin}: {e}", flush=True)
            time.sleep(1)

        for t in TARGETS:
            coin = t["coin"]
            if coin not in current_prices:
                continue

            current_price = current_prices[coin]
            prev_price = previous_spot_prices.get(coin)
            target_price = t["target"]
            is_hit = False

            if prev_price is not None:
                if t["type"] == "SHORT" and prev_price < target_price <= current_price:
                    is_hit = True
                elif t["type"] == "LONG" and prev_price > target_price >= current_price:
                    is_hit = True

            if is_hit and (time.time() - t["last_alert"]) > ALERT_COOLDOWN:
                send_discord_alert(t['label'], current_price, target_price)
                t["last_alert"] = time.time()

        for coin, price in current_prices.items():
            previous_spot_prices[coin] = price

        btc_p = current_prices.get("BTC-USD", 0)
        eth_p = current_prices.get("ETH-USD", 0)
        bnb_p = current_prices.get("BNB-USD", 0)
        print(f"--- Loop Tick: BTC ${btc_p:,.2f} | ETH ${eth_p:,.2f} | BNB ${bnb_p:,.2f} ---", flush=True)

        time.sleep(10)

# Start background threads
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
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
