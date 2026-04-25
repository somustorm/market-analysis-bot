import requests
import os
import yfinance as yf
from datetime import datetime, timezone, timedelta

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

IST = timezone(timedelta(hours=5, minutes=30))

CAPITAL = 100000
RISK_PERCENT = 0.02


# ---------------------------
# TELEGRAM
# ---------------------------
def send(msg):
    if not TOKEN or not CHAT_ID:
        print("❌ Missing Telegram config")
        return

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        res = requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
        print("Telegram:", res.status_code)
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
    except Exception as e:
        print(f"{symbol} fetch error:", e)
        return None


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
    except:
        return None, None


def levels(df):
    if df is None:
        return None, None, None
    try:
        high = float(df["High"].iloc[-2])
        low = float(df["Low"].iloc[-2])
        close = float(df["Close"].iloc[-2])

        pivot = (high + low + close) / 3

        return int(high), int(low), int(round(pivot, 0))
    except:
        return None, None, None


def fmt(pct, pts):
    if pct is None or pts is None:
        return "NA"
    sign = "+" if pts > 0 else ""
    return f"{sign}{pts} ({pct}%)"


# ---------------------------
# POSITION SIZE
# ---------------------------
def position(entry, sl):
    if entry is None or sl is None:
        return None, None

    risk_amt = CAPITAL * RISK_PERCENT
    dist = abs(entry - sl)

    if dist == 0:
        return None, None

    qty = int(risk_amt / dist)

    return qty, int(risk_amt)


# ---------------------------
# INDIA REPORT
# ---------------------------
def india_report():

    df = fetch("^NSEI")
    n_pct, n_pts = change(df)
    pdh, pdl, pivot = levels(df)

    crude = change(fetch("CL=F"))
    vix = change(fetch("^INDIAVIX"))
    dxy = change(fetch("DX-Y.NYB"))

    condition = "EXTENDED" if n_pct and abs(n_pct) > 1 else "NORMAL"
    bias = "BEARISH" if n_pct and n_pct < 0 else "BULLISH"

    entry = pivot
    sl = pdh if bias == "BEARISH" else pdl
    qty, risk_amt = position(entry, sl)

    msg = f"""🇮🇳 INDIA MARKET OUTLOOK (8:45 AM IST)

🌍 Macro
DXY: {dxy[0] if dxy[0] else "NA"}%
VIX: {vix[0] if vix[0] else "NA"}%
Crude: {fmt(*crude)}

👉 Interpretation: {"Risk-OFF" if vix[0] and vix[0] > 0 else "Neutral"}

📉 Market Structure
NIFTY: {fmt(n_pct, n_pts)}
PDH: {pdh} | PDL: {pdl} | Pivot: {pivot}

🧠 Condition: {condition}
📊 Bias: {bias}

🎯 Execution
A: {"Sell near PDH" if bias=="BEARISH" else "Buy near PDL"}
B: {"Sell near Pivot" if bias=="BEARISH" else "Buy near Pivot"}
C: Avoid chasing

🛑 SL: {sl if sl else "NA"}

💰 Risk
Capital: ₹{CAPITAL}
Risk: ₹{risk_amt if risk_amt else "NA"}
Qty: {qty if qty else "NA"}

--------------------------------------------------
🎯 ACTION

Bias: {bias}
Strategy: {"Sell on rise" if bias=="BEARISH" else "Buy dips"}
Avoid: Chasing
"""

    return msg


# ---------------------------
# US REPORT
# ---------------------------
def us_report():

    dow = change(fetch("^DJI"))
    nasdaq = change(fetch("^IXIC"))
    spx = change(fetch("^GSPC"))

    btc_df = fetch("BTC-USD")
    btc_pct, btc_pts = change(btc_df)
    pdh, pdl, pivot = levels(btc_df)

    msg = f"""🌙 US MARKET PREP (7:00 PM IST)

🌍 Global Setup
Asia: Mixed
Europe: Flat

📊 US Market
DOW: {fmt(*dow)}
NASDAQ: {fmt(*nasdaq)}
SPX: {fmt(*spx)}

🧠 Condition: Mixed

--------------------------------------------------

🪙 BTC STRUCTURE

Move: {fmt(btc_pct, btc_pts)}

PDH: {pdh}
PDL: {pdl}
Pivot: {pivot}

--------------------------------------------------

🎯 BTC PLAN

Buy above {pdh if pdh else "NA"}
Sell below {pdl if pdl else "NA"}

Avoid mid-range trading

--------------------------------------------------

🎯 ACTION

US: Mixed
BTC: Range

Strategy:
Trade breakouts only
Avoid noise
"""

    return msg


# ---------------------------
# MAIN ROUTER
# ---------------------------
def main():

    now = datetime.now(IST)
    hour = now.hour
    minute = now.minute

    print(f"Time IST: {now}")

    # 8:45 AM window (8:40–8:50)
    if hour == 8 and 40 <= minute <= 50:
        print("Running INDIA report")
        send(india_report())

    # 7:00 PM window (18:55–19:10)
    elif hour == 19 and 0 <= minute <= 10:
        print("Running US report")
        send(us_report())

    else:
        print("Outside schedule window")


# ---------------------------
# ENTRY
# ---------------------------
if __name__ == "__main__":
    main()
