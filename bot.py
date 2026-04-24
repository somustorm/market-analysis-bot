import requests
import os
import yfinance as yf
import math
import pandas as pd

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# -----------------------------
# TELEGRAM
# -----------------------------
def send(msg):
    if not TOKEN or not CHAT_ID:
        print("❌ Missing TELEGRAM_TOKEN or CHAT_ID")
        return

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    res = requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg
    })
    print(res.text)


# -----------------------------
# YFINANCE FETCH
# -----------------------------
def fetch_yf(symbol):
    try:
        df = yf.download(symbol, period="5d", interval="1d", progress=False)
        if df is None or df.empty or len(df) < 2:
            return None
        return df
    except Exception as e:
        print(f"{symbol} fetch error:", e)
        return None


# -----------------------------
# FII DATA (PROXY)
# -----------------------------
def fetch_fii_data():
    try:
        url = "https://www.nseindia.com/api/fiidiiTradeReact"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        }

        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers)

        res = session.get(url, headers=headers)
        data = res.json()

        df = pd.DataFrame(data["data"])
        latest = df.iloc[0]

        fii_net = float(latest["fiiIdxFutBuyVal"]) - float(latest["fiiIdxFutSellVal"])
        return fii_net

    except Exception as e:
        print("FII fetch error:", e)
        return None


# -----------------------------
# SAFE CHANGE
# -----------------------------
def safe_change(df):
    try:
        val = float(df["Close"].pct_change().iloc[-1])
        if math.isnan(val):
            return None
        return val
    except:
        return None


# -----------------------------
# DATA (FIXED - NO OR LOGIC)
# -----------------------------
def get_data():
    nifty = fetch_yf("^NSEI")

    if nifty is None:
        print("⚠️ Falling back to NIFTYBEES")
        nifty = fetch_yf("NIFTYBEES.NS")

    crude = fetch_yf("CL=F")
    btc = fetch_yf("BTC-USD")
    vix = fetch_yf("^INDIAVIX")

    fii = fetch_fii_data()

    return nifty, crude, btc, vix, fii


# -----------------------------
# ENGINE
# -----------------------------
def analyze(nifty, crude, btc, vix, fii):
    score = 0

    n = safe_change(nifty)
    c = safe_change(crude)
    b = safe_change(btc)
    v = safe_change(vix)

    if None in [n, c, b, v] or fii is None:
        return None, n, c, b, v, fii, False

    # NIFTY
    score += 1 if n > 0 else -1

    # CRUDE
    score += -1 if c > 0 else 1

    # BTC
    score += 1 if b > 0 else -1

    # VIX
    if v > 0.05:
        score -= 2
    elif v < -0.03:
        score += 1

    # FII
    if fii > 0:
        score += 2
    else:
        score -= 2

    crash = (v > 0.08 and fii < 0 and n < 0)

    return score, n, c, b, v, fii, crash


# -----------------------------
# FORMAT
# -----------------------------
def fmt(x):
    return f"{x:.2%}" if isinstance(x, float) else "NA"


def fmt_fii(x):
    return f"{x/1e7:.1f} Cr" if isinstance(x, float) else "NA"


# -----------------------------
# REPORT
# -----------------------------
def generate_report():
    nifty, crude, btc, vix, fii = get_data()

    if any(x is None for x in [nifty, crude, btc, vix]):
        return "⚠️ Data fetch failed"

    result = analyze(nifty, crude, btc, vix, fii)

    if result[0] is None:
        return f"""⚠️ Data Issue

NIFTY: {result[1]}
CRUDE: {result[2]}
BTC: {result[3]}
VIX: {result[4]}

❌ Skipping signal
"""

    score, n, c, b, v, fii, crash = result

    bias = "BULLISH" if score > 0 else "BEARISH"

    msg = f"""📊 Market Engine

NIFTY: {fmt(n)}
CRUDE: {fmt(c)}
BTC: {fmt(b)}
VIX: {fmt(v)}

FII: {fmt_fii(fii)}

Bias: {bias}
Score: {score}
"""

    if crash:
        msg += "\n🚨 CRASH RISK HIGH"

    return msg


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    report = generate_report()
    send(report)
