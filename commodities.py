"""
Vercel serverless function: live commodity YoY % moves.

Returns JSON shaped:
{
  "ok": true,
  "asof": "2026-05-11T16:00:00Z",
  "commodities": {
    "oil":    { "ticker": "BZ=F", "label": "Brent Crude",   "price": 84.23, "yoy_pct": 5.1, "ok": true },
    "copper": { "ticker": "HG=F", "label": "Copper",        "price": 4.65, "yoy_pct": 12.3, "ok": true },
    "iron":   { "ticker": "SCO.AX", "label": "Iron Ore (SGX proxy)", "price": 105.4, "yoy_pct": -8.2, "ok": true },
    "ag":     { "ticker": "^BCOMAG", "label": "Bloomberg Agriculture", "price": 51.2, "yoy_pct": 2.4, "ok": true },
    "broad":  { "ticker": "^BCOM", "label": "Bloomberg Commodity",     "price": 99.3, "yoy_pct": 4.1, "ok": true }
  }
}

If a single ticker fails, that commodity's `ok` is false and its `yoy_pct` is null,
but the function still returns 200 with the rest of the data. The frontend
falls back to manual entry for any commodity that didn't load.

Cached for 1 hour at the CDN via Cache-Control.
"""

import json
import datetime as dt
from http.server import BaseHTTPRequestHandler


# Ticker map. Notes:
# - BZ=F is Brent front-month (v0.9.4 displayed Brent / CO1:COM)
# - HG=F is COMEX copper front-month
# - SCO.AX is the iron ore SGX/ASX proxy. Yahoo's TIO=F is unreliable; SCO.AX is the
#   most stable iron-ore-linked ticker on Yahoo. Spot-iron-ore Bloomberg ticker is TIO1.
# - ^BCOMAG is the Bloomberg Agriculture subindex
# - ^BCOM is the Bloomberg Commodity broad index
TICKERS = {
    "oil":    {"ticker": "BZ=F",    "label": "Brent Crude"},
    "copper": {"ticker": "HG=F",    "label": "Copper"},
    "iron":   {"ticker": "SCO.AX",  "label": "Iron Ore (SGX proxy)"},
    "ag":     {"ticker": "^BCOMAG", "label": "Bloomberg Agriculture"},
    "broad":  {"ticker": "^BCOM",   "label": "Bloomberg Commodity"},
}


def fetch_one(ticker_symbol):
    """Returns (price_now, yoy_pct) or raises."""
    import yfinance as yf

    t = yf.Ticker(ticker_symbol)
    # 13 months of history to make sure we have 1y-ago even with holiday gaps
    hist = t.history(period="13mo", interval="1d", auto_adjust=False)
    if hist is None or hist.empty:
        raise RuntimeError(f"No data for {ticker_symbol}")

    closes = hist["Close"].dropna()
    if len(closes) < 30:
        raise RuntimeError(f"Insufficient history for {ticker_symbol}")

    price_now = float(closes.iloc[-1])

    # Find the close from ~365 days ago. Walk back from current date.
    target = closes.index[-1] - dt.timedelta(days=365)
    # Find the closest historical index >= target
    earlier = closes[closes.index <= target + dt.timedelta(days=7)]
    if earlier.empty:
        # Fall back to first available
        price_yago = float(closes.iloc[0])
    else:
        price_yago = float(earlier.iloc[-1])

    if price_yago == 0:
        raise RuntimeError(f"Zero base price for {ticker_symbol}")

    yoy_pct = (price_now / price_yago - 1.0) * 100.0
    return price_now, yoy_pct


def build_response():
    out = {}
    for key, meta in TICKERS.items():
        entry = {"ticker": meta["ticker"], "label": meta["label"]}
        try:
            price, yoy = fetch_one(meta["ticker"])
            entry["price"] = round(price, 4)
            entry["yoy_pct"] = round(yoy, 2)
            entry["ok"] = True
        except Exception as e:
            entry["price"] = None
            entry["yoy_pct"] = None
            entry["ok"] = False
            entry["error"] = str(e)[:200]
        out[key] = entry

    return {
        "ok": True,
        "asof": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "commodities": out,
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            payload = build_response()
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "public, s-maxage=3600, stale-while-revalidate=7200")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            err = json.dumps({"ok": False, "error": str(e)[:300]}).encode("utf-8")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(err)))
            self.end_headers()
            self.wfile.write(err)
