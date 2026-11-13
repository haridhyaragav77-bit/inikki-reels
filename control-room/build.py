"""Builds the Control Room page: the template plus the guidebook (GUIDE.md), so the guide is written once.
    python control-room/build.py [page link]      writes control-room/page.html, the file that is published as the artifact"""
import json
import pathlib
import sys

here = pathlib.Path(__file__).parent
guide = (here.parent / "GUIDE.md").read_text(encoding="utf-8")
if len(sys.argv) > 1:
    guide = guide.replace("PAGE_URL", sys.argv[1])
page = (here / "page.template.html").read_text(encoding="utf-8").replace("__GUIDE_JSON__", json.dumps(guide, ensure_ascii=False).replace("</", "<\\/"))
(here / "page.html").write_text(page, encoding="utf-8")
print("built", here / "page.html", len(page), "bytes")
