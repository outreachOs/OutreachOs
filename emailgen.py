"""
emailgen.py — AI email generation via OpenRouter free tier
Models: tries llama-4-scout first, falls back to openrouter/free router
No credit card needed.
"""

import os
import json
import re
import urllib.request
import urllib.error

# Free models to try in order — if one fails, moves to next
FREE_MODELS = [
    "meta-llama/llama-4-scout:free",
    "meta-llama/llama-4-maverick:free",
    "google/gemini-2.0-flash-exp:free",
    "openrouter/free",   # catch-all — picks any free model automatically
]


async def generate_email(company: dict, email_type: str, location: str) -> dict:
    """
    Generate a personalised cold email based on real site analysis data.
    Tries multiple free models until one works.
    """

    issues = company.get('seoIssues', [])
    top_issues = [i['title'] for i in issues[:3]] if issues else [
        f'Not ranking for plumber searches in {location}',
        'Website content too thin for Google to rank',
        'Missing local SEO signals'
    ]

    name = company.get('firstName', '') or company.get('name', '').split()[0]
    domain = (
        company.get('website', '')
        .replace('https://', '').replace('http://', '').replace('www.', '')
        .split('/')[0]
    )
    score  = company.get('seoScore', company.get('score', 25))
    reviews = company.get('reviews', 0)

    type_instructions = {
        'cold':     'a cold intro email — first ever contact. Be friendly and specific. End with one soft question.',
        'followup': "a follow-up email — they haven't replied to a previous email. Reference sending one before. Even shorter.",
        'audit':    'an email offering a completely free SEO audit. Lead with the free offer. No strings attached.',
    }

    greeting    = f"Hey {name}," if name and len(name) > 1 else "Hi there,"
    issues_str  = '\n'.join([f'- {issue}' for issue in top_issues])
    review_note = ''
    if reviews and reviews < 10:
        review_note = f'\n- Only {reviews} Google reviews (competitors likely have more)'
    elif not reviews:
        review_note = '\n- No visible Google reviews found'

    prompt = f"""You are a UK cold email expert. Write {type_instructions.get(email_type, type_instructions['cold'])}

REAL data found about this business:
- Business name: {company.get('name', 'the business')}
- Website: {domain}
- Location: {location}
- SEO Score: {score}/100 (very low — they need help)
- Word count on homepage: {company.get('wordCount', 'unknown')}
- Top issues found:
{issues_str}{review_note}
- Has schema markup: {company.get('hasSchema', False)}
- Mobile optimised: {company.get('mobileViewport', 'unknown')}

RULES:
1. Greeting must be exactly: "{greeting}"
2. Reference the REAL issues — make it feel like you actually looked at their site
3. Mention {location} naturally
4. Max 130 words — short emails get more replies
5. One clear soft CTA at the end
6. Friendly and human — NOT corporate or salesy
7. Sign off as: [Your Name] / [Your Business]
8. confidence: "auto" if email looks genuine, else "review"
9. flagReason: brief reason if "review", empty string if "auto"

Respond with ONLY a valid JSON object — no markdown, no explanation, no code fences:
{{"subject":"...","body":"...","confidence":"auto","flagReason":""}}"""

    api_key = os.environ.get('OPENROUTER_API_KEY', '').strip()
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY not set.\n"
            "Close this window, double-click START.bat and paste your key when asked."
        )

    import asyncio
    loop = asyncio.get_event_loop()

    last_error = None
    for model in FREE_MODELS:
        try:
            result = await loop.run_in_executor(None, lambda m=model: _call_api(api_key, m, prompt))
            return result
        except Exception as e:
            print(f"[EmailGen] Model {model} failed: {e} — trying next...")
            last_error = e
            continue

    raise RuntimeError(f"All free models failed. Last error: {last_error}")


def _call_api(api_key: str, model: str, prompt: str) -> dict:
    """Make a synchronous call to OpenRouter and return parsed email dict."""
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 700,
        "temperature": 0.7,
    }).encode('utf-8')

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "OutreachOS",
        }
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode('utf-8'))

    raw = data['choices'][0]['message']['content'].strip()
    raw = re.sub(r'```json|```', '', raw).strip()

    # Extract JSON if the model wraps it in extra prose
    json_match = re.search(r'\{.*\}', raw, re.DOTALL)
    if json_match:
        raw = json_match.group(0)

    return json.loads(raw)
