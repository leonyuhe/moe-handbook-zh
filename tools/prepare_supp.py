#!/usr/bin/env python3
"""Extract prose elements that were skipped inside mixed HTML/code blocks."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"
SUPP = WORK / "supp"
CHUNKS = SUPP / "chunks"
OUT = SUPP / "out"
WORD_RE = re.compile(r"[A-Za-z][A-Za-z'’\-]*")

# blocks that contained prose but were skipped because they also contain <pre>/<style>
TARGETS = ["c2f0b97", "c2f1b11", "c5f0b4"]
TAG_RE = re.compile(r"<(p|h[2-6]|figcaption|summary)\b[^>]*>.*?</\1>", re.S)


def main():
    CHUNKS.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    idx = json.loads((WORK / "index.json").read_text())
    by_id = {b["id"]: b for b in idx}
    items = []
    for bid in TARGETS:
        b = by_id[bid]
        html = b["html"]
        for m in TAG_RE.finditer(html):
            frag = m.group(0)
            if frag.startswith("<summary>") and "Megatron source" not in frag and "Every recommended" not in frag:
                continue
            text = re.sub(r"<[^>]+>", " ", frag)
            n = len(WORD_RE.findall(text))
            if n < 2:
                continue
            items.append({
                "block": bid,
                "start": m.start(),
                "end": m.end(),
                "html": frag,
                "words": n,
            })
    # group into chunks
    chunks = []
    cur = []
    cur_words = 0
    for it in items:
        if cur and cur_words + it["words"] > 700:
            chunks.append(cur)
            cur, cur_words = [], 0
        cur.append(it)
        cur_words += it["words"]
    if cur:
        chunks.append(cur)
    manifest = []
    for i, ch in enumerate(chunks, 1):
        cid = f"supp-{i:03d}"
        lines = []
        for j, it in enumerate(ch, 1):
            it["sid"] = f"s{i:03d}-{j:02d}"
            lines.append(f"<<<BLOCK {it['sid']}>>>")
            lines.append(it["html"])
        lines.append("<<<END>>>")
        (CHUNKS / f"{cid}.txt").write_text("\n".join(lines) + "\n")
        manifest.append({
            "id": cid,
            "blocks": [it["sid"] for it in ch],
            "words": sum(it["words"] for it in ch),
            "file": str(CHUNKS / f"{cid}.txt"),
            "out": str(OUT / f"{cid}.txt"),
        })
    (SUPP / "items.json").write_text(json.dumps(items, ensure_ascii=False, indent=1))
    (SUPP / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"{len(items)} prose elements, {len(manifest)} chunks")
    for c in manifest:
        print(c["id"], c["words"], len(c["blocks"]))


if __name__ == "__main__":
    main()
