"""
scraper.py — Google Maps scraper with SEO analysis
Scrapes businesses and analyzes their websites
"""

import asyncio
import random
import re
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup


async def find_businesses(trade, city, count=20):
    """
    Find businesses on Google Maps
    Returns: list of dicts with name, address, phone, website, rating, reviews
    """
    businesses = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Search Google Maps
            query = f"{trade} {city}"
            url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
            print(f"[Scraper] Searching: {url}")
            
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(3)
            
            # Scroll to load more results
            for _ in range(min(count // 10, 5)):
                await page.mouse.wheel(0, 3000)
                await asyncio.sleep(1.5)
            
            # Find business cards
            cards = await page.locator('a[href*="/maps/place/"]').all()
            print(f"[Scraper] Found {len(cards)} cards")
            
            for i, card in enumerate(cards[:count]):
                if len(businesses) >= count:
                    break
                
                try:
                    # Click card to open details
                    await card.click()
                    await asyncio.sleep(random.uniform(1.5, 2.5))
                    
                    biz = {}
                    
                    # Name
                    try:
                        biz['name'] = await page.locator('h1.DUwDvf').first.text_content(timeout=3000)
                        biz['name'] = biz['name'].strip()
                    except:
                        biz['name'] = ''
                    
                    # Address
                    try:
                        biz['address'] = await page.locator('[data-item-id="address"]').first.text_content(timeout=2000)
                    except:
                        biz['address'] = city
                    
                    # Phone
                    try:
                        phone_el = page.locator('[data-item-id*="phone"]').first
                        biz['phone'] = await phone_el.get_attribute('data-item-id', timeout=2000)
                        biz['phone'] = biz['phone'].replace('phone:', '').strip() if biz['phone'] else ''
                    except:
                        biz['phone'] = ''
                    
                    # Website
                    try:
                        website_el = page.locator('a[data-item-id="authority"]').first
                        biz['website'] = await website_el.get_attribute('href', timeout=2000)
                    except:
                        biz['website'] = ''
                    
                    # Rating (FIX: Get only rating number, not review count)
                    try:
                        rating_el = await page.locator('.F7nice span[aria-hidden="true"]').first.text_content(timeout=2000)
                        biz['rating'] = rating_el.strip() if rating_el else ''
                    except:
                        biz['rating'] = ''
                    
                    # Reviews (FIX: Extract number from aria-label)
                    try:
                        review_el = await page.locator('span[aria-label*="review"]').first
                        aria_label = await review_el.get_attribute('aria-label', timeout=2000)
                        match = re.search(r'(\d+)\s*review', aria_label or '', re.IGNORECASE)
                        biz['reviews'] = int(match.group(1)) if match else 0
                    except:
                        biz['reviews'] = 0
                    
                    if biz.get('name'):
                        biz['city'] = city
                        businesses.append(biz)
                        print(f"[Scraper] ✓ {biz['name']} — {biz.get('website', 'no website')}")
                
                except Exception as e:
                    print(f"[Scraper] Card parse error: {e}")
                    continue
                
                await asyncio.sleep(random.uniform(0.5, 1.0))
        
        except Exception as e:
            print(f"[Scraper] Fatal error: {e}")
        
        finally:
            await browser.close()
    
    return businesses


async def analyse_site(url):
    """
    Analyze website for SEO issues
    Returns: dict with seoScore, seoIssues, wordCount, hasSchema, mobileViewport
    """
    result = {
        'seoScore': 0,
        'seoIssues': [],
        'wordCount': 0,
        'hasSchema': False,
        'mobileViewport': False
    }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=15000)
            await asyncio.sleep(2)
            
            # Get HTML
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Check SEO elements
            score_data = _calculate_seo_score(soup, url)
            result.update(score_data)
            
            # Extract email if present
            result['email'] = _extract_email(soup, url)
            
        except Exception as e:
            print(f"[Analyse] Error for {url}: {e}")
            result['seoScore'] = 10
            result['seoIssues'] = [{'title': 'Site unreachable', 'severity': 'red'}]
        
        finally:
            await browser.close()
    
    return result


def _calculate_seo_score(soup, url):
    """Calculate SEO score based on common issues"""
    score = 100
    issues = []
    
    # Page title
    title = soup.find('title')
    if not title or not title.string or len(title.string.strip()) < 10:
        score -= 15
        issues.append({'title': 'No page title' if not title else 'Title too short', 'severity': 'red'})
    
    # Meta description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if not meta_desc or not meta_desc.get('content'):
        score -= 10
        issues.append({'title': 'No meta description', 'severity': 'orange'})
    
    # H1 heading
    h1 = soup.find('h1')
    if not h1:
        score -= 15
        issues.append({'title': 'No H1 heading', 'severity': 'red'})
    
    # Content length
    text = soup.get_text()
    word_count = len(text.split())
    if word_count < 200:
        score -= 20
        issues.append({'title': 'Very thin content', 'severity': 'red'})
    elif word_count < 400:
        score -= 10
        issues.append({'title': 'Thin content', 'severity': 'orange'})
    
    # Mobile viewport
    viewport = soup.find('meta', attrs={'name': 'viewport'})
    mobile_viewport = bool(viewport)
    if not mobile_viewport:
        score -= 15
        issues.append({'title': 'Not mobile optimised', 'severity': 'red'})
    
    # Schema markup
    has_schema = bool(soup.find('script', attrs={'type': 'application/ld+json'}))
    if not has_schema:
        score -= 10
        issues.append({'title': 'No schema markup', 'severity': 'orange'})
    
    # Phone number visible
    phone_patterns = [r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}', r'\d{5}\s?\d{6}', r'0\d{10}']
    has_phone = any(re.search(pattern, text) for pattern in phone_patterns)
    if not has_phone:
        score -= 10
        issues.append({'title': 'No phone number visible', 'severity': 'orange'})
    
    # Address/postcode
    has_address = bool(re.search(r'\b[A-Z]{1,2}\d{1,2}\s?\d[A-Z]{2}\b', text))  # UK postcode
    if not has_address:
        score -= 10
        issues.append({'title': 'No address/postcode found', 'severity': 'orange'})
    
    return {
        'seoScore': max(0, score),
        'seoIssues': issues,
        'wordCount': word_count,
        'hasSchema': has_schema,
        'mobileViewport': mobile_viewport
    }


def _extract_email(soup, base_url):
    """Try to find email address on page"""
    # Check for mailto links
    mailto = soup.find('a', href=re.compile(r'^mailto:', re.I))
    if mailto:
        email = mailto.get('href', '').replace('mailto:', '').split('?')[0]
        if '@' in email:
            return email.lower().strip()
    
    # Look for email patterns in text
    text = soup.get_text()
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    
    # Filter out common junk emails
    junk = ['example.com', 'test.com', 'domain.com', 'email.com', 'wix.com', 'sentry.io']
    for email in emails:
        if not any(j in email.lower() for j in junk):
            return email.lower().strip()
    
    return ''
