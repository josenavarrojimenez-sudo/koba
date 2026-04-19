---
name: web-content-extractor
description: Extract content from web pages with bot protection (Cloudflare, etc.) using Jina.ai Reader and alternative extractors — bypass paywalls, login walls, and anti-bot measures
category: research
---

# Web Content Extractor - Bypass Bot Protection

Extract readable content from web pages that have Cloudflare protection, paywalls, login requirements, or aggressive anti-bot measures.

## When to Use

Use this skill when:
- `browser_navigate` returns "Just a moment..." (Cloudflare challenge)
- You get 403 Forbidden errors from curl/requests
- The site requires login/registration to view content
- You need to extract article text without ads/clutter
- Standard web scraping tools fail due to bot detection

## Primary Tool: Jina.ai Reader

**Jina.ai Reader** is a free service that fetches web pages and returns clean markdown content. It bypasses many bot protection systems because the request comes from Jina's infrastructure, not yours.

### Basic Usage

```python
import requests

def extract_web_content(url):
    """Extract content from any URL using Jina.ai Reader"""
    jina_url = f"https://r.jina.ai/http://{url}"
    
    response = requests.get(jina_url, timeout=30)
    
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"Failed: {response.status_code}")

# Example
content = extract_web_content("claude.ai/public/artifacts/abc-123")
print(content)
```

### URL Format

```
https://r.jina.ai/http://[ORIGINAL_URL]
```

**Examples:**

| Original URL | Jina Reader URL |
|--------------|-----------------|
| `https://example.com/article` | `https://r.jina.ai/http://example.com/article` |
| `https://claude.ai/public/artifacts/xyz` | `https://r.jina.ai/http://claude.ai/public/artifacts/xyz` |
| `https://medium.com/@user/story` | `https://r.jina.ai/http://medium.com/@user/story` |

### What You Get

Jina.ai returns:
- **Title** of the page
- **URL Source** for reference
- **Markdown content** — clean text without ads/navigation
- **Warnings** about hidden elements (iframes, shadow DOM)

**Example Output:**
```
Title: AI Assistant for Supermarkets | WhatsApp Retail Solution

URL Source: http://claude.ai/public/artifacts/ae83c31b-...

Markdown Content:
# Main Heading

Article content here in clean markdown format...

- Bullet points preserved
- Links included
- Code blocks formatted
```

## Alternative Extractors

If Jina.ai fails, try these alternatives:

### 1. Firecrawl

```python
# If you have Firecrawl API key
import requests

url = "https://api.firecrawl.dev/v0/scrape"
headers = {"Authorization": "Bearer YOUR_API_KEY"}
payload = {"url": "https://target-site.com/page"}

response = requests.post(url, json=payload, headers=headers)
content = response.json()["data"]["markdown"]
```

### 2. 12ft.io (Paywall Bypass)

```python
# Bypasses paywalls for news sites
jina_url = f"https://r.jina.ai/http://12ft.io/proxy?q={target_url}"
```

### 3. Archive.org Wayback Machine

```python
# For deleted or archived pages
import requests

wayback_url = f"https://web.archive.org/web/2026/{target_url}"
response = requests.get(wayback_url)
```

### 4. Google Cache

```python
# Access cached version via Google
cache_url = f"https://webcache.googleusercontent.com/search?q=cache:{target_url}"
```

## Complete Extraction Pipeline

```python
import requests
from datetime import datetime

def extract_content_fallback(target_url):
    """Try multiple extractors until one works"""
    
    extractors = [
        # Primary: Jina.ai Reader
        f"https://r.jina.ai/http://{target_url}",
        
        # Fallback 1: Jina with 12ft proxy
        f"https://r.jina.ai/http://12ft.io/proxy?q={target_url}",
        
        # Fallback 2: Wayback Machine (current year)
        f"https://web.archive.org/web/2026/{target_url}",
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    for extractor_url in extractors:
        print(f"Trying: {extractor_url[:60]}...")
        
        try:
            response = requests.get(extractor_url, headers=headers, timeout=20)
            
            if response.status_code == 200:
                content = response.text
                
                # Check if we got actual content
                if len(content.strip()) > 500:
                    if "cloudflare" in content.lower() or "just a moment" in content.lower():
                        print("❌ Still blocked by Cloudflare")
                        continue
                    
                    print(f"✅ Success! Got {len(content)} chars")
                    return content
                else:
                    print(f"❌ Content too short: {len(content)} chars")
            else:
                print(f"❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    raise Exception("All extractors failed")

# Usage
content = extract_content_fallback("claude.ai/public/artifacts/xyz")
```

## Terminal One-Liners

Quick extraction from command line:

```bash
# Jina.ai Reader
curl -s "https://r.jina.ai/http://claude.ai/public/artifacts/abc-123"

# Save to file
curl -s "https://r.jina.ai/http://example.com/article" > content.md

# Preview first 50 lines
curl -s "https://r.jina.ai/http://example.com/article" | head -50
```

## Python Script for Reuse

Save as `~/.hermes/scripts/extract_web_content.py`:

```python
#!/usr/bin/env python3
"""
Extract web content using Jina.ai Reader
Usage: python3 extract_web_content.py <url>
"""
import sys
import requests

def extract(url):
    jina_url = f"https://r.jina.ai/http://{url}"
    print(f"📡 Extracting: {url}")
    print(f"🔗 Via: {jina_url}")
    
    resp = requests.get(jina_url, timeout=30)
    
    if resp.status_code == 200:
        print(f"✅ Success! {len(resp.text)} characters")
        print("\n" + "="*60)
        print(resp.text[:5000])  # Preview first 5000 chars
        return resp.text
    else:
        print(f"❌ Failed: HTTP {resp.status_code}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 extract_web_content.py <url>")
        sys.exit(1)
    
    extract(sys.argv[1])
```

Make executable:
```bash
chmod +x ~/.hermes/scripts/extract_web_content.py
```

## Limitations

| Limitation | Workaround |
|------------|------------|
| Shadow DOM / iframes | Jina warns about these — content may be incomplete |
| JavaScript-heavy sites | Try browser_navigate with BROWSERBASE_ADVANCED_STEALTH=true |
| Rate limiting | Add delays between requests |
| Very aggressive bot detection | May need residential proxies (Browserbase Scale plan) |
| Login-required content | Use cookies/session from authenticated browser |

## Best Practices

1. **Always try Jina.ai first** — works 80% of the time
2. **Check the warnings** — Jina tells you if content is incomplete
3. **Use fallbacks** — have 2-3 extractors ready
4. **Respect robots.txt** — don't abuse the service
5. **Cache results** — save extracted content locally for reference

## Related Skills

- `youtube-content` — Fetch YouTube transcripts
- `blogwatcher` — Monitor blogs and RSS feeds
- `ocr-and-documents` — Extract text from PDFs and scanned docs

## Example: Extract Claude Artifact

```python
import requests

url = "claude.ai/public/artifacts/ae83c31b-2f55-4e51-b29c-e10042b00171"
jina_url = f"https://r.jina.ai/http://{url}"

resp = requests.get(jina_url)
print(resp.text)
```

Output:
```
Title: AI Assistant for Supermarkets | WhatsApp Retail Solution

URL Source: http://claude.ai/public/artifacts/ae83c31b-...

Markdown Content:
[Content extracted successfully]
```

## Security Notes

- Jina.ai sees the URLs you request — don't use for sensitive/internal URLs
- The service is free but rate-limited for heavy usage
- For production use, consider self-hosting similar extractors
