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

📰 Macro Snapshot
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

🟢 A-SETUP:
Buy above {pdh}

🔴 A-SETUP:
Sell below {pdl}

🟡 B-SETUP:
Trade near Pivot ({pivot}) only with confirmation

❌ C-SETUP:
Avoid mid-range trading

--------------------------------------------------

⚠️ Risk Flags
- Event-driven volatility
- Mixed global cues

--------------------------------------------------

🎯 ACTION

US Bias: MIXED  
BTC Bias: {trend}

Strategy:
Trade breakouts only  
Avoid noise  
"""
