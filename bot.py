import requests
import os
import yfinance as yf
import math
import pandas as pd
import time
from datetime import datetime

VERSION = "v2.1-STABLE-NSE"

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# =============================
# TELEGRAM
# =============================
def send(msg):
    if not TOKEN or not CHAT_ID:
        print("❌ Missing TELEGRAM_TOKEN or CHAT_ID")
        return
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except Exception as e:
        print("Telegram Error:", e)

# =============================
# FETCH YFINANCE
# =============================
def fetch(symbol):
    try:
        df = yf.download(symbol, period="5d", interval="1d", progress=False)
        if df is None or df.empty or len(df) < 2:
            return None
        return df
    except:
        return None

# =============================
# SAFE CHANGE
# =============================
def get_change(df):
    if df is None:
        return None, None, None
    try:
        close = df["Close"]
        pct = float(close.pct_change().iloc[-1])
        pts = float(close.iloc[-1] - close.iloc[-2])
        price = float(close.iloc[-1])
        if math.isnan(pct):
            return None, None, None
        return pct, pts, price
    except:
        return None, None, None

# =============================
# PIVOT
# =============================
def calculate_pivot(df):
    try:
        h = float(df["High"].iloc[-2])
        l = float(df["Low"].iloc[-2])
        c = float(df["Close"].iloc[-2])
        return (h + l + c) / 3
    except:
        return None

# =============================
# NSE SESSION HELPER
# =============================
def get_nse_session():
    session = requests.Session()
    headers = {"User-Agent": "Mozilla/5.0"}
    session.get("https://www.nseindia.com", headers=headers, timeout=5)
    return session, headers

# =============================
# OPTION CHAIN (RETRY)
# =============================
def fetch_option_chain():
    for attempt in range(3):
        try:
            session, headers = get_nse_session()
            url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
            res = session.get(url, headers=headers, timeout=5)

            if res.status_code != 200:
                time.sleep(1)
                continue

            data = res.json()

            ce_oi = []
            pe_oi = []

            for item in data["records"]["data"]:
                if "CE" in item:
                    ce_oi.append(item["CE"]["openInterest"])
                if "PE" in item:
                    pe_oi.append(item["PE"]["openInterest"])

            if not ce_oi or not pe_oi:
                return None, None, None

            total_call = sum(ce_oi)
            total_put = sum(pe_oi)

            pcr = total_put / total_call if total_call else None

            return max(ce_oi), max(pe_oi), pcr

        except Exception as e:
            print("Option chain error:", e)
            time.sleep(1)

    return None, None, None

# =============================
# FII (RETRY)
# =============================
def fetch_fii():
    for attempt in range(3):
        try:
            session, headers = get_nse_session()
            url = "https://www.nseindia.com/api/fiidiiTradeReact"
            res = session.get(url, headers=headers, timeout=5)

            if res.status_code != 200:
                time.sleep(1)
                continue

            data = res.json()
            df = pd.DataFrame(data["data"])

            latest = df.iloc[0]

            buy = float(latest["fiiIdxFutBuyVal"])
            sell = float(latest["fiiIdxFutSellVal"])

            return buy - sell

        except Exception as e:
            print("FII error:", e)
            time.sleep(1)

    return None

# =============================
# FORMAT
# =============================
def fmt(pct, pts):
    if pct is None or pts is None:
        return "NA"
    pts = 0 if abs(pts) < 0.5 else pts
    sign = "+" if pts > 0 else ""
    return f"{sign}{pts:.0f} ({pct*100:.2f}%)"

def fmt_pct(x):
    if x is None:
        return "NA"
    return f"{x*100:.2f}%"

# =============================
# SCORING
# =============================
def core_scoring(vix, fii, pcr, price, pivot):
    score = 0
    used = 0

    if vix is not None:
        score += -0.30 if vix > 0 else 0.30
        used += 1

    if fii is not None:
        score += -0.30 if fii < 0 else 0.30
        used += 1

    if pcr is not None:
        score += -0.25 if pcr < 1 else 0.25
        used += 1

    if price is not None and pivot is not None:
        score += -0.15 if price < pivot else 0.15
        used += 1

    return round(score, 2), used

# =============================
# MAIN
# =============================
def generate_report():

    nifty = fetch("^NSEI")
    banknifty = fetch("^NSEBANK")
    sensex = fetch("^BSESN")
    vix_df = fetch("^INDIAVIX")
    crude = fetch("CL=F")
    btc = fetch("BTC-USD")

    n_pct, n_pts, n_price = get_change(nifty)
    bn_pct, bn_pts, _ = get_change(banknifty)
    s_pct, s_pts, _ = get_change(sensex)
    vix_pct, _, _ = get_change(vix_df)
    crude_pct, crude_pts, _ = get_change(crude)
    btc_pct, btc_pts, _ = get_change(btc)

    # VIX FILTER
    if vix_pct is not None and abs(vix_pct) > 0.04:
        vix_pct = None

    # NSE DATA
    max_call, max_put, pcr = fetch_option_chain()
    fii = fetch_fii()

    pivot = calculate_pivot(nifty)

    score, used = core_scoring(vix_pct, fii, pcr, n_price, pivot)

    if abs(score) > 0.6:
        confidence = "HIGH"
    elif abs(score) > 0.3:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    bias = "BULLISH" if score > 0 else "BEARISH"

    msg = f"""
📊 MARKET UPDATE

NIFTY: {fmt(n_pct, n_pts)}
BANKNIFTY: {fmt(bn_pct, bn_pts)}
SENSEX: {fmt(s_pct, s_pts)}

CRUDE: {fmt(crude_pct, crude_pts)}
BTC: {fmt(btc_pct, btc_pts)}
VIX: {fmt_pct(vix_pct)}

----------------------

📊 OPTION CHAIN
PCR: {round(pcr,2) if pcr else "NA"}

----------------------

🧠 CORE ENGINE

Score: {score}
Bias: {bias}
Confidence: {confidence}
Signals Used: {used}/4

----------------------

⚙️ SYSTEM

Version: {VERSION}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""

    return msg

# =============================
# RUN
# =============================
if __name__ == "__main__":
    send(generate_report())
