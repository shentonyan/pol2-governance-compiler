"""House style for figures, following the rules of the GOV-01 lab (docs/figure-style.md there).

Restated here in our own code: semantic palette (blue = the proposal, red = baselines and failures,
green = positive, grey = reference, gold = one highlight at most), no top/right spines, no grid,
frameless legends, PNG at 300 dpi plus vector PDF with embedded TrueType fonts.
Only tools/make_figures.py imports this; the gates never need matplotlib.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

PALETTE = {
    'blue_main': '#0F4D92', 'blue_secondary': '#3775BA',
    'green_1': '#DDF3DE', 'green_2': '#AADCA9', 'green_3': '#8BCF8B',
    'red_1': '#F6CFCB', 'red_2': '#E9A6A1', 'red_strong': '#B64342',
    'neutral': '#CFCECE', 'neutral_dark': '#767676', 'ink_soft': '#4D4D4D', 'ink': '#272727',
    'highlight': '#FFD700', 'white': '#FFFFFF',
}
FONTS = ['Helvetica', 'Arial', 'Liberation Sans', 'DejaVu Sans', 'Noto Sans CJK SC',
         'Noto Sans CJK TC', 'Microsoft YaHei']
UP, DOWN = ' ↑', ' ↓'
REF_LINE = {'color': 'black', 'alpha': 0.3, 'lw': 3, 'ls': '--'}


def apply_style(size=14):
    plt.rcParams.update({
        'font.family': 'sans-serif', 'font.sans-serif': FONTS, 'font.size': size,
        'axes.spines.top': False, 'axes.spines.right': False, 'axes.linewidth': 2,
        'axes.grid': False, 'axes.labelcolor': PALETTE['ink'], 'text.color': PALETTE['ink'],
        'xtick.major.width': 2, 'ytick.major.width': 2, 'legend.frameon': False,
        'pdf.fonttype': 42, 'ps.fonttype': 42, 'svg.fonttype': 'none',
    })


def new_figure(width, height, size=14):
    apply_style(size)
    return plt.subplots(figsize=(width, height))


def finalize_figure(fig, stem):
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    for fmt in ('png', 'pdf'):
        fig.savefig(stem.with_suffix(f'.{fmt}'), dpi=300, bbox_inches='tight',
                    metadata={'CreationDate': None} if fmt == 'pdf' else {'Software': None})
    plt.close(fig)
    return stem.with_suffix('.png')
