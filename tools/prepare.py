#!/usr/bin/env python3
"""Split the MDX `set:html` payloads into translatable HTML blocks and chunks."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
CHAPTERS = APP / "src/content/chapters"
WORK = ROOT / "work"
CHUNKS = WORK / "chunks"
OUT = WORK / "out"

FRAG_RE = re.compile(r'set:html=\{("(?:[^"\\]|\\.)*")\}')
VOID = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}
TAG_RE = re.compile(
    r"<!--.*?-->|<!\[CDATA\[.*?\]\]>|<![^>]*>|</?([a-zA-Z][\w:-]*)((?:[^>\"']|\"[^\"]*\"|'[^']*')*?)(/?)>",
    re.S,
)
WORD_RE = re.compile(r"[A-Za-z][A-Za-z'’\-]*")
HEAD_RE = re.compile(r"<h([234])\b[^>]*>(.*?)</h\1>", re.S)

CHAPTER_TITLES = {
    "1-introduction.mdx": "1. Introduction",
    "2-setup-and-your-first-run.mdx": "2. Setup and your first run",
    "3-anatomy-of-moe-training.mdx": "3. Anatomy of MoE Training",
    "4-from-training-to-serving.mdx": "4. From training to serving",
    "5-conclusion.mdx": "5. Conclusion",
    "A-appendix.mdx": "Appendix",
}


def split_blocks(html: str):
    """Return [(raw_html, translatable)] covering html exactly."""
    blocks = []
    depth = 0
    block_start = None
    pos = 0
    for m in TAG_RE.finditer(html):
        gap = html[pos:m.start()]
        if depth == 0 and block_start is None and gap:
            blocks.append([gap, False])
        token = m.group(0)
        if token.startswith("<!") or token.startswith("<?"):
            if depth == 0 and block_start is None:
                blocks.append([token, False])
            pos = m.end()
            continue
        closing = token.startswith("</")
        if closing:
            if depth > 0:
                depth -= 1
                if depth == 0 and block_start is not None:
                    blocks.append([html[block_start:m.end()], True])
                    block_start = None
            pos = m.end()
            continue
        name = (m.group(1) or "").lower()
        selfclose = bool(m.group(3)) or name in VOID
        if depth == 0 and block_start is None:
            block_start = m.start()
        if not selfclose:
            depth += 1
        elif depth == 0 and block_start is not None:
            blocks.append([html[block_start:m.end()], True])
            block_start = None
        pos = m.end()
    if depth > 0 and block_start is not None:
        # malformed / unclosed top-level element: keep it, do not translate
        blocks.append([html[block_start:], False])
    elif pos < len(html):
        blocks.append([html[pos:], False])
    assert "".join(b for b, _ in blocks) == html, "block split lost content"
    return blocks


def is_code(raw: str) -> bool:
    head = raw[:400].lower()
    return (
        "<pre" in head
        or "code-window" in head
        or "code-content" in head
        or 'class="code' in head
    )


def words(raw: str) -> int:
    text = re.sub(r"<[^>]+>", " ", raw)
    return len(WORD_RE.findall(text))


def classify(raw: str) -> bool:
    if not raw.strip():
        return False
    low = raw.lower()
    if is_code(raw):
        return False
    if "<pre" in low or "<script" in low or "<style" in low:
        return False
    if 'id="references"' in low or 'class="references"' in low:
        return False
    if "references-list" in low:
        return False
    text = re.sub(r"<[^>]+>", " ", raw)
    # skip pure HTML comments and blocks without real prose
    return len(WORD_RE.findall(text)) >= 2


def main():
    CHUNKS.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    all_chunks = []
    index = []
    for ci, fn in enumerate(sorted(CHAPTERS.glob("*.mdx")), 1):
        src = fn.read_text()
        title = CHAPTER_TITLES.get(fn.name, fn.name)
        section = title
        for fi, fm in enumerate(FRAG_RE.finditer(src)):
            raw = json.loads(fm.group(1))
            blocks = split_blocks(raw)
            for bi, (html, _) in enumerate(blocks):
                m = HEAD_RE.search(html)
                if m:
                    section = re.sub(r"<[^>]+>", "", m.group(2)).strip()
                translatable = classify(html)
                index.append({
                    "chapter": fn.name,
                    "fragment": fi,
                    "block": bi,
                    "id": f"c{ci}f{fi}b{bi}",
                    "section": section,
                    "translatable": translatable,
                    "words": words(html) if translatable else 0,
                    "html": html,
                })
    # group contiguous translatable blocks into chunks (code blocks are untouched)
    cur = []
    cur_words = 0
    for b in index:
        if not b["translatable"]:
            continue
        start_new = False
        if cur and cur_words + b["words"] > 850:
            start_new = True
        if cur and re.match(r"<h2\b", b["html"]) and cur_words > 250:
            start_new = True
        if start_new:
            all_chunks.append(cur)
            cur, cur_words = [], 0
        cur.append(b)
        cur_words += b["words"]
    if cur:
        all_chunks.append(cur)

    manifest = []
    for i, chunk in enumerate(all_chunks, 1):
        cid = f"chunk-{i:03d}"
        lines = []
        for b in chunk:
            lines.append(f"<<<BLOCK {b['id']}>>>")
            lines.append(b["html"].strip("\n"))
        lines.append("<<<END>>>")
        text = "\n".join(lines) + "\n"
        (CHUNKS / f"{cid}.txt").write_text(text)
        manifest.append({
            "id": cid,
            "chapter": chunk[0]["chapter"],
            "section": chunk[0]["section"],
            "words": sum(b["words"] for b in chunk),
            "blocks": [b["id"] for b in chunk],
            "file": str(CHUNKS / f"{cid}.txt"),
            "out": str(OUT / f"{cid}.txt"),
        })
    (WORK / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1))
    (WORK / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    total_words = sum(c["words"] for c in manifest)
    print(f"{len(index)} blocks, {len(manifest)} chunks, {total_words} translatable words")
    for c in manifest:
        print(c["id"], c["chapter"], c["words"], len(c["blocks"]), "|", c["section"])


if __name__ == "__main__":
    main()
