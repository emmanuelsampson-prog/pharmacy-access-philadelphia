"""Shared typography, export dimensions and semantic colors for research figures."""
from functools import wraps
from pathlib import Path
import matplotlib.pyplot as plt

WIDTH = 10.6
DPI = 240
FONT = 'DejaVu Sans'
TITLE = 19
PANEL = 13
LABEL = 12
TICK = 11
LEGEND = 11
NOTE = 10

INK = '#17313c'
MUTED = '#516772'
TEAL = '#187b80'
TEAL_LIGHT = '#8cc6c3'
RUST = '#b45130'
NEUTRAL = '#cbbd9f'
GRAY = '#e5e8e9'
GRID = '#e1e7e7'
BOUNDARY = '#75878b'
DISPUTED = '#ad3434'
SAME_SITE = '#6f5483'
BEFORE, AFTER = RUST, TEAL
INCREASE, DECREASE = RUST, TEAL
WALK_COLORS = ['#fff2d9', '#f9d4bc', '#ec9a6f', '#ce7049', RUST, '#7a2e25']
CHANGE_COLORS = ['#0f5b60', TEAL_LIGHT, '#fff7df', '#f9d4bc', '#ec9a6f', RUST, '#7a2e25']
TEAL_COLORS = ['#eef7f5', '#c6e2dd', TEAL_LIGHT, '#4f9fa0', TEAL, '#0f5b60']

RC = {
    'font.family': FONT, 'font.size': TICK, 'text.color': INK,
    'axes.titlesize': PANEL, 'axes.titleweight': 'bold', 'axes.titlecolor': INK,
    'axes.labelsize': LABEL, 'axes.labelcolor': MUTED, 'axes.edgecolor': MUTED,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.axisbelow': True, 'axes.linewidth': .7,
    'xtick.labelsize': TICK, 'ytick.labelsize': TICK,
    'xtick.color': MUTED, 'ytick.color': MUTED,
    'legend.fontsize': LEGEND, 'legend.title_fontsize': LEGEND,
    'legend.frameon': False, 'grid.color': GRID, 'grid.linewidth': .7,
    'grid.alpha': 1, 'savefig.facecolor': 'white', 'figure.facecolor': 'white',
    'svg.fonttype': 'path', 'pdf.fonttype': 42,
}


def publication_style(function):
    """Apply the theme locally, including nested map and chart renderers."""
    @wraps(function)
    def styled(*args, **kwargs):
        with plt.rc_context(RC):
            return function(*args, **kwargs)
    return styled


def new_figure(height, title, subtitle='', kicker='PHILADELPHIA / PHARMACY ACCESS / 2023–2025'):
    """Keep physical width and header text sizes identical across figure types."""
    fig = plt.figure(figsize=(WIDTH, height), facecolor='white')
    fig.text(.055, 1 - .23 / height, kicker, color=TEAL, fontsize=NOTE - 1, weight='bold')
    fig.text(.055, 1 - .57 / height, title, color=INK, fontsize=TITLE, weight='bold')
    if subtitle:
        fig.text(.055, 1 - .87 / height, subtitle, color=MUTED, fontsize=TICK)
    return fig


def footer(fig, text, *, second_line=None):
    height = fig.get_figheight()
    y = (.46 if second_line else .22) / height
    fig.text(.055, y, text, fontsize=NOTE, color=MUTED)
    if second_line:
        fig.text(.055, .22 / height, second_line, fontsize=NOTE, color=MUTED)


def save_figure(fig, path, *, vector=False):
    """No tight cropping: equal display widths must produce equal text scales."""
    path = Path(path)
    fig.savefig(path, dpi=DPI, facecolor='white')
    if vector:
        fig.savefig(path.with_suffix('.svg'), metadata={'Date': None})
        fig.savefig(path.with_suffix('.pdf'), metadata={'CreationDate': None, 'ModDate': None})
    plt.close(fig)
