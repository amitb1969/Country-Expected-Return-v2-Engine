# DL Country Framework v0.9.7

Static dashboard for country-level equity expected returns across 22 ETFs, with a Vercel serverless function for live commodity prices.

## Repo structure

```
.
├── index.html              ← the dashboard (single file, no build)
├── data.json               ← country inputs
├── vercel.json             ← Vercel config
├── api/
│   ├── commodities.py      ← serverless function, fetches commodity prices via yfinance
│   └── requirements.txt    ← Python deps (yfinance)
├── README.md
└── .gitignore
```

## Tabs

1. **§01 Front Dashboard** — tier aggregate banner (US / DM / EM / EMHR), compact country matrix with pass/fail vs hurdle
2. **§02 Full Inputs** — wide editable matrix, every input editable, propagates to all tabs
3. **§03 Hurdle Rate** — sorted by gap vs SPY-based hurdle, pass/fail badges
4. **§04 Country Detail** — multiplicative return waterfall, three-mode growth comparison, narrative, full editable inputs
5. **§05 Methodology** — in-app explainer

## Growth modes

| Mode | Formula |
|---|---|
| **Median** (default) | per-country median of GDP×β, LT EPS, SGR |
| GDP × β | `(gdp × λ_g + inflation) × β_GDP` |
| LT EPS | realized 10y EPS CAGR |
| SGR | `ROE × (1 − payout)` |

## Return assembly

```
local return  = FCF yield + earnings growth
local adj     = local return × (1 − 0.4 × bank weight)
r_USD         = (1 + local adj) × (1 + ΔFX) − 1
ΔFX           = annualized FX move + CAD overshoot (drag if CAD < −3%)
```

FX is multiplicative (not additive — corrects v0.9.4 linearization at high inflation). Bank haircut applies to local return before FX translation.

## Commodity panel

Live YoY % from `/api/commodities` (Vercel serverless function pulling Yahoo Finance via `yfinance`):

- Brent Crude — `BZ=F`
- Copper — `HG=F`
- Iron Ore — `SCO.AX` (SGX-linked proxy; spot iron ore on Yahoo is unreliable)
- Bloomberg Agriculture — `^BCOMAG`
- Bloomberg Commodity — `^BCOM`

Cached for 1 hour at the Vercel CDN. If yfinance fails for any ticker, the UI falls back to manual input for that one.

**The commodity panel drives only the qualitative Forecast Risk arrow per country.** Numerical commodity coefficients remain zeroed in the math (v0.9.4 deliberate retreat — bucket-based betas weren't empirically calibrated).

## Run locally

```bash
# Frontend only (commodity panel will fail since no /api/commodities locally)
python3 -m http.server 8000

# Full local with Vercel dev (requires `vercel` CLI)
npm i -g vercel
vercel dev
```

Without `vercel dev`, the commodity panel shows "Live fetch failed" and provides manual input boxes — everything else still works.

## Deploy to Vercel

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial: v0.9.7 dashboard with live commodities"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/REPO.git
   git push -u origin main
   ```

2. **Import on Vercel:**
   - Sign in at vercel.com with GitHub
   - "Add New → Project" → select your repo
   - Framework Preset: **Other**
   - Build Command: empty
   - Output Directory: empty
   - **Vercel auto-detects** `api/commodities.py` as a Python function and `api/requirements.txt` for dependencies
   - Click Deploy

3. **Verify the function** by visiting `your-app.vercel.app/api/commodities` directly — it should return JSON with the five commodity prices and YoY %.

## Updating data

Edit `data.json`, commit, push. Vercel rebuilds in ~30 seconds. Cache header on `data.json` is 1 hour — hard-refresh the browser to see changes immediately.

## Notes

- The Vercel free (Hobby) tier covers the Python function comfortably (10s typical execution, well under the 10s timeout and 100GB-hr/month bandwidth limit). Pro tier is $20/mo if you want commercial use, password protection, or higher limits.
- Yahoo's commodity tickers occasionally fail or return delayed data. The function returns 200 with per-commodity `ok: false` flags rather than 500-ing, so the UI degrades gracefully.
- Greece `c` was corrected to 1.0 (was 1.35 in earlier draft — depreciation-over-capex distortion).
- EMXC label is "Emerging x China" (was incorrectly labeled "United States" in the original spreadsheet).

## License

Internal research tool.
