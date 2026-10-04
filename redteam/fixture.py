"""A synthetic, content-free dataset for exercising the gates.

The texts are random syllable strings, the clause ids are SYN.* placeholders and the model names are
generic. Nothing here is PoL2 content, so nothing here can leak into or stand in for real data.
"""
from __future__ import annotations

import random

CLAUSES = ('SYN.1', 'SYN.2', 'SYN.3', 'SYN.4')
# per clause: (conforming, violating, insufficient)
TEST_COUNTS = (12, 12, 4)
VALIDATION_COUNTS = (4, 4, 2)
ACTIONS = {'conforming': ['allow'], 'violating': ['block', 'repair'], 'insufficient': ['clarify']}
_SYLLABLES = [c + v for c in 'bdfgklmnprstvz' for v in 'aeiou']


def _text(rng, words):
    return ' '.join(''.join(rng.choice(_SYLLABLES) for _ in range(rng.randint(2, 4)))
                    for _ in range(words))


def build(seed=0):
    """Return (public_test cases, validation cases)."""
    rng = random.Random(seed)
    test, validation = [], []
    for clause in CLAUSES:
        for split, counts, out in (('public_test', TEST_COUNTS, test),
                                   ('validation', VALIDATION_COUNTS, validation)):
            family = f'{clause.lower().replace(".", "")}-{"test" if split == "public_test" else "val"}'
            for status, count in zip(('conforming', 'violating', 'insufficient'), counts):
                for _ in range(count):
                    out.append({
                        'id': f'{split[:3]}-{len(out):04d}', 'family_id': family, 'split': split,
                        'annotation_status': 'proposed_unreviewed',
                        'input': {'surface': 'assistant_output', 'context': [_text(rng, 8)],
                                  'target': _text(rng, rng.randint(6, 14)),
                                  'policy': 'synthetic fixture', 'clause': clause},
                        'proposal': {'status': status, 'issues': [],
                                     'acceptable_actions': list(ACTIONS[status])},
                    })
    return test, validation


def honest_predictions(cases, misses=2, over_blocks=3, timeouts=1):
    """A good but imperfect candidate: a few misses, a few over-blocks, one timeout."""
    rows, missed, over, timed = [], 0, 0, 0
    for i, case in enumerate(cases):
        ref = case['proposal']
        status, action, state = ref['status'], ref['acceptable_actions'][0], 'ok'
        if status == 'violating' and missed < misses:
            status, action, missed = 'conforming', 'allow', missed + 1
        elif status == 'conforming' and over < over_blocks:
            status, action, over = 'violating', 'block', over + 1
        elif status == 'conforming' and timed < timeouts:
            status, action, state, timed = None, None, 'timeout', timed + 1
        rows.append({'id': case['id'], 'status': status, 'issues': [], 'action': action,
                     'latency_ms': 900 if state == 'timeout' else 18 + (i * 7) % 23,
                     'execution_status': state})
    return rows


def honest_card(predictions, validation):
    from gates.g10_latency import measured
    lat = measured(predictions)
    return {
        'card_version': 1,
        'candidate': 'fixture-judge',
        'data': {'version': 'redteam-fixture-v1', 'reference_status': 'proposed_unreviewed',
                 'eligible_for_ranking': False},
        'evaluation': {'split': 'public_test', 'blind': False, 'public_test_seen': True,
                       'evaluator': 'self'},
        'thresholds': {'case_ids': [c['id'] for c in validation[:6]]},
        'lineage': {
            'generator': [{'name': 'teacher-a', 'family': 'family-a'}],
            'truth': [{'name': 'teacher-b', 'family': 'family-b'},
                      {'name': 'teacher-c', 'family': 'family-c'}],
            'judges': [{'name': 'judge-d', 'family': 'family-d'}],
        },
        'clauses': list(CLAUSES),
        'latency': {**lat, 'hardware_class': 'single consumer GPU', 'concurrency': 1},
        'honesty': {'reference_not_gold_unless_reviewed': True,
                    'no_generalisation_to_real_people': True,
                    'negative_results_reported': True},
    }
