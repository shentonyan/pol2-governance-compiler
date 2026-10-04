"""Draw every figure in docs/figures from the repository's own data and gate runs.

    python -m redteam            # writes results/tables first
    python -m tools.make_figures

Needs matplotlib; nothing else in the repository does.
"""
from __future__ import annotations

import csv
import json
from collections import OrderedDict
from pathlib import Path

from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch, Polygon

from baselines.constant import POLICIES, predict
from gates import g06_floor
from gates.common import load_jsonl
from redteam import fixture

from .plotstyle import DOWN, PALETTE, REF_LINE, finalize_figure, new_figure

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / 'docs' / 'figures'
TABLES = ROOT / 'results' / 'tables'
GATES = [f'G{i:02d}' for i in range(1, 11)]
P = PALETTE


# ---------------------------------------------------------------------------------------------
# 1. Architecture
# ---------------------------------------------------------------------------------------------
def _box(ax, x, y, w, h, title, body='', main=False, fill=None):
    face = fill or (P['green_1'] if main else P['white'])
    edge = P['blue_main'] if main else P['ink_soft']
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.02,rounding_size=0.06',
                                fc=face, ec=edge, lw=2.5 if main else 1.5))
    ax.text(x + w / 2, y + h * (0.62 if body else 0.5), title, ha='center', va='center',
            fontsize=12, fontweight='bold')
    if body:
        ax.text(x + w / 2, y + h * 0.28, body, ha='center', va='center', fontsize=9.5,
                color=P['ink_soft'])


def _arrow(ax, a, b, text='', curve=0.0, color=None, offset=(0, 0)):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle='-|>', mutation_scale=14, lw=1.6,
                                 color=color or P['ink_soft'],
                                 connectionstyle=f'arc3,rad={curve}'))
    if text:
        mx, my = (a[0] + b[0]) / 2 + offset[0], (a[1] + b[1]) / 2 + offset[1]
        ax.text(mx, my, text, ha='center', va='center', fontsize=9, color=color or P['ink_soft'],
                bbox={'fc': 'white', 'ec': 'none', 'pad': 1})


def fig_architecture():
    fig, ax = new_figure(11, 6.4)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 6.4)
    ax.axis('off')
    _box(ax, 3.3, 5.55, 4.4, 0.65, 'Host requirement',
         'surfaces · clause subset · p95 budget · judges available')
    ax.add_patch(FancyBboxPatch((0.2, 3.75), 10.6, 1.45, boxstyle='round,pad=0.02,rounding_size=0.08',
                                fc=P['green_1'], ec='none', alpha=0.45))
    ax.text(0.35, 5.0, 'Knowledge (reusable, grows)', fontsize=11, fontweight='bold',
            color=P['ink_soft'])
    _box(ax, 0.5, 3.9, 3.1, 0.9, 'contracts/', 'clause crosswalk · criteria · non-triggers')
    _box(ax, 3.95, 3.9, 3.1, 0.9, 'DATA-02 ontology', '34 clauses · splits 70/20/5/5')
    _box(ax, 7.4, 3.9, 3.1, 0.9, 'rulings/', 'ambiguity → team ruling → contract')
    ax.add_patch(FancyBboxPatch((0.2, 1.3), 10.6, 2.1, boxstyle='round,pad=0.02,rounding_size=0.08',
                                fc='none', ec=P['neutral_dark'], lw=1.2, ls='--'))
    ax.text(10.65, 3.15, 'Compile loop (three isolated roles + gates)', fontsize=11, fontweight='bold',
            color=P['ink_soft'], ha='right')
    xs = [0.5, 3.0, 5.5, 8.0]
    labels = [('Compiler', 'config · thresholds · adapter'),
              ('Clause reviewer', 'checks contract coverage'),
              ('Blind evaluator', 'sees unlabeled inputs only'),
              ('Gates G01–G10', 'immutable scripts')]
    for i, (x, (t, b)) in enumerate(zip(xs, labels)):
        _box(ax, x, 1.85, 2.3, 0.95, t, b, main=(i == 3), fill=P['red_1'] if i == 3 else None)
    for a, b in zip(xs[:-1], xs[1:]):
        _arrow(ax, (a + 2.3, 2.32), (b, 2.32))
    ax.plot([9.15, 9.15, 1.65], [1.85, 1.55, 1.55], color=P['red_strong'], lw=1.6)
    _arrow(ax, (1.65, 1.55), (1.65, 1.85), color=P['red_strong'])
    ax.text(5.4, 1.55, 'any gate fails → back to the compiler', ha='center', va='center',
            fontsize=9.5, color=P['red_strong'], bbox={'fc': 'white', 'ec': 'none', 'pad': 1.5})
    _arrow(ax, (4.6, 2.8), (8.4, 3.9), 'clause ambiguity → queue', offset=(-0.2, 0.12))
    _arrow(ax, (5.5, 5.55), (5.5, 4.8))
    _arrow(ax, (2.05, 3.9), (1.65, 2.8))
    _box(ax, 0.5, 0.1, 3.4, 0.85, 'Governance layer', 'deployable · judged by gates', main=True)
    _box(ax, 4.3, 0.1, 2.9, 0.85, 'Result card', 'card.json + prose card')
    _box(ax, 7.6, 0.1, 2.9, 0.85, 'Degenerate floor', '3 constant policies + more', fill=P['red_1'])
    _arrow(ax, (2.2, 1.3), (2.2, 0.95))
    _arrow(ax, (5.75, 1.3), (5.75, 0.95))
    _arrow(ax, (9.6, 0.95), (9.6, 1.85), 'G06', offset=(0.3, -0.25))
    return finalize_figure(fig, FIG / 'fig1_architecture')


