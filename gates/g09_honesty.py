"""G09: the result card does not claim more than the evaluation can support.

Rules:

1. The three honesty statements are present and true.
2. Ranking eligibility needs reviewed reference labels and a split other than the public pilot.
3. A blind claim needs the private holdout, an independent evaluator and a test set nobody tuned on.
4. The card's split and label status match the evaluated cases (when cases are given): a card cannot
   call unreviewed proposals reviewed, or report a different split from the one that was run.
"""
from __future__ import annotations

import argparse
import json
import sys

from .card import HONESTY_FLAGS, require_sections, section
from .common import (EXIT_FAIL, EXIT_INPUT_ERROR, EXIT_PASS, GateResult, InputError, load_json,
                     load_jsonl, split_of)

GATE = 'G09'
TITLE = '诚实条款'
SPEC_RULE = ('公开测试用于共同回归；反复看过的成绩不当盲测。当前 20 例……eligible_for_ranking 永远为 false。'
             '（PoL-Governance SPEC 第 1 阶段、benchmark/PROTOCOL.md）')


def check(card, cases=None):
    require_sections(card, 'data', 'evaluation', 'honesty')
    data, ev, honesty = section(card, 'data'), section(card, 'evaluation'), section(card, 'honesty')
    findings = []
    for flag in HONESTY_FLAGS:
        if honesty.get(flag) is not True:
            findings.append(f'honesty.{flag} is not true')
    reviewed = data.get('reference_status') == 'reviewed'
    if data.get('eligible_for_ranking') is True:
        if not reviewed:
            findings.append('eligible_for_ranking with unreviewed reference labels')
        if ev.get('split') == 'pilot_public':
            findings.append('eligible_for_ranking on the public pilot')
    if ev.get('blind') is True:
        if ev.get('split') != 'private_holdout':
            findings.append(f'blind claim on split {ev.get("split")!r}; only the private holdout is blind')
        if ev.get('evaluator') != 'independent':
            findings.append('blind claim without an independent evaluator')
        if ev.get('public_test_seen') is not False:
            findings.append('blind claim although the test set was seen while building the candidate')
    if cases:
        splits = {split_of(c) for c in cases}
        if splits != {ev.get('split')}:
            findings.append(f'card reports split {ev.get("split")!r} but the cases are {sorted(map(str, splits))}')
        if reviewed and any(c.get('annotation_status') == 'proposed_unreviewed' for c in cases):
            findings.append('card says reviewed but the cases are marked proposed_unreviewed')
    metrics = {'split': ev.get('split'), 'blind': ev.get('blind'),
               'eligible_for_ranking': data.get('eligible_for_ranking'),
               'reference_status': data.get('reference_status')}
    return GateResult(GATE, TITLE, SPEC_RULE, 'fail' if findings else 'pass', findings, metrics)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--card', required=True)
    parser.add_argument('--cases', help='evaluated case JSONL, to cross-check the card')
    args = parser.parse_args(argv)
    try:
        result = check(load_json(args.card), load_jsonl(args.cases) if args.cases else None)
    except (InputError, OSError) as error:
        print(f'{GATE} input error: {error}', file=sys.stderr)
        return EXIT_INPUT_ERROR
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return EXIT_PASS if result.status == 'pass' else EXIT_FAIL


if __name__ == '__main__':
    sys.exit(main())
