"""G08: every clause the candidate claims to cover has conforming, violating and insufficient cases.

Cases are grouped by input.clause (the DATA-02 contract). Data without that field, such as the pilot,
is grouped by family_id and the report says so; a card that claims clause ids then cannot be
verified and fails. Without a card, every group present in the data must be complete.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict

from .common import (EXIT_FAIL, EXIT_INPUT_ERROR, EXIT_PASS, GateResult, InputError, load_json,
                     load_jsonl, reference_of)

GATE = 'G08'
TITLE = '条款覆盖与三类齐备'
SPEC_RULE = ('数据先覆盖诚实、平等、同意撤回、操控、帮助与修复；同时包括正常、违规、信息不足案例。'
             '（PoL-Governance SPEC，第 1 阶段）')
STATUSES = ('conforming', 'violating', 'insufficient')


def group_key(case):
    clause = (case.get('input') or {}).get('clause')
    return (clause, 'clause') if isinstance(clause, str) and clause else (case.get('family_id'), 'family')


def check(cases, labels=None, card=None):
    labels_by_id = {r['id']: r for r in labels} if labels is not None else None
    groups, kinds = defaultdict(set), set()
    for case in cases:
        key, kind = group_key(case)
        kinds.add(kind)
        ref = reference_of(case, labels_by_id) or {}
        groups[key].add(ref.get('status'))
    claimed = list(card.get('clauses') or []) if card else []
    findings = []
    if claimed and 'family' in kinds:
        findings.append('cases carry no input.clause, so claimed clause coverage cannot be verified')
    targets = claimed or sorted(k for k in groups if k is not None)
    complete = 0
    for key in targets:
        present = groups.get(key)
        if present is None:
            findings.append(f'{key}: claimed but has no cases')
            continue
        lacking = [s for s in STATUSES if s not in present]
        if lacking:
            findings.append(f'{key}: no {"/".join(lacking)} case')
        else:
            complete += 1
    metrics = {'grouped_by': sorted(kinds), 'groups_checked': len(targets),
               'groups_complete': complete,
               'status_by_group': {str(k): sorted(s for s in v if s) for k, v in sorted(groups.items(),
                                                                                       key=lambda i: str(i[0]))}}
    return GateResult(GATE, TITLE, SPEC_RULE, 'fail' if findings else 'pass', findings, metrics)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--cases', required=True, help='evaluated case JSONL')
    parser.add_argument('--labels')
    parser.add_argument('--card', help='result card; its clauses list is the coverage claim')
    args = parser.parse_args(argv)
    try:
        result = check(load_jsonl(args.cases), load_jsonl(args.labels) if args.labels else None,
                       load_json(args.card) if args.card else None)
    except (InputError, OSError) as error:
        print(f'{GATE} input error: {error}', file=sys.stderr)
        return EXIT_INPUT_ERROR
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return EXIT_PASS if result.status == 'pass' else EXIT_FAIL


if __name__ == '__main__':
    sys.exit(main())
