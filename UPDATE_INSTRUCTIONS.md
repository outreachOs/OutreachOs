# How to Update Your Dashboard

## Files That Were Fixed

1. **callscript.py** - Now generates FULL cold call scripts (not just issue lists)
2. **app.py** - Fixed duplicate prevention, added detailed comments
3. **scraper.py** - Fixed review parsing bug (was showing "NAME (63) (0 Reviews)")
4. **PROJECT_STRUCTURE.md** - Complete guide to what each file does
5. **FEATURES_TO_ADD.md** - 16 suggested features with implementation difficulty

## To Add Light Theme Toggle

Open `outreach-dashboard-complete.html` and add this after line 16 (after the :root {...} block):

```css
/* Light theme - add .light class to body to activate */
body.light {
  --bg:#f5f6fa;--card:#ffffff;--card2:#f0f2f7;--border:#e1e4eb;--border2:#d0d4de;
  --green:#00a859;--gdim:rgba(0,168,89,0.08);--gborder:rgba(0,168,89,0.2);
  --orange:#e67700;--odim:rgba(230,119,0,0.08);--oborder:rgba(230,119,0,0.2);
  --red:#e03d56;--rdim:rgba(224,61,86,0.08);--rborder:rgba(224,61,86,0.2);
  --blue:#2a7de1;--bdim:rgba(42,125,225,0.08);--bborder:rgba(42,125,225,0.2);
  --yellow:#d4a000;--text:#1a1d2e;--muted:#5a6080;--muted2:#8a90a8;
}
.theme-toggle{background:transparent;border:1px solid var(--border2);color:var(--muted);border-radius:8px;padding:6px 12px;cursor:pointer;font-size:13px;font-weight:600;transition:all 0.15s}
.theme-toggle:hover{border-color:var(--text);color:var(--text)}
```

Then in the topbar (around line 280), add this button:

```html
<button class="theme-toggle" onclick="toggleTheme()">
  <span id="themeIcon">☀️</span>
  <span id="themeText">Light</span>
</button>
```

Then in the JavaScript section (around line 600), add this function:

```javascript
function toggleTheme(){
  const body=document.body;
  const isLight=body.classList.toggle('light');
  document.getElementById('themeIcon').textContent=isLight?'🌙':'☀️';
  document.getElementById('themeText').textContent=isLight?'Dark':'Light';
  localStorage.setItem('theme',isLight?'light':'dark');
}
// Load saved theme on startup
if(localStorage.getItem('theme')==='light'){toggleTheme();}
```

## Key Improvements Made

### 1. Call Script Now Generates Full Scripts
Before: Just listed issues
Now: Complete word-for-word dialogue with:
- Opening (10 sec)
- Hook (15 sec)
- Problem breakdown (40 sec) with business impacts
- Transition (10 sec)
- Offer (15 sec)
- Close (10 sec)

### 2. Database Prevents Duplicates
- Checks domain before inserting
- Only adds new businesses
- Updates existing ones only if data is better
- Logs in console: "[DB] Skipped duplicate: example.com"

### 3. Reviews Parse Correctly
Before: "Dave's Plumbing (63) (0 Reviews)"
Now: "Dave's Plumbing" with rating "4.5" and reviews "63"

### 4. All Code Commented
Every function now has:
```python
"""
What this function does
Args: what it takes
Returns: what it gives back
EDIT THIS to: when/why you'd change it
"""
```

## Quick Reference: Where to Edit What

| What to Change | File | Function/Line |
|---|---|---|
| Email tone/style | emailgen.py | Line ~65 (prompt variable) |
| Call script structure | callscript.py | Line ~150 (prompt variable) |
| SEO scoring rules | scraper.py | _calculate_seo_score() |
| Business impact explanations | callscript.py | ISSUE_LIBRARY dict |
| Dashboard UI/colors | outreach-dashboard-complete.html | CSS section |
| Database schema | app.py | init_db() function |
| Search behavior | scraper.py | find_businesses() |
| Add new tab | outreach-dashboard-complete.html | See PROJECT_STRUCTURE.md |

## When You Run Out of Credits

1. **Add $5-10 to OpenRouter** (easiest)
   - https://openrouter.ai/settings/credits
   - Lasts for hundreds of generations

2. **Switch to different free models**
   - Edit `emailgen.py` and `callscript.py`
   - Update the `FREE_MODELS` list
   - Check https://openrouter.ai/models for current free models

3. **Force template fallback**
   - Comment out the AI call in both files
   - Return `_fallback_script()` immediately
   - Still personalizes based on issues found

## Testing Your Changes

After editing any file:
1. Close RUN.bat window (Ctrl+C)
2. Double-click RUN.bat again
3. Refresh dashboard in browser (Ctrl+R)
4. Test the feature you changed

## Backup Your Data

Your database is in: `outreach_database.db`
Copy this file regularly to backup all your businesses and call history.
