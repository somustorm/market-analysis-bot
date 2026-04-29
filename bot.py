import requests
import os
import yfinance as yf
import feedparser
from datetime import datetime, timezone, timedelta
import time

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

    if not msg or len(msg.strip()) < 5:
        print("Empty message blocked")
        return

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        res = requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
        print("Telegram:", res.status_code)
    except Exception as e:
        print("Telegram error:", e)


# ===========================
# SAFE FETCH
# ===========================
def fetch(symbol):
    for _ in range(3):
        try:
            df = yf.download(symbol, period="5d", interval="1d", progress=False)
            if df is not None and not df.empty and len(df) >= 3:
                return df
        except:
            pass
        time.sleep(2)
    return None


def safe(v):
    try:
        return float(v.item()) if hasattr(v, "item") else float(v)
    except:
        return None


def change(df):
    if df is None:
        return None, None
    c = df["Close"]
    last = safe(c.iloc[-1])
    prev = safe(c.iloc[-2])
    if not last or not prev:
        return None, None
    pct = round((last / prev - 1) * 100, 2)
    pts = int(round(last - prev, 0))
    return pct, pts


def levels(df):
    if df is None:
        return None, None, None
    h = safe(df["High"].iloc[-2])
    l = safe(df["Low"].iloc[-2])
    c = safe(df["Close"].iloc[-2])
    if None in (h, l, c):
        return None, None, None
    pivot = (h + l + c) / 3
    return int(h), int(l), int(round(pivot, 0))


def fmt(pct, pts):
    if pct is None:
        return "NA"
    s = "+" if pts > 0 else ""
    return f"{s}{pts} ({pct}%)"


def fmt_pct(p):
    if p is None:
        return "NA"
    s = "+" if p > 0 else ""
    return f"{s}{p}%"


# ===========================
# BTC (CoinGecko)
# ===========================
def btc_data():
    try:
        d = requests.get(
            "https://api.coingecko.com/api/v3/coins/bitcoin", timeout=5
        ).json()
        price = d["market_data"]["current_price"]["usd"]
        pct = d["market_data"]["price_change_percentage_24h"]
        return price, pct
    except:
        return None, None


# ===========================
# NEWS
# ===========================
def get_news():
    feeds = [
        "http://feeds.reuters.com/reuters/businessNews",
        "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    ]
    news = []
    for f in feeds:
        try:
            p = feedparser.parse(f)
            for e in p.entries[:3]:
                if e.title and len(e.title) > 10:
                    news.append(e.title.strip())
        except:
            pass
    news = list(dict.fromkeys(news))
    return news[:3] if news else ["No major news"]


# ===========================
# EVENTS
# ===========================
def get_events():
    try:
        url = "https://api.tradingeconomics.com/calendar?c=guest:guest&f=json"
        data = requests.get(url, timeout=5).json()
        today = datetime.utcnow().date()

        ev = []
        for e in data:
            d = datetime.strptime(e['Date'][:10], "%Y-%m-%d").date()
            if d >= today:
                ev.append(f"{e['Event']} ({e['Country']})")

        return ev[:3] if ev else ["No major events"]

    except:
        return ["⚠️ Events unavailable"]


# ===========================
# INDIA ENGINE
# ===========================
def india():
    nifty = fetch("^NSEI")
    bank = fetch("^NSEBANK")

    if nifty is None:
        return "❌ INDIA DATA FAILED — NO TRADE"

    n_pct, n_pts = change(nifty)
    b_pct, _ = change(bank)

    pdh, pdl, pivot = levels(nifty)

    if pdh is None or pdl is None:
        return "❌ INVALID INDIA LEVELS — NO TRADE"

    # GLOBAL CONTEXT
    dow_pct, _ = change(fetch("^DJI"))
    nas_pct, _ = change(fetch("^IXIC"))
    btc_price, btc_pct = btc_data()

    # =====================
    # SCORE MODEL
    # =====================
    score = 0

    if n_pct: score += 0.4 if n_pct > 0 else -0.4
    if dow_pct: score += 0.2 if dow_pct > 0 else -0.2
    if btc_pct: score += 0.2 if btc_pct > 0 else -0.2
    if nas_pct: score += 0.2 if nas_pct > 0 else -0.2

    score = round(score, 2)

    if score > 0.3:
        bias = "BULLISH"
        conf = "HIGH"
    elif score < -0.3:
        bias = "BEARISH"
        conf = "HIGH"
    else:
        bias = "NEUTRAL"
        conf = "LOW"

    # =====================
    # EXECUTION LOGIC
    # =====================
    mid = (pdh + pdl) // 2

    news = get_news()
    events = get_events()

    return f"""🇮🇳 INDIA MARKET OUTLOOK

🌍 News
- {news[0]}
- {news[1]}
- {news[2] if len(news)>2 else ""}

📅 Events
{chr(10).join(events)}

--------------------------------------------------

📉 NIFTY

Move: {fmt(n_pct, n_pts)}
PDH: {pdh} | PDL: {pdl} | Pivot: {pivot}

--------------------------------------------------

📊 SCORE MODEL

Score: {score}
Bias: {bias}
Confidence: {conf}

--------------------------------------------------

🎯 EXECUTION

Sell near {pdh} IF rejection  
Buy above {pdh} IF breakout  
Sell below {pdl} IF breakdown  

❌ No Trade Zone: {mid-50} – {mid+50}

--------------------------------------------------

🧠 Rule:
Confluence > Prediction
"""


# ===========================
# US / BTC
# ===========================
def us():
    price, pct = btc_data()

    if price is None:
        return "❌ BTC DATA FAILED — NO TRADE"

    trend = "BULLISH" if pct > 0 else "BEARISH"

    return f"""🌙 US MARKET

BTC: {price} ({pct}%)
Trend: {trend}

Rule: Trade only strong breakout
"""


# ===========================
# MAIN
# ===========================
def main():
    print("BOT RUN")

    msg = india() + "\n\n" + us()

    send(msg)


if __name__ == "__main__":
    main()