# ---------------------------------------------------------------------------------------------
# 2. The G06 floor
# ---------------------------------------------------------------------------------------------
def fig_floor():
    coin = json.loads((TABLES / 'coin_flip.json').read_text(encoding='utf-8'))
    test, _ = fixture.build(0)
    honest = g06_floor.check(test, fixture.honest_predictions(test)).metrics['candidate']
    base = {n: g06_floor.check(test, predict(n, test)).metrics['candidate'] for n in POLICIES}
    fig, ax = new_figure(7.2, 6.2)
    ax.add_patch(Polygon([(0, 1), (1, 0), (1.05, 0), (1.05, 1.05), (0, 1.05)], closed=True,
                         fc=P['red_1'], ec='none', alpha=0.7, zorder=0))
    ax.plot([0, 1], [1, 0], **REF_LINE, zorder=1)
    pts = coin['fixture']['points_over_miss']
    ax.scatter([p[0] for p in pts], [p[1] for p in pts], s=10, color=P['neutral_dark'], alpha=0.25,
               lw=0, zorder=2, label='coin flip, 1000 seeds')
    for name, r in base.items():
        ax.scatter(r['over'], r['miss'], s=170, marker='s', color=P['red_strong'], ec='black', lw=1.2,
                   zorder=4)
    ax.annotate('always_allow', (base['always_allow']['over'], base['always_allow']['miss']),
                xytext=(0.07, 0.93), fontsize=11, color=P['red_strong'])
    ax.annotate('always_block = always_clarify',
                (base['always_block']['over'], base['always_block']['miss']),
                xytext=(0.48, 0.07), fontsize=11, color=P['red_strong'])
    ax.scatter(honest['over'], honest['miss'], s=320, marker='*', color=P['blue_main'], ec='black',
               lw=1, zorder=5, label='honest fixture candidate')
    ax.annotate(f"J = {honest['j']:.2f}\nlower 95% = {honest['j_lower_95']:.2f}",
                (honest['over'], honest['miss']), xytext=(0.12, 0.2), fontsize=11,
                color=P['blue_main'], arrowprops={'arrowstyle': '-', 'color': P['blue_main']})
    ax.text(0.62, 0.72, 'not above floor\n(J ≤ 0)', fontsize=12, color=P['red_strong'], ha='center')
    ax.text(0.2, 0.83, 'J = 0', rotation=-45, fontsize=11, color=P['ink_soft'], ha='center')
    ax.set_xlim(-0.03, 1.05)
    ax.set_ylim(-0.03, 1.05)
    ax.set_xlabel('over-block rate on normal cases' + DOWN)
    ax.set_ylabel('miss rate on violating cases' + DOWN)
    ax.legend(loc='upper right', fontsize=10, handletextpad=0.3,
              handles=[Patch(fc=P['red_1'], label='dominated by a mixture of trivial policies'),
                       *ax.get_legend_handles_labels()[0]])
    return finalize_figure(fig, FIG / 'fig2_floor')


