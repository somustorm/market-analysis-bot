import requests
import os
import yfinance as yf
import pandas as pd
from datetime import datetime, timezone, timedelta

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

IST = timezone(timedelta(hours=5, minutes=30))

# ---------------------------
# USER CONFIG (EDIT THIS)
# ---------------------------
CAPITAL = 100000   # your capital
RISK_PERCENT = 0.02  # 2% risk


# ---------------------------
# TELEGRAM
# ---------------------------
def send(msg):
    if not TOKEN or not CHAT_ID:
        print("Missing Telegram config")
        return
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except Exception as e:
        print("Telegram error:", e)


# ---------------------------
# FETCH
# ---------------------------
def fetch(symbol):
    try:
        df = yf.download(symbol, period="2d", interval="1d", progress=False)
        if df is None or df.empty or len(df) < 2:
            return None
        return df
    except:
        return None


# ---------------------------
# CHANGE
# ---------------------------
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


# ---------------------------
# LEVELS
# ---------------------------
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


# ---------------------------
# MARKET CONDITION
# ---------------------------
def market_condition(pct):
    if pct is None:
        return "UNKNOWN"
    if abs(pct) < 0.5:
        return "RANGE"
    elif abs(pct) > 1:
        return "EXTENDED"
    else:
        return "NORMAL"


# ---------------------------
# SCORE MODEL
# ---------------------------
def score_model(n_pct):
    if n_pct is None:
        return 0, "UNKNOWN", "NO DATA"

    if abs(n_pct) > 1:
        bias = "BULLISH" if n_pct > 0 else "BEARISH"
        return n_pct, bias, f"PRICE DOMINANT ({bias})"

    return n_pct, "NEUTRAL", "LOW CONVICTION"


# ---------------------------
# EXECUTION (A/B/C)
# ---------------------------
def execution_plan(condition, bias, pdh, pdl, pivot):

    if condition == "RANGE":
        return "NO TRADE", None, None

    if bias == "BEARISH":
        entry = pivot
        sl = pdh
        return "Sell on pullback", entry, sl

    if bias == "BULLISH":
        entry = pivot
        sl = pdl
        return "Buy on dip", entry, sl

    return "No plan", None, None


# ---------------------------
# POSITION SIZING
# ---------------------------
def position_size(entry, sl):
    if entry is None or sl is None:
        return None, None

    risk_amount = CAPITAL * RISK_PERCENT
    sl_distance = abs(entry - sl)

    if sl_distance == 0:
        return None, None

    qty = int(risk_amount / sl_distance)

    return qty, int(risk_amount)


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
    n = change(df_n)

    pdh, pdl, pivot = levels(df_n)

    condition = market_condition(n[0])
    score, bias, interp = score_model(n[0])

    plan, entry, sl = execution_plan(condition, bias, pdh, pdl, pivot)

    qty, risk_amt = position_size(entry, sl)

    return f"""🇮🇳 INDIA MARKET OUTLOOK

NIFTY: {fmt(*n)}

📍 Levels
PDH: {pdh} | PDL: {pdl} | Pivot: {pivot}

🧠 Condition: {condition}

📊 Bias: {bias}
📌 {interp}

🎯 Plan:
{plan}

💰 Risk Management:
Capital: ₹{CAPITAL}
Risk/Trade: ₹{risk_amt}
Position Size: {qty if qty else "NA"}

SL: {sl}
"""


# ---------------------------
# MAIN
# ---------------------------
def main():
    send(india())


if __name__ == "__main__":
    main()
