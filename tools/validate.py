#!/usr/bin/env python3
"""Validate translated block files against the source HTML structure."""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"
OUT = WORK / "out"
VOID = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}
CJK = re.compile(r"[\u4e00-\u9fff]")
ENG = re.compile(r"[A-Za-z][A-Za-z'’\-]+")


class Node:
    __slots__ = ("tag", "attrs", "children", "text")

    def __init__(self, tag="root", attrs=None, text=""):
        self.tag = tag
        self.attrs = dict(attrs or [])
        self.children = []
        self.text = text


class Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs)
        self.stack[-1].children.append(n)
        if tag not in VOID:
            self.stack.append(n)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Node(tag, attrs))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        if data:
            self.stack[-1].children.append(Node("#text", text=data))


def parse(html: str) -> Node:
    p = Parser()
    p.feed(html)
    p.close()
    return p.root


def text_of(n: Node) -> str:
    if n.tag == "#text":
        return n.text
    return "".join(text_of(c) for c in n.children)


def structure(n: Node):
    return (
        n.tag,
        tuple(sorted(n.attrs.items())),
        tuple(structure(c) for c in n.children if c.tag != "#text"),
    )


def code_texts(n: Node, out):
    if n.tag in ("pre", "code", "script", "style"):
        out.append(text_of(n))
    for c in n.children:
        code_texts(c, out)


def collect_text(n: Node, out, in_code=False):
    if n.tag == "#text":
        if not in_code and n.text.strip():
            out.append(n.text)
        return
    for c in n.children:
        collect_text(c, out, in_code or n.tag in ("code", "pre", "script", "style"))


def parse_blocks(text: str):
    blocks = {}
    order = []
    pos = 0
    pat = re.compile(r"^<<<BLOCK ([^>\s]+)>>>[ \t]*$", re.M)
    matches = list(pat.finditer(text))
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end]
        body = re.sub(r"\n?<<<END>>>\s*$", "", body).strip("\n")
        blocks[m.group(1)] = body
        order.append(m.group(1))
    return blocks, order


def main():
    index = json.loads((WORK / "index.json").read_text())
    src = {b["id"]: b["html"] for b in index}
    manifest = json.loads((WORK / "manifest.json").read_text())
    total = 0
    bad = 0
    missing = []
    for c in manifest:
        p = Path(c["out"])
        if not p.exists():
            missing.append(c["id"])
            continue
        total += 1
        text = p.read_text()
        blocks, order = parse_blocks(text)
        errs = []
        if order != c["blocks"]:
            errs.append(f"block order/count differs: {order} != {c['blocks']}")
        for bid in c["blocks"]:
            if bid not in blocks:
                errs.append(f"missing {bid}")
                continue
            a, b = src[bid], blocks[bid]
            na, nb = parse(a), parse(b)
            if structure(na) != structure(nb):
                errs.append(f"{bid}: HTML structure changed")
                # locate first difference for debugging
                sa, sb = structure(na), structure(nb)
                errs.append(f"  src tags={sum(1 for _ in re.finditer('<[a-zA-Z]', a))} "
                            f"out tags={sum(1 for _ in re.finditer('<[a-zA-Z]', b))}")
            ca, cb = [], []
            code_texts(na, ca)
            code_texts(nb, cb)
            if ca != cb:
                errs.append(f"{bid}: code/pre text changed")
            ta, tb = [], []
            collect_text(na, ta)
            collect_text(nb, tb)
            cjk = len(CJK.findall("".join(tb)))
            eng = len(ENG.findall("".join(tb)))
            if cjk == 0 and eng > 8:
                errs.append(f"{bid}: no Chinese in a prose block")
            elif cjk < eng * 0.15 and eng > 40:
                errs.append(f"{bid}: low Chinese ratio (cjk={cjk}, eng={eng})")
        if errs:
            bad += 1
            print(f"\n[{c['id']}] {c['chapter']} | {c['section']}")
            for e in errs[:8]:
                print("  -", e)
    print(f"\nChecked {total}/{len(manifest)} chunks; {bad} with errors; missing: {missing}")


if __name__ == "__main__":
    main()
