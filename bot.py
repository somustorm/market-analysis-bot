import yfinance as yf
import requests
import os
from datetime import datetime

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def fetch(symbol):
    data = yf.download(symbol, period="2d", interval="1d")
    if len(data) < 2:
        return None, None

    close = data["Close"]
    latest = float(close.iloc[-1])
    prev = float(close.iloc[-2])
    change = ((latest - prev) / prev) * 100

    return round(latest, 2), round(change, 2)


def get_data():
    symbols = {
        "NIFTY": "^NSEI",
        "CRUDE": "CL=F",
        "GOLD": "GC=F"
    }

    out = {}
    for k, v in symbols.items():
        out[k] = fetch(v)

    return out


def report():
    data = get_data()

    def line(name):
        price, chg = data[name]
        if price is None:
            return f"{name}: NA"

        arrow = "↑" if chg > 0 else "↓"
        return f"{name}: {arrow} {price} ({chg}%)"

    return f"""
📊 MARKET UPDATE

{line("NIFTY")}
{line("CRUDE")}
{line("GOLD")}
"""


def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


if __name__ == "__main__":
    send(report())
