import requests
import os

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def main():
    print("Starting Telegram test...")

    if not TOKEN or not CHAT_ID:
        print("❌ Missing TELEGRAM_TOKEN or CHAT_ID")
        return

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": "✅ TEST SUCCESS FROM BOT"
    }

    try:
        res = requests.post(url, data=payload)
        print("Status Code:", res.status_code)
        print("Response:", res.text)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
