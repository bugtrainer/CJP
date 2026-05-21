import urllib.request

url = "http://66.33.22.105/"
req = urllib.request.Request(url, headers={
    'Host': 'cjp-production.up.railway.app',
    'User-Agent': 'Mozilla/5.0'
})

try:
    with urllib.request.urlopen(req, timeout=10) as response:
        print(f"STATUS: {response.getcode()}")
        print(f"BODY: {response.read().decode('utf-8')}")
except Exception as e:
    print(f"FAILED: {e}")
