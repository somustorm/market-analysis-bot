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
# FETCH
# -----------------------------
def fetch_yf(symbol):
    try:
        df = yf.download(symbol, period="5d", interval="1d", progress=False)
        if df is None or df.empty or len(df) < 2:
            return None
        return df
    except Exception as e:
        print(f"{symbol} error:", e)
        return None


# -----------------------------
# SAFE FALLBACK (CRITICAL FIX)
# -----------------------------
def fetch_with_fallback(primary, fallback=None):
    data = fetch_yf(primary)

    if data is None and fallback:
        print(f"⚠️ Fallback: {primary} → {fallback}")
        data = fetch_yf(fallback)

    return data


# -----------------------------
# FII
# -----------------------------
def fetch_fii_data():
    try:
        url = "https://www.nseindia.com/api/fiidiiTradeReact"
        headers = {"User-Agent": "Mozilla/5.0"}

        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers)

        res = session.get(url, headers=headers)
        data = res.json()

        df = pd.DataFrame(data["data"])
        latest = df.iloc[0]

        return float(latest["fiiIdxFutBuyVal"]) - float(latest["fiiIdxFutSellVal"])
    except Exception as e:
        print("FII error:", e)
        return None


# -----------------------------
# CHANGE + POINTS
# -----------------------------
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


# -----------------------------
# DATA
# -----------------------------
def get_data():
    nifty = fetch_with_fallback("^NSEI", "NIFTYBEES.NS")
    banknifty = fetch_with_fallback("^NSEBANK")
    sensex = fetch_with_fallback("^BSESN", "SENSEXBEES.NS")

    crude = fetch_with_fallback("CL=F")
    btc = fetch_with_fallback("BTC-USD")
    vix = fetch_with_fallback("^INDIAVIX")

    dow = fetch_with_fallback("^DJI")
    nasdaq = fetch_with_fallback("^IXIC")

    fii = fetch_fii_data()

    return nifty, banknifty, sensex, crude, btc, vix, dow, nasdaq, fii


# -----------------------------
# ENGINE
# -----------------------------
def analyze(data):
    (
        nifty, banknifty, sensex,
        crude, btc, vix,
        dow, nasdaq, fii
    ) = data

    score = 0

    n, n_pts = get_change(nifty)
    bn, bn_pts = get_change(banknifty)
    s, s_pts = get_change(sensex)
    c, c_pts = get_change(crude)
    b, b_pts = get_change(btc)
    v, v_pts = get_change(vix)
    d, d_pts = get_change(dow)
    nq, nq_pts = get_change(nasdaq)

    if None in [n, bn, s, c, b, v]:
        return None

    # Core scoring
    score += 1 if n > 0 else -1
    score += 1 if bn > 0 else -1
    score += 1 if s > 0 else -1

    score += -1 if c > 0 else 1
    score += 1 if b > 0 else -1

    if v > 0.05:
        score -= 2
    elif v < -0.03:
        score += 1

    if d is not None:
        score += 1 if d > 0 else -1

    if nq is not None:
        score += 1 if nq > 0 else -1

    if fii is not None:
        score += 2 if fii > 0 else -2

    crash = (v is not None and v > 0.08 and n < 0)

    return score, (n, n_pts), (bn, bn_pts), (s, s_pts), \
           (c, c_pts), (b, b_pts), (v, v_pts), \
           (d, d_pts), (nq, nq_pts), fii, crash


# -----------------------------
# FORMAT
# -----------------------------
def fmt(pct, pts):
    if pct is None or pts is None:
        return "NA"
    sign = "+" if pts > 0 else ""
    return f"{sign}{pts:.0f} ({pct*100:.2f}%)"


def fmt_fii(x):
    return f"{x/1e7:.1f} Cr" if isinstance(x, float) else "NA"


# -----------------------------
# REPORT
# -----------------------------
def generate_report():
    data = get_data()

    result = analyze(data)
    if result is None:
        return "⚠️ Data issue"

    score, n, bn, s, c, b, v, d, nq, fii, crash = result

    bias = "BULLISH" if score > 0 else "BEARISH"

    msg = f"""📊 Market Engine

NIFTY: {fmt(*n)}
BANKNIFTY: {fmt(*bn)}
SENSEX: {fmt(*s)}

CRUDE: {fmt(*c)}
BTC: {fmt(*b)}
VIX: {fmt(*v)}

DOW: {fmt(*d)}
NASDAQ: {fmt(*nq)}

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
    send(generate_report())
