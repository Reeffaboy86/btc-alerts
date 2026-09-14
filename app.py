import os, time, threading, requests
from flask import Flask

app = Flask(__name__)

# --- CONFIGURATION (SECURED VIA ENVIRONMENT VARIABLES) ---
# Pulls URLs securely from the environment. Falls back to None if not configured.
DISCORD_WEBHOOK_URL = os.environ.get("https://discord.com/api/webhooks/1548980198039363586/SbspEcALq9ZqK0LeGqd_D4ZBP2iHOusQEG4BAFWHSk345HC1EMfaSiObMHcbjwY9JXBN")
DISCORD_WHALE_WEBHOOK_URL = os.environ.get("https://discord.com/api/webhooks/1549037655445086288/UHg-GQbslmYflnMND5cpn7SojgXS2vdpoveuM5HirKzD2bxUD-8pdvzFDVLPcDTz1AlJ")

ALERT_COOLDOWN = 900  # 15-minute alert cooldown per target level

# Multi-Coin Target Configuration (Preserved exact target limits)
TARGETS = [
    # ==========================================
    # --- BTC SETUPS ---
    # ==========================================

    # 1. BTC SHORT SETUPS & TAKE PROFITS
    {"coin": "BTC-USD", "label": "BTC SHORT ENTRY 1 (TPOC)",        "target": 79685.0, "type": "SHORT", "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC SHORT ENTRY 2 (Range High)",  "target": 80910.0, "type": "SHORT", "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC SHORT ENTRY 3 (Swing Peak)",  "target": 81498.0, "type": "SHORT", "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC HTF SHORT ENTRY (Weekly POC)","target": 87768.0, "type": "SHORT", "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC HTF SHORT ENTRY (Monthly POC)","target": 89691.0, "type": "SHORT", "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC HTF SHORT ENTRY (Untest POC)","target": 95487.0, "type": "SHORT", "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC SHORT TP1 (TVAH Level)",      "target": 78190.0, "type": "LONG",  "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC SHORT TP2 (TVAL Support)",    "target": 75540.0, "type": "LONG",  "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC SHORT TP3 (Daily TPOC)",      "target": 72690.0, "type": "LONG",  "last_alert": 0},

    # 2. BTC LONG SETUPS & TAKE PROFITS
    {"coin": "BTC-USD", "label": "BTC LONG ENTRY 1 (TVAL Support)", "target": 75540.0, "type": "LONG",  "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC LONG ENTRY 2 (Daily TPOC)",   "target": 72690.0, "type": "LONG",  "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC MACRO LONG ENTRY 1 (POC Cluster)","target": 63506.0, "type": "LONG", "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC MACRO LONG ENTRY 2 (Untest Wkly)","target": 59965.0, "type": "LONG", "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC LONG TP1 (TVAH Resistance)",  "target": 78190.0, "type": "SHORT", "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC LONG TP2 (TPOC Level)",       "target": 79685.0, "type": "SHORT", "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC LONG TP3 (Range High)",       "target": 80910.0, "type": "SHORT", "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC LONG RUNNER (Weekly POC)",    "target": 87768.0, "type": "SHORT", "last_alert": 0},

    # ==========================================
    # --- ETH SETUPS ---
    # ==========================================

    # 1. ETH SHORT SETUPS & TAKE PROFITS
    {"coin": "ETH-USD", "label": "ETH SHORT ENTRY 1 (Local TVAH)",  "target": 2530.0,  "type": "SHORT", "last_alert": 0},
    {"coin": "ETH-USD", "label": "ETH SHORT ENTRY 2 (Range High)",  "target": 2720.0,  "type": "SHORT", "last_alert": 0},
    {"coin": "ETH-USD", "label": "ETH HTF SHORT ENTRY (Psych $3k)", "target": 2980.0,  "type": "SHORT", "last_alert": 0},
    {"coin": "ETH-USD", "label": "ETH HTF SHORT ENTRY (Macro High)","target": 3380.0,  "type": "SHORT", "last_alert": 0},
    {"coin": "ETH-USD", "label": "ETH SHORT TP1 (TVAL Support)",    "target": 2506.0,  "type": "LONG",  "last_alert": 0},
    {"coin": "ETH-USD", "label": "ETH SHORT TP2 (Untested POC)",    "target": 2435.0,  "type": "LONG",  "last_alert": 0},
    {"coin": "ETH-USD", "label": "ETH SHORT TP3 (Macro Support)",   "target": 2260.0,  "type": "LONG",  "last_alert": 0},

    # 2. ETH LONG SETUPS & TAKE PROFITS
    {"coin": "ETH-USD", "label": "ETH LONG ENTRY 1 (TVAL Level)",   "target": 2506.0,  "type": "LONG",  "last_alert": 0},
    {"coin": "ETH-USD", "label": "ETH LONG ENTRY 2 (Untested POC)", "target": 2435.0,  "type": "LONG",  "last_alert": 0},
    {"coin": "ETH-USD", "label": "ETH LONG ENTRY 3 (Macro POC)",    "target": 2260.0,  "type": "LONG",  "last_alert": 0},
    {"coin": "ETH-USD", "label": "ETH LONG TP1 (Local TVAH)",       "target": 2530.0,  "type": "SHORT", "last_alert": 0},
    {"coin": "ETH-USD", "label": "ETH LONG RUNNER (Macro High)",    "target": 3380.0,  "type": "SHORT", "last_alert": 0}
]

