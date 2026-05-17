# LensLead UK

LensLead UK is a beginner-friendly local web app that finds, stores, ranks, and displays UK photography/videography opportunities.

## What it does
- Collects leads from Reed, Adzuna, SerpAPI Google Jobs, and safe public pages.
- Classifies each lead (wedding/event/general/irrelevant/needs_review).
- Scores leads from 0–100 with transparent reasons and red flags.
- Deduplicates leads by URL, normalized keys, fuzzy similarity, and content hash.
- Provides a premium Streamlit dashboard with filtering, status tracking, manual intake, CSV export, and daily digest Markdown.

## 1) Run locally (non-coder steps)
1. Install Python 3.11+.
2. Open terminal:
   ```bash
   cd /Users/tatenda/Documents/lenslead-uk
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   ```
3. Run collectors:
   ```bash
   python -m app.run_collectors
   ```
4. Start dashboard:
   ```bash
   streamlit run app/dashboard.py
   ```

## 2) Add API keys
Edit `.env` and fill:
- `REED_API_KEY`
- `ADZUNA_APP_ID`
- `ADZUNA_APP_KEY`
- `SERPAPI_API_KEY`
- optional `OPENAI_API_KEY`

If keys are missing, that collector is skipped gracefully.

## 3) Deploy
### Option A: Streamlit Community Cloud
1. Push this repo to GitHub.
2. Connect repo in Streamlit Community Cloud.
3. Set main file to `app/dashboard.py`.
4. Add secrets (same keys as `.env`) in Streamlit secrets manager.

### Option B: GitHub Actions scheduled collection
1. Add repo secrets: `REED_API_KEY`, `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`, `SERPAPI_API_KEY`, optionally `OPENAI_API_KEY`.
2. Workflow `.github/workflows/daily_collect.yml` runs daily and on manual trigger.

## 4) Add new sources
1. Create a new collector file in `app/collectors/`.
2. Add a `run(settings) -> {"source", "leads", "errors"}` function.
3. Normalize outputs with `normalize_lead` from `app/collectors/common.py`.
4. Register the collector in `app/run_collectors.py`.
5. Add source toggle in `app/config.py`.

## Legal + safety
- No bypass of logins, CAPTCHAs, paywalls, or private groups.
- Public-page collector checks `robots.txt`.
- Includes request delay + caching.
- Stores source/apply URLs for traceability.
- No auto-contact; human approval is always required.

## Tests
```bash
pytest -q
```
