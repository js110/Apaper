#!/usr/bin/env python3
"""Check protected manuscript content against a pre-edit style snapshot.

This checks token preservation, not semantic equivalence or an AI detector score.
"""
import argparse
from collections import Counter
import difflib
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('before', type=Path)
    args = parser.parse_args()
    before = args.before.read_text()
    after = (ROOT / 'paper_a.tex').read_text()
    patterns = {
        'numeric tokens': r'\d+(?:[.,]\d+)*',
        'citation tokens': r'\\cite\{[^}]+\}',
        'cross-references and labels': r'\\(?:eqref|ref|label)\{[^}]+\}',
        'inline mathematics': r'\$[^$]+\$',
        'displayed equations': r'\\begin\{equation\}.*?\\end\{equation\}',
        'tabular bodies': r'\\begin\{tabular\}.*?\\end\{tabular\}',
        'comparison table': r'\\begin\{tabularx\}.*?\\end\{tabularx\}',
        'figure captions': r'\\caption\{[^\n]+',
        'propositions and lemmas': r'\\begin\{(?:proposition|lemma)\}.*?\\end\{(?:proposition|lemma)\}',
        'proofs': r'\\begin\{proof\}.*?\\end\{proof\}',
    }
    checks = []
    for name, pattern in patterns.items():
        old = Counter(re.findall(pattern, before, re.S))
        new = Counter(re.findall(pattern, after, re.S))
        checks.append({'check': name, 'passed': old == new,
                       'removed': list((old-new).elements()),
                       'added': list((new-old).elements())})
    for name, old, new in (
        ('title and author metadata', before.split(r'\begin{abstract}')[0], after.split(r'\begin{abstract}')[0]),
        ('funding declarations and appendix', before.split(r'\section*{Funding}', 1)[1], after.split(r'\section*{Funding}', 1)[1]),
    ):
        checks.append({'check': name, 'passed': old == new})
    report = {
        'date': '2026-09-23',
        'scope': 'Protected-token preservation; semantic equivalence separately reviewed. No AI-detection claim.',
        'before_sha256': hashlib.sha256(before.encode()).hexdigest(),
        'after_sha256': hashlib.sha256(after.encode()).hexdigest(),
        'checks': checks,
        'passed': sum(row['passed'] for row in checks),
        'total': len(checks),
    }
    (ROOT/'evidence/style_integrity_20260923.json').write_text(json.dumps(report, indent=2)+'\n')
    (ROOT/'evidence/style_rewrite_20260923.diff').write_text(''.join(difflib.unified_diff(
        before.splitlines(keepends=True), after.splitlines(keepends=True),
        fromfile='paper_a.before-style.tex', tofile='paper_a.tex')))
    print(json.dumps(report, indent=2))
    if report['passed'] != report['total']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