previous_prices = {}

# --- DISCORD NOTIFICATION LOGIC ---
def send_discord_alert(coin_label, price, target):
    if not DISCORD_WEBHOOK_URL:
        print("Skipping Level Alert: DISCORD_WEBHOOK_URL environment variable is missing.")
        return
        
    payload = {
        "username": "Crypto Level Bot",
        "embeds": [{
            "title": f"🚨 {coin_label}: ${price:,.2f}",
            "description": f"**Price crossed target zone of ${target:,.2f}**",
            "color": 15158332,
            "fields": [{"name": "Action Required", "value": "Check 1H Candle Close & Order Flow", "inline": False}]
        }]
    }
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
        print(f"Level Alert Status Code: {response.status_code}")
    except Exception as e:
        print(f"Level Alert Exception: {e}")

def send_whale_move_alert(coin, move_pct, current_price):
    if not DISCORD_WHALE_WEBHOOK_URL:
        print("Skipping Whale Alert: DISCORD_WHALE_WEBHOOK_URL environment variable is missing.")
        return
        
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
        response = requests.post(DISCORD_WHALE_WEBHOOK_URL, json=payload, timeout=5)
        print(f"Whale Alert Status Code: {response.status_code}")
    except Exception as e:
        print(f"Whale Alert Exception: {e}")

# --- MONITORING THREAD ---
def monitor_prices():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    # 🧪 FORCED BOOT TEST FOR BOTH CHANNELS (BTC & ETH)
    time.sleep(3)
    print("Triggering secure test alerts for BTC and ETH...")
    
    # BTC Test Pings
    send_discord_alert("🧪 TEST ALERT - BTC LEVEL BOT", 78500.0, 78000.0)
    send_whale_move_alert("BTC-USD (TEST)", 0.85, 78500.0)
    
    # ETH Test Pings
    send_discord_alert("🧪 TEST ALERT - ETH LEVEL BOT", 2550.0, 2500.0)
    send_whale_move_alert("ETH-USD (TEST)", 1.20, 2550.0)

    tracked_coins = list(set([t["coin"] for t in TARGETS]))

    while True:
        current_prices = {}

        for coin in tracked_coins:
            try:
                url = f"https://coinbase.com{coin}/spot"
                r = requests.get(url, headers=headers, timeout=5).json()
                current_prices[coin] = float(r["data"]["amount"])
            except Exception as e:
                print(f"Error fetching {coin}: {e}")
            time.sleep(1)

        for t in TARGETS:
            coin = t["coin"]
            if coin not in current_prices:
                continue

            current_price = current_prices[coin]
            is_hit = False

            if t["type"] == "SHORT" and current_price >= t["target"]:
                is_hit = True
            elif t["type"] == "LONG" and current_price <= t["target"]:
                is_hit = True

            if is_hit and (time.time() - t["last_alert"]) > ALERT_COOLDOWN:
                send_discord_alert(t['label'], current_price, t['target'])
                t["last_alert"] = time.time()

        for coin, current_price in current_prices.items():
            if coin in previous_prices:
                old_price = previous_prices[coin]
                pct_change = ((current_price - old_price) / old_price) * 100
                
                if abs(pct_change) >= 0.75:
                    send_whale_move_alert(coin, pct_change, current_price)

            previous_prices[coin] = current_price

        time.sleep(10)

# Start background thread
threading.Thread(target=monitor_prices, daemon=True).start()

@app.route('/health')
def health():
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

