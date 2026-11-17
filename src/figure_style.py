"""Plain Matplotlib notebook styling shared by maps and statistical plots."""
from functools import wraps
from pathlib import Path
import matplotlib.pyplot as plt

WIDTH = 10.6
DPI = 240
FONT = 'DejaVu Sans'
TITLE = 12
PANEL = 12
LABEL = 10
TICK = 10
LEGEND = 9
NOTE = 8

INK = 'black'
MUTED = '#444444'
BLUE = '#1f77b4'
ORANGE = '#ff7f0e'
NEUTRAL = '#7f7f7f'
GRAY = '#eeeeee'
GRID = '#b0b0b0'
BOUNDARY = '#666666'
DISPUTED = '#d62728'
SAME_SITE = '#9467bd'
BEFORE, AFTER = BLUE, ORANGE
INCREASE, DECREASE = ORANGE, BLUE
WALK_COLORS = [plt.colormaps['viridis'](i / 5) for i in range(6)]
CHANGE_COLORS = ['#2171b5', '#9ecae1', '#f7f7f7', '#fee6ce', '#fdae6b', '#f16913', '#a63603']
CONTEXT_COLORS = [plt.colormaps['Blues'](.15 + .8 * i / 5) for i in range(6)]

RC = {
    'font.family': FONT, 'font.size': TICK, 'text.color': INK,
    'axes.titlesize': PANEL, 'axes.titleweight': 'normal', 'axes.titlecolor': INK,
    'axes.labelsize': LABEL, 'axes.labelcolor': INK, 'axes.edgecolor': INK,
    'axes.spines.top': True, 'axes.spines.right': True,
    'axes.axisbelow': True, 'axes.linewidth': .8,
    'xtick.labelsize': TICK, 'ytick.labelsize': TICK,
    'xtick.color': INK, 'ytick.color': INK,
    'legend.fontsize': LEGEND, 'legend.title_fontsize': LEGEND,
    'legend.frameon': True, 'grid.color': GRID, 'grid.linewidth': .6,
    'grid.alpha': .3, 'savefig.facecolor': 'white', 'figure.facecolor': 'white',
    'svg.fonttype': 'path', 'pdf.fonttype': 42,
}


def publication_style(function):
    """Apply the theme locally, including nested map and chart renderers."""
    @wraps(function)
    def styled(*args, **kwargs):
        with plt.style.context('default'), plt.rc_context(RC):
            return function(*args, **kwargs)
    return styled


def new_figure(height, title, subtitle=''):
    """A regular-weight Matplotlib title, with no branding or decorative heading."""
    fig = plt.figure(figsize=(WIDTH, height), facecolor='white')
    fig.suptitle(title, y=1 - .18 / height, fontsize=TITLE, fontweight='normal', color=INK)
    if subtitle:
        fig.text(.5, 1 - .50 / height, subtitle, color=MUTED, fontsize=NOTE + 1, ha='center')
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
