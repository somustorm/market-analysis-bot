import requests
import os
import yfinance as yf
from datetime import datetime, timezone, timedelta

# ===========================
# CONFIG
# ===========================
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

IST = timezone(timedelta(hours=5, minutes=30))


# ===========================
# TELEGRAM
# ===========================
def send(msg):
    print("Sending message...")

    if not TOKEN or not CHAT_ID:
        print("❌ Missing TELEGRAM_TOKEN or CHAT_ID")
        return

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        res = requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
        print("Telegram response:", res.text)
    except Exception as e:
        print("Telegram error:", e)


# ===========================
# DATA HELPERS
# ===========================
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
        c = df["Close"]
        last = float(c.iloc[-1])
        prev = float(c.iloc[-2])
        pct = round((last / prev - 1) * 100, 2)
        pts = int(round(last - prev, 0))
        return pct, pts
    except:
        return None, None


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


def fmt(pct, pts):
    if pct is None or pts is None:
        return "NA"
    sign = "+" if pts > 0 else ""
    return f"{sign}{pts} ({pct}%)"


# ===========================
# INDIA (DECISION GRADE)
# ===========================
def india():

    df = fetch("^NSEI")
    pct, pts = change(df)
    pdh, pdl, pivot = levels(df)

    bias = "BEARISH" if pct and pct < 0 else "BULLISH"
    condition = "EXTENDED" if pct and abs(pct) > 1 else "NORMAL"

    return f"""🇮🇳 INDIA MARKET OUTLOOK

📉 NIFTY: {fmt(pct, pts)}

PDH: {pdh}  
PDL: {pdl}  
Pivot: {pivot}

🧠 Condition: {condition}  
📊 Bias: {bias}

--------------------------------------------------

🎯 EXECUTION PLAN

🔥 A-SETUP
{"Sell near PDH (rejection)" if bias=="BEARISH" else "Buy near PDL (support)"}

🟡 B-SETUP
{"Sell near Pivot if weakness" if bias=="BEARISH" else "Buy near Pivot if strength"}

❌ C-SETUP
{"Avoid selling at lows" if bias=="BEARISH" else "Avoid buying at highs"}

🛑 Stop Loss:
{"Above PDH" if bias=="BEARISH" else "Below PDL"}

📉 Invalidation:
{"Break above PDH" if bias=="BEARISH" else "Break below PDL"}

--------------------------------------------------

🎯 FINAL CALL

Market: {bias} + {condition}

🔥 Best Trade:
{"Sell near PDH" if bias=="BEARISH" else "Buy near PDL"}

⚠️ Avoid:
{"Chasing downside" if bias=="BEARISH" else "Chasing upside"}

📊 Confidence:
{"Medium (extended move)" if condition=="EXTENDED" else "Moderate"}

🧠 Rule:
Wait for level → Do NOT chase
"""


# ===========================
# US + BTC (DECISION GRADE)
# ===========================
def us():

    dow = change(fetch("^DJI"))
    nasdaq = change(fetch("^IXIC"))
    spx = change(fetch("^GSPC"))

    btc_df = fetch("BTC-USD")
    btc_pct, btc_pts = change(btc_df)
    pdh, pdl, pivot = levels(btc_df)

    trend = "BULLISH" if btc_pct and btc_pct > 0 else "BEARISH"

    return f"""🌙 US MARKET PREP (7:00 PM IST)

🌍 Global Setup
Asia: Mixed  
Europe: Flat  

👉 Interpretation: Mixed global tone

--------------------------------------------------

🇺🇸 US MARKET STRUCTURE

DOW: {fmt(*dow)}  
NASDAQ: {fmt(*nasdaq)}  
S&P 500: {fmt(*spx)}  

🧠 Market Condition: MIXED  

--------------------------------------------------

🪙 BTC STRUCTURE

Move: {fmt(btc_pct, btc_pts)}

PDH: {pdh}  
PDL: {pdl}  
Pivot: {pivot}

Trend: {trend}

--------------------------------------------------

🎯 BTC EXECUTION PLAN

🟢 A-SETUP
Buy above {pdh}

🔴 A-SETUP
Sell below {pdl}

🟡 B-SETUP
Trade near Pivot ({pivot}) with confirmation

❌ C-SETUP
Avoid mid-range trading

🛑 Stop Loss:
Opposite side of breakout

📉 Invalidation:
Fake breakout

--------------------------------------------------

🎯 FINAL CALL

US Market: MIXED → No strong edge  
BTC Bias: {trend}

🔥 Best Opportunity:
BTC breakout trade  

⚠️ Avoid:
Mid-range trading  

📊 Confidence:
Medium (event-driven)

🧠 Rule:
React to levels → Do NOT predict
"""


# ===========================
# MAIN (STABLE)
# ===========================
def main():

    print("=== BOT STARTED ===")

    try:
        now = datetime.now(IST)
        print("Time IST:", now)

        # Send both (stable mode)
        india_msg = india()
        print(india_msg)
        send(india_msg)

        us_msg = us()
        print(us_msg)
        send(us_msg)

    except Exception as e:
        print("ERROR:", e)


# ===========================
# ENTRY
# ===========================
if __name__ == "__main__":
    main()
