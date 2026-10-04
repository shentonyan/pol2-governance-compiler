"""Run the red-team matrix and write results/tables/redteam_matrix.csv and coin_flip.json.

    python -m redteam
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from gates.common import load_jsonl

from . import fixture, scenarios

ROOT = Path(__file__).resolve().parents[1]
GATES = [f'G{i:02d}' for i in range(1, 11)]


def main():
    out = ROOT / 'results' / 'tables'
    out.mkdir(parents=True, exist_ok=True)
    rows = scenarios.run_matrix(seed=0)
    with (out / 'redteam_matrix.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, ['key', 'title', 'loophole', 'intended', 'verdict', 'caught_by']
                                + GATES, lineterminator='\n')
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, 'caught_by': ' '.join(row['caught_by'])})
    test, _ = fixture.build(0)
    pilot = load_jsonl(ROOT / 'data' / 'pilot' / 'pilot.jsonl')
    summary = {}
    for name, cases in (('fixture', test), ('pilot', pilot)):
        rate, points = scenarios.coin_flip_pass_rate(cases, trials=1000)
        summary[name] = {'trials': 1000, 'seeds': [1, 1000], 'pass_rate': rate,
                         'points_over_miss': [[round(o, 4), round(m, 4)] for o, m in points]}
    (out / 'coin_flip.json').write_text(json.dumps(summary, indent=1), encoding='utf-8')
    print(json.dumps({'scenarios': len(rows),
                      'honest_control': next(r['verdict'] for r in rows if r['key'] == 'H0'),
                      'cheats_caught': sum(r['verdict'] == 'fail' for r in rows if r['key'] != 'H0'),
                      'coin_flip_pass_rate': {k: v['pass_rate'] for k, v in summary.items()}}))


if __name__ == '__main__':
    main()
