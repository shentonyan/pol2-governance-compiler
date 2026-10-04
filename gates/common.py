"""Shared helpers for gates: strict JSONL loading and one result shape for every gate."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

EXIT_PASS, EXIT_FAIL, EXIT_INPUT_ERROR = 0, 1, 2


class InputError(ValueError):
    """The input is malformed, so the gate cannot give a verdict at all."""


def _unique_keys(pairs):
    keys = [k for k, _ in pairs]
    if len(keys) != len(set(keys)):
        raise InputError(f'duplicate keys in object: {keys}')
    return dict(pairs)


def _reject_constant(value):
    raise InputError(f'non-finite number not allowed: {value}')


def parse_json(text, where):
    try:
        return json.loads(text, object_pairs_hook=_unique_keys, parse_constant=_reject_constant)
    except json.JSONDecodeError as error:
        raise InputError(f'{where}: {error}') from None


def load_jsonl(path):
    """Read a JSONL file; every non-blank line must be one JSON object."""
    path = Path(path)
    rows = []
    with path.open(encoding='utf-8') as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = parse_json(line, f'{path.name}:{number}')
            if not isinstance(row, dict):
                raise InputError(f'{path.name}:{number}: expected a JSON object')
            rows.append(row)
    return rows


def index_by_id(rows, what):
    """Map id -> row, refusing rows without an id and duplicate ids."""
    out = {}
    for row in rows:
        key = row.get('id')
        if not isinstance(key, str) or not key:
            raise InputError(f'{what}: row without a string id')
        if key in out:
            raise InputError(f'{what}: duplicate id {key}')
        out[key] = row
    return out


@dataclass
class GateResult:
    """What every gate returns. ``status`` is one of pass, fail, not_applicable, not_implemented."""

    gate: str
    title: str
    spec_rule: str
    status: str
    findings: list = field(default_factory=list)
    metrics: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


def load_json(path):
    """Read one JSON document (e.g. a result card) with the same strictness as load_jsonl."""
    path = Path(path)
    value = parse_json(path.read_text(encoding='utf-8'), path.name)
    if not isinstance(value, dict):
        raise InputError(f'{path.name}: expected a JSON object')
    return value


def split_of(row):
    """Split name of a case: ``split`` in the pilot, ``region`` in the DATA-02 contract."""
    for key in ('split', 'region'):
        value = row.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def reference_of(case, labels_by_id=None):
    """Reference label of a case: a labels file wins over a proposal embedded in the case."""
    if labels_by_id is not None:
        return labels_by_id.get(case.get('id'))
    return case.get('proposal')
