import os, time, threading, requests
from flask import Flask

app = Flask(__name__)

# Config
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1548980198039363586/SbspEcALq9ZqK0LeGqd_D4ZBP2iHOusQEG4BAFWHSk345HC1EMfaSi0bMHcbjwY9JXBN"
TARGET_ENTRY = 1.0  # Set low for testing
ALERT_COOLDOWN = 900 

last_alert_time = 0

def send_discord_alert(price):
    global last_alert_time
    payload = {
        "username": "BTC Execution Bot",
        "embeds": [{
            "title": f"🚨 TARGET HIT: {price} USDT",
            "description": "**Price wicking into target short zone.**",
            "color": 15158332,
            "fields": [
                {"name": "Action Required", "value": "Check 1H Candle Close", "inline": False}
            ]
        }]
    }
    try:
        r = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
        print(f"Discord Post Status: {r.status_code}")
    except Exception as e:
        print(f"Discord Post Error: {e}")
        
    last_alert_time = time.time()

def monitor_price():
    print(">>> PRICE MONITOR STARTED SUCCESSFULLY <<<")
    while True:
        try:
            # Using Coinbase API to avoid US IP block issues
            r = requests.get("https://api.coinbase.com/v2/prices/BTC-USD/spot", timeout=5).json()
            current_price = float(r["data"]["amount"])
            print(f"Current BTC Price: {current_price}")
            
            if current_price >= TARGET_ENTRY and (time.time() - last_alert_time) > ALERT_COOLDOWN:
                print("Target reached! Sending Discord notification...")
                send_discord_alert(current_price)
                
        except Exception as e:
            print(f"Error checking price: {e}")
            
        time.sleep(5)

# Force background thread execution on Gunicorn worker startup
t = threading.Thread(target=monitor_price, daemon=True)
t.start()

@app.route('/health')
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
