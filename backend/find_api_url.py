import urllib.request
import re
from bs4 import BeautifulSoup

url = "https://www.cjphub.com/"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    print("Fetching homepage...")
    html = urllib.request.urlopen(req).read().decode('utf-8')
    
    # Extract and fetch Next.js JS bundles
    soup = BeautifulSoup(html, 'html.parser')
    scripts = soup.find_all('script')
    js_urls = []
    for s in scripts:
        src = s.get('src')
        if src and '_next/static' in src:
            if src.startswith('/'):
                js_urls.append(url.rstrip('/') + src)
            else:
                js_urls.append(src)
                
    print(f"Found {len(js_urls)} Next.js script bundles. Scanning them...")
    for js_url in js_urls:
        try:
            js_req = urllib.request.Request(js_url, headers={'User-Agent': 'Mozilla/5.0'})
            js_content = urllib.request.urlopen(js_req).read().decode('utf-8')
            
            # Find all http/https urls
            matches = re.findall(r'https?://[a-zA-Z0-9\-\.\/]+', js_content)
            
            # Filter specifically for railway, render, supabase, neon, cjp, cjphub, or api
            target_matches = []
            for m in matches:
                m_lower = m.lower()
                if any(t in m_lower for t in ['railway', 'render', 'supabase', 'neon', 'cjp', 'api']):
                    target_matches.append(m)
                    
            if target_matches:
                print(f"FOUND IN {js_url.split('/')[-1]}:", set(target_matches))
        except Exception as e:
            pass
            
except Exception as e:
    print("Error:", e)
