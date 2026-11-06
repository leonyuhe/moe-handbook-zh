#!/usr/bin/env python3
"""Apply supplement translations back into work/index.json."""
import json, re, sys
from pathlib import Path
from html.parser import HTMLParser
ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"
VOID = {"area","base","br","col","embed","hr","img","input","link","meta","param","source","track","wbr"}

class N:
    __slots__=("tag","attrs","children","text")
    def __init__(self,tag="root",attrs=None,text=""):
        self.tag=tag; self.attrs=dict(attrs or []); self.children=[]; self.text=text
class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.root=N(); self.stack=[self.root]
    def handle_starttag(self,tag,attrs):
        n=N(tag,attrs); self.stack[-1].children.append(n)
        if tag not in VOID: self.stack.append(n)
    def handle_startendtag(self,tag,attrs): self.stack[-1].children.append(N(tag,attrs))
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,0,-1):
            if self.stack[i].tag==tag: del self.stack[i:]; return
    def handle_data(self,data):
        if data: self.stack[-1].children.append(N("#text",text=data))
def parse(s): p=P(); p.feed(s); p.close(); return p.root
def sig(n):
    return (n.tag, tuple(sorted(n.attrs.items())), tuple(sig(c) for c in n.children if c.tag!="#text"))
def txt(n):
    return n.text if n.tag=="#text" else "".join(txt(c) for c in n.children)
def code(n,out):
    if n.tag in ("pre","code","script","style"): out.append(txt(n))
    for c in n.children: code(c,out)
def parse_blocks(text):
    d={}
    pat=re.compile(r"^<<<BLOCK ([^>\s]+)>>>[ \t]*$",re.M); ms=list(pat.finditer(text))
    for i,m in enumerate(ms):
        end=ms[i+1].start() if i+1<len(ms) else len(text)
        d[m.group(1)]=re.sub(r"\n?<<<END>>>\s*$","",text[m.end():end]).strip("\n")
    return d

def main():
    idx=json.loads((WORK/"index.json").read_text())
    by_id={b["id"]:b for b in idx}
    total=0
    for supp in ("supp","supp2"):
        man=json.loads((WORK/supp/"manifest.json").read_text())
        items={i["sid"]:i for i in json.loads((WORK/supp/"items.json").read_text())}
        for c in man:
            p=Path(c["out"])
            if not p.exists():
                print(f"missing {p}"); sys.exit(2)
            blocks=parse_blocks(p.read_text())
            for sid in c["blocks"]:
                src=items[sid]["html"]; out=blocks.get(sid)
                if out is None: print("missing block",sid); sys.exit(2)
                a,b=parse(src),parse(out)
                if sig(a)!=sig(b):
                    print("STRUCTURE MISMATCH",sid); print(src[:200]); print(out[:200]); sys.exit(3)
                ca,cb=[],[]
                code(a,ca); code(b,cb)
                if ca!=cb: print("CODE MISMATCH",sid); sys.exit(3)
                blk=by_id[items[sid]["block"]]
                if src not in blk["html"]:
                    print("SOURCE NOT FOUND",sid); sys.exit(3)
                blk["html"]=blk["html"].replace(src,out,1)
                total+=1
    (WORK/"index.json").write_text(json.dumps(idx,ensure_ascii=False,indent=1))
    print("applied",total,"supplement blocks")

if __name__=="__main__": main()
