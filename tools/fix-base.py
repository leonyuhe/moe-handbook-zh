#!/usr/bin/env python3
"""Prefix root-absolute public asset URLs for GitHub Pages project hosting."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "app" / "dist"
BASE = "/moe-handbook-zh"
PATTERN = re.compile(
    r'(["\'(=`\s])/(viz/|scripts/|figures/|headline-iso/|headline-overlap/|thumb\.auto\.jpg|viz-fit\.js)'
)
SUFFIXES = {".html", ".js", ".css", ".json", ".txt", ".xml", ".webmanifest"}


def main():
    changed = 0
    for p in DIST.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in SUFFIXES:
            continue
        try:
            s = p.read_text()
        except UnicodeDecodeError:
            continue
        t = PATTERN.sub(lambda m: f'{m.group(1)}{BASE}/{m.group(2)}', s)
        t = t.replace('href="/"', f'href="{BASE}/"')
        if t != s:
            p.write_text(t)
            changed += 1
    print(f"rewrote {changed} files under {DIST}")


if __name__ == "__main__":
    main()
