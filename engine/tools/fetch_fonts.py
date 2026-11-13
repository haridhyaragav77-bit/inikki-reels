#!/usr/bin/env python3
"""Download the brand fonts (free Google Fonts) into engine/.cache/fonts and write fonts.local.css. No AI."""
import os, re, subprocess
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "engine", ".cache", "fonts"); os.makedirs(OUT, exist_ok=True)
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
URL = ("https://fonts.googleapis.com/css2?family=Anton&family=Bebas+Neue&family=Noto+Sans+Tamil:wght@500;700;900"
       "&family=Inter:wght@500;600;700;800;900&family=Playfair+Display:ital,wght@1,800&display=block")
css = subprocess.run(["curl", "-s", "-A", UA, URL], capture_output=True, text=True, check=True).stdout
out = []
for sub, body in re.findall(r"/\* ([^*]+) \*/\s*@font-face \{(.*?)\}", css, re.S):
    sub = sub.strip()
    if sub not in ("latin", "latin-ext", "tamil"):
        continue
    fam = re.search(r"font-family: '([^']+)'", body).group(1); w = re.search(r"font-weight: (\d+)", body).group(1)
    st = re.search(r"font-style: (\w+)", body).group(1); url = re.search(r"url\((https://[^)]+)\)", body).group(1)
    ur = re.search(r"unicode-range: ([^;]+);", body).group(1)
    fn = f"{fam.replace(' ', '')}-{w}-{st}-{sub}.woff2"
    if not os.path.exists(os.path.join(OUT, fn)):
        subprocess.run(["curl", "-s", "-o", os.path.join(OUT, fn), url], check=True)
    out.append(f"@font-face{{font-family:'{fam}';font-style:{st};font-weight:{w};font-display:block;src:url('{fn}') format('woff2');unicode-range:{ur};}}")
open(os.path.join(OUT, "fonts.local.css"), "w").write("\n".join(out) + "\n")
print(f"{len(out)} font faces ready")
