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
    if not TOKEN or not CHAT_ID:
        print("Missing Telegram config")
        return
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except Exception as e:
        print("Telegram error:", e)


# ---------------------------
# DATA
# ---------------------------
def fetch(symbol):
    try:
        df = yf.download(symbol, period="2d", interval="1d", progress=False)
        if df is None or df.empty or len(df) < 2:
            return None
        return df
    except Exception as e:
        print(f"Fetch error {symbol}:", e)
        return None


def change(df):
    if df is None:
        return None, None
    try:
        c = df["Close"]
        pct = round((c.iloc[-1] / c.iloc[-2] - 1) * 100, 2)
        pts = int(round(c.iloc[-1] - c.iloc[-2], 0))
        return pct, pts
    except:
        return None, None


def levels(df):
    if df is None:
        return None, None, None
    try:
        h = int(df["High"].iloc[-2])
        l = int(df["Low"].iloc[-2])
        c = df["Close"].iloc[-2]
        pivot = int(round((h + l + c) / 3, 0))
        return h, l, pivot
    except:
        return None, None, None


def fmt(pct, pts):
    if pct is None:
        return "NA"
    sign = "+" if pts > 0 else ""
    return f"{sign}{pts} ({pct}%)"


# ---------------------------
# INDIA REPORT (AM)
# ---------------------------
def india():
    df_n = fetch("^NSEI")
    df_bn = fetch("^NSEBANK")
    df_s = fetch("^BSESN")

    n = change(df_n)
    bn = change(df_bn)
    s = change(df_s)

    pdh, pdl, pivot = levels(df_n)

    crude = change(fetch("CL=F"))
    dxy = change(fetch("DX-Y.NYB"))

    bias = "BEARISH" if n[0] and n[0] < 0 else "BULLISH"

    return f"""🇮🇳 INDIA MARKET OUTLOOK

NIFTY: {fmt(*n)}
BANKNIFTY: {fmt(*bn)}
SENSEX: {fmt(*s)}

📍 Levels (NIFTY)
PDH: {pdh}
PDL: {pdl}
Pivot: {pivot}

🌍 Macro:
Crude: {fmt(*crude)}
Dollar: {fmt(*dxy)}

📉 Bias: {bias}
Plan: {"Sell on rise" if bias=="BEARISH" else "Buy dips"}
"""


# ---------------------------
# US REPORT (PM)
# ---------------------------
def us():
    dow = change(fetch("^DJI"))
    nasdaq = change(fetch("^IXIC"))
    spx = change(fetch("^GSPC"))

    crude = change(fetch("CL=F"))
    btc = change(fetch("BTC-USD"))

    bias = "BEARISH" if nasdaq[0] and nasdaq[0] < 0 else "BULLISH"

    return f"""🌙 US MARKET PREP

DOW: {fmt(*dow)}
NASDAQ: {fmt(*nasdaq)}
SPX: {fmt(*spx)}

🌍 Macro:
Crude: {fmt(*crude)}
BTC: {fmt(*btc)}

📉 Bias: {bias}
Plan: {"Cautious / sell rallies" if bias=="BEARISH" else "Buy dips"}
"""


# ---------------------------
# ROUTER
# ---------------------------
def main():
    now = datetime.now(IST)
    hour = now.hour

    if hour == 8:
        send(india())
    elif hour in [18, 19]:
        send(us())
    else:
        print("Skip run")


if __name__ == "__main__":
    main()
