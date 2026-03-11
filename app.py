"""
OutreachOS Backend — Complete with persistent database
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import asyncio
import threading
import json
import time
import random
import sqlite3
import os
from scraper import find_businesses, analyse_site
from emailgen import generate_email
from callscript import generate_call_script_ai

app = Flask(__name__)
CORS(app)

# Database setup
DB_PATH = 'outreach_database.db'

def init_db():
    """Initialize SQLite database for persistent storage"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS businesses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        domain TEXT UNIQUE,
        email TEXT,
        phone TEXT,
        address TEXT,
        city TEXT,
        rating TEXT,
        reviews INTEGER,
        seo_score INTEGER,
        seo_issues TEXT,
        word_count INTEGER,
        has_schema BOOLEAN,
        mobile_viewport BOOLEAN,
        first_seen TEXT,
        last_updated TEXT,
        status TEXT DEFAULT 'pending'
    )''')
    conn.commit()
    conn.close()

init_db()

jobs = {}

def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(coro)
    loop.close()
    return result


@app.route('/api/search', methods=['POST'])
def search():
    data = request.json
    trade = data.get('trade', 'Plumbers')
    city = data.get('city', 'Leicester')
    count = int(data.get('count', 10))
    email_type = data.get('emailType', 'cold')

    job_id = f"job_{int(time.time()*1000)}"
    jobs[job_id] = {
        'status': 'running',
        'progress': 0,
        'total': count,
        'leads': [],
        'log': [f'Starting search for {trade} in {city}...']
    }

    def run():
        try:
            run_async(pipeline(job_id, trade, city, count, email_type))
        except Exception as e:
            jobs[job_id]['status'] = 'error'
            jobs[job_id]['log'].append(f'Fatal error: {str(e)}')

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return jsonify({'job_id': job_id})


@app.route('/api/job/<job_id>')
def get_job(job_id):
    if job_id == 'test':
        return jsonify({'status': 'test_ok'}), 200
    job = jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify(job)


@app.route('/api/generate-call-script', methods=['POST'])
def gen_call_script():
    data = request.json
    result = run_async(generate_call_script_ai(data['company'], data.get('location', 'Leicester')))
    return jsonify(result)


@app.route('/api/database', methods=['GET'])
def get_database():
    """Return all businesses in database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM businesses ORDER BY seo_score ASC, id DESC')
    rows = c.fetchall()
    conn.close()
    
    businesses = []
    for row in rows:
        businesses.append({
            'id': row[0],
            'name': row[1],
            'domain': row[2],
            'email': row[3],
            'phone': row[4],
            'address': row[5],
            'city': row[6],
            'rating': row[7],
            'reviews': row[8],
            'seoScore': row[9],
            'seoIssues': json.loads(row[10]) if row[10] else [],
            'wordCount': row[11],
            'hasSchema': row[12],
            'mobileViewport': row[13],
            'firstSeen': row[14],
            'lastUpdated': row[15],
            'status': row[16]
        })
    return jsonify(businesses)


@app.route('/api/database/<int:biz_id>', methods=['PATCH'])
def update_business(biz_id):
    """Update business status"""
    data = request.json
    status = data.get('status', 'pending')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE businesses SET status = ? WHERE id = ?', (status, biz_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


def save_to_db(business):
    """
    Save or update business in database
    Prevents duplicates by checking domain first
    
    EDIT THIS to: change what fields get saved, add new columns
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    domain = business.get('website', '').replace('https://','').replace('http://','').replace('www.','').split('/')[0]
    
    # Skip if no domain (can't identify duplicates without it)
    if not domain:
        conn.close()
        return
    
    # Check if this business already exists
    c.execute('SELECT id, seo_score FROM businesses WHERE domain = ?', (domain,))
    existing = c.fetchone()
    
    if existing:
        # Business exists — only update if we have new/better data
        existing_id, existing_score = existing
        new_score = business.get('seoScore', 0)
        
        # Only update if new score is different or we have new email
        if new_score != existing_score or business.get('email'):
            c.execute('''UPDATE businesses SET 
                email = COALESCE(NULLIF(?, ''), email),
                phone = COALESCE(NULLIF(?, ''), phone),
                seo_score = ?,
                seo_issues = ?,
                word_count = ?,
                has_schema = ?,
                mobile_viewport = ?,
                last_updated = ?
                WHERE domain = ?''',
                (business.get('email',''), business.get('phone',''), new_score,
                 json.dumps(business.get('seoIssues',[])), business.get('wordCount',0),
                 business.get('hasSchema',False), business.get('mobileViewport',False),
                 now, domain))
            print(f"[DB] Updated existing: {domain}")
        else:
            print(f"[DB] Skipped duplicate: {domain}")
    else:
        # New business — insert it
        c.execute('''INSERT INTO businesses 
            (name, domain, email, phone, address, city, rating, reviews, seo_score, 
             seo_issues, word_count, has_schema, mobile_viewport, first_seen, last_updated)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (business.get('name',''), domain, business.get('email',''), business.get('phone',''),
             business.get('address',''), business.get('city',''), business.get('rating',''),
             business.get('reviews',0), business.get('seoScore',0),
             json.dumps(business.get('seoIssues',[])), business.get('wordCount',0),
             business.get('hasSchema',False), business.get('mobileViewport',False), now, now))
        print(f"[DB] Added new: {domain}")
    
    conn.commit()
    conn.close()


