"""
scraper.py — Real scraping with Playwright
Handles: Google Maps search, website content extraction, email finding, SEO scoring
"""

import re
import asyncio
import random
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# Playwright imports
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️  Playwright not installed. Run: pip install playwright && playwright install chromium")


# ── User agents to rotate (avoids basic bot detection) ──
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36",
]


async def find_businesses(trade: str, city: str, count: int = 10) -> list:
    """
    Search Google Maps for businesses and return list of results.
    Falls back to a direct Google search if Maps scraping fails.
    """
    if not PLAYWRIGHT_AVAILABLE:
        raise RuntimeError("Playwright not installed. Run: pip install playwright && playwright install chromium")

    businesses = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
            ]
        )

        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={'width': 1280, 'height': 720},
            locale='en-GB',
            timezone_id='Europe/London',
        )

        page = await context.new_page()

        # Remove webdriver flag (basic bot detection bypass)
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)

        try:
            # ── Search Google Maps ──
            search_query = f"{trade} {city}"
            maps_url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"

            print(f"[Scraper] Opening Google Maps: {maps_url}")
            await page.goto(maps_url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(2)

            # Scroll to load more results
            results_panel = page.locator('[role="feed"]').first
            for _ in range(3):
                try:
                    await results_panel.evaluate('el => el.scrollTop += 800')
                    await asyncio.sleep(1.5)
                except:
                    break

            # Extract listing cards
            cards = await page.locator('[jsaction*="pane.resultSection"]').all()
            if not cards:
                # Alternative selector
                cards = await page.locator('.Nv2PK').all()

            print(f"[Scraper] Found {len(cards)} listing cards")

            for card in cards[:count]:
                try:
                    # Click to open business panel
                    await card.click()
                    await asyncio.sleep(1.5)

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

                    # Rating & reviews
                    try:
                        # Get rating (e.g., "4.5")
                        rating_el = await page.locator('.F7nice span[aria-hidden="true"]').first.text_content(timeout=2000)
                        biz['rating'] = rating_el.strip() if rating_el else ''
                    except:
                        biz['rating'] = ''

                    try:
                        # Get review count from aria-label (e.g., "63 reviews")
                        review_el = await page.locator('span[aria-label*="review"]').first
                        aria_label = await review_el.get_attribute('aria-label', timeout=2000)
                        # Extract number from "63 reviews" or "1 review"
                        match = re.search(r'(\d+)\s*review', aria_label or '', re.IGNORECASE)
                        biz['reviews'] = int(match.group(1)) if match else 0
                    except:
                        biz['reviews'] = 0

                    if biz.get('name'):
                        businesses.append(biz)
                        print(f"[Scraper] ✓ {biz['name']} — {biz.get('website', 'no website')}")

                except Exception as e:
                    print(f"[Scraper] Card parse error: {e}")
                    continue

                await asyncio.sleep(random.uniform(0.5, 1.0))

        except Exception as e:
            print(f"[Scraper] Maps scraping error: {e}")
            # Fallback: try direct Google search
            businesses = await _google_search_fallback(page, trade, city, count)

        await browser.close()

    return businesses[:count]


async def _google_search_fallback(page, trade: str, city: str, count: int) -> list:
    """Fallback: scrape regular Google search results for business websites"""
    businesses = []
    try:
        query = f'{trade} {city} site:.co.uk OR site:.com'
        await page.goto(f'https://www.google.co.uk/search?q={query.replace(" ", "+")}', timeout=20000)
        await asyncio.sleep(2)

        # Extract organic results
        results = await page.locator('div.g').all()
        for r in results[:count]:
            try:
                title = await r.locator('h3').first.text_content(timeout=1000)
                link_el = r.locator('a').first
                href = await link_el.get_attribute('href', timeout=1000)
                if href and 'http' in href and 'google' not in href:
                    domain = urlparse(href).netloc.replace('www.', '')
                    businesses.append({
                        'name': title.strip() if title else domain,
                        'website': href,
                        'address': city,
                        'phone': '',
                        'email': '',
                        'rating': '',
                        'reviews': 0,
                    })
            except:
                continue
    except Exception as e:
        print(f"[Scraper] Google fallback error: {e}")

    return businesses


async def analyse_site(url: str) -> dict:
    """
    Visit a website and extract:
    - Page content, meta tags, headings
    - Contact email
    - SEO score and issues
    """
    if not url.startswith('http'):
        url = 'https://' + url

    result = {
        'url': url,
        'score': 0,
        'issues': [],
        'email': '',
        'title': '',
        'description': '',
        'h1': '',
        'wordCount': 0,
        'hasPhone': False,
        'hasAddress': False,
        'hasSchema': False,
        'mobileViewport': False,
        'locationMentions': 0,
    }

    if not PLAYWRIGHT_AVAILABLE:
        return result

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={'width': 375, 'height': 812},  # Mobile viewport test
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=20000)
            await asyncio.sleep(1)

            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')

            # ── Extract basic info ──
            title_tag = soup.find('title')
            result['title'] = title_tag.text.strip() if title_tag else ''

            meta_desc = soup.find('meta', attrs={'name': 'description'})
            result['description'] = meta_desc.get('content', '') if meta_desc else ''

            h1 = soup.find('h1')
            result['h1'] = h1.text.strip() if h1 else ''

            # Word count
            body_text = soup.get_text()
            words = [w for w in body_text.split() if w.strip()]
            result['wordCount'] = len(words)

            # Schema markup
            result['hasSchema'] = bool(soup.find('script', attrs={'type': 'application/ld+json'}))

            # Mobile viewport
            viewport_meta = soup.find('meta', attrs={'name': 'viewport'})
            result['mobileViewport'] = bool(viewport_meta)

            # Phone number detection
            phone_pattern = re.compile(r'(\+44|0)[\s\-]?[0-9]{3,4}[\s\-]?[0-9]{3,4}[\s\-]?[0-9]{3,4}')
            result['hasPhone'] = bool(phone_pattern.search(body_text))

            # Address detection
            postcode_pattern = re.compile(r'[A-Z]{1,2}[0-9][0-9A-Z]?\s*[0-9][A-Z]{2}', re.IGNORECASE)
            result['hasAddress'] = bool(postcode_pattern.search(body_text))

            # Extract domain to guess city
            domain = urlparse(url).netloc.replace('www.', '')

            # Find email on this page and linked pages
            result['email'] = extract_email(html, domain)
            if not result['email']:
                # Try /contact page
                contact_url = urljoin(url, '/contact')
                try:
                    await page.goto(contact_url, timeout=10000)
                    contact_html = await page.content()
                    result['email'] = extract_email(contact_html, domain)
                except:
                    pass

        except Exception as e:
            print(f"[Analyser] Error analysing {url}: {e}")

        await browser.close()

    # ── SEO Scoring ──
    result['score'], result['issues'] = _calculate_seo_score(result)
    return result


