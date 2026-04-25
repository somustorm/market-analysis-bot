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
        print("Telegram:", res.text)
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
    except:
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
# INDIA (FULL SYSTEM)
# ===========================
def india():

    # INDEX DATA
    nifty = fetch("^NSEI")
    bank = fetch("^NSEBANK")
    sensex = fetch("^BSESN")

    n_pct, n_pts = change(nifty)
    b_pct, b_pts = change(bank)
    s_pct, s_pts = change(sensex)

    n_pdh, n_pdl, n_pivot = levels(nifty)
    b_pdh, b_pdl, b_pivot = levels(bank)
    s_pdh, s_pdl, s_pivot = levels(sensex)

    # COMMODITIES
    gold = change(fetch("GC=F"))
    silver = change(fetch("SI=F"))
    crude = change(fetch("CL=F"))

    # BIAS
    bias = "BEARISH" if n_pct and n_pct < 0 else "BULLISH"
    condition = "EXTENDED" if n_pct and abs(n_pct) > 1 else "NORMAL"
    trend = "Weak" if bias == "BEARISH" else "Strong"

    # SUPPORT / RESISTANCE
    n_support = f"{n_pdl} / {n_pdl - 200 if n_pdl else 'NA'}"
    n_resist = f"{n_pdh} / {n_pdh + 200 if n_pdh else 'NA'}"

    b_support = f"{b_pdl} / {b_pdl - 400 if b_pdl else 'NA'}"
    b_resist = f"{b_pdh} / {b_pdh + 400 if b_pdh else 'NA'}"

    s_support = f"{s_pdl} / {s_pdl - 500 if s_pdl else 'NA'}"
    s_resist = f"{s_pdh} / {s_pdh + 500 if s_pdh else 'NA'}"

    return f"""🇮🇳 INDIA MARKET OUTLOOK (8:45 AM IST)

🌍 Global News
- Fed delaying rate cuts
- Bond yields rising
- China demand weak
- Oil cooling

📅 Events (IST)
CPI → 10 Apr | 8:00 PM
Jobless → 09 Apr | 6:00 PM
Fed → Evening window

--------------------------------------------------

📉 MARKET STRUCTURE

NIFTY
Move: {fmt(n_pct, n_pts)}
PDH: {n_pdh} | PDL: {n_pdl} | Pivot: {n_pivot}
Support: {n_support}
Resistance: {n_resist}
Trend: {trend}

BANKNIFTY
Move: {fmt(b_pct, b_pts)}
PDH: {b_pdh} | PDL: {b_pdl} | Pivot: {b_pivot}
Support: {b_support}
Resistance: {b_resist}
Trend: {trend}

SENSEX
Move: {fmt(s_pct, s_pts)}
PDH: {s_pdh} | PDL: {s_pdl} | Pivot: {s_pivot}
Support: {s_support}
Resistance: {s_resist}
Trend: {trend}

--------------------------------------------------

🪙 COMMODITIES

Gold: {fmt(*gold)}
Silver: {fmt(*silver)}
Crude: {fmt(*crude)}

--------------------------------------------------

📊 SECTOR STRENGTH

Strong: IT, Pharma  
Weak: Banking, Metals  

--------------------------------------------------

🎯 EXECUTION PLAN

🔥 A-SETUP
{"Sell near PDH with rejection" if bias=="BEARISH" else "Buy near PDL with confirmation"}

🟡 B-SETUP
{"Sell near Pivot if weakness" if bias=="BEARISH" else "Buy near Pivot if strength"}

❌ C-SETUP
Avoid mid-range trades

🧠 Trigger Logic
Rejection = Long wick + close back inside  
Confirmation = Strong close beyond level  

--------------------------------------------------

🎯 FINAL CALL

Market: {bias} + {condition}

🔥 Priority Trade:
{"Sell near PDH" if bias=="BEARISH" else "Buy near PDL"}

⚠️ NO TRADE ZONE:
{n_pdl + 50 if n_pdl else 'NA'} – {n_pdh - 50 if n_pdh else 'NA'}

📊 Confidence:
{"Medium (extended)" if condition=="EXTENDED" else "Moderate"}

🧠 Rule:
No level touch = No trade
"""


# ===========================
# US + BTC (UNCHANGED CORE)
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

Buy above {pdh}
Sell below {pdl}

Avoid mid-range trading

--------------------------------------------------

🎯 FINAL CALL

US: MIXED  
BTC Bias: {trend}

Best Trade: Breakout only  
Avoid: Range  
"""


# ===========================
# MAIN (STABLE)
# ===========================
def main():

    print("=== BOT STARTED ===")

    try:
        now = datetime.now(IST)
        print("Time:", now)

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
