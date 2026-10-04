"""G07: the model that judges is not from the same family as the models that wrote or labelled the data.

The card lists three roles in lineage: generator (wrote the cases), truth (produced reference
labels) and judges (the candidate governance layer). Rules:

1. Every entry declares a family; a model fine-tuned from another declares base_family too.
2. A judge's family or base family must not appear among generator or truth families.
3. Truth teachers must not share a family with the generator (DATA-02 removes the generator's
   lineage from the truth pool).
4. When truth teachers exist there must be at least two distinct families (DATA-02 requires
   agreement of at least two lineages before a label is issued).

Names that reveal a known base model (for example Kev is built on Qwen) must declare it; hiding a
base model is how a same-family judge would slip through rule 2.
"""
from __future__ import annotations

import argparse
import json
import sys

from .card import require_sections, section
from .common import EXIT_FAIL, EXIT_INPUT_ERROR, EXIT_PASS, GateResult, InputError, load_json

GATE = 'G07'
TITLE = '血缘隔离'
SPEC_RULE = ('教师 A 生成，教师 B 不看 A 标签独立判断……不把同源教师一致当真值。'
             '（PoL-Governance SPEC，教师生成与质量检查第 3 条）')

# substring of a lower-cased model name -> family it reveals. Kev-4B is built on Qwen (models/CATALOG.md).
FAMILY_HINTS = {
    'gpt': 'openai', 'claude': 'anthropic', 'gemini': 'google', 'gemma': 'google',
    'qwen': 'qwen', 'kev': 'qwen', 'llama': 'meta-llama', 'deepseek': 'deepseek', 'grok': 'xai',
    'mimo': 'xiaomi', 'glm': 'zhipu', 'kimi': 'moonshot', 'mistral': 'mistral',
    'shieldstral': 'mistral', 'intern': 'internlm',
}


def _families(entry):
    fams = {entry.get('family'), entry.get('base_family')}
    return {f.lower() for f in fams if isinstance(f, str) and f}


def check(card):
    require_sections(card, 'lineage')
    lineage = section(card, 'lineage')
    findings = []
    roles = {}
    for role in ('generator', 'truth', 'judges'):
        entries = lineage.get(role)
        if not isinstance(entries, list):
            raise InputError(f'result card: lineage.{role} must be a list (empty if unused)')
        roles[role] = entries
        for entry in entries:
            name = str(entry.get('name', '')).lower()
            if not entry.get('family'):
                findings.append(f'{role}: {entry.get("name")!r} declares no family')
                continue
            declared = _families(entry)
            for hint, fam in FAMILY_HINTS.items():
                if hint in name and fam not in declared:
                    findings.append(f'{role}: {entry.get("name")!r} looks like {fam} but declares '
                                    f'{sorted(declared)}; add base_family')
    if not roles['judges']:
        findings.append('lineage.judges is empty: the candidate must declare its models')
    data_fams = set().union(*(_families(e) for e in roles['generator'] + roles['truth'])) \
        if roles['generator'] or roles['truth'] else set()
    gen_fams = set().union(*(_families(e) for e in roles['generator'])) if roles['generator'] else set()
    truth_fams = set().union(*(_families(e) for e in roles['truth'])) if roles['truth'] else set()
    for judge in roles['judges']:
        clash = _families(judge) & data_fams
        if clash:
            findings.append(f'judge {judge.get("name")!r} shares lineage {sorted(clash)} with the data')
    if truth_fams & gen_fams:
        findings.append(f'truth teachers share lineage {sorted(truth_fams & gen_fams)} with the generator')
    if roles['truth'] and len(truth_fams) < 2:
        findings.append('reference labels come from fewer than two families')
    metrics = {'generator_families': sorted(gen_fams), 'truth_families': sorted(truth_fams),
               'judge_families': sorted(set().union(*(_families(j) for j in roles['judges'])))
               if roles['judges'] else []}
    return GateResult(GATE, TITLE, SPEC_RULE, 'fail' if findings else 'pass', findings, metrics)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--card', required=True)
    args = parser.parse_args(argv)
    try:
        result = check(load_json(args.card))
    except (InputError, OSError) as error:
        print(f'{GATE} input error: {error}', file=sys.stderr)
        return EXIT_INPUT_ERROR
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return EXIT_PASS if result.status == 'pass' else EXIT_FAIL


if __name__ == '__main__':
    sys.exit(main())
