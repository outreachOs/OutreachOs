# OutreachOS Platform — Complete Railway Deploy Package

## What's Included

**Backend (Python/Flask):**
- `app.py` — Main API server with all fixes applied
- `scraper.py` — Google Maps scraper (review parsing fixed)
- `callscript.py` — AI call script generator (full scripts, not just tips)
- `emailgen.py` — AI email generator

**Frontend:**
- `outreach-complete-FINAL.html` — Complete dashboard with mobile responsive CSS
- `manifest.json` — PWA support
- `service-worker.js` — Offline functionality

**Deployment:**
- `requirements.txt` — Python dependencies
- `Procfile` — Railway start command
- `runtime.txt` — Python version
- `railway.json` — Railway build configuration
- `.gitignore` — Files to exclude

## Deploy to Railway

### 1. Create Railway Project

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Create new project
railway init
```

### 2. Set Environment Variables

In Railway dashboard, add:

```
OPENROUTER_API_KEY=your_key_here
```

Get free key at: https://openrouter.ai/settings/keys

### 3. Deploy

```bash
# Link to project
railway link

# Deploy
railway up
```

### 4. Update Dashboard

In `outreach-complete-FINAL.html`, change line 581:

```javascript
const API='http://localhost:5000/api';
```

To:

```javascript
const API='https://your-railway-url.up.railway.app/api';
```

Get your Railway URL from the dashboard.

## Features Fixed

✅ Call script generates FULL customized scripts (not just issue lists)
✅ Database prevents duplicates (checks domain before inserting)
✅ Review parsing fixed (separates rating from review count)
✅ Database tab has Call/Email/Add to Leads/Delete buttons
✅ Light theme toggle (stays dark by default)
✅ Call notes tracker in script modal
✅ Mobile responsive (works on iPhone/Android)
✅ PWA ready (Add to Home Screen)
✅ DELETE endpoint added to backend

## Local Testing

```bash
pip install -r requirements.txt
playwright install chromium
python app.py
```

Open `outreach-complete-FINAL.html` in browser.

## File Structure

```
outreach-platform/
├── app.py                          # Flask backend
├── scraper.py                      # Google Maps scraper
├── callscript.py                   # AI script generator
├── emailgen.py                     # AI email generator
├── requirements.txt                # Python deps
├── Procfile                        # Railway start
├── runtime.txt                     # Python version
├── railway.json                    # Build config
├── outreach-complete-FINAL.html    # Main dashboard
├── manifest.json                   # PWA manifest
└── service-worker.js               # PWA worker
```

## Environment Variables

**Required:**
- `OPENROUTER_API_KEY` — Get from https://openrouter.ai (free tier available)

**Optional:**
- `PORT` — Railway sets this automatically (default: 5000)

## Database

SQLite database (`outreach_database.db`) auto-creates on first run.

**Schema:**
- id, name, domain, email, phone, address, city
- rating, reviews, seo_score, seo_issues
- word_count, has_schema, mobile_viewport
- first_seen, last_updated, status

## Troubleshooting

**"Backend not running":**
- Check Railway logs: `railway logs`
- Verify OPENROUTER_API_KEY is set
- Check build succeeded

**"Playwright install failed":**
- Railway.json includes playwright install in buildCommand
- If fails, add to Procfile: `web: playwright install chromium && python app.py`

**"Database not persisting":**
- Railway uses ephemeral filesystem
- Add Railway Volume for persistent storage
- Or use external database (PostgreSQL/MySQL)

## Cost

**Railway Free Tier:**
- $5 credit/month
- ~500 hours runtime
- Should cover development/testing

**OpenRouter Free Tier:**
- Multiple free models available
- Rate limited but sufficient for testing
- Upgrade for production ($0.001-0.10 per request)
