import requests

def crypto():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin,ethereum",
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }

    r = requests.get(url, params=params).json()

    btc = r["bitcoin"]["usd"]
    btc_ch = r["bitcoin"]["usd_24h_change"]

    eth = r["ethereum"]["usd"]
    eth_ch = r["ethereum"]["usd_24h_change"]

    def trend(x):
        if x > 2:
            return "📈 STRONG UP"
        if x < -2:
            return "📉 STRONG DOWN"
        return "➡️ SIDEWAYS"

    return f"""₿ CRYPTO
BTC: ${btc} ({btc_ch:.2f}%) {trend(btc_ch)}
ETH: ${eth} ({eth_ch:.2f}%) {trend(eth_ch)}
"""


def macro():
    events = [
        "🔴 CPI Inflation",
        "🔴 NFP Jobs Report",
        "🔴 FOMC Meeting"
    ]
    return "🌍 MACRO\n" + "\n".join(events)


def stocks():
    return """📈 STOCKS
NVDA +2.1%
TSLA -1.3%
AAPL +0.7%
"""


def build_brief():
    return f"""📊 MARKET INTELLIGENCE PRO v1

{macro()}

{crypto()}

{stocks()}
"""
