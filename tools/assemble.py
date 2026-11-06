#!/usr/bin/env python3
"""Put translated blocks back into the MDX fragments and localize figure captions."""
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
SRC = APP / "src" / "content"
WORK = ROOT / "work"
FRAG_RE = re.compile(r'set:html=\{("(?:[^"\\]|\\.)*")\}')


def parse_blocks(text: str):
    blocks = {}
    order = []
    pat = re.compile(r"^<<<BLOCK ([^>\s]+)>>>[ \t]*$", re.M)
    ms = list(pat.finditer(text))
    for i, m in enumerate(ms):
        start = m.end()
        end = ms[i + 1].start() if i + 1 < len(ms) else len(text)
        body = text[start:end]
        body = re.sub(r"\n?<<<END>>>\s*$", "", body).strip("\n")
        blocks[m.group(1)] = body
        order.append(m.group(1))
    return blocks, order


def main():
    index = json.loads((WORK / "index.json").read_text())
    manifest = json.loads((WORK / "manifest.json").read_text())
    translations = {}
    for c in manifest:
        p = Path(c["out"])
        if not p.exists():
            print(f"WARNING: missing {p.name}; leaving those blocks in English")
            continue
        blocks, order = parse_blocks(p.read_text())
        translations.update(blocks)

    by_chapter = {}
    for b in index:
        by_chapter.setdefault(b["chapter"], {}).setdefault(b["fragment"], []).append(b)

    # keep a pristine English copy once
    en = SRC / "chapters.en"
    if not en.exists():
        shutil.copytree(SRC / "chapters", en)
        shutil.copy2(SRC / "article.mdx", SRC / "article.en.mdx")

    for chapter, frags in by_chapter.items():
        path = SRC / "chapters" / chapter
        src = path.read_text()
        ms = list(FRAG_RE.finditer(src))
        out = []
        last = 0
        for fi, fm in enumerate(ms):
            frag = json.loads(fm.group(1))
            blocks = sorted(frags.get(fi, []), key=lambda b: b["block"])
            pieces = []
            for b in blocks:
                pieces.append(translations.get(b["id"], b["html"]))
            rebuilt = "".join(pieces)
            out.append(src[last:fm.start()])
            out.append("set:html={" + json.dumps(rebuilt, ensure_ascii=False) + "}")
            last = fm.end()
        out.append(src[last:])
        text = "".join(out)
        # figure captions and code-copy UI live outside the translatable prose blocks
        text = text.replace('caption="Figure ', 'caption="图 ')
        text = text.replace('<b>Figure ', '<b>图 ')
        text = text.replace(">Copy</button>", ">复制</button>")
        text = text.replace(">Copied</button>", ">已复制</button>")
        text = text.replace(">Select and copy</button>", ">选择并复制</button>")
        text = text.replace('aria-label="Copy commands"', 'aria-label="复制命令"')
        text = text.replace('aria-label="Copy code"', 'aria-label="复制代码"')
        text = text.replace('aria-label="Commands"', 'aria-label="命令"')
        # short headings fell below the prose threshold and were left in English
        heading_fixes = {
            "1. Introduction": "1. 引言",
            "2.3 Tokenize": "2.3 分词",
            "3.1 Router scoring: how logits become weights": "3.1 路由器打分：logits 如何变成权重",
            "4. From training to serving": "4. 从训练到推理",
            "5. Conclusion": "5. 结论",
            "Appendix": "附录",
            "Sharpness": "锐度",
            "Precision": "精度",
            "Scope": "作用范围",
            "Quantile": "分位数",
            "Activation": "激活函数",
            "Upcycling": "Upcycling（专家升级复用）",
            "Optimizer": "优化器",
            "MTP": "多 token 预测（MTP）",
            "Stability": "稳定性",
            "Profiling": "性能分析",
            "Interconnect": "互连",
            "Overlap": "重叠",
            "Memory": "显存",
            "Acknowledgements": "致谢",
            "Code, configs and data": "代码、配置与数据",
        }
        for old, new in heading_fixes.items():
            text = re.sub(
                r"(<h([2-6])\b[^>]*>)" + re.escape(old) + r"(</h\2>)",
                lambda m: m.group(1) + new + m.group(3),
                text,
            )
        text = text.replace("<summary>Every recommended flag, by section</summary>", "<summary>按章节汇总的全部推荐参数</summary>")
        path.write_text(text)
        print(f"wrote {chapter}: {len(ms)} fragments, {sum(len(v) for v in frags.values())} blocks")

    # llms.txt is generated at build time from the MDX, now translated automatically


if __name__ == "__main__":
    main()
