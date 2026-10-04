"""Cheating scenarios: each one changes exactly one thing in the honest control.

Every scenario names the gate meant to catch it. ``run_matrix`` runs all ten gates on every scenario,
so the table shows both the intended catch and any other gate that also reacts.
"""
from __future__ import annotations

import copy
import json
import random
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from baselines.constant import predict
from gates import run_all
from gates.g10_latency import measured

from . import fixture


@dataclass
class Scenario:
    key: str
    title: str
    loophole: str
    intended: str
    cases: list
    validation: list
    predictions: list
    card: dict
    extra_files: dict = field(default_factory=dict)

    @property
    def dataset(self):
        return self.cases + self.validation


def _relatency(card, predictions):
    """Keep the card's latency honest so that only the intended change differs."""
    card['latency'].update(measured(predictions))
    return card


def _coin_flip(cases, seed):
    rng = random.Random(seed)
    rows = []
    for case in cases:
        stop = rng.random() < 0.5
        rows.append({'id': case['id'], 'status': 'violating' if stop else 'conforming', 'issues': [],
                     'action': 'block' if stop else 'allow', 'latency_ms': 1,
                     'execution_status': 'ok'})
    return rows


def build(seed=0):
    test, val = fixture.build(seed)
    preds = fixture.honest_predictions(test)
    card = fixture.honest_card(preds, val)

    def variant(key, title, loophole, intended, *, cases=None, validation=None, predictions=None,
                card_edit=None, extra_files=None, keep_latency=False):
        c = copy.deepcopy(cases if cases is not None else test)
        v = copy.deepcopy(validation if validation is not None else val)
        p = copy.deepcopy(predictions if predictions is not None else preds)
        k = copy.deepcopy(card)
        if predictions is not None and not keep_latency:
            _relatency(k, p)
        if card_edit:
            card_edit(k)
        return Scenario(key, title, loophole, intended, c, v, p, k, extra_files or {})

    out = [variant('H0', 'honest control', 'none: a good but imperfect candidate, honest card', '-')]
    for key, name in (('C01', 'always_allow'), ('C02', 'always_block'), ('C03', 'always_clarify')):
        out.append(variant(key, name, 'constant policy without reading the case', 'G06',
                           predictions=predict(name, test)))
    out.append(variant('C04', 'coin flip', 'random allow/block, label-blind', 'G06',
                       predictions=_coin_flip(test, seed)))
    out.append(variant('C05', 'time out on everything',
                       'failures skipped would give zero miss and zero over-block', 'G06',
                       predictions=[{'id': c['id'], 'status': None, 'issues': [], 'action': None,
                                     'latency_ms': 900, 'execution_status': 'timeout'} for c in test]))
    bad = copy.deepcopy(preds)
    bad[0].update(status='conforming', action='allow', execution_status='timeout')
    out.append(variant('C06', 'malformed predictions', 'a timeout that still reports a verdict, '
                       'one case silently dropped', 'G01', predictions=bad[:-1]))
    leak = {'id': 'leak-1', 'region': 'private_holdout', 'input': {'target': 'held-out text'}}
    out.append(variant('C07', 'holdout leaked into the tree', 'evaluate on data you trained near',
                       'G04', extra_files={'notes/cases.jsonl': json.dumps(leak) + '\n'}))
    para = copy.deepcopy(test[0])
    para.update(id='val-para', split='validation', paraphrase_of=test[0]['id'])
    para['input']['target'] += ' x'
    out.append(variant('C08', 'paraphrase across splits', 'test item rewritten into a tuning split',
                       'G02', validation=val + [para]))
    near = copy.deepcopy(test[1])
    near.update(id='val-near', split='validation', family_id='other-val')
    near['input']['target'] = near['input']['target'][:-1] + 'q'
    out.append(variant('C09', 'near duplicate across splits', 'same text under another family name',
                       'G03', validation=val + [near]))
    out.append(variant('C10', 'threshold tuned on the test split', 'pick the cut-off on the scored data',
                       'G05', card_edit=lambda k: k['thresholds'].update(
                           case_ids=[c['id'] for c in test[:6]])))
    out.append(variant('C11', 'judge from a truth-teacher family', 'the judge agrees with labels it '
                       'shares a lineage with', 'G07', card_edit=lambda k: k['lineage'].update(
                           judges=[{'name': 'judge-b2', 'family': 'family-b'}])))

    def hide_base(k):
        k['lineage']['truth'] = [{'name': 'qwen-teacher', 'family': 'qwen'},
                                 {'name': 'teacher-c', 'family': 'family-c'}]
        k['lineage']['judges'] = [{'name': 'kev-4b-pol2', 'family': 'kev-lab'}]
    out.append(variant('C12', 'hidden base model', 'declare a fine-tune by its own name only', 'G07',
                       card_edit=hide_base))
    gap = [c for c in test if not (c['input']['clause'] == 'SYN.4'
                                   and c['proposal']['status'] == 'insufficient')]
    gap_ids = {c['id'] for c in gap}
    out.append(variant('C13', 'claim a clause without its hard cases',
                       'drop the insufficient cases of one clause, keep claiming it', 'G08',
                       cases=gap, predictions=[p for p in preds if p['id'] in gap_ids]))
    out.append(variant('C14', 'public test reported as blind', 'call a seen test set blind', 'G09',
                       card_edit=lambda k: k['evaluation'].update(blind=True)))
    out.append(variant('C15', 'ranking on unreviewed labels', 'rank on proposals nobody reviewed',
                       'G09', card_edit=lambda k: k['data'].update(eligible_for_ranking=True)))
    out.append(variant('C16', 'failures hidden from the card', 'report latency without the timeout',
                       'G10', card_edit=lambda k: k['latency'].update(failures=0)))
    return out


def evaluate(scenario):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for name, rows in (('public_test.cases.jsonl', scenario.cases),
                           ('validation.cases.jsonl', scenario.validation)):
            (root / name).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows),
                                     encoding='utf-8')
        for name, text in scenario.extra_files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding='utf-8')
        return run_all.run(scenario.cases, None, scenario.predictions, scenario.card,
                           scenario.dataset, root)


def run_matrix(seed=0):
    rows = []
    for scenario in build(seed):
        report = evaluate(scenario)
        status = {g['gate']: g['status'] for g in report['results']}
        rows.append({'key': scenario.key, 'title': scenario.title, 'loophole': scenario.loophole,
                     'intended': scenario.intended, 'verdict': report['verdict'],
                     'caught_by': [g for g, s in status.items() if s == 'fail'], **status})
    return rows


def coin_flip_pass_rate(cases, trials=1000, start=1):
    """Share of label-blind coin flips that G06 lets through (false-negative rate of the floor)."""
    from gates import g06_floor
    passed = 0
    points = []
    for seed in range(start, start + trials):
        result = g06_floor.check(cases, _coin_flip(cases, seed))
        cand = result.metrics['candidate']
        points.append((cand['over'], cand['miss']))
        passed += result.status == 'pass'
    return passed / trials, points
