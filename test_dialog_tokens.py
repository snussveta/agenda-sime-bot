import re

with open("dialog.html", encoding="utf-8") as f:
    dhtml = f.read()

# Find all hidden inputs
inputs = re.findall(r'<input[^>]+type=["\']hidden["\'][^>]*>', dhtml, re.I)
print(f"Total hidden inputs: {len(inputs)}")
for inp in inputs:
    name_m = re.search(r'name=["\']([^"\']+)["\']', inp)
    id_m = re.search(r'id=["\']([^"\']+)["\']', inp)
    val_m = re.search(r'value=["\']([^"\']*)["\']', inp)
    name = name_m.group(1) if name_m else (id_m.group(1) if id_m else "")
    val = val_m.group(1) if val_m else ""
    print(f"  Input: {name} = {val[:30]}")

# Find form action
form_m = re.search(r'<form[^>]+action=["\']([^"\']+)["\']', dhtml, re.I)
if form_m:
    print("Form action:", form_m.group(1))

# Find item checksums
ck_pattern = re.compile(r'"name":"(P101_[^"]+)","value":"[^"]*","checksum":"([^"]+)"')
for m in ck_pattern.finditer(dhtml):
    print("JSON Checksum:", m.group(1), "=", m.group(2))
