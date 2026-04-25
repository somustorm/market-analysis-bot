import requests
import os
import yfinance as yf
import math

# =============================
# CONFIG
# =============================
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
        res = requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
        print(res.text)
    except Exception as e:
        print("Telegram Error:", e)


# =============================
# FETCH DATA (SAFE)
# =============================
def fetch(symbol):
    try:
        df = yf.download(symbol, period="5d", interval="1d", progress=False)
        if df is None or df.empty or len(df) < 2:
            print(f"⚠️ {symbol} insufficient data")
            return None
        return df
    except Exception as e:
        print(f"{symbol} fetch error:", e)
        return None


# =============================
# SAFE CHANGE CALCULATION
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
    except Exception as e:
        print("Change calc error:", e)
        return None, None, None


# =============================
# FORMATTER (NO -0 BUG)
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
# CORE SCORING (ONLY 4 SIGNALS)
# =============================
def core_scoring(vix, fii, pcr, price, pivot):
    score = 0

    try:
        # VIX
        if vix is not None:
            score += -0.30 if vix > 0 else 0.30

        # FII (placeholder)
        if fii is not None:
            score += -0.30 if fii < 0 else 0.30

        # PCR
        if pcr is not None:
            score += -0.25 if pcr < 1 else 0.25

        # Structure
        if price is not None and pivot is not None:
            score += -0.15 if price < pivot else 0.15

        return round(score, 2)

    except Exception as e:
        print("Scoring error:", e)
        return 0


# =============================
# MAIN ENGINE
# =============================
def generate_report():

    # ---- FETCH ----
    nifty = fetch("^NSEI")
    banknifty = fetch("^NSEBANK")
    sensex = fetch("^BSESN")
    vix_df = fetch("^INDIAVIX")
    crude = fetch("CL=F")
    btc = fetch("BTC-USD")

    # ---- CHANGES ----
    n_pct, n_pts, n_price = get_change(nifty)
    bn_pct, bn_pts, _ = get_change(banknifty)
    s_pct, s_pts, _ = get_change(sensex)
    vix_pct, _, _ = get_change(vix_df)
    crude_pct, crude_pts, _ = get_change(crude)
    btc_pct, btc_pts, _ = get_change(btc)

    # ---- PLACEHOLDERS ----
    fii = -1        # Replace later
    pcr = 0.85      # Replace later

    # ---- SIMPLE PIVOT ----
    pivot = n_price  # temporary (safe)

    # ---- SCORE ----
    score = core_scoring(vix_pct, fii, pcr, n_price, pivot)

    bias = "BULLISH" if score > 0 else "BEARISH"
    confidence = "HIGH" if abs(score) > 0.6 else "MEDIUM"

    # ---- MESSAGE ----
    msg = f"""
📊 MARKET UPDATE

NIFTY: {fmt(n_pct, n_pts)}
BANKNIFTY: {fmt(bn_pct, bn_pts)}
SENSEX: {fmt(s_pct, s_pts)}

CRUDE: {fmt(crude_pct, crude_pts)}
BTC: {fmt(btc_pct, btc_pts)}
VIX: {fmt_pct(vix_pct)}

----------------------

🧠 CORE ENGINE

Score: {score}
Bias: {bias}
Confidence: {confidence}

----------------------

⚠️ TEST MODE
- FII, PCR, Pivot are placeholders
- Using Yahoo data

"""

    return msg


# =============================
# RUN
# =============================
if __name__ == "__main__":
    report = generate_report()
    send(report)
