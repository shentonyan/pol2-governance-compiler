"""Run every implemented gate and list the ones that are not implemented yet.

The overall verdict is ``fail`` if any implemented gate fails, otherwise ``incomplete`` until all ten
gates exist. ``incomplete`` is never reported as a pass.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import g02_family_split, g04_holdout, g06_floor
from .common import EXIT_FAIL, EXIT_INPUT_ERROR, EXIT_PASS, GateResult, InputError, load_jsonl

ROOT = Path(__file__).resolve().parents[1]

PLANNED = {
    'G01': ('schema 与执行状态', 'PROTOCOL：execution_status 非 ok 时 status=null、issues=[]；重复/未知 ID 拒绝计算'),
    'G03': ('去重', 'SPEC：去除精确及语义近重复，检查标签捷径'),
    'G05': ('阈值来源', 'SPEC：阈值与校准只用预留校验数据'),
    'G07': ('血缘隔离', 'SPEC：不把同源教师一致当真值'),
    'G08': ('条款覆盖与三类齐备', 'SPEC：同时包括正常、违规、信息不足案例'),
    'G09': ('诚实条款', 'SPEC：公开测试反复看过的成绩不当盲测；PROTOCOL：pilot 永不具排名资格'),
    'G10': ('延迟与成本', 'PROTOCOL：p50/p95 nearest-rank，披露请求数与失败数；不跨硬件排名'),
}


def run(cases=None, labels=None, predictions=None, root=ROOT, allow=()):
    results = []
    if cases is not None:
        results.append(g02_family_split.check(cases))
    results.append(g04_holdout.check(root, allow))
    if cases is not None:
        results.append(g06_floor.check(cases, predictions, labels))
    for gate, (title, rule) in PLANNED.items():
        results.append(GateResult(gate, title, rule, 'not_implemented'))
    results.sort(key=lambda r: r.gate)
    statuses = [r.status for r in results]
    verdict = 'fail' if 'fail' in statuses else (
        'incomplete' if 'not_implemented' in statuses or 'not_applicable' in statuses else 'pass')
    implemented = sum(s != 'not_implemented' for s in statuses)
    return {'verdict': verdict, 'gates_implemented': f'{implemented}/{len(results)}',
            'results': [r.to_dict() for r in results]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', help='case JSONL; enables G02 and G06')
    parser.add_argument('--labels', help='label JSONL for G06; default: proposals embedded in cases')
    parser.add_argument('--predictions', help='candidate predictions for G06')
    parser.add_argument('--root', default=str(ROOT), help='tree scanned by G04 (default: repo root)')
    parser.add_argument('--allow', action='append', default=[], help='path exempted from G04')
    args = parser.parse_args(argv)
    try:
        cases = load_jsonl(args.cases) if args.cases else None
        labels = load_jsonl(args.labels) if args.labels else None
        predictions = load_jsonl(args.predictions) if args.predictions else None
        report = run(cases, labels, predictions, args.root, args.allow)
    except (InputError, OSError) as error:
        print(f'input error: {error}', file=sys.stderr)
        return EXIT_INPUT_ERROR
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return EXIT_FAIL if report['verdict'] == 'fail' else EXIT_PASS


if __name__ == '__main__':
    sys.exit(main())
