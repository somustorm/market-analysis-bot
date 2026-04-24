import requests
import os
import yfinance as yf

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    res = requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg
    })
    print(res.text)

def get_data():
    nifty = yf.download("^NSEI", period="2d", interval="1d")
    crude = yf.download("CL=F", period="2d", interval="1d")
    btc = yf.download("BTC-USD", period="2d", interval="1d")
    return nifty, crude, btc

def analyze(nifty, crude, btc):
    score = 0

    nifty_chg = float(nifty["Close"].pct_change().iloc[-1])
    crude_chg = float(crude["Close"].pct_change().iloc[-1])
    btc_chg = float(btc["Close"].pct_change().iloc[-1])

    if nifty_chg < 0:
        score -= 1
    else:
        score += 1

    if crude_chg > 0:
        score -= 1
    else:
        score += 1

    if btc_chg < 0:
        score -= 1
    else:
        score += 1

    return score, nifty_chg, crude_chg, btc_chg

def generate_report():
    nifty, crude, btc = get_data()

    if nifty.empty or crude.empty or btc.empty:
        return "⚠️ Data fetch failed"

    score, n, c, b = analyze(nifty, crude, btc)

    bias = "BULLISH" if score > 0 else "BEARISH"

    msg = f"""
📊 Market Update

NIFTY: {n:.2%}
CRUDE: {c:.2%}
BTC: {b:.2%}

Bias: {bias}
Score: {score}
"""
    return msg

if __name__ == "__main__":
    report = generate_report()
    send(report)
