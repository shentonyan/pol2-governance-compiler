"""Constant policies: the cheapest ways to produce a prediction file without reading any case.

Each row follows the prediction interface of PoL-Governance benchmark/PROTOCOL.md:
id, status, issues, action, latency_ms, execution_status.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

POLICIES = {
    # name: (status, action, the loophole it tries)
    'always_allow': ('conforming', 'allow', '零误拦：一个都不拦'),
    'always_block': ('violating', 'block', '零漏判：全部拦'),
    'always_clarify': ('insufficient', 'clarify', '零自动处置：全部推回给人'),
}


def predict(policy, cases):
    status, action, _ = POLICIES[policy]
    return [{'id': row['id'], 'status': status, 'issues': [], 'action': action,
             'latency_ms': 0, 'execution_status': 'ok'} for row in cases]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--policy', required=True, choices=sorted(POLICIES))
    parser.add_argument('--inputs', required=True, help='JSONL with at least an id per row')
    parser.add_argument('--out', required=True, help='new file; an existing file is refused')
    args = parser.parse_args(argv)
    out = Path(args.out)
    if out.exists():
        parser.error(f'{out} exists; write to a new path instead of overwriting results')
    with open(args.inputs, encoding='utf-8') as handle:
        cases = [json.loads(line) for line in handle if line.strip()]
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('x', encoding='utf-8', newline='\n') as handle:
        for row in predict(args.policy, cases):
            handle.write(json.dumps(row, ensure_ascii=False) + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
