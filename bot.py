import yfinance as yf
import requests
import time
from datetime import datetime
import pytz
import feedparser
import os

# =========================
# CONFIG
# =========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
IST = pytz.timezone("Asia/Kolkata")

# =========================
# TELEGRAM SEND (WITH RETRY)
# =========================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    for i in range(3):
        try:
            res = requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
            if res.status_code == 200:
                return
        except Exception as e:
            print("Telegram attempt failed:", e)
        time.sleep(2)

    print("❌ Telegram failed after retries")


# =========================
# SAFE DATA FETCH
# =========================
def fetch_data(symbol, period="5d", interval="1d"):
    for i in range(3):
        try:
            df = yf.download(symbol, period=period, interval=interval, progress=False)
            if df is not None and not df.empty:
                return df
        except Exception as e:
            print(f"Fetch error {symbol}:", e)
        time.sleep(2)

    return None


# =========================
# BTC DATA
# =========================
def get_btc_levels():
    df = fetch_data("BTC-USD", interval="1h")

    if df is None or len(df) < 3:
        return None

    try:
        pdh = round(df['High'].iloc[-2], 2)
        pdl = round(df['Low'].iloc[-2], 2)
        close = df['Close'].iloc[-2]
        pivot = round((pdh + pdl + close) / 3, 2)

        move = round(df['Close'].iloc[-1] - df['Close'].iloc[-2], 2)
        trend = "BULLISH" if move > 0 else "BEARISH"

        if pdh <= pdl:
            return None

        return pdh, pdl, pivot, move, trend

    except Exception as e:
        print("BTC calc error:", e)
        return None


# =========================
# INDEX DATA
# =========================
def get_index(symbol):
    df = fetch_data(symbol)

    if df is None or len(df) < 3:
        return None

    try:
        pdh = int(df['High'].iloc[-2])
        pdl = int(df['Low'].iloc[-2])
        close = df['Close'].iloc[-1]
        prev_close = df['Close'].iloc[-2]

        move = round(close - prev_close, 2)
        pct = round((move / prev_close) * 100, 2)
        pivot = int((pdh + pdl + prev_close) / 3)

        if pdh <= pdl:
            return None

        # Better trend classification
        if pct > 1:
            trend = "Strong Bullish"
        elif pct > 0.3:
            trend = "Mild Bullish"
        elif pct > -0.3:
            trend = "Sideways"
        elif pct > -1:
            trend = "Mild Bearish"
        else:
            trend = "Strong Bearish"

        return pdh, pdl, pivot, move, pct, trend

    except Exception as e:
        print("Index calc error:", e)
        return None


# =========================
# GLOBAL NEWS (RSS)
# =========================
def get_global_news():
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


# =========================
# EVENTS (FILTERED)
# =========================
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
                    events.append(f"{e['Event']} ({e['Country']}) → {event_date}")
            except:
                continue

    except Exception as e:
        print("Event fetch error:", e)
        return ["⚠️ Event data unavailable"]

    return events[:4] if events else ["✅ No major events today"]


# =========================
# INDIA REPORT
# =========================
def india_report():
    now = datetime.now(IST)
    print("Running INDIA report:", now)

    nifty = get_index("^NSEI")

    if nifty is None:
        send_telegram("❌ NIFTY DATA ERROR – NO TRADE")
        return

    pdh, pdl, pivot, move, pct, trend = nifty

    news = get_global_news()
    events = get_events()

    mid = (pdh + pdl) // 2

    msg = f"""🇮🇳 INDIA MARKET OUTLOOK ({now.strftime('%I:%M %p IST')})

🌍 Global News
- {news[0]}
- {news[1]}
- {news[2] if len(news)>2 else ""}

📅 EVENTS
{chr(10).join(events)}

📉 NIFTY STRUCTURE
Move: {move} ({pct}%)
PDH: {pdh} | PDL: {pdl} | Pivot: {pivot}
Trend: {trend}

🎯 EXECUTION

Sell near {pdh} IF rejection  
Buy above {pdh} IF breakout  
Sell below {pdl} IF breakdown  

❌ No Trade Zone: {mid - 50} – {mid + 50}

🧠 Rule:
No confirmation → No trade
"""

    send_telegram(msg)


# =========================
# US + BTC REPORT
# =========================
def us_report():
    now = datetime.now(IST)
    print("Running US report:", now)

    btc = get_btc_levels()

    if btc is None:
        send_telegram("❌ BTC DATA ERROR – NO TRADE")
        return

    pdh, pdl, pivot, move, trend = btc

    mid = (pdh + pdl) // 2

    msg = f"""🌙 US MARKET PREP ({now.strftime('%I:%M %p IST')})

🪙 BTC STRUCTURE
Move: {move}
PDH: {pdh}
PDL: {pdl}
Pivot: {pivot}
Trend: {trend}

🎯 EXECUTION

Buy above {pdh}  
Sell below {pdl}

❌ No Trade Zone: {mid - 100} – {mid + 100}

🧠 Rule:
Breakout only → No breakout = No trade
"""

    send_telegram(msg)


# =========================
# MAIN CONTROL (TIME SAFE)
# =========================
if __name__ == "__main__":
    now = datetime.now(IST)
    print("=== BOT STARTED ===", now)

    try:
        hour = now.hour

        if 7 <= hour <= 11:
            india_report()
        elif 16 <= hour <= 21:
            us_report()
        else:
            print("No valid execution window")

    except Exception as e:
        print("FATAL ERROR:", e)
        send_telegram(f"❌ BOT ERROR: {e}")
