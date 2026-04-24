import yfinance as yf
import requests
import os
from datetime import datetime

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def fetch_price(symbol):
    data = yf.download(symbol, period="2d", interval="1d")
    if data.empty or len(data) < 2:
        return None, None

    latest = data["Close"].iloc[-1]
    prev = data["Close"].iloc[-2]
    change_pct = ((latest - prev) / prev) * 100

    return round(latest, 2), round(change_pct, 2)


def get_market_data():
    symbols = {
        "NIFTY": "^NSEI",
        "SENSEX": "^BSESN",
        "CRUDE": "CL=F",
        "GOLD": "GC=F",
        "SILVER": "SI=F",
        "COPPER": "HG=F",
        "DXY": "DX-Y.NYB",
        "US10Y": "^TNX"
    }

    result = {}

    for key, symbol in symbols.items():
        price, change = fetch_price(symbol)
        result[key] = {
            "price": price,
            "change": change
        }

    return result


def generate_report():
    data = get_market_data()

    def fmt(name):
        item = data.get(name)
        if item["price"] is None:
            return f"{name}: Data not available"

        arrow = "↑" if item["change"] > 0 else "↓"
        return f"{name}: {arrow} {item['price']} ({item['change']}%)"

    report = f"""
📊 MARKET ANALYSIS ({datetime.now().strftime('%d %b %Y %I:%M %p IST')})

🇮🇳 INDIA MARKET
{fmt("NIFTY")}
{fmt("SENSEX")}

🌍 GLOBAL & MACRO
{fmt("CRUDE")}
{fmt("GOLD")}
{fmt("SILVER")}
{fmt("COPPER")}
{fmt("DXY")}
{fmt("US10Y")}

📌 MARKET VIEW:
Bias: Neutral (basic version – upgrade later)

⚠️ Avoid:
- Trading in range
- Blind breakout trades
"""

    return report


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": msg
    }

    response = requests.post(url, data=payload)
    print(response.text)


if __name__ == "__main__":
    report = generate_report()
    send_telegram(report)