async def pipeline(job_id, trade, city, count, email_type):
    job = jobs[job_id]
    
    job['log'].append(f'🔍 Searching Google Maps + organic for {trade} in {city}...')
    businesses = await find_businesses(trade, city, count)
    job['log'].append(f'✅ Found {len(businesses)} businesses')
    job['total'] = len(businesses)
    
    for i, biz in enumerate(businesses):
        job['log'].append(f'🌐 Analysing {biz["name"]}...')
        
        lead = {
            'id': i,
            'name': biz['name'],
            'address': biz.get('address', ''),
            'phone': biz.get('phone', ''),
            'website': biz.get('website', ''),
            'email': biz.get('email', ''),
            'rating': biz.get('rating', ''),
            'reviews': biz.get('reviews', 0),
            'city': city,
            'seoScore': 0,
            'seoIssues': [],
            'subject': '',
            'body': '',
            'status': 'analysing'
        }
        
        if biz.get('website'):
            try:
                site_data = await analyse_site(biz['website'])
                lead['seoScore'] = site_data.get('score', 0)
                lead['seoIssues'] = site_data.get('issues', [])
                lead['wordCount'] = site_data.get('wordCount', 0)
                lead['hasSchema'] = site_data.get('hasSchema', False)
                lead['mobileViewport'] = site_data.get('mobileViewport', False)
                if not lead['email']:
                    lead['email'] = site_data.get('email', '')
                job['log'].append(f'  SEO: {lead["seoScore"]}/100 — {len(lead["seoIssues"])} issues')
            except Exception as e:
                job['log'].append(f'  ⚠️ Analysis failed: {str(e)}')
                lead['seoScore'] = 20
        
        # Save to database
        save_to_db(lead)
        
        if lead['email']:
            try:
                biz_data = {**biz, **lead}
                email_result = await generate_email(biz_data, email_type, city)
                lead['subject'] = email_result.get('subject', '')
                lead['body'] = email_result.get('body', '')
                lead['confidence'] = email_result.get('confidence', 'review')
                lead['flagReason'] = email_result.get('flagReason', '')
                lead['status'] = 'ready'
                job['log'].append(f'  ✉️ Email generated')
            except Exception as e:
                lead['status'] = 'email_failed'
                job['log'].append(f'  ⚠️ Email failed: {str(e)}')
        else:
            lead['status'] = 'no_email'
            job['log'].append(f'  ❌ No email found')
        
        job['leads'].append(lead)
        job['progress'] = i + 1
        await asyncio.sleep(random.uniform(1.5, 3.0))
    
    job['status'] = 'complete'
    job['log'].append(f'🎉 Done! {len([l for l in job["leads"] if l["status"]=="ready"])} ready to send')


if __name__ == '__main__':
    print("\n" + "="*50)
    print("  OutreachOS Backend + Database running!")
    print("  Database: outreach_database.db")
    print("  Open outreach-dashboard-complete.html")
    print("="*50 + "\n")
    app.run(port=5000, debug=False)
