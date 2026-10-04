"""G03: no duplicated or near-duplicated case text across splits, and no length shortcut.

Text = input.context + input.target, whitespace and punctuation normalised. Similarity is the
Jaccard index of character 3-grams, which works for Chinese without a tokenizer.

* Exact duplicates anywhere fail.
* Near duplicates (>= --near, default 0.85) across different splits fail. Minimal pairs that share a
  pair_id are exempt: DATA-02 builds them to be near-identical on purpose.
* Near duplicates within one split but across families are reported in metrics, not failed.
* Length shortcut: if text length alone separates violating from conforming with AUC >= 0.95 and
  both classes have at least 30 cases, the labels can be learned without reading the text.

The thresholds are engineering defaults, recorded as an open ruling, not PoL2 doctrine.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from itertools import combinations

from .common import (EXIT_FAIL, EXIT_INPUT_ERROR, EXIT_PASS, GateResult, InputError, load_jsonl,
                     reference_of, split_of)

GATE = 'G03'
TITLE = '去重与长度捷径'
SPEC_RULE = '去除精确及语义近重复，检查标签捷径。（PoL-Governance SPEC，教师生成与质量检查第 4 条）'
NEAR = 0.85
SHORTCUT_AUC = 0.95
SHORTCUT_MIN = 30
_STRIP = re.compile(r'[\s\W_]+', re.UNICODE)


def text_of(case):
    inp = case.get('input') or {}
    context = inp.get('context') or []
    parts = (context if isinstance(context, list) else [str(context)]) + [str(inp.get('target', ''))]
    return _STRIP.sub('', ''.join(parts)).lower()


def grams(text, n=3):
    return {text[i:i + n] for i in range(max(1, len(text) - n + 1))}


def jaccard(a, b):
    return len(a & b) / len(a | b) if a or b else 1.0


def length_auc(cases, labels_by_id=None):
    """AUC of 'longer text => violating', both directions folded so 0.5 means no shortcut."""
    pos, neg = [], []
    for case in cases:
        ref = reference_of(case, labels_by_id) or {}
        if ref.get('status') == 'violating':
            pos.append(len(text_of(case)))
        elif ref.get('status') == 'conforming':
            neg.append(len(text_of(case)))
    if not pos or not neg:
        return None, len(pos), len(neg)
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    auc = wins / (len(pos) * len(neg))
    return max(auc, 1 - auc), len(pos), len(neg)


def check(cases, labels=None, near=NEAR):
    labels_by_id = {r['id']: r for r in labels} if labels is not None else None
    findings = []
    texts = {c['id']: text_of(c) for c in cases}
    seen = {}
    for case in cases:
        t = texts[case['id']]
        if t in seen:
            findings.append(f'{case["id"]}: exact duplicate of {seen[t]}')
        else:
            seen[t] = case['id']
    shingles = {k: grams(v) for k, v in texts.items()}
    within = []
    for a, b in combinations(cases, 2):
        if a.get('pair_id') is not None and a.get('pair_id') == b.get('pair_id'):
            continue
        if texts[a['id']] == texts[b['id']]:
            continue  # already reported as exact
        score = jaccard(shingles[a['id']], shingles[b['id']])
        if score < near:
            continue
        if split_of(a) != split_of(b):
            findings.append(f'{a["id"]} ~ {b["id"]}: near duplicate across splits '
                            f'({split_of(a)} / {split_of(b)}, jaccard {score:.2f})')
        elif a.get('family_id') != b.get('family_id'):
            within.append([a['id'], b['id'], round(score, 3)])
    auc, n_pos, n_neg = length_auc(cases, labels_by_id)
    if auc is not None and auc >= SHORTCUT_AUC and min(n_pos, n_neg) >= SHORTCUT_MIN:
        findings.append(f'length shortcut: text length alone separates violating from conforming '
                        f'(AUC {auc:.3f})')
    metrics = {'cases': len(cases), 'near_threshold': near,
               'near_duplicates_within_split_across_families': within,
               'length_auc': None if auc is None else round(auc, 4),
               'length_auc_classes': [n_pos, n_neg]}
    return GateResult(GATE, TITLE, SPEC_RULE, 'fail' if findings else 'pass', findings, metrics)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('cases', nargs='+', help='case JSONL files of all splits, checked together')
    parser.add_argument('--labels', help='label JSONL; default: proposals embedded in cases')
    parser.add_argument('--near', type=float, default=NEAR)
    args = parser.parse_args(argv)
    try:
        cases = [row for path in args.cases for row in load_jsonl(path)]
        labels = load_jsonl(args.labels) if args.labels else None
        result = check(cases, labels, args.near)
    except (InputError, OSError, KeyError) as error:
        print(f'{GATE} input error: {error}', file=sys.stderr)
        return EXIT_INPUT_ERROR
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return EXIT_PASS if result.status == 'pass' else EXIT_FAIL


if __name__ == '__main__':
    sys.exit(main())