# ---------------------------------------------------------------------------------------------
# 3. Red-team matrix
# ---------------------------------------------------------------------------------------------
def fig_redteam():
    with (TABLES / 'redteam_matrix.csv').open(encoding='utf-8') as handle:
        rows = list(csv.DictReader(handle))
    fig, ax = new_figure(10.5, 0.42 * len(rows) + 1.4, size=12)
    color = {'pass': P['green_2'], 'fail': P['red_strong'], 'not_applicable': P['neutral']}
    for i, row in enumerate(rows):
        y = len(rows) - 1 - i
        for j, gate in enumerate(GATES):
            status = row[gate]
            ax.add_patch(FancyBboxPatch((j + 0.06, y + 0.08), 0.88, 0.84,
                                        boxstyle='round,pad=0,rounding_size=0.08',
                                        fc=color[status], ec='white', lw=1.5))
            if status == 'fail':
                ax.text(j + 0.5, y + 0.5, '×', ha='center', va='center', color='white',
                        fontsize=12, fontweight='bold')
            if gate == row['intended']:
                ax.add_patch(FancyBboxPatch((j + 0.02, y + 0.04), 0.96, 0.92,
                                            boxstyle='round,pad=0,rounding_size=0.1',
                                            fc='none', ec='black', lw=2.2))
    ax.set_xlim(0, len(GATES))
    ax.set_ylim(0, len(rows))
    ax.set_xticks([j + 0.5 for j in range(len(GATES))], GATES)
    ax.xaxis.tick_top()
    ax.set_yticks([len(rows) - 1 - i + 0.5 for i in range(len(rows))],
                  [f"{r['key']}  {r['title']}" for r in rows])
    for side in ('left', 'bottom', 'top'):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0)
    ax.legend(handles=[Patch(fc=P['green_2'], label='gate passes'),
                       Patch(fc=P['red_strong'], label='gate fails (cheat caught)'),
                       Patch(fc=P['neutral'], label='not applicable'),
                       Patch(fc='none', ec='black', lw=2, label='gate meant to catch it')],
              loc='upper center', bbox_to_anchor=(0.45, -0.01), ncol=4, fontsize=10)
    return finalize_figure(fig, FIG / 'fig3_redteam')


# ---------------------------------------------------------------------------------------------
# 4. Clause crosswalk coverage
# ---------------------------------------------------------------------------------------------
def fig_crosswalk():
    with (ROOT / 'contracts' / 'crosswalk.csv').open(encoding='utf-8') as handle:
        rows = list(csv.DictReader(handle))

    def group(row):
        cid = row['clause_id']
        if not cid:
            return 'Ch.7 public welfare'
        return OrderedDict([('PoL.1', 'Ch.1 love2 / hate2'), ('PoL.2', 'Ch.2 love languages'),
                            ('EAP', 'Ch.4 EAP'), ('PoL.5', 'Ch.5 governance layer'),
                            ('ENG', 'Engineering strategy')])[next(k for k in
                            ('PoL.1', 'PoL.2', 'EAP', 'PoL.5', 'ENG') if cid.startswith(k))]

    order = ['Ch.1 love2 / hate2', 'Ch.2 love languages', 'Ch.4 EAP', 'Ch.5 governance layer',
             'Engineering strategy', 'Ch.7 public welfare']
    sources = [('in_ontology', 'DATA-02 ontology'), ('gov01', 'GOV-01 lab'),
               ('lit01_axes', 'LIT-01 survey')]
    counts = {g: [0, 0, 0] for g in order}
    totals = {g: 0 for g in order}
    for row in rows:
        g = group(row)
        totals[g] += 1
        for k, (col, _) in enumerate(sources):
            hit = row[col] == 'yes' if col == 'in_ontology' else bool(row[col].strip())
            counts[g][k] += hit
    fig, ax = new_figure(8.4, 4.6, size=12)
    for i, g in enumerate(order):
        y = len(order) - 1 - i
        for k in range(3):
            share = counts[g][k] / totals[g]
            face = P['blue_main'] if share == 1 else (P['blue_secondary'] if share > 0 else P['white'])
            ax.add_patch(FancyBboxPatch((k + 0.06, y + 0.08), 0.88, 0.84,
                                        boxstyle='round,pad=0,rounding_size=0.08', fc=face,
                                        ec=P['neutral_dark'] if share == 0 else 'white',
                                        alpha=1 if share else 1, lw=1.2))
            ax.text(k + 0.5, y + 0.5, f'{counts[g][k]}/{totals[g]}', ha='center', va='center',
                    color='white' if share else P['ink_soft'], fontsize=12, fontweight='bold')
    ax.set_xlim(0, 3)
    ax.set_ylim(0, len(order))
    ax.set_xticks([k + 0.5 for k in range(3)], [s for _, s in sources])
    ax.xaxis.tick_top()
    ax.set_yticks([len(order) - 1 - i + 0.5 for i in range(len(order))], order)
    for side in ('left', 'bottom', 'top'):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0)
    return finalize_figure(fig, FIG / 'fig4_crosswalk')


