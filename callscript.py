"""
callscript.py — AI-generated unique call scripts
Translates SEO issues into real business consequences
"""

import os
import json
import re
import urllib.request


ISSUE_LIBRARY = {
    "No page title": {
        "pitch": "your site has no page title — Google literally can't tell what you do",
        "impact": "When people search 'plumber in [CITY]', you're invisible. Your competitors with proper titles are getting those jobs. You're losing 5-10 calls a day minimum.",
        "severity": "very high"
    },
    "Title too short": {
        "pitch": "your page title is way too short — missing the location and service keywords",
        "impact": "Google doesn't know where you operate or what you do, so it ranks you below competitors who make it obvious. Costs you 3-5 calls daily.",
        "severity": "high"
    },
    "No meta description": {
        "pitch": "you're missing the description that shows up under your site in Google",
        "impact": "When people DO find you, they see a messy auto-snippet instead of a compelling reason to click. Your click-through rate is probably 50% of what it should be.",
        "severity": "medium"
    },
    "No H1 heading": {
        "pitch": "your homepage has no main heading",
        "impact": "Google reads the H1 first to understand your page. Without it, Google literally guesses what you do and usually gets it wrong. You won't rank for anything specific.",
        "severity": "very high"
    },
    "Very thin content": {
        "pitch": "your site has barely any text — only [WORDS] words",
        "impact": "Google needs 400+ words to take a page seriously. Thin content = low quality in Google's eyes = you don't rank. Plus customers land and bounce immediately because there's no info. You're losing every single person who does find you.",
        "severity": "critical"
    },
    "Thin content": {
        "pitch": "your homepage is light on content — only [WORDS] words",
        "impact": "Your competitors with 500+ words consistently outrank you. Every position down in Google = 30% fewer clicks. If you're on page 2, you've lost 95% of potential customers.",
        "severity": "high"
    },
    "Not mobile optimised": {
        "pitch": "your site isn't set up for mobile",
        "impact": "60% of plumber searches happen on phones. Your site is unusable on mobile, so people hit back and call someone else within 3 seconds. You're literally turning away 6 out of 10 potential customers.",
        "severity": "critical"
    },
    "No schema markup": {
        "pitch": "you're missing structured data",
        "impact": "Your competitors show up with star ratings, phone numbers, and prices directly in Google. You show up as plain text. They get 40% more clicks even when ranking below you.",
        "severity": "medium"
    },
    "No phone number visible": {
        "pitch": "there's no phone number on your homepage",
        "impact": "Emergency plumbing = people want to call NOW. They land on your site, can't find a number in 3 seconds, and bounce to a competitor. You're losing urgent jobs every single day.",
        "severity": "high"
    },
    "No address/postcode found": {
        "pitch": "your physical address isn't on the site",
        "impact": "Google uses addresses for local rankings. Without one visible, Google doesn't trust you're actually in [CITY]. You won't show up for 'plumber near me' or any area-specific searches. That's 70% of local searches you're invisible for.",
        "severity": "critical"
    },
}


