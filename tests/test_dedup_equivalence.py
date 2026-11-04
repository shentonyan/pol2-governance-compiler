"""Compare G03's optimized paths with exhaustive, small-data references."""

import math
import random
import unittest
from itertools import combinations
from unittest.mock import patch

from gates import g03_dedup as gate
from gates.common import InputError, reference_of


def case(case_id, target, split='public_test', status='conforming', pair_id=None):
    return {
        'id': case_id,
        'input': {'context': [], 'target': target},
        'split': split,
        'family_id': case_id,
        'pair_id': pair_id,
        'proposal': {'status': status},
    }


def exhaustive_auc(cases, labels_by_id=None):
    pos, neg = [], []
    for row in cases:
        status = (reference_of(row, labels_by_id) or {}).get('status')
        if status == 'violating':
            pos.append(len(gate.text_of(row)))
        elif status == 'conforming':
            neg.append(len(gate.text_of(row)))
    if not pos or not neg:
        return None, len(pos), len(neg)
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    auc = wins / (len(pos) * len(neg))
    return max(auc, 1 - auc), len(pos), len(neg)


class DedupEquivalenceTest(unittest.TestCase):
    def assert_matches_exhaustive(self, cases, labels=None, near=gate.NEAR):
        actual = gate.check(cases, labels, near).to_dict()
        with patch.object(gate, '_candidate_pairs', side_effect=lambda rows, *_: combinations(rows, 2)):
            with patch.object(gate, 'length_auc', side_effect=exhaustive_auc):
                expected = gate.check(cases, labels, near).to_dict()
        self.assertEqual(actual, expected)
        return actual

    def test_threshold_boundary_and_pair_exemption_keep_order(self):
        text = 'ABCDEFGHIJKLMNOPQRSTUV'
        cases = [
            case('base', text[:19], pair_id='minimal'),
            case('near-cross', text, 'validation'),
            case('minimal', text[:21], pair_id='minimal'),
            case('near-within', text[:20]),
            case('exact', '-'.join(text.lower()[:19])),
        ]
        boundary = 17 / 20
        for near in (math.nextafter(boundary, 0), boundary, math.nextafter(boundary, 1)):
            with self.subTest(near=near):
                report = self.assert_matches_exhaustive(cases, near=near)
                self.assertEqual(report['findings'][0], 'exact: exact duplicate of base')
                self.assertNotIn('minimal', [p[1] for p in report['metrics'][
                    'near_duplicates_within_split_across_families'] if p[0] == 'base'])
                cross_pair = any(f.startswith('base ~ near-cross:') for f in report['findings'])
                self.assertEqual(cross_pair, near <= boundary)

    def test_rounding_at_a_prefix_boundary(self):
        cases = [case('large', ''), case('small', '')]
        common = {f'shared-{i}' for i in range(7)}
        shingles = {'large': common | {f'unique-{i}' for i in range(43)}, 'small': common}
        near = 7 / 50
        self.assertGreater(near * 50, 7)
        self.assertEqual(list(gate._candidate_pairs(cases, shingles, near)), [tuple(cases)])

    def test_seeded_sets_cover_all_threshold_regimes(self):
        rng = random.Random(13)
        statuses = ('conforming', 'violating', 'insufficient')
        cases = []
        for group in range(20):
            base = ''.join(rng.choices('abcd爱道治理', k=24))
            for variation in range(4):
                cases.append(case(f'{group}-{variation}', base[:24 - variation] + '关' * variation,
                                  ('public_test', 'validation')[variation % 2],
                                  statuses[(group + variation) % len(statuses)],
                                  pair_id=f'pair-{group}' if variation < 2 else None))
        labels = [{'id': row['id'], 'status': statuses[i % len(statuses)]}
                  for i, row in enumerate(reversed(cases))]
        for near in (-1.0, 0.0, math.nextafter(0, 1), 0.4, 0.85, 1.0, 1.01, math.nan):
            with self.subTest(near=near):
                self.assert_matches_exhaustive(cases, labels, near)

    def test_auc_folds_directions_and_counts_ties(self):
        cases = [case(str(i), 'a' * length, status=status)
                 for i, (length, status) in enumerate(
                     [(2, 'violating'), (3, 'violating'), (5, 'violating'),
                      (1, 'conforming'), (2, 'conforming'), (2, 'conforming')])]
        self.assertEqual(gate.length_auc(cases), (8 / 9, 3, 3))
        self.assertEqual(gate.length_auc(cases), exhaustive_auc(cases))
        reversed_labels = {row['id']: {'status': 'conforming' if i < 3 else 'violating'}
                           for i, row in enumerate(cases)}
        self.assertEqual(gate.length_auc(cases, reversed_labels), exhaustive_auc(cases, reversed_labels))

    def test_auc_detects_exact_cutoff_with_ties(self):
        cases = [case(f'long-{i}', 'abcde', status='violating') for i in range(27)]
        cases += [case(f'tie-{i}', 'abc', status='violating') for i in range(3)]
        cases += [case(f'short-{i}', 'abc') for i in range(30)]
        report = self.assert_matches_exhaustive(cases)
        self.assertEqual(report['metrics']['length_auc'], 0.95)
        self.assertTrue(report['findings'][-1].startswith('length shortcut:'))

    def test_malformed_ids_and_inputs_raise_input_error(self):
        valid = case('valid', 'abc')
        malformed = [({}, 'without a string id'), (valid, 'duplicate id'),
                     ({**case('wrong', ''), 'input': 'abc'}, 'input must be an object'),
                     ({**case('wrong', ''), 'input': {'context': [1]}}, 'must contain strings')]
        for row, message in malformed:
            with self.subTest(row=row), self.assertRaisesRegex(InputError, message):
                gate.check([valid, row])
        with self.assertRaisesRegex(InputError, 'duplicate id'):
            gate.check([valid], labels=[{'id': 'valid'}, {'id': 'valid'}])


if __name__ == '__main__':
    unittest.main()
