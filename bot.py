import requests
import os
import yfinance as yf
import feedparser
from datetime import datetime, timezone, timedelta

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

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    res = requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg
    })

    print("Telegram:", res.status_code, res.text)


# ===========================
# DATA
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
    c = df["Close"]
    last = float(c.iloc[-1])
    prev = float(c.iloc[-2])
    pct = round((last / prev - 1) * 100, 2)
    pts = int(round(last - prev, 0))
    return pct, pts


def levels(df):
    if df is None:
        return None, None, None
    h = float(df["High"].iloc[-2])
    l = float(df["Low"].iloc[-2])
    c = float(df["Close"].iloc[-2])
    pivot = (h + l + c) / 3
    return int(h), int(l), int(round(pivot, 0))


def fmt(pct, pts):
    if pct is None:
        return "NA"
    sign = "+" if pts > 0 else ""
    return f"{sign}{pts} ({pct}%)"


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
            parsed = feedparser.parse(f)
            for e in parsed.entries[:2]:
                news.append(e.title)
        except:
            pass

    return news[:3] if news else ["No major news"]


# ===========================
# EVENTS
# ===========================
def get_events():
    today = datetime.utcnow().date()
    events = []

    try:
        url = "https://api.tradingeconomics.com/calendar?c=guest:guest&f=json"
        data = requests.get(url, timeout=5).json()

        for e in data:
            d = datetime.strptime(e['Date'][:10], "%Y-%m-%d").date()
            if d >= today:
                events.append(f"{e['Event']} ({e['Country']}) → {d}")

    except:
        return ["⚠️ Event data unavailable"]

    return events[:3] if events else ["No major events"]


# ===========================
# INDIA
# ===========================
def india():
    df = fetch("^NSEI")
    if df is None:
        return "❌ INDIA DATA FAILED"

    pct, pts = change(df)
    pdh, pdl, pivot = levels(df)

    news = get_news()
    events = get_events()

    return f"""🇮🇳 INDIA MARKET OUTLOOK

🌍 News
- {news[0]}
- {news[1]}
- {news[2] if len(news)>2 else ""}

📅 Events
{chr(10).join(events)}

NIFTY Move: {fmt(pct, pts)}
PDH: {pdh} | PDL: {pdl} | Pivot: {pivot}
"""


# ===========================
# US
# ===========================
def us():
    df = fetch("BTC-USD")
    if df is None:
        return "❌ BTC DATA FAILED"

    pct, pts = change(df)
    pdh, pdl, pivot = levels(df)

    return f"""🌙 US MARKET

BTC Move: {fmt(pct, pts)}
PDH: {pdh} | PDL: {pdl} | Pivot: {pivot}
"""


# ===========================
# MAIN
# ===========================
def main():
    print("BOT START")

    msg = india() + "\n\n" + us()

    send(msg)


if __name__ == "__main__":
    main()
