"""The red-team matrix: the honest control passes everything, every cheat is caught where intended."""
from __future__ import annotations

import unittest

from redteam import fixture, scenarios


class RedTeamTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = {r['key']: r for r in scenarios.run_matrix(seed=0)}

    def test_honest_control_passes_all_ten_gates(self):
        row = self.rows['H0']
        self.assertEqual(row['verdict'], 'pass', row)
        self.assertEqual(row['caught_by'], [])

    def test_every_cheat_is_caught_by_its_intended_gate(self):
        for key, row in self.rows.items():
            if key == 'H0':
                continue
            with self.subTest(key=key, title=row['title']):
                self.assertEqual(row['verdict'], 'fail')
                self.assertIn(row['intended'], row['caught_by'])

    def test_every_gate_catches_at_least_one_cheat(self):
        caught = {g for r in self.rows.values() for g in r['caught_by']}
        self.assertEqual(caught, {f'G{i:02d}' for i in range(1, 11)})

    def test_coin_flip_rarely_passes_the_floor(self):
        test, _ = fixture.build(0)
        rate, _ = scenarios.coin_flip_pass_rate(test, trials=300)
        self.assertLess(rate, 0.10)


if __name__ == '__main__':
    unittest.main()
