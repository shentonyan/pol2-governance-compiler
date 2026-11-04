from __future__ import annotations

import unittest

from gates import g02_family_split, g05_thresholds
from gates.common import InputError


def case(case_id='case', split='public_test', **fields):
    return {'id': case_id, 'family_id': f'family-{case_id}', 'split': split,
            'input': {'target': 'synthetic fixture', 'context': ['synthetic context']}, **fields}


def threshold_card(*case_ids):
    return {'thresholds': {'case_ids': list(case_ids)}}


class DatasetBindingTest(unittest.TestCase):
    def test_split_aliases_and_json_key_order_are_equivalent(self):
        row = case()
        evaluated = {'input': {'context': ['synthetic context'], 'target': 'synthetic fixture'},
                     'region': 'public_test', 'family_id': row['family_id'], 'id': row['id']}
        self.assertEqual(g02_family_split.check([row], [evaluated]).status, 'pass')
        evaluated['split'] = 'public_test'
        self.assertEqual(g02_family_split.check([row], [evaluated]).status, 'pass')

    def test_evaluated_case_missing_from_dataset_fails(self):
        result = g02_family_split.check([case('cal', 'validation')], [case()])
        self.assertEqual(result.status, 'fail')
        self.assertIn('evaluated case missing from dataset', result.findings[0])

    def test_changed_record_with_same_id_fails_without_exposing_text(self):
        row = case()
        evaluated = dict(row, input={'target': 'different synthetic fixture'})
        result = g02_family_split.check([row], [evaluated])
        self.assertEqual(result.status, 'fail')
        self.assertEqual(result.findings, ['case: evaluated case differs from dataset record'])

    def test_conflicting_split_aliases_are_rejected(self):
        row = case()
        conflict = dict(row, region='validation')
        with self.assertRaisesRegex(InputError, 'conflicting split and region'):
            g02_family_split.check([conflict])
        with self.assertRaisesRegex(InputError, 'conflicting split and region'):
            g02_family_split.check([row], [conflict])

    def test_duplicate_ids_are_rejected_in_both_inputs(self):
        row = case()
        with self.assertRaisesRegex(InputError, 'dataset cases: duplicate id'):
            g02_family_split.check([row, row])
        with self.assertRaisesRegex(InputError, 'evaluated cases: duplicate id'):
            g02_family_split.check([row], [row, row])


class ThresholdBindingTest(unittest.TestCase):
    def test_calibration_tag_required_when_validation_subsets_exist(self):
        legacy = case('untagged', 'validation')
        marked = case('calibrated', 'validation', subset='calibration')
        dataset = [legacy, marked]
        result = g05_thresholds.check(threshold_card('untagged'), dataset)
        self.assertEqual(result.status, 'fail')
        self.assertIn('validation subset must be calibration', result.findings[0])
        self.assertEqual(g05_thresholds.check(threshold_card('calibrated'), dataset).status, 'pass')

    def test_legacy_validation_without_subsets_still_passes(self):
        dataset = [case('legacy', 'validation')]
        self.assertEqual(g05_thresholds.check(threshold_card('legacy'), dataset).status, 'pass')

    def test_duplicate_dataset_ids_cannot_override_threshold_split(self):
        dataset = [case('duplicate'), case('duplicate', 'validation')]
        with self.assertRaisesRegex(InputError, 'dataset cases: duplicate id'):
            g05_thresholds.check(threshold_card('duplicate'), dataset)

    def test_duplicate_threshold_ids_are_rejected(self):
        dataset = [case('cal', 'validation', subset='calibration')]
        with self.assertRaisesRegex(InputError, 'thresholds.case_ids must contain unique ids'):
            g05_thresholds.check(threshold_card('cal', 'cal'), dataset)


if __name__ == '__main__':
    unittest.main()
