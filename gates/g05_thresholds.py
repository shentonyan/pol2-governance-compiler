"""G05: every case used to set a threshold comes from the validation split.

The result card lists the ids in thresholds.case_ids (an empty list means no tuned threshold). Each id
must exist in the dataset, sit in the validation split, carry subset "calibration" when the dataset
marks subsets, and must not be one of the evaluated cases.
"""
from __future__ import annotations

import argparse
import json
import sys

from .card import require_sections, section
from .common import (EXIT_FAIL, EXIT_INPUT_ERROR, EXIT_PASS, GateResult, InputError, load_json,
                     load_jsonl, split_of)

GATE = 'G05'
TITLE = '阈值来源'
SPEC_RULE = ('阈值与校准只用预留校验数据……需要概率/阈值校准时，在其中预先划出互不重叠的开发与校准子集。'
             '（PoL-Governance SPEC，第 1、3 阶段）')
ALLOWED_SPLIT = 'validation'


def check(card, dataset, evaluated=None):
    require_sections(card, 'thresholds')
    ids = section(card, 'thresholds').get('case_ids')
    if not isinstance(ids, list) or not all(isinstance(i, str) for i in ids):
        raise InputError('result card: thresholds.case_ids must be a list of ids')
    by_id = {row.get('id'): row for row in dataset}
    evaluated_ids = {row.get('id') for row in (evaluated or [])}
    findings = []
    for case_id in ids:
        row = by_id.get(case_id)
        if row is None:
            findings.append(f'{case_id}: threshold case not found in the dataset')
            continue
        if split_of(row) != ALLOWED_SPLIT:
            findings.append(f'{case_id}: threshold set on split {split_of(row)!r}, '
                            f'only {ALLOWED_SPLIT!r} is allowed')
        if 'subset' in row and row['subset'] != 'calibration':
            findings.append(f'{case_id}: validation subset {row["subset"]!r}, expected calibration')
        if case_id in evaluated_ids:
            findings.append(f'{case_id}: threshold case is also an evaluated case')
    metrics = {'threshold_cases': len(ids), 'tuned': bool(ids)}
    return GateResult(GATE, TITLE, SPEC_RULE, 'fail' if findings else 'pass', findings, metrics)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--card', required=True)
    parser.add_argument('--dataset', required=True, nargs='+', help='case JSONL of all splits')
    parser.add_argument('--evaluated', help='case JSONL that was evaluated')
    args = parser.parse_args(argv)
    try:
        dataset = [row for path in args.dataset for row in load_jsonl(path)]
        evaluated = load_jsonl(args.evaluated) if args.evaluated else None
        result = check(load_json(args.card), dataset, evaluated)
    except (InputError, OSError) as error:
        print(f'{GATE} input error: {error}', file=sys.stderr)
        return EXIT_INPUT_ERROR
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return EXIT_PASS if result.status == 'pass' else EXIT_FAIL


if __name__ == '__main__':
    sys.exit(main())
