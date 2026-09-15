import os, time, threading, requests
from flask import Flask

app = Flask(__name__)

# --- CONFIGURATION ---
# Channel 1: TPO Level & Entry Alerts
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1549075247108456458/K6p2w-tPBxR_Cdpdn9kqKfA_3KAM4HxX_sr2I2EgAPv5bxW-pXgJzSQWm57WTEPcIxM8"

# Channel 2: Whale / Big Move Impulse Alerts
DISCORD_WHALE_WEBHOOK_URL = "https://discord.com/api/webhooks/1549076176662831246/U24bHAk-GSWqy0aX5sBq3RV_GFhTeLql2Kb4JUx-tv--gU1s4UMn8IcKq9T3GsGB47Tv"

ALERT_COOLDOWN = 900         # 15-minute cooldown per target level
WHALE_WINDOW_SECONDS = 300  # 5-minute rolling window for impulse tracking
WHALE_COOLDOWN = 900        # 15-minute cooldown for whale alerts per coin

# Multi-Coin Target Configuration (BTC & ETH Entries Only)
TARGETS = [
    # ==========================================
    # --- BTC ENTRY SETUPS ---
    # ==========================================
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

    # ==========================================
    # --- ETH ENTRY SETUPS ---
    # ==========================================
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
    {"coin": "ETH-USD", "label": "ETH OBSERVE FOR ENTRY 19", "target": 1445.34, "type": "LONG",  "last_alert": 0}
]

# Tracking state for whale rolling windows
whale_price_history = {}
whale_last_alert = {}

# --- DISCORD NOTIFICATION LOGIC ---
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
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=15)
    except Exception as e:
        print(f"Level Alert Error: {e}")

def send_whale_move_alert(coin, move_pct, current_price):
    is_up = move_pct > 0
    title = f"🟢 🐋 WHALE BUY IMPULSE: {coin} +{move_pct:.2f}%" if is_up else f"🔴 🐋 WHALE SELL IMPULSE: {coin} {move_pct:.2f}%"
    color = 3066993 if is_up else 15158332
    
    payload = {
        "username": "Whale Tracker Bot",
        "embeds": [{
            "title": title,
            "description": f"**Sudden price impulse detected on {coin}!**",
            "color": color,
            "fields": [{"name": "Current Price", "value": f"${current_price:,.2f}", "inline": True}]
        }]
    }
    try:
        requests.post(DISCORD_WHALE_WEBHOOK_URL, json=payload, timeout=15)
    except Exception as e:
        print(f"Whale Alert Error: {e}")

def check_whale_impulses(current_prices):
    now = time.time()

    for coin, current_price in current_prices.items():
        if coin not in whale_price_history:
            whale_price_history[coin] = []

        # 1. Store price snapshot with timestamp
        whale_price_history[coin].append((now, current_price))

        # 2. Keep only snapshots from the last 5 minutes
        whale_price_history[coin] = [
            entry for entry in whale_price_history[coin] if now - entry[0] <= WHALE_WINDOW_SECONDS
        ]

        # 3. Calculate move relative to the oldest snapshot in the window
        if len(whale_price_history[coin]) > 1:
            oldest_price = whale_price_history[coin][0][1]
            pct_change = ((current_price - oldest_price) / oldest_price) * 100

            # 4. Trigger alert if change >= 0.75% and cooldown expired
            last_ping = whale_last_alert.get(coin, 0)
            if abs(pct_change) >= 0.75 and (now - last_ping) > WHALE_COOLDOWN:
                send_whale_move_alert(coin, pct_change, current_price)
                whale_last_alert[coin] = now

# --- MONITORING THREAD ---
def monitor_prices():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    tracked_coins = list(set([t["coin"] for t in TARGETS]))

    while True:
        current_prices = {}

        # 1. Fetch Coinbase spot price once per unique asset
        for coin in tracked_coins:
            try:
                url = f"https://api.coinbase.com/v2/prices/{coin}/spot"
                r = requests.get(url, headers=headers, timeout=15).json()
                current_prices[coin] = float(r["data"]["amount"])
            except Exception as e:
                print(f"Error fetching {coin}: {e}")
            time.sleep(1)

        # 2. Check Directional Target Levels
        for t in TARGETS:
            coin = t["coin"]
            if coin not in current_prices:
                continue

            current_price = current_prices[coin]
            target_price = t["target"]
            is_hit = False

            if t["type"] == "SHORT" and current_price >= target_price:
                is_hit = True
            elif t["type"] == "LONG" and current_price <= target_price:
                is_hit = True

            if is_hit and (time.time() - t["last_alert"]) > ALERT_COOLDOWN:
                send_discord_alert(t['label'], current_price, target_price)
                t["last_alert"] = time.time()

        # 3. Check 5-minute Rolling Whale Impulses
        check_whale_impulses(current_prices)

        time.sleep(10)

# Start background thread
threading.Thread(target=monitor_prices, daemon=True).start()

@app.route('/')
def home():
    return "BTC & ETH Level and Whale Alert Bot is Active!", 200

@app.route('/health')
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
