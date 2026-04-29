import requests
import os
import yfinance as yf
import feedparser
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
        print("❌ Missing Telegram config")
        return

    if not msg or len(msg.strip()) < 5:
        print("❌ Empty message blocked")
        return

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        res = requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
        print("Telegram:", res.status_code, res.text)
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


def safe_float(val):
    try:
        return float(val.item()) if hasattr(val, "item") else float(val)
    except:
        return None


def change(df):
    if df is None or "Close" not in df:
        return None, None

    try:
        c = df["Close"]
        last = safe_float(c.iloc[-1])
        prev = safe_float(c.iloc[-2])

        if last is None or prev is None:
            return None, None

        pct = round((last / prev - 1) * 100, 2)
        pts = int(round(last - prev, 0))

        return pct, pts

    except Exception as e:
        print("Change error:", e)
        return None, None


def levels(df):
    if df is None:
        return None, None, None

    try:
        h = safe_float(df["High"].iloc[-2])
        l = safe_float(df["Low"].iloc[-2])
        c = safe_float(df["Close"].iloc[-2])

        if None in (h, l, c):
            return None, None, None

        pivot = (h + l + c) / 3

        return int(h), int(l), int(round(pivot, 0))

    except Exception as e:
        print("Levels error:", e)
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
# LIVE NEWS
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
# LIVE EVENTS
# ===========================
def get_events():
    today = datetime.utcnow().date()
    events = []

    try:
        url = "https://api.tradingeconomics.com/calendar?c=guest:guest&f=json"
        data = requests.get(url, timeout=5).json()

        for e in data:
            try:
                d = datetime.strptime(e['Date'][:10], "%Y-%m-%d").date()
                if d >= today:
                    events.append(f"{e['Event']} ({e['Country']}) → {d}")
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

    if nifty is None:
        return "❌ NIFTY DATA ERROR – NO TRADE"

    n_pct, n_pts = change(nifty)
    b_pct, b_pts = change(bank)
    s_pct, s_pts = change(sensex)

    n_pdh, n_pdl, n_pivot = levels(nifty)
    b_pdh, b_pdl, b_pivot = levels(bank)
    s_pdh, s_pdl, s_pivot = levels(sensex)

    news = get_news()
    events = get_events()

    return f"""🇮🇳 INDIA MARKET OUTLOOK (8:45 AM IST)

🌍 Global News
- {news[0]}
- {news[1]}
- {news[2] if len(news)>2 else ""}
- {news[3] if len(news)>3 else ""}

📅 EVENTS
{chr(10).join(events)}

--------------------------------------------------

📉 MARKET STRUCTURE

NIFTY
Move: {fmt(n_pct, n_pts)}
PDH: {n_pdh} | PDL: {n_pdl} | Pivot: {n_pivot}

BANKNIFTY
Move: {fmt(b_pct, b_pts)}
PDH: {b_pdh} | PDL: {b_pdl} | Pivot: {b_pivot}

SENSEX
Move: {fmt(s_pct, s_pts)}
PDH: {s_pdh} | PDL: {s_pdl} | Pivot: {s_pivot}

--------------------------------------------------

🧠 Rule:
Confluence > Prediction
"""


# ===========================
# US REPORT
# ===========================
def us():
    btc_df = fetch("BTC-USD")

    if btc_df is None:
        return "❌ BTC DATA ERROR – NO TRADE"

    btc_pct, btc_pts = change(btc_df)
    pdh, pdl, pivot = levels(btc_df)

    trend = "BULLISH" if btc_pct and btc_pct > 0 else "BEARISH"

    return f"""🌙 US MARKET PREP (6:45 PM IST)

🪙 BTC STRUCTURE

Move: {fmt(btc_pct, btc_pts)}

PDH: {pdh}  
PDL: {pdl}  
Pivot: {pivot}

Trend: {trend}

--------------------------------------------------

🧠 Rule:
No breakout → No trade
"""


# ===========================
# MAIN
# ===========================
def main():
    print("BOT STARTED")

    india_msg = india()
    us_msg = us()

    final_msg = india_msg + "\n\n" + us_msg

    send(final_msg)


if __name__ == "__main__":
    main()
