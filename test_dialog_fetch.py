import urllib.request
import http.cookiejar
import re
import html

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# 1. Fetch public
req1 = urllib.request.Request("https://agenda.sime.md/ords/r/agenda/main/public", headers=headers)
with opener.open(req1) as resp1:
    raw_html = resp1.read().decode("utf-8")
    print("Public page fetched, cookies:", len(cj))

# 2. Extract dialog URL
text = html.unescape(raw_html)
try:
    text = text.encode("utf-8").decode("unicode_escape")
except Exception:
    pass

pattern = r'(/ords/r/agenda/main/login[^"\'\)]*p101_user_type=2[^"\'\)]*)'
m = re.search(pattern, text, re.IGNORECASE)
if not m:
    print("Could not find dialog url!")
    exit(1)

dialog_rel = m.group(1).split("',")[0].split('",')[0].strip()
dialog_url = "https://agenda.sime.md" + dialog_rel
print("Dialog URL:", dialog_url)

# 3. Fetch dialog with cookies
req2 = urllib.request.Request(dialog_url, headers={**headers, "Referer": "https://agenda.sime.md/ords/r/agenda/main/public"})
with opener.open(req2) as resp2:
    dhtml = resp2.read().decode("utf-8")
    print("Dialog HTML fetched, length:", len(dhtml))
    with open("dialog.html", "w", encoding="utf-8") as f:
        f.write(dhtml)
    print("Cookies now:", len(cj))
    for c in cj:
        print("  Cookie:", c.name, "=", c.value[:20])
