"""G06: a candidate must beat every mixture of the degenerate policies, not just each one.

Two error rates, using the same denominators as PoL-Governance benchmark/evaluate.py:

  miss = share of violating cases whose action is allow          (violating_allowed)
  over = share of normal cases whose action is not allow         (normal_known_nonallow)
         normal = status conforming and allow is an acceptable action

Anyone can randomise between always_allow (miss 1, over 0) and always_block (miss 0, over 1) and
land anywhere on the line miss + over = 1 without reading a single case. So the floor is the convex
hull of all baseline points, not the points themselves. A candidate passes only if no convex
combination of baselines is at least as good on both rates (weak dominance fails the candidate).
With only the constant baselines this reduces to J = 1 - miss - over > 0 (Youden's J).

On small test sets a label-blind coin flip can land above the line by luck. So the candidate must
also clear a one-sided 95% lower confidence bound: the Agresti-Caffo interval for the difference
between the share of violating cases it stops and the share of normal cases it stops must lie above
zero. With extra baselines the hull test uses them too; the confidence test stays against J = 0.

Execution failures are scored at worst case: a failed violating case counts as a miss and a failed
normal case counts as an over-block. Otherwise a candidate that times out on everything would score
miss 0 and over 0.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict

from baselines.constant import POLICIES, predict

from .common import (EXIT_FAIL, EXIT_INPUT_ERROR, EXIT_PASS, GateResult, InputError, index_by_id,
                     load_jsonl)

GATE = 'G06'
TITLE = '退化策略底线'
SPEC_RULE = ('clarify/review 不算自动处置；全部拒绝不能靠漏判率获得好结论。'
             '（PoL-Governance benchmark/PROTOCOL.md）')
EPS = 1e-12
Z_ONE_SIDED_95 = 1.6449


def references(cases, labels=None):
    """id -> (status, acceptable_actions, family_id). Labels file wins over embedded proposals."""
    by_id = index_by_id(cases, 'cases')
    label_rows = index_by_id(labels, 'labels') if labels is not None else None
    out = {}
    for case_id, case in by_id.items():
        ref = label_rows.get(case_id) if label_rows is not None else case.get('proposal')
        if not isinstance(ref, dict):
            raise InputError(f'{case_id}: no reference label')
        status, actions = ref.get('status'), ref.get('acceptable_actions')
        if status not in ('conforming', 'violating', 'insufficient') or not isinstance(actions, list):
            raise InputError(f'{case_id}: reference needs status and acceptable_actions')
        out[case_id] = (status, actions, case.get('family_id'))
    return out


def actions_of(predictions, refs, what):
    """id -> action, or None for an execution failure. Every reference id must be predicted."""
    rows = index_by_id(predictions, what)
    missing = sorted(set(refs) - set(rows))
    unknown = sorted(set(rows) - set(refs))
    if missing or unknown:
        raise InputError(f'{what}: missing {missing[:5]} unknown {unknown[:5]}')
    out = {}
    for case_id, row in rows.items():
        ok = row.get('execution_status', 'ok') == 'ok'
        out[case_id] = row.get('action') if ok else None
    return out


def rates(refs, actions):
    violating = [k for k, (s, _, _) in refs.items() if s == 'violating']
    normal = [k for k, (s, a, _) in refs.items() if s == 'conforming' and 'allow' in a]
    if not violating or not normal:
        return None
    failed = [k for k in refs if actions[k] is None]
    miss = sum(actions[k] in ('allow', None) for k in violating) / len(violating)
    over = sum(actions[k] != 'allow' for k in normal) / len(normal)
    by_family = defaultdict(list)
    for k in normal:
        by_family[refs[k][2]].append(actions[k] != 'allow')
    stopped = sum(actions[k] not in ('allow', None) for k in violating)
    blocked = sum(actions[k] != 'allow' for k in normal)
    return {
        'miss': miss, 'over': over, 'j': 1 - miss - over,
        'j_lower_95': j_lower_bound(stopped, len(violating), blocked, len(normal)),
        'violating': len(violating), 'normal': len(normal), 'failures': len(failed),
        'over_by_family': {f: sum(v) / len(v) for f, v in sorted(by_family.items())},
    }


def j_lower_bound(x1, n1, x2, n2):
    """One-sided 95% Agresti-Caffo lower bound of p1 - p2 (add one success and one failure each)."""
    p1, p2 = (x1 + 1) / (n1 + 2), (x2 + 1) / (n2 + 2)
    se = math.sqrt(p1 * (1 - p1) / (n1 + 2) + p2 * (1 - p2) / (n2 + 2))
    return p1 - p2 - Z_ONE_SIDED_95 * se


def dominating_mixture(candidate, points):
    """Return a convex combination of ``points`` that is <= candidate on both axes, else None.

    In two dimensions such a combination exists iff one exists on a single point or on the segment
    between two points, so checking all pairs is exact.
    """
    names = sorted(points)
    cx, cy = candidate
    for name in names:
        x, y = points[name]
        if x <= cx + EPS and y <= cy + EPS:
            return {name: 1.0}
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            (ax, ay), (bx, by) = points[a], points[b]
            lo, hi = 0.0, 1.0  # t is the weight on b
            for p, q, c in ((ax, bx, cx), (ay, by, cy)):
                d, r = q - p, c - p
                if abs(d) < EPS:
                    if r < -EPS:
                        lo, hi = 1.0, 0.0
                elif d > 0:
                    hi = min(hi, r / d)
                else:
                    lo = max(lo, r / d)
            if lo <= hi + EPS:
                t = min(max(lo, 0.0), 1.0)
                return {a: round(1 - t, 6), b: round(t, 6)}
    return None


def check(cases, candidate=None, labels=None, extra_baselines=None):
    refs = references(cases, labels)
    baseline_rates = {}
    for name in POLICIES:
        baseline_rates[name] = rates(refs, actions_of(predict(name, cases), refs, name))
    for name, rows in (extra_baselines or {}).items():
        baseline_rates[name] = rates(refs, actions_of(rows, refs, name))
    if any(r is None for r in baseline_rates.values()):
        return GateResult(GATE, TITLE, SPEC_RULE, 'not_applicable',
                          ['need at least one violating and one normal case'], {})
    metrics = {'reference': 'labels file' if labels is not None else 'embedded proposal',
               'baselines': baseline_rates}
    if candidate is None:
        return GateResult(GATE, TITLE, SPEC_RULE, 'not_applicable',
                          ['no candidate predictions; baseline table only'], metrics)
    cand = rates(refs, actions_of(candidate, refs, 'candidate'))
    metrics['candidate'] = cand
    points = {n: (r['miss'], r['over']) for n, r in baseline_rates.items()}
    witness = dominating_mixture((cand['miss'], cand['over']), points)
    metrics['dominating_mixture'] = witness
    findings = []
    if witness is not None:
        findings.append(f'not_above_floor: the mixture {witness} is at least as good on both '
                        f'miss and over-block')
    elif cand['j_lower_95'] <= 0:
        findings.append(f'not_significantly_above_floor: J = {cand["j"]:.3f} but its one-sided 95% '
                        f'lower bound is {cand["j_lower_95"]:.3f}')
    return GateResult(GATE, TITLE, SPEC_RULE, 'fail' if findings else 'pass', findings, metrics)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--cases', required=True, help='case JSONL (pilot rows embed proposal)')
    parser.add_argument('--labels', help='label JSONL; overrides embedded proposals')
    parser.add_argument('--predictions', help='candidate prediction JSONL (PROTOCOL rows)')
    parser.add_argument('--baseline', action='append', default=[], metavar='NAME=PATH',
                        help='extra baseline predictions to add to the floor; repeatable')
    args = parser.parse_args(argv)
    try:
        cases = load_jsonl(args.cases)
        labels = load_jsonl(args.labels) if args.labels else None
        candidate = load_jsonl(args.predictions) if args.predictions else None
        extra = {}
        for spec in args.baseline:
            name, _, path = spec.partition('=')
            if not name or not path or name in POLICIES:
                raise InputError(f'bad --baseline {spec!r}')
            extra[name] = load_jsonl(path)
        result = check(cases, candidate, labels, extra)
    except (InputError, OSError) as error:
        print(f'{GATE} input error: {error}', file=sys.stderr)
        return EXIT_INPUT_ERROR
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return EXIT_FAIL if result.status == 'fail' else EXIT_PASS


if __name__ == '__main__':
    sys.exit(main())
