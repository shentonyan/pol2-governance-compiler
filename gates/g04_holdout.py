"""G04: nothing from the private holdout is inside the repository tree.

A registry entry that records only version and size of the holdout is allowed (AGENTS lets the
repository register those). What fails is a row that carries case content, a data file named like
a holdout split, a CSV/TSV row with a private_holdout cell, or a binary data file that cannot be
inspected. A path can be exempted with --allow after a human has looked at it.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from .common import EXIT_FAIL, EXIT_INPUT_ERROR, EXIT_PASS, GateResult, InputError, parse_json

GATE = 'G04'
TITLE = '保留集零接触'
SPEC_RULE = ('私有保留集不进入任何公开分支、fork、PR、日志、截图或训练 Agent 上下文。'
             '（PoL-Governance AGENTS，数据边界）')
MARK = 'private_holdout'
SPLIT_KEYS = ('split', 'region')
CONTENT_KEYS = {'input', 'context', 'target', 'proposal', 'label', 'labels', 'status',
                'acceptable_actions', 'answers', 'prompt', 'messages'}
TEXT_DATA = {'.jsonl', '.json', '.csv', '.tsv'}
BINARY_DATA = {'.parquet', '.arrow', '.feather', '.pkl', '.npz'}
SKIP_DIRS = {'.git', '__pycache__', '.venv', 'venv', 'node_modules', '.pytest_cache'}
CELL = re.compile(r'(^|[,\t])\s*"?private_holdout"?\s*($|[,\t])')


def _content_rows(value):
    """Yield objects marked as holdout that also carry case content."""
    if isinstance(value, dict):
        if any(value.get(k) == MARK for k in SPLIT_KEYS) and CONTENT_KEYS & set(value):
            yield value
        for child in value.values():
            yield from _content_rows(child)
    elif isinstance(value, list):
        for child in value:
            yield from _content_rows(child)


def _scan_file(path, rel):
    suffix = path.suffix.lower()
    if suffix in BINARY_DATA:
        return [f'{rel}: binary data file cannot be inspected; keep it outside the repository '
                f'and register it by hash']
    if 'holdout' in path.name.lower():
        return [f'{rel}: data file named like a holdout split']
    try:
        text = path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        return [f'{rel}: data file is not valid UTF-8']
    if suffix == '.json':
        try:
            if any(_content_rows(parse_json(text, rel))):
                return [f'{rel}: holdout-marked object with case content']
        except InputError:
            return [f'{rel}: JSON data cannot be parsed']
    elif suffix == '.jsonl':
        for number, line in enumerate(text.split('\n'), 1):
            if not line.strip():
                continue
            location = f'{rel}:{number}'
            try:
                row = parse_json(line, location)
            except InputError:
                return [f'{location}: JSONL data cannot be parsed']
            if not isinstance(row, dict):
                return [f'{location}: JSONL row must be an object']
            if any(_content_rows(row)):
                return [f'{location}: holdout row with case content']
    else:  # csv / tsv: cannot tell a registry row from content, so a human must allow it
        for number, line in enumerate(text.splitlines(), 1):
            if CELL.search(line):
                return [f'{rel}:{number}: row with a private_holdout cell']
    return []


def check(root, allow=()):
    root = Path(root).resolve()
    if not root.is_dir():
        raise InputError('G04 scan root must be an existing directory')
    allow = {a.replace('\\', '/') for a in allow}
    findings, scanned = [], 0
    for path in sorted(root.rglob('*')):
        rel = path.relative_to(root).as_posix()
        if set(Path(rel).parts) & SKIP_DIRS or rel in allow:
            continue
        if path.suffix.lower() not in TEXT_DATA | BINARY_DATA:
            continue
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            findings.append(f'{rel}: linked data path cannot be inspected inside the repository')
            continue
        if not path.is_file():
            continue
        scanned += 1
        findings.extend(_scan_file(path, rel))
    metrics = {'data_files_scanned': scanned, 'allowed_paths': sorted(allow)}
    return GateResult(GATE, TITLE, SPEC_RULE, 'fail' if findings else 'pass', findings, metrics)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', nargs='?', default='.', help='directory to scan (default: .)')
    parser.add_argument('--allow', action='append', default=[],
                        help='relative path a human has reviewed and exempted; repeatable')
    args = parser.parse_args(argv)
    try:
        result = check(args.root, args.allow)
    except (InputError, OSError) as error:
        print(f'{GATE} input error: {error}', file=sys.stderr)
        return EXIT_INPUT_ERROR
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return EXIT_PASS if result.status == 'pass' else EXIT_FAIL


if __name__ == '__main__':
    sys.exit(main())
