"""G10: the latency and failure numbers on the card are the ones the predictions actually show.

Recomputes request count, failure count and p50/p95 latency (nearest rank, over every request,
failures included, as in PoL-Governance benchmark/evaluate.py) and compares them with the card.
The card must also state a hardware class and the concurrency. The hardware class is a category such
as "single consumer GPU"; a long model number is refused because it is a machine detail and invites
cross-hardware ranking.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys

from .card import require_sections, section
from .common import (EXIT_FAIL, EXIT_INPUT_ERROR, EXIT_PASS, GateResult, InputError, finite_number,
                     load_json, load_jsonl)
from .g01_schema import EXECUTION

GATE = 'G10'
TITLE = '延迟与失败披露'
SPEC_RULE = ('延迟为客户端处理一次请求的全部时间……p50/p95 用 nearest-rank，并披露已观测请求数与失败数；'
             '不把同一模型在不同硬件下的延迟直接排名。（PoL-Governance benchmark/PROTOCOL.md）')
TOLERANCE_MS = 0.5
MODEL_NUMBER = re.compile(r'\d{3,}')


def nearest_rank(values, q):
    ordered = sorted(values)
    return ordered[max(0, math.ceil(q * len(ordered)) - 1)] if ordered else None


def _valid_latency(value):
    return finite_number(value) and value >= 0


def measured(predictions):
    if not isinstance(predictions, (list, tuple)) or not predictions:
        raise InputError('latency requires a non-empty sequence of predictions')
    latencies = []
    failures = 0
    for number, prediction in enumerate(predictions, 1):
        if not isinstance(prediction, dict):
            raise InputError(f'prediction row {number}: expected an object')
        latency = prediction.get('latency_ms')
        if not _valid_latency(latency):
            raise InputError(f'prediction row {number}: latency_ms must be a finite number >= 0')
        state = prediction.get('execution_status')
        if state not in EXECUTION:
            raise InputError(f'prediction row {number}: unknown or missing execution_status')
        latencies.append(latency)
        failures += state != 'ok'
    return {'requests': len(latencies), 'failures': failures,
            'p50_ms': nearest_rank(latencies, 0.5), 'p95_ms': nearest_rank(latencies, 0.95)}


def check(card, predictions):
    require_sections(card, 'latency')
    reported = section(card, 'latency')
    actual = measured(predictions)
    findings = []
    for key in ('requests', 'failures'):
        value = reported.get(key)
        if type(value) is not int or value != actual[key]:
            findings.append(f'latency.{key}: card says {value!r}, predictions show {actual[key]}')
    for key in ('p50_ms', 'p95_ms'):
        value = reported.get(key)
        if not _valid_latency(value) or abs(value - actual[key]) > TOLERANCE_MS:
            findings.append(f'latency.{key}: card says {value!r}, predictions show {actual[key]}')
    hardware = reported.get('hardware_class')
    if not isinstance(hardware, str) or not hardware.strip():
        findings.append('latency.hardware_class is missing')
    elif MODEL_NUMBER.search(hardware):
        findings.append('latency.hardware_class looks like a model number; give a category instead')
    concurrency = reported.get('concurrency')
    if type(concurrency) is not int or concurrency < 1:
        findings.append('latency.concurrency must be a positive integer')
    return GateResult(GATE, TITLE, SPEC_RULE, 'fail' if findings else 'pass', findings,
                      {'measured': actual})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--card', required=True)
    parser.add_argument('--predictions', required=True)
    args = parser.parse_args(argv)
    try:
        result = check(load_json(args.card), load_jsonl(args.predictions))
    except (InputError, OSError) as error:
        print(f'{GATE} input error: {error}', file=sys.stderr)
        return EXIT_INPUT_ERROR
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return EXIT_PASS if result.status == 'pass' else EXIT_FAIL


if __name__ == '__main__':
    sys.exit(main())
