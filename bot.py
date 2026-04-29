import requests
import os
import yfinance as yf
from datetime import datetime, timezone, timedelta
import feedparser

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


def fmt_clean(pct):
    if pct is None:
        return "NA"
    sign = "+" if pct > 0 else ""
    return f"{sign}{pct}%"


# ===========================
# ✅ LIVE NEWS (NEW)
# ===========================
def get_news():
    feeds = [
        "http://feeds.reuters.com/reuters/businessNews",
        "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "https://feeds.bloomberg.com/markets/news.rss"
    ]

    news = []

    for feed in feeds:
        try:
            parsed = feedparser.parse(feed)
            for entry in parsed.entries[:2]:
                news.append(entry.title)
        except:
            continue

    return news[:4] if news else ["No major news available"]


# ===========================
# ✅ LIVE EVENTS (NEW)
# ===========================
def get_events():
    today = datetime.utcnow().date()
    events = []

    try:
        url = "https://api.tradingeconomics.com/calendar?c=guest:guest&f=json"
        res = requests.get(url, timeout=5).json()

        for e in res:
            try:
                event_date = datetime.strptime(e['Date'][:10], "%Y-%m-%d").date()
                if event_date >= today:
                    events.append(
                        f"{e['Event']} ({e['Country']}) → {event_date}"
                    )
            except:
                continue

    except:
        return ["⚠️ Event data unavailable"]

    return events[:4] if events else ["✅ No major events today"]


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

    n_pdh, n_pdl, n_pivot = levels(nifty)
    b_pdh, b_pdl, b_pivot = levels(bank)
    s_pdh, s_pdl, s_pivot = levels(sensex)

    # ADR
    hdfc_pct, _ = change(fetch("HDB"))
    icici_pct, _ = change(fetch("IBN"))
    infy_pct, _ = change(fetch("INFY"))
    wipro_pct, _ = change(fetch("WIT"))

    banking_bias = "WEAK" if (icici_pct and icici_pct < 0) else "MIXED"

    # GLOBAL
    dow = change(fetch("^DJI"))
    nasdaq = change(fetch("^IXIC"))
    btc_pct, _ = change(fetch("BTC-USD"))

    # COMMODITIES
    gold = change(fetch("GC=F"))
    silver = change(fetch("SI=F"))
    crude = change(fetch("CL=F"))

    # BIAS
    bias = "BEARISH" if n_pct and n_pct < 0 else "BULLISH"
    condition = "EXTENDED" if n_pct and abs(n_pct) > 1 else "NORMAL"
    trend = "Weak" if bias == "BEARISH" else "Strong"

    # SCORE
    score = 0
    if n_pct: score += -0.4 if n_pct < 0 else 0.4
    if dow[0]: score += -0.2 if dow[0] < 0 else 0.2
    if btc_pct: score += -0.2 if btc_pct < 0 else 0.2
    if nasdaq[0]: score += 0.1 if nasdaq[0] > 0 else -0.1

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

    if bias == score_bias:
        alignment = "STRONG"
    else:
        alignment = "MODERATE"

    n_support = f"{n_pdl} / {n_pdl - 200 if n_pdl else 'NA'}"
    n_resist = f"{n_pdh} / {n_pdh + 200 if n_pdh else 'NA'}"
    b_support = f"{b_pdl} / {b_pdl - 400 if b_pdl else 'NA'}"
    b_resist = f"{b_pdh} / {b_pdh + 400 if b_pdh else 'NA'}"
    s_support = f"{s_pdl} / {s_pdl - 500 if s_pdl else 'NA'}"
    s_resist = f"{s_pdh} / {s_pdh + 500 if s_pdh else 'NA'}"

    news = get_news()
    events = get_events()

    return f"""🇮🇳 INDIA MARKET OUTLOOK (8:45 AM IST)

🌍 Global News
- {news[0]}
- {news[1]}
- {news[2] if len(news)>2 else ""}
- {news[3] if len(news)>3 else ""}

📅 EVENTS (IST)
{chr(10).join(events)}

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
... (UNCHANGED BELOW — KEEP YOUR FULL ORIGINAL BLOCK)
"""