def extract_email(html: str, domain: str = '') -> str:
    """Extract email address from HTML content"""
    # Method 1: mailto: links
    mailto_pattern = re.compile(r'mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})')
    matches = mailto_pattern.findall(html)
    if matches:
        # Filter out noreply, privacy etc
        for match in matches:
            if not any(x in match.lower() for x in ['noreply', 'no-reply', 'donotreply', 'privacy', 'unsubscribe']):
                return match

    # Method 2: Plain text email pattern
    email_pattern = re.compile(r'\b([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})\b')
    matches = email_pattern.findall(html)
    for match in matches:
        if not any(x in match.lower() for x in ['noreply', 'example', 'test@', 'privacy', '@sentry', '@w3']):
            # Prefer domain-matched emails
            if domain and domain.split('.')[0] in match.lower():
                return match

    # Return first valid match
    for match in matches:
        if not any(x in match.lower() for x in ['noreply', 'example', 'test@', 'privacy', '@sentry', '@w3']):
            return match

    return ''


def _calculate_seo_score(data: dict) -> tuple:
    """Score the site and return (score, issues list)"""
    score = 100
    issues = []

    # Title tag
    if not data['title']:
        score -= 15
        issues.append({'severity': 'red', 'title': 'No page title', 'detail': 'Missing <title> tag — critical for Google ranking'})
    elif len(data['title']) < 20:
        score -= 8
        issues.append({'severity': 'orange', 'title': 'Title too short', 'detail': f'"{data["title"]}" — needs location + service keywords'})

    # Meta description
    if not data['description']:
        score -= 10
        issues.append({'severity': 'orange', 'title': 'No meta description', 'detail': 'Missing description shown in Google search results'})

    # H1
    if not data['h1']:
        score -= 12
        issues.append({'severity': 'red', 'title': 'No H1 heading', 'detail': 'Primary heading missing — Google uses this for ranking'})

    # Word count
    if data['wordCount'] < 200:
        score -= 15
        issues.append({'severity': 'red', 'title': 'Very thin content', 'detail': f'Only {data["wordCount"]} words — Google needs 400+ to rank pages'})
    elif data['wordCount'] < 400:
        score -= 8
        issues.append({'severity': 'orange', 'title': 'Thin content', 'detail': f'{data["wordCount"]} words — competitors likely have more'})

    # Mobile viewport
    if not data['mobileViewport']:
        score -= 12
        issues.append({'severity': 'red', 'title': 'Not mobile optimised', 'detail': '60%+ of searches are on mobile — Google penalises non-mobile sites'})

    # Schema markup
    if not data['hasSchema']:
        score -= 8
        issues.append({'severity': 'orange', 'title': 'No schema markup', 'detail': 'Missing structured data — competitors using this get rich results in Google'})

    # Phone number
    if not data['hasPhone']:
        score -= 5
        issues.append({'severity': 'yellow', 'title': 'No phone number visible', 'detail': 'Phone should be prominent — affects trust and conversion'})

    # Address/postcode
    if not data['hasAddress']:
        score -= 8
        issues.append({'severity': 'orange', 'title': 'No address/postcode found', 'detail': 'Local SEO requires your address on the page for area rankings'})

    return max(0, score), issues