# ---------------------------------------------------------------------------------------------
# 5. Roadmap
# ---------------------------------------------------------------------------------------------
def fig_roadmap():
    phases = [('Phase 0', 'Gates + floor', 'G01–G10, 3 constant\npolicies, red-team matrix', 'done'),
              ('Phase 1', 'Contracts + rulings', 'crosswalk done;\ncontract files, first rulings', 'part'),
              ('Phase 2', 'First compile (MVP)', 'one host, keyword +\none local judge', 'todo'),
              ('Phase 3', 'Adapt + shadow run', 'needs DATA-02 truth\nand APP-01 host', 'todo')]
    gates = ['all gates pass on\nhonest control', 'team rulings on\nOPEN.md', 'result card passes\nG01–G10',
             'holdout scored\noutside the repo']
    fig, ax = new_figure(11, 3.4, size=12)
    face = {'done': P['blue_main'], 'part': P['blue_secondary'], 'todo': P['white']}
    ink = {'done': 'white', 'part': 'white', 'todo': P['ink']}
    ax.plot([0, 10.95], [0.6, 0.6], color=P['ink_soft'], lw=2, zorder=0)
    for i, (name, title, body, state) in enumerate(phases):
        x = i * 2.75
        ax.plot([x + 1.225, x + 1.225], [1.15, 0.6], color=P['neutral_dark'], lw=1.2, zorder=0)
        ax.add_patch(FancyBboxPatch((x, 1.15), 2.45, 1.7, boxstyle='round,pad=0.02,rounding_size=0.1',
                                    fc=face[state], ec=P['blue_main'], lw=2))
        ax.text(x + 1.225, 2.55, name, ha='center', fontsize=11, color=ink[state])
        ax.text(x + 1.225, 2.2, title, ha='center', fontsize=12.5, fontweight='bold', color=ink[state])
        ax.text(x + 1.225, 1.55, body, ha='center', va='center', fontsize=10, color=ink[state])
        ax.add_patch(Polygon([(x + 2.6, 0.75), (x + 2.75, 0.6), (x + 2.6, 0.45), (x + 2.45, 0.6)],
                             closed=True, fc=P['ink_soft']))
        ax.text(x + 2.6, 0.22, gates[i], ha='center', va='top', fontsize=9, color=P['ink_soft'])
    ax.set_xlim(-0.1, 11.1)
    ax.set_ylim(-0.6, 3.0)
    ax.axis('off')
    ax.legend(handles=[Patch(fc=P['blue_main'], label='done'), Patch(fc=P['blue_secondary'], label='in progress'),
                       Patch(fc='white', ec=P['blue_main'], label='not started')],
              loc='upper right', bbox_to_anchor=(1.0, 1.12), ncol=3, fontsize=10)
    return finalize_figure(fig, FIG / 'fig5_roadmap')


def main():
    for draw in (fig_architecture, fig_floor, fig_redteam, fig_crosswalk, fig_roadmap):
        print(draw())


if __name__ == '__main__':
    main()
