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
# TRADE SETUP
# ---------------------------
def trade_setup(cond, pdh, pdl, pivot, current):
    if None in [pdh, pdl, pivot, current]:
        return "Data insufficient"

    if cond == "RANGE":
        return "No trade → Sideways market"

    if cond == "EXTENDED":
        if current < pdl:
            return f"Wait for pullback near Pivot ({pivot}) to SELL"
        elif current > pdh:
            return f"Wait for pullback near Pivot ({pivot}) to BUY"
        else:
            return "Wait → No clear setup"

    if cond == "NORMAL":
        if current > pdh:
            return "Buy breakout above PDH"
        elif current < pdl:
            return "Sell breakdown below PDL"
        else:
            return "Inside range → No trade"

    return "No setup"


# ---------------------------
# SCORE MODEL
# ---------------------------
def score_model(n_pct, vix_pct, crude_pct, usd_pct):

    score = 0

    # NIFTY trend
    if n_pct is not None:
        score += 0.4 if n_pct > 0 else -0.4

    # VIX (inverse)
    if vix_pct is not None:
        score += -0.2 if vix_pct > 0 else 0.2

    # Crude
    if crude_pct is not None:
        score += -0.2 if crude_pct > 0 else 0.2

    # USD
    if usd_pct is not None:
        score += -0.2 if usd_pct > 0 else 0.2

    # Bias
    if score > 0.3:
        bias = "BULLISH"
    elif score < -0.3:
        bias = "BEARISH"
    else:
        bias = "NEUTRAL"

    # Confidence
    if abs(score) > 0.6:
        conf = "HIGH"
    elif abs(score) > 0.3:
        conf = "MEDIUM"
    else:
        conf = "LOW"

    return round(score, 2), bias, conf


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

    current = int(float(df_n["Close"].iloc[-1])) if df_n is not None else None

    condition = market_condition(n[0])
    setup = trade_setup(condition, pdh, pdl, pivot, current)

    crude = change(fetch("CL=F"))
    usd = change(fetch("DX-Y.NYB"))
    vix = change(fetch("^INDIAVIX"))

    score, sbias, conf = score_model(n[0], vix[0], crude[0], usd[0])

    bias = "BEARISH" if n[0] and n[0] < 0 else "BULLISH"

    return f"""🇮🇳 INDIA MARKET OUTLOOK

NIFTY: {fmt(*n)}
BANKNIFTY: {fmt(*bn)}
SENSEX: {fmt(*s)}

📍 Levels
PDH: {pdh} | PDL: {pdl} | Pivot: {pivot}

🧠 Condition: {condition}

🎯 Setup:
{setup}

📊 Score Model
Score: {score}
Bias: {sbias}
Confidence: {conf}

🌍 Macro:
Crude: {fmt(*crude)}
USD: {fmt(*usd)}
VIX: {fmt(*vix)}

📉 Price Bias: {bias}
"""


# ---------------------------
# MAIN
# ---------------------------
def main():
    now = datetime.now(IST)
    if now.hour == 8:
        send(india())
    else:
        send(india())


if __name__ == "__main__":
    main()
