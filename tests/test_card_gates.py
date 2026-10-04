"""G01, G03, G05, G07, G08, G09, G10: each must accept the honest fixture and refuse one bad input."""
from __future__ import annotations

import copy
import unittest

from gates import g01_schema, g03_dedup, g05_thresholds, g07_lineage, g08_coverage, g09_honesty, g10_latency
from gates.common import InputError
from redteam import fixture

TEST, VAL = fixture.build(0)
PREDS = fixture.honest_predictions(TEST)
CARD = fixture.honest_card(PREDS, VAL)


def card(**sections):
    k = copy.deepcopy(CARD)
    for name, patch in sections.items():
        if isinstance(patch, dict):
            k[name].update(patch)
        else:
            k[name] = patch
    return k


class G01Test(unittest.TestCase):
    def test_honest_predictions_pass(self):
        self.assertEqual(g01_schema.check(TEST, PREDS).status, 'pass')

    def test_failure_with_a_verdict_fails(self):
        rows = copy.deepcopy(PREDS)
        rows[0].update(execution_status='error', status='violating')
        self.assertEqual(g01_schema.check(TEST, rows).status, 'fail')

    def test_missing_and_unknown_ids_fail(self):
        rows = copy.deepcopy(PREDS[1:]) + [dict(PREDS[0], id='nope')]
        findings = ' '.join(g01_schema.check(TEST, rows).findings)
        self.assertIn('unknown ids', findings)
        self.assertIn('missing ids', findings)

    def test_probabilities_must_sum_to_one(self):
        rows = copy.deepcopy(PREDS)
        ok = next(r for r in rows if r['execution_status'] == 'ok')
        ok['status_probs'] = {'conforming': 0.5, 'violating': 0.4, 'insufficient': 0.2}
        self.assertEqual(g01_schema.check(TEST, rows).status, 'fail')

    def test_issue_enum_when_given(self):
        rows = copy.deepcopy(PREDS)
        rows[1]['issues'] = ['made_up']
        self.assertEqual(g01_schema.check(TEST, rows, issue_enum=['dishonesty']).status, 'fail')


class G03Test(unittest.TestCase):
    def test_fixture_passes(self):
        result = g03_dedup.check(TEST + VAL)
        self.assertEqual(result.status, 'pass', result.findings)
        self.assertLess(result.metrics['length_auc'], 0.95)

    def test_exact_duplicate_fails(self):
        dup = dict(copy.deepcopy(TEST[0]), id='dup')
        self.assertEqual(g03_dedup.check(TEST + [dup]).status, 'fail')

    def test_minimal_pairs_are_exempt(self):
        a, b = copy.deepcopy(TEST[0]), copy.deepcopy(TEST[0])
        b.update(id='pair-b', split='validation')
        b['input']['target'] += ' x'
        a['pair_id'] = b['pair_id'] = 'p'
        self.assertEqual(g03_dedup.check([a, b]).status, 'pass')

    def test_length_shortcut_fails(self):
        rows = copy.deepcopy(TEST)
        for r in rows:
            if r['proposal']['status'] == 'violating':
                r['input']['target'] += ' padding words' * 20
        self.assertEqual(g03_dedup.check(rows).status, 'fail')


class G05Test(unittest.TestCase):
    def test_validation_ids_pass(self):
        self.assertEqual(g05_thresholds.check(CARD, TEST + VAL, TEST).status, 'pass')

    def test_test_ids_fail(self):
        bad = card(thresholds={'case_ids': [TEST[0]['id']]})
        self.assertEqual(g05_thresholds.check(bad, TEST + VAL, TEST).status, 'fail')

    def test_wrong_subset_fails(self):
        val = copy.deepcopy(VAL)
        val[0]['subset'] = 'dev'
        self.assertEqual(g05_thresholds.check(CARD, TEST + val, TEST).status, 'fail')

    def test_no_threshold_section_is_an_input_error(self):
        bad = copy.deepcopy(CARD)
        del bad['thresholds']
        with self.assertRaises(InputError):
            g05_thresholds.check(bad, TEST + VAL)


class G07Test(unittest.TestCase):
    def test_disjoint_families_pass(self):
        self.assertEqual(g07_lineage.check(CARD).status, 'pass')

    def test_truth_from_one_family_fails(self):
        bad = card(lineage={'truth': [{'name': 'teacher-b', 'family': 'family-b'}]})
        self.assertEqual(g07_lineage.check(bad).status, 'fail')

    def test_truth_sharing_the_generator_family_fails(self):
        bad = card(lineage={'truth': [{'name': 't1', 'family': 'family-a'},
                                      {'name': 't2', 'family': 'family-c'}]})
        self.assertEqual(g07_lineage.check(bad).status, 'fail')

    def test_declared_base_family_is_used(self):
        bad = card(lineage={'judges': [{'name': 'my-judge', 'family': 'lab', 'base_family': 'family-c'}]})
        self.assertEqual(g07_lineage.check(bad).status, 'fail')


class G08Test(unittest.TestCase):
    def test_fixture_covers_every_clause(self):
        self.assertEqual(g08_coverage.check(TEST, card=CARD).status, 'pass')

    def test_claimed_clause_without_cases_fails(self):
        bad = card(clauses=list(fixture.CLAUSES) + ['SYN.9'])
        self.assertEqual(g08_coverage.check(TEST, card=bad).status, 'fail')

    def test_claim_on_data_without_clause_field_fails(self):
        rows = copy.deepcopy(TEST)
        for r in rows:
            del r['input']['clause']
        self.assertEqual(g08_coverage.check(rows, card=CARD).status, 'fail')


class G09Test(unittest.TestCase):
    def test_honest_card_passes(self):
        self.assertEqual(g09_honesty.check(CARD, TEST).status, 'pass')

    def test_honesty_flag_missing_fails(self):
        bad = card(honesty={'negative_results_reported': False})
        self.assertEqual(g09_honesty.check(bad).status, 'fail')

    def test_reviewed_claim_on_unreviewed_cases_fails(self):
        bad = card(data={'reference_status': 'reviewed'})
        self.assertEqual(g09_honesty.check(bad, TEST).status, 'fail')

    def test_wrong_split_on_card_fails(self):
        bad = card(evaluation={'split': 'private_holdout'})
        self.assertEqual(g09_honesty.check(bad, TEST).status, 'fail')

    def test_blind_needs_holdout_independent_and_unseen(self):
        ok = card(evaluation={'split': 'private_holdout', 'blind': True, 'evaluator': 'independent',
                              'public_test_seen': False})
        self.assertEqual(g09_honesty.check(ok).status, 'pass')


class G10Test(unittest.TestCase):
    def test_honest_card_passes(self):
        self.assertEqual(g10_latency.check(CARD, PREDS).status, 'pass')

    def test_p95_understated_fails(self):
        bad = card(latency={'p95_ms': 1})
        self.assertEqual(g10_latency.check(bad, PREDS).status, 'fail')

    def test_model_number_as_hardware_fails(self):
        bad = card(latency={'hardware_class': 'GPU 4090'})
        self.assertEqual(g10_latency.check(bad, PREDS).status, 'fail')

    def test_nearest_rank(self):
        self.assertEqual(g10_latency.nearest_rank([5, 1, 3, 2, 4], 0.5), 3)
        self.assertEqual(g10_latency.nearest_rank(list(range(1, 21)), 0.95), 19)


if __name__ == '__main__':
    unittest.main()
