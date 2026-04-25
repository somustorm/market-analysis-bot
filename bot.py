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
        print("❌ Missing Telegram config")
        return

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        res = requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
        print("Telegram response:", res.text)
    except Exception as e:
        print("Telegram error:", e)


# ---------------------------
# FETCH DATA
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


# ---------------------------
# CHANGE (SAFE)
# ---------------------------
def change(df):
    if df is None:
        return None, None

    try:
        close = df["Close"]
        last = float(close.iloc[-1])
        prev = float(close.iloc[-2])

        pct = round((last / prev - 1) * 100, 2)
        pts = int(round(last - prev, 0))

        return pct, pts
    except Exception as e:
        print("Change error:", e)
        return None, None


# ---------------------------
# LEVELS (PDH / PDL / Pivot)
# ---------------------------
def levels(df):
    if df is None:
        return None, None, None

    try:
        high = float(df["High"].iloc[-2])
        low = float(df["Low"].iloc[-2])
        close = float(df["Close"].iloc[-2])

        pivot = (high + low + close) / 3

        return int(high), int(low), int(round(pivot, 0))
    except Exception as e:
        print("Levels error:", e)
        return None, None, None


# ---------------------------
# BREAKOUT LOGIC
# ---------------------------
def breakout_signal(pdh, pdl, current):
    if pdh is None or pdl is None or current is None:
        return "NA"

    if current > pdh:
        return "Above PDH → Buy strength"
    elif current < pdl:
        return "Below PDL → Sell weakness"
    else:
        return "Inside range → No trade"


# ---------------------------
# MARKET CONDITION FILTER
# ---------------------------
def market_condition(pct):
    if pct is None:
        return "UNKNOWN"

    if abs(pct) < 0.5:
        return "RANGE → Avoid trades"
    elif abs(pct) > 1.0:
        return "EXTENDED → Avoid chasing"
    else:
        return "NORMAL → Trades allowed"


# ---------------------------
# FORMAT
# ---------------------------
def fmt(pct, pts):
    if pct is None:
        return "NA"
    sign = "+" if pts > 0 else ""
    return f"{sign}{pts} ({pct}%)"


# ---------------------------
# INDIA REPORT
# ---------------------------
def india():

    df_n = fetch("^NSEI")
    df_bn = fetch("^NSEBANK")
    df_s = fetch("^BSESN")

    n = change(df_n)
    bn = change(df_bn)
    s = change(df_s)

    pdh, pdl, pivot = levels(df_n)

    # Current price
    current_price = None
    if df_n is not None:
        try:
            current_price = int(float(df_n["Close"].iloc[-1]))
        except:
            current_price = None

    signal = breakout_signal(pdh, pdl, current_price)

    # Market condition
    condition = market_condition(n[0])

    crude = change(fetch("CL=F"))
    dxy = change(fetch("DX-Y.NYB"))

    # SAFE BIAS
    if n[0] is None:
        bias = "UNKNOWN"
    elif float(n[0]) < 0:
        bias = "BEARISH"
    else:
        bias = "BULLISH"

    msg = f"""🇮🇳 INDIA MARKET OUTLOOK

NIFTY: {fmt(*n)}
BANKNIFTY: {fmt(*bn)}
SENSEX: {fmt(*s)}

📍 Levels (NIFTY)
PDH: {pdh}
PDL: {pdl}
Pivot: {pivot}

⚡ Breakout:
{signal}

🧠 Market Condition:
{condition}

🌍 Macro:
Crude: {fmt(*crude)}
Dollar: {fmt(*dxy)}

📉 Bias: {bias}
Plan: {"Sell on rise" if bias=="BEARISH" else "Buy dips"}
"""

    return msg


# ---------------------------
# US REPORT
# ---------------------------
def us():

    dow = change(fetch("^DJI"))
    nasdaq = change(fetch("^IXIC"))
    spx = change(fetch("^GSPC"))

    crude = change(fetch("CL=F"))
    btc = change(fetch("BTC-USD"))

    condition = market_condition(nasdaq[0])

    if nasdaq[0] is None:
        bias = "UNKNOWN"
    elif float(nasdaq[0]) < 0:
        bias = "BEARISH"
    else:
        bias = "BULLISH"

    msg = f"""🌙 US MARKET PREP

DOW: {fmt(*dow)}
NASDAQ: {fmt(*nasdaq)}
SPX: {fmt(*spx)}

🧠 Market Condition:
{condition}

🌍 Macro:
Crude: {fmt(*crude)}
BTC: {fmt(*btc)}

📉 Bias: {bias}
Plan: {"Cautious / sell rallies" if bias=="BEARISH" else "Buy dips"}
"""

    return msg


# ---------------------------
# MAIN ROUTER
# ---------------------------
def main():
    now = datetime.now(IST)
    hour = now.hour

    print(f"Current IST time: {now}")

    if hour == 8:
        print("Running India report")
        send(india())

    elif hour in [18, 19]:
        print("Running US report")
        send(us())

    else:
        print("Manual run → sending India report")
        send(india())


# ---------------------------
# ENTRY
# ---------------------------
if __name__ == "__main__":
    main()
