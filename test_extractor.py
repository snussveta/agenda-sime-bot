import re
import urllib.parse
import html

with open("public_page.html", encoding="utf-8") as f:
    raw = f.read()

# 1. Unescape HTML entities (&#x2F; -> /)
text = html.unescape(raw)
# 2. Decode unicode escape sequences (\u002F -> /)
try:
    text = text.encode("utf-8").decode("unicode_escape")
except Exception:
    pass

def extract_login_url(content: str, user_type: str) -> str:
    # Pattern 1: match dialog or openUrl with login_desktop or login
    pattern = rf'(/ords/r/agenda/main/login[^"\'\)]*p101_user_type={user_type}[^"\'\)]*)'
    m = re.search(pattern, content, re.IGNORECASE)
    if m:
        raw_url = m.group(1).split("',")[0].split('",')[0].strip()
        return urllib.parse.urljoin("https://agenda.sime.md", raw_url)
    return ""

print("Student (2):", extract_login_url(text, "2"))
print("Parent (1):", extract_login_url(text, "1"))
