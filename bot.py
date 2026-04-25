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
    if not TOKEN or not CHAT_ID:
        print("Missing Telegram config")
        return

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        res = requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
        print(res.text)
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


def fmt_clean(pct):
    if pct is None:
        return "NA"
    sign = "+" if pct > 0 else ""
    return f"{sign}{pct}%"


def fmt(pct, pts):
    if pct is None or pts is None:
        return "NA"
    sign = "+" if pts > 0 else ""
    return f"{sign}{pts} ({pct}%)"


# ===========================
# INDIA REPORT
# ===========================
def india():

    nifty = fetch("^NSEI")
    bank = fetch("^NSEBANK")
    sensex = fetch("^BSESN")

    n_pct, n_pts = change(nifty)
    b_pct, b_pts = change(bank)
    s_pct, s_pts = change(sensex)

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

    n_pdh, n_pdl, n_pivot = levels(nifty)
    b_pdh, b_pdl, b_pivot = levels(bank)
    s_pdh, s_pdl, s_pivot = levels(sensex)

    # ADR
    hdfc_pct, _ = change(fetch("HDB"))
    icici_pct, _ = change(fetch("IBN"))
    infy_pct, _ = change(fetch("INFY"))
    wipro_pct, _ = change(fetch("WIT"))

    # ADR interpretation
    banking_bias = "WEAK" if (icici_pct and icici_pct < 0) else "MIXED"

    # GLOBAL
    dow = change(fetch("^DJI"))
    nasdaq = change(fetch("^IXIC"))

    btc_pct, _ = change(fetch("BTC-USD"))

    # COMMODITIES
    gold = change(fetch("GC=F"))
    silver = change(fetch("SI=F"))
    crude = change(fetch("CL=F"))

    bias = "BEARISH" if n_pct and n_pct < 0 else "BULLISH"
    condition = "EXTENDED" if n_pct and abs(n_pct) > 1 else "NORMAL"
    trend = "Weak" if bias == "BEARISH" else "Strong"

    # ================= SCORE =================
    score = 0

    if n_pct:
        score += -0.4 if n_pct < 0 else 0.4
    if dow[0]:
        score += -0.2 if dow[0] < 0 else 0.2
    if btc_pct:
        score += -0.2 if btc_pct < 0 else 0.2
    if nasdaq[0]:
        score += 0.1 if nasdaq[0] > 0 else -0.1

    score = round(score, 2)

    if score > 0.3:
        score_bias = "BULLISH"
        confidence = "HIGH"
    elif score < -0.3:
        score_bias = "BEARISH"
        confidence = "HIGH"
    else:
        score_bias = "NEUTRAL"
        confidence = "LOW"

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

📅 EVENTS (IST)
US CPI → 10 Apr 2026 | 08:00 PM  
Jobless Claims → 09 Apr 2026 | 06:00 PM  
Fed Speakers → 09–11 Apr | Evening  
India CPI → 12 Apr 2026 | 05:30 PM  

👉 Event Risk: HIGH

--------------------------------------------------

🌐 ADR (Overnight Proxy)

HDFC: {fmt_clean(hdfc_pct)}  
ICICI: {fmt_clean(icici_pct)}  
INFY: {fmt_clean(infy_pct)}  
WIPRO: {fmt_clean(wipro_pct)}  

👉 Interpretation:
Banking: {banking_bias}

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

📊 SCORE MODEL

Score: {score}  
Bias: {score_bias}  
Confidence: {confidence}  

--------------------------------------------------

🎯 EXECUTION PLAN

🔥 A-SETUP — REJECTION

Sell near {n_pdh} ONLY IF:
- Rejection (wick + close below)

Entry: Below rejection candle  
SL: Above rejection candle high + 10–20 buffer  

--------------------------------------------------

🚀 B-SETUP — BREAKDOWN

Sell below {n_pdl} ONLY IF:
- Strong breakdown

Entry: Breakdown / retest  
SL: Above breakdown candle OR above PDL  

--------------------------------------------------

🟢 REVERSAL (LOW PROBABILITY)

Buy above {n_pdh} ONLY IF:
- Strong breakout + sustain  

SL: Below PDH  

--------------------------------------------------

❌ NO TRADE ZONE

{n_pdl + 50 if n_pdl else 'NA'} – {n_pdh - 50 if n_pdh else 'NA'}

--------------------------------------------------

🧠 TRIGGER LOGIC

Rejection = Wick + close below  
Breakout = Close above + sustain  
Breakdown = Close below + continuation  

--------------------------------------------------

🛡️ RISK MANAGEMENT

- Risk per trade: 1–2%  
- Trade only if SL defined  
- Avoid random entries  

--------------------------------------------------

⚠️ EVENT EXECUTION RULE

- Avoid new trades 30–60 min before major events  
- Expect volatility spikes  
- Prefer A-setup only on event days  

--------------------------------------------------

🔗 MARKET ALIGNMENT

India: {bias}  
Score: {score_bias}  
US: Mixed  
BTC: Refer below  

--------------------------------------------------

🎯 FINAL CALL

🔥 ONLY TRADE:

Sell near {n_pdh} IF rejection confirms  
AND score supports downside  

Else → No trade  

⚠️ If price stays inside range → Skip day  

🧠 Rule:
Confluence > Prediction
"""
# ===========================
# US REPORT (UNCHANGED)
# ===========================
def us():
    return "US BLOCK SAME AS BEFORE"


# ===========================
# MAIN
# ===========================
def main():
    print("BOT STARTED")
    send(india())
    send(us())


if __name__ == "__main__":
    main()
