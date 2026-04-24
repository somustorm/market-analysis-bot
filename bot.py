import yfinance as yf
import requests
import os

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def fetch_data():
    symbols = {
        "nifty": "^NSEI",
        "sensex": "^BSESN",
        "crude": "CL=F",
        "gold": "GC=F",
        "silver": "SI=F",
        "copper": "HG=F",
        "dxy": "DX-Y.NYB",
        "us10y": "^TNX",
        "vix_india": "^INDIAVIX",
        "vix_us": "^VIX"
    }

    data = {}
    for key, symbol in symbols.items():
        df = yf.download(symbol, period="2d", interval="1d", progress=False)
        data[key] = df

    return data


def get_change(df):
    try:
        last = df['Close'].iloc[-1]
        prev = df['Close'].iloc[-2]
        change = ((last - prev) / prev) * 100
        return round(last, 2), round(change, 2)
    except:
        return None, None


def analyze_macro(data):
    crude, crude_chg = get_change(data["crude"])
    gold, gold_chg = get_change(data["gold"])
    silver, silver_chg = get_change(data["silver"])
    copper, copper_chg = get_change(data["copper"])
    dxy, dxy_chg = get_change(data["dxy"])
    us10y, us10y_chg = get_change(data["us10y"])

    score = 0
    if not crude_chg.empty and crude_chg.iloc[-1] > 0: score -= 1
    if dxy_chg and dxy_chg > 0: score -= 1
    if us10y_chg and us10y_chg > 0: score -= 1

    bias = "BULLISH" if score >= 0 else "BEARISH"

    macro_text = f"""
🛢 Crude: {crude} ({crude_chg}%) {'↑' if crude_chg>0 else '↓'}
🥇 Gold: {gold} ({gold_chg}%) {'↑' if gold_chg>0 else '↓'}
🥈 Silver: {silver} ({silver_chg}%) {'↑' if silver_chg>0 else '↓'}
🔩 Copper: {copper} ({copper_chg}%) {'↑' if copper_chg>0 else '↓'}
💵 DXY: {dxy} ({dxy_chg}%) {'↑' if dxy_chg>0 else '↓'}
📉 US10Y: {us10y} ({us10y_chg}) {'↑' if us10y_chg>0 else '↓'}
"""

    return bias, macro_text


def get_levels(df):
    try:
        high = round(df['High'].iloc[-2], 0)
        low = round(df['Low'].iloc[-2], 0)

        return high, low
    except:
        return None, None


def generate_report():
    data = fetch_data()

    bias, macro = analyze_macro(data)

    nifty_high, nifty_low = get_levels(data["nifty"])
    sensex_high, sensex_low = get_levels(data["sensex"])

    vix_india, vix_india_chg = get_change(data["vix_india"])
    vix_us, vix_us_chg = get_change(data["vix_us"])

    tone = "VOLATILE" if vix_india_chg and vix_india_chg > 3 else bias

    report = f"""
📊 INDIA MARKET OUTLOOK (AUTO)

🌍 MACRO:
{macro}

📉 VIX (India): {vix_india} ({vix_india_chg}%)
📊 VIX (US): {vix_us} ({vix_us_chg}%)

🎯 MARKET TONE: {tone}

📍 NIFTY:
Resistance: {nifty_high}
Support: {nifty_low}

📍 SENSEX:
Resistance: {sensex_high}
Support: {sensex_low}

📊 MARKET BEHAVIOR:
- First 30 min volatile
- Trend after 10:15 AM

📅 EVENTS:
- Placeholder (upgrade later)

📌 WHAT TO AVOID:
- No trading first 15 mins
- No chasing breakout

📌 PLAN:
{"Sell rallies" if bias=="BEARISH" else "Buy dips"}
"""

    return report


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


if __name__ == "__main__":
    report = generate_report()
    send_telegram(report)
