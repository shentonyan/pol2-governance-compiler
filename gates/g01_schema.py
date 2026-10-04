"""G01: prediction rows follow the PROTOCOL machine interface, and every case is predicted.

Mirrors the checks in PoL-Governance benchmark/evaluate.py so a file that passes here also loads
there. The issue enum is not fixed here because the pilot and the DATA-02 ontology use different
lists; pass --issues to enforce one.
"""
from __future__ import annotations

import argparse
import json
import math
import sys

from .common import EXIT_FAIL, EXIT_INPUT_ERROR, EXIT_PASS, GateResult, InputError, load_jsonl

GATE = 'G01'
TITLE = 'schema 与执行状态'
SPEC_RULE = ('每条预测：id, status, issues[], action, latency_ms, execution_status；非 ok 时 '
             'status=null、issues=[]、不提供概率。缺失 ID 保留在总分母，重复/未知 ID 拒绝计算。'
             '（PoL-Governance benchmark/PROTOCOL.md）')
STATUSES = ('conforming', 'violating', 'insufficient')
ACTIONS = ('allow', 'repair', 'block', 'clarify', 'review')
EXECUTION = ('ok', 'timeout', 'error', 'invalid')
REQUIRED = {'id', 'status', 'issues', 'action', 'latency_ms', 'execution_status'}
ALLOWED = REQUIRED | {'status_probs'}


def _number(value):
    return type(value) in (int, float) and math.isfinite(value)


def _row_findings(key, row, issue_enum):
    out = []
    extra, missing = set(row) - ALLOWED, REQUIRED - set(row)
    if extra:
        out.append(f'{key}: unexpected fields {sorted(extra)}')
    if missing:
        return out + [f'{key}: missing fields {sorted(missing)}']
    state = row['execution_status']
    if state not in EXECUTION:
        return out + [f'{key}: execution_status {state!r}']
    ok = state == 'ok'
    issues = row['issues']
    if ok and row['status'] not in STATUSES:
        out.append(f'{key}: status {row["status"]!r}')
    if not ok and row['status'] is not None:
        out.append(f'{key}: a failed request must have status null')
    if not (isinstance(issues, list) and all(isinstance(x, str) for x in issues)
            and len(issues) == len(set(issues))):
        out.append(f'{key}: issues must be a list of unique strings')
    elif issue_enum and not set(issues) <= issue_enum:
        out.append(f'{key}: issues outside the enum {sorted(set(issues) - issue_enum)}')
    elif not ok and issues:
        out.append(f'{key}: a failed request must not invent issues')
    if ok and row['action'] not in ACTIONS:
        out.append(f'{key}: action {row["action"]!r}')
    if not ok and row['action'] is not None and row['action'] not in ACTIONS:
        out.append(f'{key}: fallback action {row["action"]!r}')
    if not (_number(row['latency_ms']) and row['latency_ms'] >= 0):
        out.append(f'{key}: latency_ms must be a finite number >= 0')
    if 'status_probs' in row:
        probs = row['status_probs']
        if not ok:
            out.append(f'{key}: a failed request must not report probabilities')
        elif not (isinstance(probs, dict) and set(probs) == set(STATUSES)
                  and all(_number(v) and 0 <= v <= 1 for v in probs.values())
                  and abs(sum(probs.values()) - 1) <= 1e-6):
            out.append(f'{key}: status_probs must cover the three statuses and sum to one')
    return out


def check(cases, predictions, issue_enum=None):
    case_ids = [c.get('id') for c in cases]
    findings, seen = [], {}
    for row in predictions:
        key = row.get('id')
        if not isinstance(key, str) or not key:
            findings.append('a prediction row has no string id')
            continue
        if key in seen:
            findings.append(f'{key}: duplicate prediction id')
            continue
        seen[key] = row
        findings.extend(_row_findings(key, row, set(issue_enum or ())))
    unknown = sorted(set(seen) - set(case_ids))
    missing = sorted(set(case_ids) - set(seen))
    if unknown:
        findings.append(f'unknown ids: {unknown[:5]}{" …" if len(unknown) > 5 else ""}')
    if missing:
        findings.append(f'missing ids (still counted in the denominator): '
                        f'{missing[:5]}{" …" if len(missing) > 5 else ""}')
    states = [r.get('execution_status') for r in seen.values()]
    metrics = {'cases': len(case_ids), 'predictions': len(seen), 'missing': len(missing),
               'failures': sum(s != 'ok' for s in states)}
    return GateResult(GATE, TITLE, SPEC_RULE, 'fail' if findings else 'pass', findings, metrics)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', required=True)
    parser.add_argument('--predictions', required=True)
    parser.add_argument('--issues', nargs='*', help='optional issue enum to enforce')
    args = parser.parse_args(argv)
    try:
        result = check(load_jsonl(args.cases), load_jsonl(args.predictions), args.issues)
    except (InputError, OSError) as error:
        print(f'{GATE} input error: {error}', file=sys.stderr)
        return EXIT_INPUT_ERROR
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return EXIT_PASS if result.status == 'pass' else EXIT_FAIL


if __name__ == '__main__':
    sys.exit(main())
