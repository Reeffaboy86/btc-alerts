import os, time, threading, requests
from flask import Flask

app = Flask(__name__)

# Config
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1548980198039363586/SbspEcALq9ZqK0LeGqd_D4ZBP2iHOusQEG4BAFWHSk345HC1EMfaSiObMHcbjwY9JXBN"
TARGET_ENTRY = 77990.0
ALERT_COOLDOWN = 900  # 2 minute pause between pings

last_alert_time = 0

def send_discord_alert(price):
    global last_alert_time
    payload = {
        "username": "BTC Execution Bot",
        "embeds": [{
            "title": f"🚨 TARGET HIT: {price} USDT",
            "description": "**Price wicking into 77,990 USDT short zone.**",
            "color": 15158332,
            "fields": [
                {"name": "Action Required", "value": "Check 1H Candle Close & CVD Divergence", "inline": False},
                {"name": "Stop Loss", "value": "~80,950 USDT", "inline": True},
                {"name": "TP1 / TP2", "value": "76,040 / 69,810 USDT", "inline": True}
            ],
            "footer": {"text": "Spot/Futures Order Flow System"}
        }]
    }
    requests.post(DISCORD_WEBHOOK_URL, json=payload)
    last_alert_time = time.time()

def monitor_price():
    while True:
        try:
            r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=5).json()
            current_price = float(r["price"])
            
            if current_price >= TARGET_ENTRY and (time.time() - last_alert_time) > ALERT_COOLDOWN:
                send_discord_alert(current_price)
                
        except Exception as e:
            print(f"Error checking price: {e}")
            
        time.sleep(3)

threading.Thread(target=monitor_price, daemon=True).start()

@app.route('/health')
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
