# OutreachOS — Real Scraper Setup

## What this does
1. You type "Plumbers Derby" and click search
2. It searches Google Maps for real plumbing businesses
3. Visits each website and scores their SEO (word count, mobile, schema, etc.)
4. Finds their contact email automatically
5. Writes a personalised cold email based on REAL issues found
6. One click opens Outlook with the email pre-filled — you just hit Send

---

## First Time Setup (5 minutes)

### Step 1 — Install Python
Download from https://www.python.org/downloads/
⚠️ IMPORTANT: Tick "Add Python to PATH" during install

### Step 2 — Get your Anthropic API Key
Go to https://console.anthropic.com
Create an account → API Keys → Create Key
Copy it — you'll need it in Step 3

### Step 3 — Run Setup
Double-click START.bat
It will:
- Install all packages automatically
- Install the Chrome browser for scraping
- Ask you to paste your API key
- Start the backend server

### Step 4 — Open the Dashboard
Open outreach-dashboard-live.html in Chrome
The green "Backend connected" banner confirms it's working

---

## Daily Use (after first setup)
1. Double-click RUN.bat to start the backend
2. Open outreach-dashboard-live.html in Chrome
3. Type your trade + city, hit search
4. Emails generate automatically
5. Click "Open Outlook" on any ready lead
6. Click Send in Outlook

---

## Troubleshooting

**"Backend offline" banner**
→ Make sure RUN.bat is running in a terminal window
→ Check nothing else is using port 5000

**Google blocking the scraper**
→ This happens sometimes — add a longer delay in scraper.py (increase the sleep values)
→ For serious volume, consider SerpAPI (100 free searches/month): https://serpapi.com

**No emails found for many businesses**
→ Common — only ~60% of small trade sites have findable emails
→ Use the "+ Add Email" button to manually enter ones you find
→ Try calling those ones directly

**Python not found**
→ Reinstall Python and make sure "Add to PATH" is ticked
→ Restart your computer after installing

---

## Upgrading to paid for more volume
- SerpAPI: $50/month for 5,000 searches (real Google results, no blocking)
- ScrapingBee: $49/month for rotating proxies (stops sites blocking you)
- Both have free tiers to test with

---

## File Structure
- app.py          — Flask backend server
- scraper.py      — Google Maps + website scraper
- emailgen.py     — Claude AI email generator
- outreach-dashboard-live.html — Your dashboard
- START.bat       — First time setup
- RUN.bat         — Daily start
