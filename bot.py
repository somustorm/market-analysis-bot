import requests
import os
import yfinance as yf
import math
from datetime import datetime, timezone, timedelta

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

IST = timezone(timedelta(hours=5, minutes=30))

# =============================
# TELEGRAM
# =============================
def send(msg):
    if not TOKEN or not CHAT_ID:
        print("Missing Telegram config")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


# =============================
# FETCH
# =============================
def fetch(symbol):
    try:
        df = yf.download(symbol, period="5d", interval="1d", progress=False)
        if df is None or df.empty or len(df) < 2:
            return None
        return df
    except:
        return None


def get_change(df):
    if df is None:
        return None, None
    try:
        close = df["Close"]
        pct = float(close.pct_change().iloc[-1])
        pts = float(close.iloc[-1] - close.iloc[-2])
        if math.isnan(pct):
            return None, None
        return pct, pts
    except:
        return None, None


def fmt(pct, pts):
    if pct is None or pts is None:
        return "NA"
    sign = "+" if pts > 0 else ""
    return f"{sign}{pts:.0f} ({pct*100:.2f}%)"


# =============================
# INDIA MORNING REPORT
# =============================
def india_report():

    nifty = fetch("^NSEI")
    banknifty = fetch("^NSEBANK")
    sensex = fetch("^BSESN")

    crude = fetch("CL=F")
    usd = fetch("DX-Y.NYB")

    n = get_change(nifty)
    bn = get_change(banknifty)
    s = get_change(sensex)
    c = get_change(crude)
    dxy = get_change(usd)

    bias = "BEARISH" if n[0] and n[0] < 0 else "BULLISH"

    msg = f"""🇮🇳 INDIA MARKET OUTLOOK (8:45 AM)

🌍 Macro:
- Crude: {fmt(*c)}
- Dollar Index: {fmt(*dxy)}

📉 Bias: {bias}

📊 Indices:
NIFTY: {fmt(*n)}
BANKNIFTY: {fmt(*bn)}
SENSEX: {fmt(*s)}

🧠 Plan:
{"Sell on rise" if bias=="BEARISH" else "Buy on dips"}
"""

    return msg


# =============================
# US EVENING REPORT
# =============================
def us_report():

    dow = fetch("^DJI")
    nasdaq = fetch("^IXIC")
    spx = fetch("^GSPC")

    crude = fetch("CL=F")
    btc = fetch("BTC-USD")

    d = get_change(dow)
    nq = get_change(nasdaq)
    sp = get_change(spx)
    c = get_change(crude)
    b = get_change(btc)

    bias = "BEARISH" if nq[0] and nq[0] < 0 else "BULLISH"

    msg = f"""🌙 US MARKET PREP (7 PM)

🌍 Macro:
- Crude: {fmt(*c)}
- BTC: {fmt(*b)}

📊 Indices:
DOW: {fmt(*d)}
NASDAQ: {fmt(*nq)}
SPX: {fmt(*sp)}

📉 Bias: {bias}

🧠 Plan:
{"Cautious / sell rallies" if bias=="BEARISH" else "Buy dips"}
"""

    return msg


# =============================
# ROUTER (IMPORTANT)
# =============================
def main():

    now = datetime.now(IST)

    hour = now.hour
    minute = now.minute

    # Morning India
    if hour == 8 and 40 <= minute <= 50:
        send(india_report())

    # Evening US
    elif hour == 18 or hour == 19:
        send(us_report())

    else:
        send("⚠️ Scheduler triggered outside defined window")


if __name__ == "__main__":
    main()
