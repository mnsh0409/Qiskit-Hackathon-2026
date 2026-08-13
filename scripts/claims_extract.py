"""claims_extract.py - build the C4 audit claims table from draft files.

Usage:
  python claims_extract.py deck/script.md README.md deck/slides.txt > audit/claims_pass1.md

Flags every sentence containing a digit OR a claim keyword. Over-capture is the
design goal: C4 marking a row N/A costs seconds; a missed claim survives to the
stage. Fenced code blocks are skipped. Source tags [R###] [GIT] [LIT] [SRCH]
are collected per claim; untagged rows default to UNSUPPORTED in the audit.
"""
from __future__ import annotations

import re
import sys

KEYWORDS = re.compile(
    r"\b(first|only|novel|unbiased|exact(?:ly)?|free|all|every|guarantee[sd]?|"
    r"match(?:es|ed)?|agree[sd]?|converge[sd]?|shrink(?:s|ed)?|improve[sd]?|"
    r"outperform(?:s|ed)?|faster|better|best|reproduc\w*|pass(?:es|ed)?|"
    r"valid(?:ated)?|conserved|flat|within)\b",
    re.I,
)
DIGIT = re.compile(r"\d")
TAG = re.compile(r"\[(R\d{3}|GIT[^\]]*|LIT[^\]]*|SRCH[^\]]*)\]")
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(])")


def sentences(path: str):
    fenced = False
    for lineno, line in enumerate(open(path, encoding="utf-8"), 1):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        text = line.strip().lstrip("#>-*•").strip()
        if not text:
            continue
        for s in SENT_SPLIT.split(text):
            s = s.strip()
            if s:
                yield lineno, s


def main(paths):
    rows = []
    for path in paths:
        for lineno, s in sentences(path):
            if not (DIGIT.search(s) or KEYWORDS.search(s)):
                continue
            tags = TAG.findall(s) or ["-"]
            excerpt = (s[:157] + "...") if len(s) > 160 else s
            excerpt = excerpt.replace("|", "\\|")
            rows.append((path, lineno, ",".join(tags), excerpt))
    untagged = sum(1 for r in rows if r[2] == "-")
    print("# Claims table (generated - do not edit; regenerate instead)")
    print(f"# {len(rows)} claims, {untagged} untagged -> UNSUPPORTED by default\n")
    print("| C## | file:line | tags | claim | verdict |")
    print("|---|---|---|---|---|")
    for i, (path, lineno, tags, excerpt) in enumerate(rows, 1):
        print(f"| C{i:03d} | {path}:{lineno} | {tags} | {excerpt} | |")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1:]))
