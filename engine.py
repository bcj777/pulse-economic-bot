import os
import requests

FINNHUB_KEY = os.getenv("FINNHUB_KEY")
CRYPTOPANIC_KEY = os.getenv("CRYPTOPANIC_KEY")

seen = set()


def get_real_news():
    alerts = []

    # =========================
    # CRYPTO NEWS (CRYPTOPANIC)
    # =========================
    try:
        url = f"https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTOPANIC_KEY}&public=true"
        data = requests.get(url, timeout=10).json()

        for item in data.get("results", [])[:10]:
            title = item.get("title", "")
            key = f"crypto_{title}"

            if key in seen:
                continue

            seen.add(key)

            if any(x in title.lower() for x in ["bitcoin", "ethereum", "crypto", "btc"]):
                alerts.append(f"🚨 CRYPTO NEWS\n\n{title}")

    except:
        pass

    # =========================
    # STOCK + FOREX + MACRO (FINNHUB)
    # =========================
    try:
        url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_KEY}"
        data = requests.get(url, timeout=10).json()

        for item in data[:10]:
            headline = item.get("headline", "")
            key = f"macro_{headline}"

            if key in seen:
                continue

            seen.add(key)

            # HIGH IMPACT FILTER
            keywords = [
                "fed", "inflation", "rate", "cpi", "nfp",
                "usd", "recession", "stock", "crash",
                "nasdaq", "dow", "earnings"
            ]

            if any(k in headline.lower() for k in keywords):
                alerts.append(f"🚨 MACRO/STOCK NEWS\n\n{headline}")

    except:
        pass

    return alerts
