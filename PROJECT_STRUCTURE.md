# OutreachOS — Project Structure & File Guide

## Core Files (What Each Does)

### Backend Files (Python)

**app.py** — Main Flask backend server
- Handles all API endpoints
- Manages job queue for search operations
- Connects to SQLite database
- Routes: /api/search, /api/job/<id>, /api/generate-call-script, /api/database
- START HERE when debugging backend issues

**scraper.py** — Google Maps & website scraper
- Searches Google Maps for businesses
- Falls back to organic Google results if Maps fails
- Visits each website and extracts content
- Scores SEO (0-100) based on common issues
- Finds contact emails automatically
- EDIT HERE to change: search behavior, SEO scoring algorithm, what data gets extracted

**emailgen.py** — AI email generator
- Calls OpenRouter API to write cold emails
- Uses free tier models with fallbacks
- Personalizes based on real SEO issues found
- EDIT HERE to change: email tone, length, style, which model is used

**callscript.py** — AI call script generator
- Calls OpenRouter API to write cold call scripts
- Translates technical SEO issues into business impact language
- Generates unique scripts for each business
- EDIT HERE to change: script structure, business impact explanations, call style

### Frontend Files (HTML/JS)

**outreach-dashboard-complete.html** — Main dashboard (THE ONE TO USE)
- Single-page application with all features
- JavaScript handles: search, database, filters, persistence, API calls
- CSS defines all styling and themes
- EDIT HERE to change: UI layout, colors, add new tabs/features, modify filters

**START.bat** — Windows setup script
- Installs Python packages
- Installs Chromium browser for scraping
- Asks for OpenRouter API key
- Sets environment variable
- RUN THIS ONCE on first setup

**RUN.bat** — Daily startup script
- Starts Flask backend server
- RUN THIS every time you want to use the tool

### Database

**outreach_database.db** — SQLite database (auto-created)
- Stores all businesses ever found
- Schema: id, name, domain, email, phone, address, city, rating, reviews, seo_score, seo_issues, word_count, has_schema, mobile_viewport, first_seen, last_updated, status
- Persists forever across sessions
- Located in same folder as app.py

## When You Run Out of Credits

### Option 1: Get More OpenRouter Credits
1. Go to https://openrouter.ai/settings/credits
2. Add $5-10 (lasts for hundreds of emails/scripts)

### Option 2: Switch to Different Free Models
Edit `emailgen.py` and `callscript.py`:
```python
# Find this line:
FREE_MODELS = [
    "meta-llama/llama-4-scout:free",
    # Add more free models here
]
```
Check https://openrouter.ai/models?order=newest&supported_parameters=tools for current free models

### Option 3: Use Anthropic API Directly
Replace OpenRouter calls with direct Anthropic API calls if you have credits there

### Option 4: Disable AI Generation (Use Templates)
In `emailgen.py` and `callscript.py`, comment out the API call and force fallback to template

## Common Edits You'll Want to Make

### Change Email Tone
File: `emailgen.py`
Line: ~65 (the prompt variable)
Edit: Change "Friendly and human" to "Professional and corporate" or "Casual and funny"

### Change Call Script Structure
File: `callscript.py`
Line: ~140 (the prompt variable)
Edit: Rewrite the section headers or add new ones

### Add More SEO Issues
File: `scraper.py`
Function: `_calculate_seo_score()`
Add new checks and scoring logic

### Change Database Schema
File: `app.py`
Function: `init_db()`
Add new columns, then update `save_to_db()` function

### Add New Dashboard Tab
File: `outreach-dashboard-complete.html`
1. Add nav item in sidebar (~line 150)
2. Add page div (~line 300)
3. Add to titles object in JavaScript (~line 600)
4. Write render function

## How Data Flows Through the System

1. USER searches for "Plumbers Derby"
2. FRONTEND calls /api/search
3. BACKEND creates job, starts pipeline() in background
4. SCRAPER finds_businesses() from Google Maps
5. SCRAPER analyse_site() for each business
6. DATABASE save_to_db() stores each business
7. EMAILGEN generate_email() writes cold email
8. BACKEND returns results to frontend
9. FRONTEND renders leads, user clicks "Call Script"
10. CALLSCRIPT generate_call_script_ai() writes custom script
11. USER makes call, clicks "Mark as Called"
12. DATABASE updates status to 'called'
