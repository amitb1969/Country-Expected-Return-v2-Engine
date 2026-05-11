# DL Country Framework v0.9.6

Static dashboard for country-level equity expected returns across 22 ETFs.

## What's in this repo

- `index.html` — the dashboard, single file, no build step
- `data.json` — country inputs (PE, c, ROE, payout, LT EPS, FX, CAD, etc.)
- `vercel.json` — Vercel config (clean URLs, cache headers)

## Methodology

Three growth modes, switchable in-app; **median is the default**:

- **GDP × β** — `(real GDP × λ_g + inflation) × β_EPS` (legacy spec)
- **LT EPS** — realized 10-year EPS CAGR (no β, no λ, no inflation add)
- **SGR** — `ROE × (1 − payout)` (DuPont sustainable growth)
- **Median** — per-country median of the three above (default)

Return assembly:
```
local return = FCF yield + earnings growth
local adj    = local return × (1 − 0.4 × bank weight)
r_USD        = (1 + local adj) × (1 + ΔFX) − 1
```

FX is multiplicative (not additive), and the bank haircut applies to local return before FX translation. Both are corrections to the v0.9.4 spec — see in-app explainer for the rationale.

## Run locally

The dashboard fetches `data.json`, so opening `index.html` directly from the filesystem will fail (browsers block `fetch()` on `file://` URLs). Run a local server:

```bash
python3 -m http.server 8000
# then visit http://localhost:8000
```

## Deploy to Vercel

1. **Create a GitHub repo** (public or private) and push these files to it:
   ```bash
   git init
   git add .
   git commit -m "Initial: v0.9.6 dashboard"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
   git push -u origin main
   ```

2. **Import to Vercel:**
   - Sign in at vercel.com with GitHub
   - "Add New → Project" → select your repo
   - Framework Preset: **Other** (it's plain HTML)
   - Build Command: *(leave empty)*
   - Output Directory: *(leave empty)*
   - Deploy

3. **Updates auto-deploy.** Push to `main` and Vercel rebuilds within ~30 seconds.

## Updating the data

Edit `data.json` directly, commit, push. The dashboard refreshes on next page load (`Cache-Control: max-age=3600`, so allow up to an hour or hard-refresh).

## Inputs schema (one object per ETF)

```json
{
  "ticker": "SPY",
  "country": "United States",
  "tier": "US",              // US | DM | EM | EMHR (or "EM HR" — auto-normalized)
  "fin": 11.92,              // % financials in index
  "tech": 45.10,             // % tech (display only)
  "com": 6.08,               // % commodities (display only)
  "gdp": 1.99,               // real GDP growth %
  "inflation": 2.24,         // CPI YoY %
  "fx_chg": 0.42,            // 10y annualized FX move vs USD %
  "fx_vol": 0.00,            // historical FX vol (display only)
  "roe": 20.71,              // 5y avg ROE %
  "payout": 28.78,           // payout ratio %
  "sgr": 14.75,              // ROE × (1 − payout) — computed in spreadsheet, recomputed live
  "c": 0.754,                // FCF / Net Income
  "cad_curr": -3.71,         // current account % GDP (negative = deficit)
  "cad_n5y": -3.59,          // 5y forward CAD (display only)
  "lt_eps": 12.78,           // 10y EPS CAGR %
  "beta_gdp": 1.40,          // EPS-to-GDP elasticity
  "pe": 20.98                // P/E multiple
}
```

## License

Internal research tool.
