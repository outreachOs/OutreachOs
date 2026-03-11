# CRITICAL FIXES TO APPLY

## Problem 1: Call Script Not Generating Customized Scripts

**CAUSE**: The `renderCallScript()` function is displaying the issues breakdown instead of the actual script.

**FIX** in `outreach-dashboard-complete.html` around line 550:

FIND this function:
```javascript
function renderCallScript(lead,data){
  let html=`<div class="script-intro">...
```

REPLACE the entire function with:
```javascript
function renderCallScript(lead,data){
  // Script column
  let scriptHTML=`<div class="script-intro">
    <div class="script-intro-title">📊 ${lead.name} — SEO Score: ${data.score||lead.seoScore}/100</div>
    <div class="script-intro-text">${lead.website||''} ${lead.email?'· '+lead.email:''} ${lead.phone?'· '+lead.phone:''}</div>
  </div>`;

  // Parse and display the ACTUAL script text
  const lines=data.script.split('\n');
  let currentSection='';
  let currentText='';

  lines.forEach(line=>{
    const trimmed=line.trim();
    // Detect section headers (all caps or starts with number)
    if(trimmed.match(/^[A-Z\s]+\(/)||trimmed.match(/^\d+\./)||trimmed.match(/^[A-Z\s]+$/)){
      if(currentSection&&currentText){
        scriptHTML+=`<div class="script-section"><div class="script-heading">${currentSection}</div><div class="script-text">${currentText.trim()}</div></div>`;
      }
      currentSection=trimmed;
      currentText='';
    }else if(trimmed){
      currentText+=line+'\n';
    }
  });
  if(currentSection&&currentText){
    scriptHTML+=`<div class="script-section"><div class="script-heading">${currentSection}</div><div class="script-text">${currentText.trim()}</div></div>`;
  }

  // Issue breakdown
  if(data.issues_breakdown&&data.issues_breakdown.length){
    scriptHTML+=`<div class="breakdown-section">
      <div class="breakdown-title">📚 What These Issues Mean (For You)</div>`;
    data.issues_breakdown.forEach(issue=>{
      const sevBadge=issue.severity==='very high'||issue.severity==='high'||issue.severity==='critical'?'sev-high':'sev-medium';
      scriptHTML+=`<div class="breakdown-item">
        <div class="breakdown-issue">${issue.issue}<span class="severity-badge ${sevBadge}">${issue.severity} impact</span></div>
        <div class="breakdown-exp">${issue.explanation}</div>
      </div>`;
    });
    scriptHTML+=`</div>`;
  }

  // Notes column
  const notesHTML=`<div class="notes-col">
    <div class="notes-title">📝 Call Notes</div>
    <textarea class="notes-area" id="callNotes" placeholder="Track what happened:\n• Left voicemail\n• Spoke to Dave\n• Follow up Friday\n• Not interested"></textarea>
    <div class="call-outcome">
      <div class="notes-title">Outcome</div>
      <div class="outcome-btns">
        <button class="btn bpri bsm" onclick="saveCallOutcome('${lead.name}','${lead.email||''}','${lead.website||''}',${data.score||0},'success')">✅ Interested</button>
        <button class="btn bout bsm" onclick="saveCallOutcome('${lead.name}','${lead.email||''}','${lead.website||''}',${data.score||0},'followup')">📅 Follow Up</button>
        <button class="btn bout bsm" onclick="saveCallOutcome('${lead.name}','${lead.email||''}','${lead.website||''}',${data.score||0},'voicemail')">📞 Voicemail</button>
        <button class="btn bout bsm" onclick="saveCallOutcome('${lead.name}','${lead.email||''}','${lead.website||''}',${data.score||0},'not_interested')">❌ Not Interested</button>
      </div>
    </div>
  </div>`;

  document.getElementById('scriptContent').innerHTML=`<div style="display:grid;grid-template-columns:1fr 300px;gap:24px"><div>${scriptHTML}</div>${notesHTML}</div>`;
  document.getElementById('scriptFooter').innerHTML=`
    <button class="btn bout" onclick="closeScript()">Close</button>`;
}
```

ADD this new function after renderCallScript:
```javascript
function saveCallOutcome(name,email,website,score,outcome){
  const notes=document.getElementById('callNotes').value;
  callHistory.push({name,email,website,score,outcome,notes,date:new Date().toISOString()});
  saveState();renderHistory();closeScript();updateStats();
  toast(`📞 Call logged: ${outcome}`);
}
```

## Problem 2: Database Tab Missing Call/Email/Add Buttons

FIND the renderDatabase() function around line 650

REPLACE the actions section with:
```javascript
<div class="lc-actions">
  <select class="btn bout bsm" onchange="updateDBStatus(${b.id},this.value)" style="cursor:pointer;padding:5px 8px;font-size:12px">
    <option value="pending" ${b.status==='pending'?'selected':''}>⬜ Pending</option>
    <option value="called" ${b.status==='called'?'selected':''}>📞 Called</option>
    <option value="contacted" ${b.status==='contacted'?'selected':''}>✅ Contacted</option>
  </select>
  <button class="btn bpri bsm" onclick="openCallScriptDB(${i})">📞 Call Script</button>
  ${b.email?`<button class="btn bout bsm" onclick="emailFromDB(${i})">📧 Email</button>`:' '}
  <button class="btn bout bsm" onclick="addToLeads(${b.id})">📋 Add to Leads</button>
  <button class="btn bred bsm" onclick="deleteFromDB(${b.id})">🗑 Delete</button>
</div>
```

ADD these new functions:
```javascript
function emailFromDB(idx){
  const b=window._filteredDB?.[idx];
  if(!b||!b.email)return;
  window.location.href=`mailto:${encodeURIComponent(b.email)}`;
  toast('📧 Opened email client');
}

function addToLeads(bizId){
  const biz=database.find(b=>b.id===bizId);
  if(!biz)return;
  leads.push({
    id:Date.now(),
    domain:biz.domain,
    email:biz.email||'',
    name:biz.name,
    score:biz.seoScore,
    type:'cold',
    status:'pending',
    date:new Date().toLocaleDateString('en-GB')
  });
  saveState();updateStats();renderLeads();
  toast('📋 Added to leads tracker!');
}

async function deleteFromDB(bizId){
  if(!confirm('Delete this business from database?'))return;
  try{
    await fetch(API+`/database/${bizId}`,{method:'DELETE'});
    database=database.filter(b=>b.id!==bizId);
    applyDBFilters();
    toast('🗑 Deleted');
  }catch{toast('❌ Delete failed')}
}
```

## Problem 3: Text Contrast & Size

FIND line 16 in CSS (after :root{...}):

CHANGE:
```css
--yellow:#ffd93d;--text:#e0e4f0;--muted:#5a6080;--muted2:#3a3f58;
```

TO:
```css
--yellow:#ffd93d;--text:#f0f4f8;--muted:#7a8499;--muted2:#4a5568;
```

FIND body{...} around line 18:

ADD:
```css
body{background:var(--bg);color:var(--text);font-family:'Familjen Grotesk',sans-serif;min-height:100vh;font-size:15px}
```

## Problem 4: Light Theme Toggle

AFTER the :root{...} block (line 16), ADD:
```css
body.light {
  --bg:#f5f6fa;--card:#ffffff;--card2:#f0f2f7;--border:#e1e4eb;--border2:#d0d4de;
  --green:#00a859;--gdim:rgba(0,168,89,0.08);--gborder:rgba(0,168,89,0.2);
  --orange:#e67700;--odim:rgba(230,119,0,0.08);--oborder:rgba(230,119,0,0.2);
  --red:#e03d56;--rdim:rgba(224,61,86,0.08);--rborder:rgba(224,61,86,0.2);
  --blue:#2a7de1;--bdim:rgba(42,125,225,0.08);--bborder:rgba(42,125,225,0.2);
  --yellow:#d4a000;--text:#1a1d2e;--muted:#5a6080;--muted2:#8a90a8;
}
.theme-toggle{background:transparent;border:1px solid var(--border2);color:var(--muted);border-radius:8px;padding:7px 14px;cursor:pointer;font-size:13px;font-weight:600;transition:all 0.15s;display:flex;align-items:center;gap:7px}
.theme-toggle:hover{border-color:var(--text);color:var(--text)}
```

IN THE TOPBAR (around line 260), REPLACE the opill div with:
```html
<button class="theme-toggle" onclick="toggleTheme()">
  <span id="themeIcon">☀️</span>
  <span id="themeText">Light</span>
</button>
```

IN JAVASCRIPT (end of file), ADD:
```javascript
function toggleTheme(){
  const body=document.body;
  const isLight=body.classList.toggle('light');
  document.getElementById('themeIcon').textContent=isLight?'🌙':'☀️';
  document.getElementById('themeText').textContent=isLight?'Dark':'Light';
  localStorage.setItem('theme',isLight?'light':'dark');
}
// Load saved theme
const savedTheme=localStorage.getItem('theme');
if(savedTheme==='light'){document.body.classList.add('light');document.getElementById('themeIcon').textContent='🌙';document.getElementById('themeText').textContent='Dark';}
```

## Problem 5: Comprehensive Call Guide

REPLACE the entire Call Guide page content with the comprehensive version in CALL_GUIDE.html (see next file)

## Problem 6: Modal Needs Notes Column

The modal-body CSS needs updating:

FIND .modal-body{...} and CHANGE to:
```css
.modal-body{padding:24px;max-width:100%}
```

ADD these styles:
```css
.notes-col{background:var(--card2);border-radius:10px;padding:16px;min-width:280px}
.notes-title{font-size:12px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:var(--muted);margin-bottom:10px}
.notes-area{width:100%;min-height:150px;background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:10px;font-size:13px;line-height:1.6;color:var(--text);font-family:'Familjen Grotesk',sans-serif;resize:vertical}
.call-outcome{margin-top:14px}
.outcome-btns{display:flex;flex-direction:column;gap:6px;margin-top:8px}
```

## Files to Delete

Delete these old dashboard files (not needed anymore):
- dashboard-pro.html
- outreach-dashboard-live.html

Keep only: **outreach-dashboard-complete.html** (or rename to outreach-pro-platform.html)

## Backend FIX

Add DELETE endpoint to app.py:

```python
@app.route('/api/database/<int:biz_id>', methods=['DELETE'])
def delete_business(biz_id):
    """Delete business from database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM businesses WHERE id = ?', (biz_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})
```
