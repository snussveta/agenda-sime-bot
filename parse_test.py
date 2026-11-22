import re

with open("public_page.html", encoding="utf-8") as f:
    html = f.read()

print("HTML size:", len(html))

# Search for any URL containing r/agenda or login
urls = re.findall(r'https?://[^\s"\'<>]+', html)
print(f"Total URLs found: {len(urls)}")
for u in urls:
    if "agenda" in u or "ords" in u:
        print("URL:", u)

# Let's search for "autentificare" in context
for m in re.finditer(r'.{0,100}autentificare.{0,100}', html, re.IGNORECASE):
    print("Autentificare context:\n", m.group(0))

# Also search for p_flow or apex
for m in re.finditer(r'.{0,100}apex\.navigation.{0,100}', html, re.IGNORECASE):
    print("Navigation context:\n", m.group(0))
