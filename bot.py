import requests
import os
import yfinance as yf
import pandas as pd
import time
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
# NSE SESSION
# ---------------------------
def nse_session():
    session = requests.Session()
    headers = {"User-Agent": "Mozilla/5.0"}
    session.get("https://www.nseindia.com", headers=headers, timeout=5)
    return session, headers


# ---------------------------
# FII
# ---------------------------
def fetch_fii():
    try:
        session, headers = nse_session()
        url = "https://www.nseindia.com/api/fiidiiTradeReact"
        res = session.get(url, headers=headers, timeout=5)
        data = res.json()
        df = pd.DataFrame(data["data"])
        latest = df.iloc[0]
        return float(latest["fiiIdxFutBuyVal"]) - float(latest["fiiIdxFutSellVal"])
    except:
        return None


# ---------------------------
# PCR
# ---------------------------
def fetch_pcr():
    try:
        session, headers = nse_session()
        url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
        res = session.get(url, headers=headers, timeout=5)
        data = res.json()

        ce, pe = [], []
        for item in data["records"]["data"]:
            if "CE" in item:
                ce.append(item["CE"]["openInterest"])
            if "PE" in item:
                pe.append(item["PE"]["openInterest"])

        return round(sum(pe) / sum(ce), 2)
    except:
        return None


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
def score_model(n_pct, vix_pct, crude_pct, usd_pct, fii, pcr):

    score = 0

    if n_pct is not None:
        score += 0.6 if n_pct > 0 else -0.6

    if vix_pct is not None:
        score += -0.15 if vix_pct > 0 else 0.15

    if crude_pct is not None:
        score += -0.1 if crude_pct > 0 else 0.1

    if usd_pct is not None:
        score += -0.05 if usd_pct > 0 else 0.05

    if fii is not None:
        score += 0.05 if fii > 0 else -0.05

    if pcr is not None:
        score += 0.05 if pcr > 1 else -0.05

    if n_pct is not None and abs(n_pct) > 1:
        bias = "BULLISH" if n_pct > 0 else "BEARISH"
        interp = f"PRICE DOMINANT ({bias})"
    else:
        if score > 0.3:
            bias = "BULLISH"
            interp = "BULLISH (> +0.3)"
        elif score < -0.3:
            bias = "BEARISH"
            interp = "BEARISH (< -0.3)"
        else:
            bias = "NEUTRAL"
            interp = "NEUTRAL"

    return round(score, 2), bias, interp


# ---------------------------
# EXECUTION (A/B/C SETUPS)
# ---------------------------
def execution_plan(condition, bias, pdh, pdl, pivot):

    if None in [pdh, pdl, pivot]:
        return "No plan (missing data)"

    if condition == "RANGE":
        return "NO TRADE → Sideways market"

    if bias == "BEARISH":

        if condition == "EXTENDED":
            return f"""A-SETUP (High Probability):
Sell near PDH ({pdh}) on rejection

B-SETUP (Moderate):
Sell near Pivot ({pivot}) if price stalls

C-SETUP (Avoid):
Selling below current price (market extended)

STOP LOSS:
Above {pdh}

INVALIDATION:
Sustained move above PDH

NOTE:
Wait for price to come to you — do NOT chase"""

        else:
            return f"""A-SETUP:
Sell below PDL ({pdl})

STOP LOSS:
Above Pivot ({pivot})

INVALIDATION:
Move above pivot"""

    if bias == "BULLISH":

        if condition == "EXTENDED":
            return f"""A-SETUP (High Probability):
Buy near PDL ({pdl}) on support

B-SETUP (Moderate):
Buy near Pivot ({pivot})

C-SETUP (Avoid):
Buying at highs

STOP LOSS:
Below {pdl}

INVALIDATION:
Break below PDL"""

        else:
            return f"""A-SETUP:
Buy above PDH ({pdh})

STOP LOSS:
Below Pivot ({pivot})

INVALIDATION:
Move below pivot"""

    return "No clear plan"


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

    crude = change(fetch("CL=F"))
    usd = change(fetch("DX-Y.NYB"))
    vix = change(fetch("^INDIAVIX"))

    fii = fetch_fii()
    pcr = fetch_pcr()

    score, bias, interp = score_model(
        n[0], vix[0], crude[0], usd[0], fii, pcr
    )

    condition = market_condition(n[0])

    plan = execution_plan(condition, bias, pdh, pdl, pivot)

    return f"""🇮🇳 INDIA MARKET OUTLOOK

NIFTY: {fmt(*n)}

📍 Levels
PDH: {pdh} | PDL: {pdl} | Pivot: {pivot}

🧠 Condition: {condition}

📊 Score
Score: {score}
Bias: {bias}

📌 Interpretation:
{interp}

🎯 EXECUTION PLAN:
{plan}

🌍 Macro:
Crude: {fmt(*crude)}
USD: {fmt(*usd)}
VIX: {fmt(*vix)}

🏦 FII: {"{:.0f} Cr".format(fii/1e7) if fii else "NA"}
📊 PCR: {pcr if pcr else "NA"}
"""


# ---------------------------
# MAIN
# ---------------------------
def main():
    send(india())


if __name__ == "__main__":
    main()