async def generate_call_script_ai(company: dict, location: str) -> dict:
    """
    Generate UNIQUE AI call script - no templates
    """
    
    name = company.get('firstName', '') or (company.get('name', '').split()[0] if company.get('name') else '')
    business_name = company.get('name', 'the business')
    score = company.get('seoScore', company.get('score', 25))
    issues = company.get('seoIssues', [])
    word_count = company.get('wordCount', 0)
    
    # Pick top 3 issues
    priority_issues = sorted(
        issues[:5],
        key=lambda i: {'red': 3, 'orange': 2, 'yellow': 1}.get(i.get('severity', 'yellow'), 0),
        reverse=True
    )[:3]
    
    # Build business impact explanations
    issues_breakdown = []
    issues_for_prompt = []
    
    for issue in priority_issues:
        title = issue.get('title', '')
        template = ISSUE_LIBRARY.get(title, {
            "pitch": f"{title.lower()}",
            "impact": "This makes it harder for customers to find you and costs you calls every day.",
            "severity": "medium"
        })
        
        pitch = template['pitch'].replace('[WORDS]', str(word_count)).replace('[CITY]', location)
        impact = template['impact'].replace('[CITY]', location)
        
        issues_for_prompt.append(f"Issue: {pitch}\nBusiness impact: {impact}")
        issues_breakdown.append({
            'issue': title,
            'explanation': impact,
            'severity': template['severity']
        })
    
    # Call AI to generate unique script
    api_key = os.environ.get('OPENROUTER_API_KEY', '').strip()
    if not api_key:
        return _fallback_script(name, business_name, location, score, issues_breakdown)
    
    issues_text = '\n\n'.join(issues_for_prompt)
    
    prompt = f"""You are a UK sales expert writing a unique cold call script for calling {business_name}, a plumbing business in {location}.

Their website scores {score}/100 for SEO. Here are the specific problems and business impacts:

{issues_text}

Write a natural, conversational script with these sections:

OPENING (10 seconds):
Start with: "Hi {name if name else 'there'}, this is [Your Name] — I'll be upfront, this is a cold call about your website, but I'll keep it really quick. Is now okay?"

THE HOOK (15 seconds):
Mention you searched for plumbers in {location} on Google and {business_name} wasn't appearing. Their SEO score is {score}/100 which explains why.

THE PROBLEMS (30 seconds):
Pick the 2 most impactful issues from above. Explain them in PLAIN ENGLISH using the business impacts provided. Focus on what it's costing them in real terms — lost calls, lost customers, lost revenue. Be specific with numbers where possible. Make it feel urgent but not aggressive.

THE OFFER (10 seconds):
Offer to send them a free breakdown of what you found. 5 minute read, shows exactly what's wrong, zero strings attached.

THE CLOSE:
Ask for their email to send it to.

CRITICAL RULES:
- Write NATURALLY like a real conversation — not robotic
- Use SHORT sentences — easy to say out loud
- NO jargon or technical terms
- Focus on CONSEQUENCES — lost calls, customers going elsewhere, wasted money
- Make each script unique based on THEIR specific issues
- Be friendly but direct
- Don't be salesy or pushy

Format as clean text with clear section headers."""

    import asyncio
    loop = asyncio.get_event_loop()
    
    try:
        script = await loop.run_in_executor(None, lambda: _call_ai(api_key, prompt))
        return {
            'script': script,
            'issues_breakdown': issues_breakdown,
            'score': score,
            'confidence': 'high'
        }
    except Exception as e:
        print(f"[CallScript] AI failed: {e}")
        return _fallback_script(name, business_name, location, score, issues_breakdown)


def _call_ai(api_key, prompt):
    models = [
        "meta-llama/llama-4-scout:free",
        "google/gemini-2.0-flash-exp:free",
        "openrouter/free"
    ]
    
    for model in models:
        try:
            payload = json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 900,
                "temperature": 0.9,
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
            
            return data['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"[CallScript] Model {model} failed: {e}")
            continue
    
    raise RuntimeError("All models failed")


def _fallback_script(name, business_name, location, score, issues_breakdown):
    """Last resort if AI completely fails"""
    greeting = f"Hi {name}," if name else "Hi there,"
    
    issues_text = ""
    for i, issue in enumerate(issues_breakdown[:2], 1):
        issues_text += f"\n{i}. {issue['issue']}: {issue['explanation']}"
    
    script = f"""OPENING (10 seconds)
{greeting} this is [Your Name] — I'll be upfront, this is a cold call about your website's visibility on Google, but I'll keep it really quick. Is now okay?

THE HOOK (15 seconds)
I was searching for plumbers in {location} on Google and {business_name} wasn't showing up. I had a look at your site and it's scoring {score}/100 for SEO — which explains why you're invisible.

THE PROBLEMS (30 seconds)
A couple of specific things that are costing you calls:{issues_text}

THE OFFER (10 seconds)
I can send you a free breakdown showing exactly what's wrong and how to fix it. 5 minute read, zero strings attached.

THE CLOSE
What's the best email to send that to?"""

    return {
        'script': script,
        'issues_breakdown': issues_breakdown,
        'score': score,
        'confidence': 'medium'
    }
