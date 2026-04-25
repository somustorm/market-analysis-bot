import requests
import os
import yfinance as yf
from datetime import datetime, timezone, timedelta

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

IST = timezone(timedelta(hours=5, minutes=30))


# ---------------------------
# TELEGRAM
# ---------------------------
def send(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        res = requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
        print("Telegram:", res.text)
    except Exception as e:
        print("Telegram error:", e)


# ---------------------------
# DATA HELPERS
# ---------------------------
def fetch(symbol):
    try:
        df = yf.download(symbol, period="2d", interval="1d", progress=False)
        if df is None or df.empty or len(df) < 2:
            return None
        return df
    except:
        return None


def change(df):
    if df is None:
        return None, None
    try:
        c = df["Close"]
        last = float(c.iloc[-1])
        prev = float(c.iloc[-2])
        pct = round((last / prev - 1) * 100, 2)
        pts = int(round(last - prev, 0))
        return pct, pts
    except:
        return None, None


def levels(df):
    if df is None:
        return None, None, None
    try:
        h = float(df["High"].iloc[-2])
        l = float(df["Low"].iloc[-2])
        c = float(df["Close"].iloc[-2])
        pivot = (h + l + c) / 3
        return int(h), int(l), int(round(pivot, 0))
    except:
        return None, None, None


def fmt(pct, pts):
    if pct is None or pts is None:
        return "NA"
    sign = "+" if pts > 0 else ""
    return f"{sign}{pts} ({pct}%)"


# ---------------------------
# INDIA REPORT
# ---------------------------
def india():

    df = fetch("^NSEI")
    pct, pts = change(df)
    pdh, pdl, pivot = levels(df)

    return f"""🇮🇳 INDIA MARKET OUTLOOK

NIFTY: {fmt(pct, pts)}

PDH: {pdh}
PDL: {pdl}
Pivot: {pivot}

Bias: {"BEARISH" if pct and pct < 0 else "BULLISH"}
Strategy: {"Sell on rise" if pct and pct < 0 else "Buy dips"}
"""


# ---------------------------
# US REPORT
# ---------------------------
def us():

    dow = change(fetch("^DJI"))
    nasdaq = change(fetch("^IXIC"))

    btc_df = fetch("BTC-USD")
    btc_pct, btc_pts = change(btc_df)
    pdh, pdl, pivot = levels(btc_df)

    return f"""🌙 US MARKET PREP

DOW: {fmt(*dow)}
NASDAQ: {fmt(*nasdaq)}

BTC:
Move: {fmt(btc_pct, btc_pts)}
PDH: {pdh}
PDL: {pdl}

Plan:
Buy above {pdh}
Sell below {pdl}
"""


# ---------------------------
# MAIN
# ---------------------------
def main():

    now = datetime.now(IST)
    hour = now.hour

    print("Time:", now)

    # Morning
    if hour < 12:
        print("Sending INDIA report")
        send(india())

    # Evening
    else:
        print("Sending US report")
        send(us())


if __name__ == "__main__":
    main()
