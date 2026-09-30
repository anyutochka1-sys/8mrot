#!/usr/bin/env python3
import json, re, pathlib, datetime, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "mrot.json"

# Consolidated text of Federal Law No. 82-FZ.
SOURCES = [
    "https://base.garant.ru/10180093/",
    "https://www.consultant.ru/document/cons_doc_LAW_27572/"
]

UA = "Mozilla/5.0 (compatible; 8mrot-auto-update/1.0)"

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="ignore")

def extract(text):
    # Handles wording such as:
    # "с 1 января 2026 года в сумме 27 093 рубля в месяц"
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ").replace("&#160;", " ")
    text = re.sub(r"\s+", " ", text)
    patterns = [
        r"с\s+1\s+января\s+(20\d{2})\s+года[^0-9]{0,120}(\d{2,3}(?:[ \u00a0]\d{3})+)\s*руб",
        r"МРОТ[^0-9]{0,100}(20\d{2})[^0-9]{0,100}(\d{2,3}(?:[ \u00a0]\d{3})+)\s*руб"
    ]
    found = {}
    for pat in patterns:
        for y, val in re.findall(pat, text, flags=re.I):
            n = int(re.sub(r"\D", "", val))
            if 10000 <= n <= 100000:
                found[int(y)] = n
    return found

with DATA.open("r", encoding="utf-8") as f:
    current = json.load(f)

all_found = {}
used_source = None
for url in SOURCES:
    try:
        vals = extract(get(url))
        if vals:
            all_found.update(vals)
            used_source = url
    except Exception as e:
        print(f"Source failed: {url}: {e}")

today = datetime.date.today().isoformat()
changed = False
for year, mrot in sorted(all_found.items()):
    if year < 2026:
        continue
    k = str(year)
    old = current.get(k, {})
    if old.get("mrot") != mrot or old.get("status") != "official":
        current[k] = {
            "mrot": mrot,
            "status": "official",
            "source": "Федеральный закон № 82-ФЗ (действующая редакция)",
            "source_url": used_source,
            "checked_at": today
        }
        changed = True
    else:
        # Keep an audit date without creating pointless commits every run.
        pass

if changed:
    with DATA.open("w", encoding="utf-8") as f:
        json.dump(current, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("MROT data updated:", current)
else:
    print("No official MROT changes found.")
