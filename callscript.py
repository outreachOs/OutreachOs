"""
callscript.py — AI call script generator
Generates unique cold call scripts based on real SEO data
"""

import os
import json
import urllib.request


# Business impact translations for common SEO issues
ISSUE_LIBRARY = {
    "No page title": {
        "pitch": "your site has no page title — Google literally can't tell what you do",
        "impact": "When people search 'plumber in [CITY]', you're invisible. Competitors with proper titles are getting those jobs. You're losing 5-10 calls a day minimum.",
        "severity": "very high"
    },
    "Title too short": {
        "pitch": "your page title is way too short — missing location and service keywords",
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
        "impact": "Google needs 400+ words to take a page seriously. Thin content = low quality in Google's eyes = you don't rank. Plus customers land and bounce immediately because there's no info.",
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
    Generate FULL AI-powered call script customized to this business
    
    Args:
        company: Dict with name, seoScore, seoIssues, wordCount, etc.
        location: City name
    
    Returns:
        Dict with script (full text), issues_breakdown, score, confidence
    """
    
    # Extract business details
    name = company.get('firstName', '') or (company.get('name', '').split()[0] if company.get('name') else '')
    business_name = company.get('name', 'the business')
    score = company.get('seoScore', company.get('score', 25))
    issues = company.get('seoIssues', [])
    word_count = company.get('wordCount', 0)
    
    # Pick top 3 most impactful issues
    priority_issues = sorted(
        issues[:5],
        key=lambda i: {'red': 3, 'orange': 2, 'yellow': 1}.get(i.get('severity', 'yellow'), 0),
        reverse=True
    )[:3]
    
    # Build business-friendly explanations
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
    
    # Get API key
    api_key = os.environ.get('OPENROUTER_API_KEY', '').strip()
    if not api_key:
        print("[CallScript] No API key — using fallback")
        return _fallback_script(name, business_name, location, score, issues_breakdown)
    
    # Build prompt
    issues_text = '\n\n'.join(issues_for_prompt)
    
    prompt = f"""You are a UK sales expert. Write a COMPLETE cold call script for calling {business_name}, a plumbing business in {location}.

Their website scores {score}/100 for SEO. Here are the specific problems:

{issues_text}

Write a FULL SCRIPT with word-for-word dialogue for each section:

1. OPENING (Your first 10 seconds):
Write EXACT words: "Hi {name if name else 'there'}, this is [Your Name] from [Your Company]. I'll be upfront — this is a cold call about your website, but I promise I'll keep it really quick. Is now a good time?"

2. THE HOOK (15 seconds):
Write EXACT dialogue: I searched for plumbers in {location} on Google and {business_name} wasn't showing up. I looked at your site and it's scoring {score}/100, which explains the issue.

3. THE PROBLEM BREAKDOWN (40 seconds):
Pick the 2 WORST issues from above. For each:
- Explain in PLAIN ENGLISH (no jargon)
- State EXACT business impact (lost calls, customers going elsewhere)
- Use NUMBERS (e.g., "You're losing 5-10 calls a day")

Write as SPOKEN DIALOGUE — short sentences, easy to say out loud.

4. THE TRANSITION (10 seconds):
"Look, I know you're busy running a business, not worrying about websites..."

5. THE OFFER (15 seconds):
Offer free breakdown. Make it clear:
- Completely free
- Takes 5 minutes to read
- Shows exactly what's wrong
- No strings attached

6. THE CLOSE (10 seconds):
Ask for their email. Make it easy and low-pressure.

RULES:
- Write EVERY WORD they should say
- Short sentences — easy to say
- NO jargon or technical terms
- Conversational tone
- Focus on CONSEQUENCES (lost money, lost customers)
- Make each script UNIQUE based on their issues
- Include natural pauses

Format with clear section headers."""

    # Call AI
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
        print(f"[CallScript] AI failed: {e} — using fallback")
        return _fallback_script(name, business_name, location, score, issues_breakdown)


def _call_ai(api_key, prompt):
    """Make HTTP request to OpenRouter API"""
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
                "max_tokens": 1200,
                "temperature": 0.85,
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
            
            with urllib.request.urlopen(req, timeout=35) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            
            return data['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"[CallScript] Model {model} failed: {e}")
            continue
    
    raise RuntimeError("All AI models failed")


def _fallback_script(name, business_name, location, score, issues_breakdown):
    """Fallback template if AI fails"""
    greeting = f"Hi {name}," if name else "Hi there,"
    
    issues_text = ""
    for i, issue in enumerate(issues_breakdown[:2], 1):
        issues_text += f"\n\n{i}. {issue['issue']}\n{issue['explanation']}"
    
    script = f"""OPENING (10 seconds)
{greeting} this is [Your Name] from [Your Company]. I'll be upfront — this is a cold call about your website's Google visibility, but I promise I'll keep it really quick. Is now a good time?

[If yes, continue. If no: "No worries — can I call back tomorrow?"]

THE HOOK (15 seconds)
So I was searching for plumbers in {location} on Google earlier, and {business_name} wasn't showing up at all. I had a quick look at your site and ran it through our SEO tool — it's scoring {score} out of 100, which explains why you're not appearing in searches.

THE PROBLEM BREAKDOWN (40 seconds)
There are a couple of specific things costing you calls every day:{issues_text}

THE TRANSITION (10 seconds)
Look, I know you're busy running a business, not worrying about websites. That's exactly why I'm calling.

THE OFFER (15 seconds)
What I'd like to do is send you a free breakdown of what I found. It's a 5-minute read, shows you exactly what's wrong and how to fix it. Completely free, no strings attached, I'm not going to call you trying to sell anything.

THE CLOSE (10 seconds)
If that sounds useful, what's the best email address to send it to?

[Get email, thank them, end call]"""

    return {
        'script': script,
        'issues_breakdown': issues_breakdown,
        'score': score,
        'confidence': 'medium'
    }
