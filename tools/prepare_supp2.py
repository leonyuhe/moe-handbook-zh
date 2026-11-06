#!/usr/bin/env python3
"""Second supplement: prose inside <details> blocks that also contain source code."""
import json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"; SUPP = WORK / "supp2"; CH = SUPP / "chunks"; OUT = SUPP / "out"
WORD = re.compile(r"[A-Za-z][A-Za-z'’\-]*")
TAG = re.compile(r"<(p|h[2-6]|figcaption|li)\b[^>]*>.*?</\1>", re.S)
SKIP = {"c2f0b97", "c2f1b11", "c5f0b4", "c6f0b109", "c6f0b110"}
def main():
    CH.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
    idx = json.loads((WORK / "index.json").read_text())
    items = []
    for b in idx:
        if b["translatable"] or b["id"] in SKIP: continue
        h = b["html"]
        if h.lstrip().startswith("<div class=\"full code-window"): continue
        h2 = re.sub(r"<pre.*?</pre>", "", h, flags=re.S)
        h2 = re.sub(r"<style.*?</style>", "", h2, flags=re.S)
        h2 = re.sub(r"<script.*?</script>", "", h2, flags=re.S)
        for m in TAG.finditer(h2):
            frag = m.group(0)
            n = len(WORD.findall(re.sub(r"<[^>]+>", " ", frag)))
            if n >= 8 and not (frag.startswith("<li") and n < 12):
                items.append({"block": b["id"], "html": frag, "words": n})
    # one chunk
    lines = []
    for j, it in enumerate(items, 1):
        it["sid"] = f"s2-{j:02d}"
        lines += [f"<<<BLOCK {it['sid']}>>>", it["html"]]
    lines.append("<<<END>>>")
    (CH / "supp2-001.txt").write_text("\n".join(lines) + "\n")
    (SUPP / "items.json").write_text(json.dumps(items, ensure_ascii=False, indent=1))
    (SUPP / "manifest.json").write_text(json.dumps([{"id":"supp2-001","blocks":[i["sid"] for i in items],"words":sum(i["words"] for i in items),"file":str(CH/"supp2-001.txt"),"out":str(OUT/"supp2-001.txt")}], ensure_ascii=False, indent=2))
    print(len(items), "items", sum(i["words"] for i in items), "words")
    for i in items: print(i["block"], i["words"], i["html"][:90].replace("\n"," "))
if __name__ == "__main__": main()
