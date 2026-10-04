"""The machine-readable result card that G05, G07, G09 and G10 read.

A human-readable card still follows the PoL-Governance results template; this JSON sits next to it so
the gates can check the claims the prose makes. See docs/result-card.md for every field.
"""
from __future__ import annotations

from .common import InputError

SECTIONS = ('candidate', 'data', 'evaluation', 'thresholds', 'lineage', 'clauses', 'latency',
            'honesty')
HONESTY_FLAGS = ('reference_not_gold_unless_reviewed', 'no_generalisation_to_real_people',
                 'negative_results_reported')


def require_sections(card, *names):
    """Raise InputError if any of the named sections is missing."""
    missing = [n for n in names if n not in card]
    if missing:
        raise InputError(f'result card is missing sections: {missing}')


def section(card, name, kind=dict):
    value = card.get(name)
    if not isinstance(value, kind):
        raise InputError(f'result card: {name} must be a {kind.__name__}')
    return value
