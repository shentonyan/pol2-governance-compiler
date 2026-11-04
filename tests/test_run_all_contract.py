"""Exercise the aggregate CLI with synthetic inputs and machine-readable exit codes."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from gates import run_all
from redteam import fixture


class RunAllContractTest(unittest.TestCase):
    def test_unrepresentable_latency_does_not_drop_aggregate_report(self):
        cases, validation = fixture.build()
        predictions = fixture.honest_predictions(cases)
        card = fixture.honest_card(predictions, validation)
        predictions[0]['latency_ms'] = 10**400
        with tempfile.TemporaryDirectory() as root:
            report = run_all.run(cases=cases, predictions=predictions, card=card,
                                 dataset=cases + validation, root=root)
        self.assertEqual(report['verdict'], 'fail')
        statuses = {gate['gate']: gate['status'] for gate in report['results']}
        self.assertEqual((statuses['G01'], statuses['G06'], statuses['G10']),
                         ('fail', 'not_applicable', 'fail'))

    def test_only_complete_evidence_can_exit_zero(self):
        cases, validation = fixture.build()
        predictions = fixture.honest_predictions(cases)
        card = fixture.honest_card(predictions, validation)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name, rows in (('cases', cases), ('validation', validation),
                               ('predictions', predictions)):
                (root / f'{name}.jsonl').write_text(
                    ''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')
            (root / 'card.json').write_text(json.dumps(card), encoding='utf-8')
            command = [sys.executable, '-X', 'utf8', '-m', 'gates.run_all',
                       '--root', str(root), '--cases', str(root / 'cases.jsonl'),
                       '--predictions', str(root / 'predictions.jsonl'),
                       '--card', str(root / 'card.json')]
            for expected_exit, expected_verdict, datasets in (
                    (0, 'pass', ('cases', 'validation')),
                    (3, 'incomplete', ()),
                    (1, 'fail', ('validation',))):
                with self.subTest(datasets=datasets):
                    dataset_args = (['--dataset', *(str(root / f'{name}.jsonl') for name in datasets)]
                                    if datasets else [])
                    run = subprocess.run(command + dataset_args, capture_output=True, encoding='utf-8')
                    self.assertEqual(run.returncode, expected_exit, run.stderr)
                    report = json.loads(run.stdout)
                    self.assertEqual(report['verdict'], expected_verdict)
                    gates = {item['gate']: item['status'] for item in report['results']}
                    if expected_verdict == 'incomplete':
                        self.assertEqual({gates[gate] for gate in ('G02', 'G03', 'G05')},
                                         {'not_applicable'})
                    elif expected_verdict == 'fail':
                        self.assertEqual(gates['G02'], 'fail')

    def test_missing_scan_root_fails_in_json(self):
        with tempfile.TemporaryDirectory() as temp:
            missing = Path(temp) / 'missing'
            run = subprocess.run(
                [sys.executable, '-X', 'utf8', '-m', 'gates.run_all', '--root', str(missing)],
                capture_output=True, encoding='utf-8')
        self.assertEqual(run.returncode, 1, run.stderr)
        report = json.loads(run.stdout)
        self.assertEqual(report['verdict'], 'fail')
        self.assertEqual(report['results'][3]['status'], 'fail')
