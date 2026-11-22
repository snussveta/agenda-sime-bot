import urllib.request
import re

url = "https://agenda.sime.md/ords/r/agenda/main/public"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode("utf-8")
        print("Status: 200, length:", len(html))
        # Look for login dialog urls
        for utype in ["1", "2"]:
            pattern = rf'openUrl\((["\'])(https?://agenda\.sime\.md/ords/r/agenda/main/login[^"\']*P101_USER_TYPE={utype}[^"\']*)\1'
            m = re.search(pattern, html)
            print(f"User type {utype} regex match:", bool(m))
            if m:
                print(f"   URL: {m.group(2)[:80]}...")
            else:
                # Search all login occurrences
                all_login = re.findall(r'https?://agenda\.sime\.md/ords/r/agenda/main/login[^\'"]*', html)
                print(f"   All login matches count: {len(all_login)}")
                for l in all_login[:3]:
                    print("     ", l[:80])
except Exception as e:
    print("Request error:", e)
