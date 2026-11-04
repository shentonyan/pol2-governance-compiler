"""Benchmark G03 on fixed synthetic inputs and optionally compare a local baseline.

Run from the repository root:
    python -m tools.benchmark_dedup --baseline <old-checkout> --sizes 1000 3000
    python -m tools.benchmark_dedup --sizes 10000

The timer covers check() and result construction. Input generation, subprocess
startup, JSON parsing and comparison are outside the timed section.
"""
from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = 721
_WORKER = """\
import json
import sys
from time import perf_counter
from gates import g03_dedup

cases = json.load(sys.stdin)
start = perf_counter()
report = g03_dedup.check(cases).to_dict()
seconds = perf_counter() - start
print(json.dumps({"seconds": seconds, "report": report}))
"""


def sample(size):
    rng = random.Random(SEED)
    shared_context = 'request reviewed after notice: '
    previous = ''
    cases = []
    for i in range(size):
        if i % 301 == 1:
            target = previous + 'x'
        else:
            suffix = ''.join(rng.choices('abcdefghijklmnopqrstuvwxyz治理任务', k=rng.randint(50, 90)))
            target = shared_context + suffix
        previous = target
        cases.append({
            'id': str(i),
            'split': ('public_test', 'validation')[i % 2],
            'family_id': f'family-{i}',
            'input': {'target': target},
            'proposal': {'status': ('conforming', 'violating')[i % 2]},
        })
    return cases


def timed_check(checkout, cases_json):
    result = subprocess.run(
        [sys.executable, '-B', '-X', 'utf8', '-c', _WORKER],
        cwd=checkout, input=cases_json, encoding='utf-8', capture_output=True,
    )
    if result.returncode:
        raise RuntimeError(f'G03 benchmark worker failed: {result.stderr.strip()}')
    return json.loads(result.stdout)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, help='local checkout of the earlier G03 implementation')
    parser.add_argument('--sizes', type=int, nargs='+', default=[1000, 3000])
    args = parser.parse_args(argv)
    if any(size < 1 for size in args.sizes):
        parser.error('--sizes values must be positive')
    if args.baseline and not (args.baseline / 'gates' / 'g03_dedup.py').is_file():
        parser.error('--baseline must contain gates/g03_dedup.py')

    results = []
    for size in args.sizes:
        cases_json = json.dumps(sample(size), ensure_ascii=False)
        current = timed_check(ROOT, cases_json)
        result = {'cases': size, 'optimized_seconds': current['seconds']}
        if args.baseline:
            baseline = timed_check(args.baseline, cases_json)
            if baseline['report'] != current['report']:
                parser.error(f'G03 reports differ for {size} cases')
            result.update(baseline_seconds=baseline['seconds'],
                          speedup=baseline['seconds'] / current['seconds'],
                          reports_equal=True)
        results.append(result)
    print(json.dumps({'seed': SEED, 'results': results}, indent=2))


if __name__ == '__main__':
    main()
