
import os, time, threading, requests
from flask import Flask

app = Flask(__name__)

# Config
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1548980198039363586/SbspEcALq9ZqK0LeGqd_D4ZBP2iHOusQEG4BAFWHSk345HC1EMfaSiObMHcbjwY9JXBN"
ALERT_COOLDOWN = 900 

# Multi-Coin Target Configuration (BTC + ETH TPO Levels)
TARGETS = [
    # --- BTC TARGETS ---
    {"coin": "BTC-USD", "label": "BTC TVAH Short",        "target": 78190.0, "type": "SHORT", "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC TPOC Short",        "target": 79685.0, "type": "SHORT", "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC Range High Short",  "target": 80910.0, "type": "SHORT", "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC TVAL Long",         "target": 75540.0, "type": "LONG",  "last_alert": 0},
    {"coin": "BTC-USD", "label": "BTC Daily TPOC Long",   "target": 72690.0, "type": "LONG",  "last_alert": 0},

    # --- ETH TARGETS ---
    {"coin": "ETH-USD", "label": "ETH Local TVAH Short",  "target": 2533.0,  "type": "SHORT", "last_alert": 0},
    {"coin": "ETH-USD", "label": "ETH Range High Short",  "target": 2650.0,  "type": "SHORT", "last_alert": 0},
    {"coin": "ETH-USD", "label": "ETH Local TVAL Long",   "target": 2500.0,  "type": "LONG",  "last_alert": 0},
    {"coin": "ETH-USD", "label": "ETH Untested TPOC Long","target": 2435.0,  "type": "LONG",  "last_alert": 0},
    {"coin": "ETH-USD", "label": "ETH Macro POC Long",    "target": 2260.0,  "type": "LONG",  "last_alert": 0}
]
def send_discord_alert(coin_label, price, target):
    payload = {
        "username": "Crypto Execution Bot",
        "embeds": [{
            "title": f"🚨 {coin_label} TARGET HIT: ${price:,.2f}",
            "description": f"**Price crossed target zone of ${target:,.2f}**",
            "color": 15158332,
            "fields": [
                {"name": "Action Required", "value": "Check 1H Candle Close & Order Flow", "inline": False}
            ]
        }]
    }
    try:
        r = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
        print(f"Discord Post Status for {coin_label}: {r.status_code}")
    except Exception as e:
        print(f"Discord Post Error ({coin_label}): {e}")

def monitor_prices():
    print(">>> MULTI-COIN MONITOR STARTED SUCCESSFULLY <<<")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    while True:
        for t in TARGETS:
            try:
                url = f"https://api.coinbase.com/v2/prices/{t['coin']}/spot"
                r = requests.get(url, headers=headers, timeout=5).json()
                current_price = float(r["data"]["amount"])
                print(f"{t['label']} Price: ${current_price:,.2f} | Target: ${t['target']:,.2f}")
                
                # Logic check based on position type
                is_hit = False
                if t["type"] == "SHORT" and current_price >= t["target"]:
                    is_hit = True
                elif t["type"] == "LONG" and current_price <= t["target"]:
                    is_hit = True

                if is_hit and (time.time() - t["last_alert"]) > ALERT_COOLDOWN:
                    print(f"Target reached for {t['label']}! Sending Discord notification...")
                    send_discord_alert(t['label'], current_price, t['target'])
                    t["last_alert"] = time.time()
                    
            except Exception as e:
                print(f"Error checking {t['label']} price: {e}")
                
            time.sleep(2)
            
        time.sleep(10)

t = threading.Thread(target=monitor_prices, daemon=True)
t.start()

@app.route('/health')
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
