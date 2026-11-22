import re
import html
from bs4 import BeautifulSoup

with open("dialog.html", encoding="utf-8") as f:
    dhtml = f.read()

soup = BeautifulSoup(dhtml, "html.parser")

def get_input(soup, *names):
    for n in names:
        inp = soup.find("input", id=n) or soup.find("input", attrs={"name": n})
        if inp and inp.has_attr("value"):
            return inp["value"]
    return ""

tokens = {
    "p_flow_id": get_input(soup, "p_flow_id", "pFlowId"),
    "p_flow_step_id": get_input(soup, "p_flow_step_id", "pFlowStepId"),
    "p_instance": get_input(soup, "p_instance", "pInstance"),
    "p_page_submission_id": get_input(soup, "p_page_submission_id", "pPageSubmissionId"),
    "p_reload_on_submit": get_input(soup, "p_reload_on_submit", "pReloadOnSubmit") or "S",
    "salt": get_input(soup, "pSalt", "p_salt"),
    "protected": get_input(soup, "pPageItemsProtected", "p_protected"),
}

# Checksums from data-for attributes
checksums = {}
for inp in soup.find_all("input"):
    if inp.has_attr("data-for") and inp.has_attr("value"):
        checksums[inp["data-for"]] = inp["value"]
    if inp.has_attr("id") and inp["id"].endswith("_CHECKSUM"):
        checksums[inp["id"].replace("_CHECKSUM", "")] = inp.get("value", "")

# Action
form = soup.find("form", id="wwvFlowForm") or soup.find("form")
action = form.get("action", "wwv_flow.accept") if form else "wwv_flow.accept"
tokens["action"] = action
tokens["checksums"] = checksums

print("Parsed tokens:")
for k, v in tokens.items():
    if k != "checksums":
        print(f"  {k}: {v}")
    else:
        print("  checksums:", v)
