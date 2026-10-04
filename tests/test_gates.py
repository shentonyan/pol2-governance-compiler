"""Every gate has cases it must pass and cases it must refuse."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from baselines.constant import POLICIES, predict
from gates import g02_family_split, g04_holdout, g06_floor, run_all
from gates.common import InputError, load_jsonl

ROOT = Path(__file__).resolve().parents[1]
PILOT = load_jsonl(ROOT / 'data' / 'pilot' / 'pilot.jsonl')


def case(cid, family, split='train', status='conforming', actions=('allow',), **extra):
    row = {'id': cid, 'family_id': family, 'split': split,
           'proposal': {'status': status, 'acceptable_actions': list(actions)}}
    row.update(extra)
    return row


def reference_policy(cases):
    """Predict the first acceptable action: what a perfect governance layer would do."""
    return [{'id': c['id'], 'status': c['proposal']['status'], 'issues': [],
             'action': c['proposal']['acceptable_actions'][0], 'latency_ms': 1,
             'execution_status': 'ok'} for c in cases]


class G02Test(unittest.TestCase):
    def test_pilot_passes(self):
        result = g02_family_split.check(PILOT)
        self.assertEqual(result.status, 'pass', result.findings)
        self.assertEqual(result.metrics['families'], 10)

    def test_family_across_splits_fails(self):
        result = g02_family_split.check([case('a', 'f', 'train'), case('b', 'f', 'public_test')])
        self.assertEqual(result.status, 'fail')
        self.assertIn('spans splits', result.findings[0])

    def test_paraphrase_must_follow_its_source(self):
        rows = [case('a', 'f', 'train'), case('b', 'g', 'public_test', paraphrase_of='a')]
        findings = ' '.join(g02_family_split.check(rows).findings)
        self.assertIn('another family', findings)
        self.assertIn('another split', findings)

    def test_unverifiable_paraphrase_is_reported(self):
        result = g02_family_split.check([case('b', 'g', paraphrase_of='elsewhere')])
        self.assertEqual(result.status, 'fail')

    def test_pair_across_splits_fails(self):
        rows = [case('a', 'f', 'train', pair_id='p1'), case('b', 'f2', 'validation', pair_id='p1')]
        findings = ' '.join(g02_family_split.check(rows).findings)
        self.assertIn('pair p1 spans splits', findings)

    def test_region_key_from_data02_contract(self):
        rows = [{'id': 'x', 'family_id': 'f', 'region': 'train'},
                {'id': 'y', 'family_id': 'f', 'region': 'validation'}]
        self.assertEqual(g02_family_split.check(rows).status, 'fail')


class G04Test(unittest.TestCase):
    def scan(self, files):
        with tempfile.TemporaryDirectory() as tmp:
            for name, text in files.items():
                path = Path(tmp) / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding='utf-8')
            return g04_holdout.check(tmp)

    def test_repository_itself_passes(self):
        self.assertEqual(g04_holdout.check(ROOT).status, 'pass')

    def test_registry_entry_without_content_passes(self):
        entry = [{'id': 'pol2-v0.1-holdout', 'split': 'private_holdout', 'cases': 512,
                  'sha256': 'ab' * 32}]
        self.assertEqual(self.scan({'registry.json': json.dumps(entry)}).status, 'pass')

    def test_holdout_row_with_content_fails(self):
        row = {'id': 'h1', 'region': 'private_holdout', 'input': {'target': 'x'}}
        result = self.scan({'data/cases.jsonl': json.dumps(row) + '\n'})
        self.assertEqual(result.status, 'fail')

    def test_file_named_like_holdout_fails(self):
        self.assertEqual(self.scan({'private_holdout.cases.jsonl': '{}\n'}).status, 'fail')

    def test_csv_cell_fails_unless_allowed(self):
        files = {'splits.csv': 'family,split\nf1,private_holdout\n'}
        self.assertEqual(self.scan(files).status, 'fail')
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'splits.csv').write_text(files['splits.csv'], encoding='utf-8')
            self.assertEqual(g04_holdout.check(tmp, allow=['splits.csv']).status, 'pass')

    def test_binary_data_fails(self):
        self.assertEqual(self.scan({'x.parquet': 'not really parquet'}).status, 'fail')


class G06Test(unittest.TestCase):
    def test_every_constant_policy_is_not_above_floor(self):
        for name in POLICIES:
            result = g06_floor.check(PILOT, predict(name, PILOT))
            self.assertEqual(result.status, 'fail', name)

    def test_reference_policy_passes_with_j_one(self):
        result = g06_floor.check(PILOT, reference_policy(PILOT))
        self.assertEqual(result.status, 'pass', result.findings)
        self.assertAlmostEqual(result.metrics['candidate']['j'], 1.0)

    def test_mixture_on_the_line_fails(self):
        # half the normal cases blocked, half the violating cases allowed: miss + over = 1
        cases = [case(f'n{i}', 'f') for i in range(4)]
        cases += [case(f'v{i}', 'g', status='violating', actions=('block',)) for i in range(4)]
        preds = [{'id': c['id'], 'action': 'block' if c['id'] in ('n0', 'n1', 'v0', 'v1')
                  else 'allow', 'execution_status': 'ok'} for c in cases]
        result = g06_floor.check(cases, preds)
        self.assertEqual(result.status, 'fail')
        self.assertIsNotNone(result.metrics['dominating_mixture'])

    def test_failures_are_scored_at_worst_case(self):
        preds = [{'id': c['id'], 'action': None, 'execution_status': 'timeout'} for c in PILOT]
        result = g06_floor.check(PILOT, preds)
        self.assertEqual(result.status, 'fail')
        self.assertEqual((result.metrics['candidate']['miss'], result.metrics['candidate']['over']),
                         (1.0, 1.0))

    def test_extra_baseline_raises_the_floor(self):
        good = reference_policy(PILOT)
        result = g06_floor.check(PILOT, good, extra_baselines={'oracle_copy': good})
        self.assertEqual(result.status, 'fail')

    def test_missing_prediction_is_an_input_error(self):
        with self.assertRaises(InputError):
            g06_floor.check(PILOT, reference_policy(PILOT)[1:])

    def test_dominance_is_exact_on_segments(self):
        points = {'allow': (1.0, 0.0), 'block': (0.0, 1.0)}
        self.assertIsNone(g06_floor.dominating_mixture((0.4, 0.4), points))
        self.assertIsNotNone(g06_floor.dominating_mixture((0.5, 0.5), points))
        self.assertIsNotNone(g06_floor.dominating_mixture((0.7, 0.4), points))


class RunAllTest(unittest.TestCase):
    def test_pilot_with_reference_policy_is_incomplete_not_pass(self):
        report = run_all.run(PILOT, None, reference_policy(PILOT))
        self.assertEqual(report['verdict'], 'incomplete')
        self.assertEqual(report['gates_implemented'], '3/10')
        statuses = {r['gate']: r['status'] for r in report['results']}
        self.assertEqual(statuses['G06'], 'pass')
        self.assertEqual(statuses['G08'], 'not_implemented')

    def test_degenerate_candidate_fails_overall(self):
        report = run_all.run(PILOT, None, predict('always_block', PILOT))
        self.assertEqual(report['verdict'], 'fail')


if __name__ == '__main__':
    unittest.main()
