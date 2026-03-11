"""
emailgen.py — AI email generator
Generates personalized cold emails based on SEO data
"""

import os
import json
import urllib.request


async def generate_email(company: dict, location: str, email_type: str = 'cold') -> dict:
    """
    Generate personalized email using OpenRouter free tier
    
    Args:
        company: Dict with name, seoScore, seoIssues, email, etc.
        location: City name
        email_type: 'cold', 'audit', or 'followup'
    
    Returns:
        Dict with subject, body, confidence, flagReason (if flagged)
    """
    
    api_key = os.environ.get('OPENROUTER_API_KEY', '').strip()
    if not api_key:
        return {'subject': '', 'body': '', 'reason': 'No API key set'}
    
    # Build prompt
    issues_text = '\n'.join([f"- {issue.get('title', 'Unknown')}" for issue in company.get('seoIssues', [])[:3]])
    
    prompt = f"""Write a cold email to {company.get('name', 'this business')} in {location}.

Business details:
- SEO Score: {company.get('seoScore', 25)}/100
- Website: {company.get('website', 'unknown')}
- Main issues found:
{issues_text}

Write a {email_type} email that:
- Mentions their actual score and 1-2 real issues
- Explains business impact (lost calls, customers going to competitors)
- Offers free audit/breakdown
- Friendly, human tone (not salesy)
- 150 words max
- UK spelling

Return ONLY a JSON object with "subject" and "body" keys. No markdown, no code blocks."""

    # Try free models in order
    models = [
        "meta-llama/llama-4-scout:free",
        "meta-llama/llama-4-maverick:free",
        "google/gemini-2.0-flash-exp:free",
        "openrouter/free"
    ]
    
    for model in models:
        try:
            result = _call_api(api_key, model, prompt)
            
            # Parse JSON response
            clean = result.strip()
            if clean.startswith('```json'):
                clean = clean.split('```json')[1].split('```')[0].strip()
            elif clean.startswith('```'):
                clean = clean.split('```')[1].split('```')[0].strip()
            
            data = json.loads(clean)
            
            if data.get('subject') and data.get('body'):
                return {
                    'subject': data['subject'],
                    'body': data['body'],
                    'confidence': 'high'
                }
        
        except Exception as e:
            print(f"[EmailGen] Model {model} failed: {e}")
            continue
    
    # All models failed
    return {
        'subject': '',
        'body': '',
        'reason': 'All AI models failed to generate email'
    }


def _call_api(api_key, model, prompt):
    """Make HTTP request to OpenRouter"""
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500,
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
    
    return data['choices'][0]['message']['content']
