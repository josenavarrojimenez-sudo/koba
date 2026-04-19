#!/usr/bin/env python3
"""
Extract web content using Jina.ai Reader — bypass Cloudflare and bot protection
Usage: python3 extract_web_content.py <url>

Example:
  python3 extract_web_content.py claude.ai/public/artifacts/ae83c31b-2f55-4e51-b29c-e10042b00171
"""
import sys
import requests
from pathlib import Path

def extract(url, save_output=False):
    """Extract content from URL using Jina.ai Reader"""
    
    # Normalize URL (remove https:// prefix if present)
    url = url.replace("https://", "").replace("http://", "").lstrip("/")
    
    jina_url = f"https://r.jina.ai/http://{url}"
    
    print(f"📡 Extracting: {url}")
    print(f"🔗 Via Jina: {jina_url}")
    print("="*60)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        resp = requests.get(jina_url, headers=headers, timeout=30)
        
        if resp.status_code == 200:
            content = resp.text
            
            # Check for Cloudflare block
            if "cloudflare" in content.lower() or "just a moment" in content.lower():
                print("❌ Still blocked by Cloudflare")
                sys.exit(1)
            
            print(f"✅ Success! {len(content)} characters\n")
            
            # Save to file if requested
            if save_output:
                output_path = Path(f"/root/.hermes/extracted_content/{Path(url).name or 'content'}.md")
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(content)
                print(f"💾 Saved to: {output_path}")
            
            # Print content
            print("="*60)
            print("EXTRACTED CONTENT:")
            print("="*60)
            print(content)
            
            return content
        else:
            print(f"❌ HTTP {resp.status_code}")
            print(f"Response: {resp.text[:500]}")
            sys.exit(1)
            
    except requests.exceptions.Timeout:
        print("❌ Timeout — Jina.ai took too long")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        sys.exit(1)

def extract_with_fallback(url):
    """Try multiple extractors until one works"""
    
    extractors = [
        ("Jina.ai", f"https://r.jina.ai/http://{url}"),
        ("Jina + 12ft", f"https://r.jina.ai/http://12ft.io/proxy?q={url}"),
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    for name, extractor_url in extractors:
        print(f"\n🔍 Trying {name}...")
        
        try:
            resp = requests.get(extractor_url, headers=headers, timeout=20)
            
            if resp.status_code == 200 and len(resp.text) > 500:
                if "cloudflare" not in resp.text.lower():
                    print(f"✅ {name} succeeded!")
                    return resp.text
                    
        except Exception as e:
            print(f"❌ {name} failed: {e}")
    
    raise Exception("All extractors failed")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    url = sys.argv[1]
    save = "--save" in sys.argv or "-s" in sys.argv
    
    extract(url, save_output=save)
