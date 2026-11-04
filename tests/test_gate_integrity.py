"""Checks for evaluation evidence that the standalone gates must reject."""
from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gates import g04_holdout, g07_lineage, g10_latency
from gates.common import EXIT_INPUT_ERROR, InputError


class HoldoutScanTest(unittest.TestCase):
    def test_invalid_scan_roots_are_input_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            file = root / 'file'
            file.touch()
            for path in (root / 'missing', file):
                with self.subTest(path=path.name):
                    with self.assertRaises(InputError):
                        g04_holdout.check(path)
                    with contextlib.redirect_stderr(io.StringIO()) as error:
                        code = g04_holdout.main([str(path)])
                    self.assertEqual(code, EXIT_INPUT_ERROR)
                    self.assertIn('existing directory', error.getvalue())

    def test_json_formats_decode_escaped_markers(self):
        row = r'{"region":"private\u005fholdout","input":"synthetic marker"}'
        for suffix, text in (('.json', '{"rows": [' + row + ']}'), ('.jsonl', row + '\n')):
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as tmp:
                (Path(tmp) / f'fixture{suffix}').write_text(text, encoding='utf-8')
                result = g04_holdout.check(tmp)
                self.assertEqual(result.status, 'fail')
                self.assertIn('holdout', result.findings[0])
                self.assertNotIn('synthetic marker', result.findings[0])

    def test_recognized_holdout_file_is_rejected_without_opening_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'holdout.jsonl').touch()
            with patch.object(Path, 'read_text', side_effect=AssertionError('unexpected read')):
                self.assertEqual(g04_holdout.check(tmp).status, 'fail')

    def test_malformed_json_is_not_evidence_of_a_clean_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'fixture.json').write_text('{"broken": ', encoding='utf-8')
            result = g04_holdout.check(tmp)
            self.assertEqual(result.status, 'fail')
            self.assertIn('cannot be parsed', result.findings[0])


class LineageTest(unittest.TestCase):
    def test_base_families_and_aliases_form_one_lineage(self):
        truth = [
            {'name': 'teacher-1', 'family': 'adapter-a', 'base_family': 'root-a'},
            {'name': 'teacher-2', 'family': 'adapter-b', 'base_family': ' ROOT-A '},
            {'name': 'teacher-3', 'family': 'adapter-c', 'base_family': 'adapter-b'},
        ]
        card = {'lineage': {'generator': [], 'truth': truth, 'judges': [{'family': 'independent'}]}}
        result = g07_lineage.check(card)
        self.assertEqual(result.status, 'fail')
        self.assertEqual(result.metrics['independent_truth_lineages'], 1)
        truth.append({'name': 'teacher-4', 'family': 'root-b'})
        result = g07_lineage.check(card)
        self.assertEqual(result.status, 'pass')
        self.assertEqual(result.metrics['independent_truth_lineages'], 2)


class LatencyInputTest(unittest.TestCase):
    def test_unusable_latency_rows_raise_input_errors(self):
        valid = {'execution_status': 'ok', 'latency_ms': 1}
        invalid = [
            None,
            [],
            1,
            [{'execution_status': 'ok'}],
            [{**valid, 'execution_status': 'unknown'}],
            [{'latency_ms': 1}],
        ] + [[{**valid, 'latency_ms': value}]
             for value in (None, True, -1, '1', float('inf'), float('nan'), 10**400)]
        for predictions in invalid:
            with self.subTest(predictions=predictions), self.assertRaises(InputError):
                g10_latency.measured(predictions)

    def test_standalone_latency_gate_reports_empty_and_bad_predictions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            card = root / 'card.json'
            predictions = root / 'predictions.jsonl'
            card.write_text(json.dumps({'latency': {}}), encoding='utf-8')
            for text in ('', '{"execution_status": "ok"}\n'):
                with self.subTest(text=text):
                    predictions.write_text(text, encoding='utf-8')
                    with contextlib.redirect_stderr(io.StringIO()) as error:
                        code = g10_latency.main(['--card', str(card), '--predictions', str(predictions)])
                    self.assertEqual(code, EXIT_INPUT_ERROR)
                    self.assertIn('G10 input error:', error.getvalue())

    def test_measured_latency_includes_failed_requests(self):
        rows = [
            {'execution_status': 'ok', 'latency_ms': 1},
            {'execution_status': 'timeout', 'latency_ms': 10},
        ]
        self.assertEqual(g10_latency.measured(rows), {
            'requests': 2, 'failures': 1, 'p50_ms': 1, 'p95_ms': 10,
        })
