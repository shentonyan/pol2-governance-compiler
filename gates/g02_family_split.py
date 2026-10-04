"""G02: a scenario family lives in exactly one split, and so do its pairs and paraphrases.

Run it over all splits at once; a paraphrase whose source sits in another file cannot be checked
and is reported as a finding rather than silently skipped.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict

from .common import EXIT_FAIL, EXIT_INPUT_ERROR, EXIT_PASS, GateResult, InputError, load_jsonl

GATE = 'G02'
TITLE = '分区不跨族'
SPEC_RULE = '按场景族预先划分……同情节、翻译和改写不得跨区。（PoL-Governance SPEC，第 1 阶段）'
SPLIT_KEYS = ('split', 'region')  # pilot uses split, the DATA-02 contract uses region


def split_of(row):
    for key in SPLIT_KEYS:
        value = row.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def check(cases):
    findings = []
    family_splits = defaultdict(set)
    by_id = {}
    pairs = defaultdict(list)
    for row in cases:
        case_id = row.get('id')
        family = row.get('family_id')
        split = split_of(row)
        if not isinstance(family, str) or not family:
            findings.append(f'{case_id}: missing family_id')
            continue
        if split is None:
            findings.append(f'{case_id}: missing split/region')
            continue
        family_splits[family].add(split)
        by_id[case_id] = row
        if row.get('pair_id') is not None:
            pairs[row['pair_id']].append(row)

    for family, splits in sorted(family_splits.items()):
        if len(splits) > 1:
            findings.append(f'family {family} spans splits {sorted(splits)}')

    for pair_id, members in sorted(pairs.items(), key=lambda item: str(item[0])):
        if len({m['family_id'] for m in members}) > 1:
            findings.append(f'pair {pair_id} spans families')
        if len({split_of(m) for m in members}) > 1:
            findings.append(f'pair {pair_id} spans splits')

    for case_id, row in by_id.items():
        source = row.get('paraphrase_of')
        if source is None:
            continue
        if source not in by_id:
            findings.append(f'{case_id}: paraphrase_of {source} is not in the checked set')
            continue
        if by_id[source]['family_id'] != row['family_id']:
            findings.append(f'{case_id}: paraphrase of {source} sits in another family')
        if split_of(by_id[source]) != split_of(row):
            findings.append(f'{case_id}: paraphrase of {source} sits in another split')

    metrics = {
        'cases': len(cases),
        'families': len(family_splits),
        'splits': sorted({s for splits in family_splits.values() for s in splits}),
        'pairs': len(pairs),
    }
    return GateResult(GATE, TITLE, SPEC_RULE, 'fail' if findings else 'pass', findings, metrics)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cases', nargs='+', help='one or more case JSONL files, checked together')
    args = parser.parse_args(argv)
    try:
        rows = [row for path in args.cases for row in load_jsonl(path)]
    except (InputError, OSError) as error:
        print(f'{GATE} input error: {error}', file=sys.stderr)
        return EXIT_INPUT_ERROR
    result = check(rows)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return EXIT_PASS if result.status == 'pass' else EXIT_FAIL


if __name__ == '__main__':
    sys.exit(main())
