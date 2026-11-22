import urllib.request
import urllib.parse
import json
import http.cookiejar
import html
import re

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "ro-MD,ro;q=0.9,ru;q=0.8,en;q=0.7",
}

# 1. Fetch public
print("Step 1: Fetching public portal...")
req1 = urllib.request.Request("https://agenda.sime.md/ords/r/agenda/main/public", headers=headers)
with opener.open(req1) as resp:
    raw_html = resp.read().decode("utf-8")

# 2. Extract dialog URL
text = html.unescape(raw_html)
try:
    text = text.encode("utf-8").decode("unicode_escape")
except Exception:
    pass

m = re.search(r'(/ords/r/agenda/main/login[^"\'\)]*p101_user_type=2[^"\'\)]*)', text, re.IGNORECASE)
dialog_url = "https://agenda.sime.md" + m.group(1).split("',")[0].split('",')[0].strip()
print("Step 2: Dialog URL:", dialog_url)

# 3. Fetch dialog HTML
print("Step 3: Fetching dialog HTML...")
req2 = urllib.request.Request(dialog_url, headers={**headers, "Referer": "https://agenda.sime.md/ords/r/agenda/main/public"})
with opener.open(req2) as resp:
    dhtml = resp.read().decode("utf-8")

# 4. Parse tokens
from bs4 import BeautifulSoup
soup = BeautifulSoup(dhtml, "html.parser")
def get_input(soup, *names):
    for n in names:
        inp = soup.find("input", id=n) or soup.find("input", attrs={"name": n})
        if inp and inp.has_attr("value"):
            return inp["value"]
    return ""

checksums = {}
for inp in soup.find_all("input"):
    if inp.has_attr("data-for") and inp.has_attr("value"):
        checksums[inp["data-for"]] = inp["value"]
    if inp.has_attr("id") and inp["id"].endswith("_CHECKSUM"):
        checksums[inp["id"].replace("_CHECKSUM", "")] = inp.get("value", "")

p_flow_id = get_input(soup, "p_flow_id", "pFlowId")
p_flow_step_id = get_input(soup, "p_flow_step_id", "pFlowStepId")
p_instance = get_input(soup, "p_instance", "pInstance")
p_page_submission_id = get_input(soup, "p_page_submission_id", "pPageSubmissionId")
p_reload_on_submit = get_input(soup, "p_reload_on_submit", "pReloadOnSubmit") or "S"
salt = get_input(soup, "pSalt", "p_salt")
protected = get_input(soup, "pPageItemsProtected", "p_protected")
form = soup.find("form", id="wwvFlowForm") or soup.find("form")
action = form.get("action", "wwv_flow.accept") if form else "wwv_flow.accept"

items_to_submit = [
    {"n": "P101_USER_TYPE", "v": "2", "ck": checksums.get("P101_USER_TYPE")},
    {"n": "P101_USER_TYPE_NAME", "v": "Autentificare elev", "ck": checksums.get("P101_USER_TYPE_NAME")},
    {"n": "P101_USERNAME", "v": "kmihail2"},
    {"n": "P101_PASSWORD", "v": "dummy_wrong_password_test"},
]

r_obj = {
    "salt": salt,
    "pageItems": {
        "itemsToSubmit": items_to_submit,
        "protected": protected,
        "rowVersion": "",
        "formRegionChecksums": [],
    },
}

post_payload = {
    "p_flow_id": p_flow_id,
    "p_flow_step_id": p_flow_step_id,
    "p_instance": p_instance,
    "p_page_submission_id": p_page_submission_id,
    "p_request": "LOGIN",
    "p_reload_on_submit": p_reload_on_submit,
    "p_json": json.dumps(r_obj),
}

post_url = f"https://agenda.sime.md/ords/{action}" if not action.startswith("http") else action
print("Step 4: Posting login to:", post_url)

post_data = urllib.parse.urlencode(post_payload).encode("utf-8")
post_req = urllib.request.Request(
    post_url,
    data=post_data,
    headers={
        **headers,
        "Referer": dialog_url,
        "Origin": "https://agenda.sime.md",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json, text/javascript, */*; q=0.01",
    }
)

with opener.open(post_req) as post_resp:
    res_text = post_resp.read().decode("utf-8")
    print("Login Response Status:", post_resp.status)
    print("Login Response Body:", res_text[:300])
