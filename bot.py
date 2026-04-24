import requests
import os

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send():
    msg = "✅ Bot is working!"

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    res = requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg
    })

    print(res.text)

if __name__ == "__main__":
    send()
