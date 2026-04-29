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
# SAFE FETCH (yfinance)
# ===========================
def fetch(symbol):
    for _ in range(3):
        try:
            df = yf.download(symbol, period="5d", interval="1d", progress=False)
            if df is not None and not df.empty and len(df) >= 3:
                return df
        except Exception as e:
            print("Fetch error:", symbol, e)
        time.sleep(2)
    return None


def safe_float(val):
    try:
        return float(val.item()) if hasattr(val, "item") else float(val)
    except:
        return None


def change(df):
    if df is None:
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

    except:
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

    except:
        return None, None, None


def fmt(pct, pts):
    if pct is None:
        return "NA"
    sign = "+" if pts > 0 else ""
    return f"{sign}{pts} ({pct}%)"


# ===========================
# BTC (CoinGecko)
# ===========================
def get_btc():
    try:
        url = "https://api.coingecko.com/api/v3/coins/bitcoin"
        data = requests.get(url, timeout=5).json()

        price = data["market_data"]["current_price"]["usd"]
        change_24h = data["market_data"]["price_change_percentage_24h"]

        return round(price, 2), round(change_24h, 2)
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
# INDIA REPORT
# ===========================
def india():
    nifty = fetch("^NSEI")

    if nifty is None:
        return "❌ INDIA DATA FAILED — NO TRADE"

    pct, pts = change(nifty)
    pdh, pdl, pivot = levels(nifty)

    if pdh is None or pdl is None:
        return "❌ INVALID INDIA DATA — NO TRADE"

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
# US REPORT
# ===========================
def us():
    btc_price, btc_pct = get_btc()

    if btc_price is None:
        return "❌ BTC DATA FAILED — NO TRADE"

    return f"""🌙 US MARKET

BTC Price: {btc_price}
24h Change: {btc_pct}%

Rule: No breakout → No trade
"""


# ===========================
# MAIN
# ===========================
def main():
    print("BOT START")

    india_msg = india()
    us_msg = us()

    final_msg = india_msg + "\n\n" + us_msg

    send(final_msg)


if __name__ == "__main__":
    main()
