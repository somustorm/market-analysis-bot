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

👉 Interpretation: Mixed global tone

📰 Major News
- Inflation concerns persist
- Bond yields elevated
- Tech sector showing strength
- Oil easing slightly

📅 Events (IST)
CPI / Jobless Claims / Fed Speakers

👉 Event Risk: HIGH

--------------------------------------------------

🇺🇸 US MARKET STRUCTURE

DOW: {fmt(*dow)}
NASDAQ: {fmt(*nasdaq)}
S&P 500: {fmt(*spx)}

🧠 Market Condition: MIXED / ROTATIONAL

📊 Sector Strength
Strong: Tech  
Weak: Financials, Industrials  

--------------------------------------------------

🪙 BTC STRUCTURE

Move: {fmt(btc_pct, btc_pts)}

PDH: {pdh}  
PDL: {pdl}  
Pivot: {pivot}

Trend: {trend}

Support: {pdl}  
Resistance: {pdh}

--------------------------------------------------

🎯 BTC EXECUTION PLAN

🟢 A-SETUP:
Buy above {pdh}

🔴 A-SETUP:
Sell below {pdl}

🟡 B-SETUP:
Trade near Pivot ({pivot}) with confirmation

❌ C-SETUP:
Avoid mid-range trading

🛑 Stop Loss:
Opposite side of breakout

📉 Invalidation:
False breakout / rejection

--------------------------------------------------

⚠️ Risk Flags
- Event-driven volatility
- Mixed global cues
- Diverging sectors

--------------------------------------------------

🎯 ACTION

US Bias: MIXED  
BTC Bias: {trend}

Strategy:
Trade breakouts only  
Avoid mid-range noise  

🧠 Rule:
Wait for confirmation → no prediction trades
"""
