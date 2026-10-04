"""Run all ten gates on whatever inputs are given.

A gate whose inputs are missing reports ``not_applicable``. The overall verdict is ``fail`` if any gate
fails, ``pass`` only if all ten pass, and ``incomplete`` otherwise. ``incomplete`` is never a pass.

Inputs:
  --cases        the evaluated cases (G01, G06, G08, G09)
  --dataset      all splits together (G02, G03, G05); defaults to --cases
  --labels       reference labels; default: proposals embedded in the cases
  --predictions  the candidate's predictions (G01, G06, G10)
  --card         the machine-readable result card (G05, G07, G08, G09, G10)
  --root         the tree G04 scans; defaults to the repository root
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import (g01_schema, g02_family_split, g03_dedup, g04_holdout, g05_thresholds, g06_floor,
               g07_lineage, g08_coverage, g09_honesty, g10_latency)
from .common import (EXIT_FAIL, EXIT_INPUT_ERROR, EXIT_PASS, GateResult, InputError, load_json,
                     load_jsonl)

ROOT = Path(__file__).resolve().parents[1]
MODULES = (g01_schema, g02_family_split, g03_dedup, g04_holdout, g05_thresholds, g06_floor,
           g07_lineage, g08_coverage, g09_honesty, g10_latency)


def _skip(module, why):
    return GateResult(module.GATE, module.TITLE, module.SPEC_RULE, 'not_applicable', [why])


def _guard(module, call):
    """Run one gate; a malformed input for that gate is a failure of that gate, not a crash."""
    try:
        return call()
    except InputError as error:
        return GateResult(module.GATE, module.TITLE, module.SPEC_RULE, 'fail',
                          [f'input rejected: {error}'])


def run(cases=None, labels=None, predictions=None, card=None, dataset=None, root=ROOT, allow=()):
    dataset = dataset if dataset is not None else cases
    r = {}
    r['G01'] = (_guard(g01_schema, lambda: g01_schema.check(cases, predictions))
                if cases is not None and predictions is not None
                else _skip(g01_schema, 'needs --cases and --predictions'))
    r['G02'] = (_guard(g02_family_split, lambda: g02_family_split.check(dataset))
                if dataset is not None else _skip(g02_family_split, 'needs --dataset or --cases'))
    r['G03'] = (_guard(g03_dedup, lambda: g03_dedup.check(dataset, labels))
                if dataset is not None else _skip(g03_dedup, 'needs --dataset or --cases'))
    r['G04'] = g04_holdout.check(root, allow)
    r['G05'] = (_guard(g05_thresholds, lambda: g05_thresholds.check(card, dataset, cases))
                if card is not None and dataset is not None
                else _skip(g05_thresholds, 'needs --card and the dataset'))
    if cases is not None and r['G01'].status == 'fail' and predictions is not None:
        r['G06'] = _skip(g06_floor, 'G01 failed; predictions are not scored')
    else:
        r['G06'] = (_guard(g06_floor, lambda: g06_floor.check(cases, predictions, labels))
                    if cases is not None else _skip(g06_floor, 'needs --cases'))
    r['G07'] = (_guard(g07_lineage, lambda: g07_lineage.check(card))
                if card is not None else _skip(g07_lineage, 'needs --card'))
    r['G08'] = (_guard(g08_coverage, lambda: g08_coverage.check(cases, labels, card))
                if cases is not None else _skip(g08_coverage, 'needs --cases'))
    r['G09'] = (_guard(g09_honesty, lambda: g09_honesty.check(card, cases))
                if card is not None else _skip(g09_honesty, 'needs --card'))
    r['G10'] = (_guard(g10_latency, lambda: g10_latency.check(card, predictions))
                if card is not None and predictions is not None
                else _skip(g10_latency, 'needs --card and --predictions'))
    statuses = [g.status for g in r.values()]
    verdict = 'fail' if 'fail' in statuses else ('pass' if set(statuses) == {'pass'} else 'incomplete')
    return {'verdict': verdict,
            'gates_passed': f'{statuses.count("pass")}/{len(statuses)}',
            'results': [g.to_dict() for g in r.values()]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--cases')
    parser.add_argument('--dataset', nargs='+')
    parser.add_argument('--labels')
    parser.add_argument('--predictions')
    parser.add_argument('--card')
    parser.add_argument('--root', default=str(ROOT))
    parser.add_argument('--allow', action='append', default=[], help='path exempted from G04')
    args = parser.parse_args(argv)
    try:
        cases = load_jsonl(args.cases) if args.cases else None
        dataset = [row for p in args.dataset for row in load_jsonl(p)] if args.dataset else None
        labels = load_jsonl(args.labels) if args.labels else None
        predictions = load_jsonl(args.predictions) if args.predictions else None
        card = load_json(args.card) if args.card else None
        report = run(cases, labels, predictions, card, dataset, args.root, args.allow)
    except (InputError, OSError) as error:
        print(f'input error: {error}', file=sys.stderr)
        return EXIT_INPUT_ERROR
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return EXIT_FAIL if report['verdict'] == 'fail' else EXIT_PASS


if __name__ == '__main__':
    sys.exit(main())
