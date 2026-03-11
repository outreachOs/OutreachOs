"""
app.py — Flask backend with all fixes applied
Main API server for OutreachOS platform
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import json
import time
import threading
import asyncio
from scraper import find_businesses, analyse_site
from emailgen import generate_email

app = Flask(__name__)
CORS(app)

DB_PATH = 'outreach_database.db'
jobs = {}  # In-memory job storage


def init_db():
    """Initialize SQLite database with schema"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS businesses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        domain TEXT UNIQUE,
        email TEXT,
        phone TEXT,
        address TEXT,
        city TEXT,
        rating TEXT,
        reviews INTEGER DEFAULT 0,
        seo_score INTEGER DEFAULT 0,
        seo_issues TEXT,
        word_count INTEGER DEFAULT 0,
        has_schema BOOLEAN DEFAULT 0,
        mobile_viewport BOOLEAN DEFAULT 0,
        first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'pending'
    )''')
    conn.commit()
    conn.close()
    print("[DB] Database initialized")


def save_to_db(business):
    """
    Save or update business in database
    Prevents duplicates by checking domain first
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    domain = business.get('website', '').replace('https://','').replace('http://','').replace('www.','').split('/')[0]
    
    # Skip if no domain
    if not domain:
        conn.close()
        return
    
    # Check if exists
    c.execute('SELECT id, seo_score FROM businesses WHERE domain = ?', (domain,))
    existing = c.fetchone()
    
    if existing:
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
        # New business
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


def pipeline(job_id, trade, city, count, email_type):
    """
    Main processing pipeline
    1. Find businesses
    2. Analyze each site
    3. Save to database
    4. Generate email
    """
    job = jobs[job_id]
    
    try:
        # Step 1: Find businesses
        job['log'].append(f"🔍 Searching Google Maps for {trade} in {city}...")
        businesses = asyncio.run(find_businesses(trade, city, count))
        job['log'].append(f"✅ Found {len(businesses)} businesses")
        job['total'] = len(businesses)
        
        # Step 2-4: Process each
        for i, biz in enumerate(businesses):
            job['progress'] = i + 1
            job['log'].append(f"[{i+1}/{len(businesses)}] Analyzing {biz.get('name', 'Unknown')}...")
            
            # Analyze website
            if biz.get('website'):
                analysis = asyncio.run(analyse_site(biz['website']))
                biz.update(analysis)
            
            # Save to database
            save_to_db(biz)
            
            # Generate email if has email
            if biz.get('email'):
                job['log'].append(f"  → Generating email for {biz['name']}...")
                email_result = asyncio.run(generate_email(biz, city, email_type))
                
                if email_result.get('subject'):
                    biz['subject'] = email_result['subject']
                    biz['body'] = email_result['body']
                    biz['status'] = 'ready'
                    job['log'].append(f"  ✅ Email ready")
                else:
                    biz['status'] = 'flagged'
                    job['log'].append(f"  ⚠️ Flagged: {email_result.get('reason', 'Unknown')}")
            else:
                biz['status'] = 'no_email'
                job['log'].append(f"  ❌ No email found")
            
            job['leads'].append(biz)
        
        job['status'] = 'complete'
        job['log'].append(f"🎉 Complete! {len([l for l in job['leads'] if l.get('status')=='ready'])} emails ready")
        
    except Exception as e:
        job['status'] = 'error'
        job['log'].append(f"❌ Error: {str(e)}")
        print(f"[Pipeline] Error: {e}")


@app.route('/api/search', methods=['POST'])
def search():
    """Start a new search job"""
    data = request.json
    job_id = str(int(time.time() * 1000))
    
    jobs[job_id] = {
        'id': job_id,
        'status': 'running',
        'progress': 0,
        'total': 0,
        'log': [],
        'leads': []
    }
    
    # Start pipeline in background
    thread = threading.Thread(
        target=pipeline,
        args=(job_id, data['trade'], data['city'], data['count'], data.get('emailType', 'cold'))
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({'job_id': job_id})


@app.route('/api/job/<job_id>', methods=['GET'])
def get_job(job_id):
    """Poll job status"""
    # Handle connection check
    if job_id == 'test':
        return jsonify({'status': 'ok'}), 200
    
    job = jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(job)


@app.route('/api/generate-call-script', methods=['POST'])
def generate_call_script():
    """Generate AI call script for a business"""
    from callscript import generate_call_script_ai
    
    data = request.json
    company = data.get('company', {})
    location = data.get('location', 'Leicester')
    
    try:
        result = asyncio.run(generate_call_script_ai(company, location))
        return jsonify(result)
    except Exception as e:
        print(f"[CallScript] Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/database', methods=['GET'])
def get_database():
    """Get all businesses from database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM businesses ORDER BY last_updated DESC')
    rows = c.fetchall()
    conn.close()
    
    businesses = []
    for row in rows:
        biz = dict(row)
        # Parse JSON fields
        if biz.get('seo_issues'):
            try:
                biz['seoIssues'] = json.loads(biz['seo_issues'])
            except:
                biz['seoIssues'] = []
        biz['seoScore'] = biz.get('seo_score', 0)
        biz['firstSeen'] = biz.get('first_seen', '')
        businesses.append(biz)
    
    return jsonify(businesses)


@app.route('/api/database/<int:biz_id>', methods=['PATCH'])
def update_business(biz_id):
    """Update business status"""
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE businesses SET status = ?, last_updated = ? WHERE id = ?',
              (data.get('status', 'pending'), time.strftime('%Y-%m-%d %H:%M:%S'), biz_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/database/<int:biz_id>', methods=['DELETE'])
def delete_business(biz_id):
    """Delete business from database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM businesses WHERE id = ?', (biz_id,))
    conn.commit()
    conn.close()
    print(f"[DB] Deleted business ID: {biz_id}")
    return jsonify({'success': True})


if __name__ == '__main__':
    init_db()
    print("[Server] Starting on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
