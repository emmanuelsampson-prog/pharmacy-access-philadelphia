"""Small shared map furniture for local, meter-based projected maps."""
from src.figure_style import MUTED, NOTE, TICK


def tract_background(ax, tracts, facecolor='#f1f3f3', edgecolor='#d2d9da', linewidth=.3):
    """Show tract geography for context without assigning unsampled values."""
    tracts.plot(ax=ax, facecolor=facecolor, edgecolor=edgecolor, linewidth=linewidth, zorder=0)
    xmin, ymin, xmax, ymax = tracts.total_bounds
    padding = max(xmax - xmin, ymax - ymin) * .04
    ax.set_xlim(xmin - padding, xmax + padding)
    ax.set_ylim(ymin - padding, ymax + padding)
    ax.set_aspect('equal')


def map_furniture(ax, bounds, scale_m=5000):
    xmin, ymin, xmax, ymax = bounds
    x = xmin + (xmax - xmin) * .06
    y = ymin + (ymax - ymin) * .015
    ax.plot([x, x + scale_m], [y, y], color=MUTED, linewidth=2)
    ax.text(x + scale_m / 2, y + 500, f'{scale_m / 1000:g} km',
            ha='center', fontsize=NOTE, color=MUTED)
    ax.annotate('N', xy=(.92, .93), xytext=(.92, .84), xycoords='axes fraction',
                textcoords='axes fraction', ha='center', fontsize=TICK,
                arrowprops={'arrowstyle': '-|>', 'color': MUTED}, color=MUTED)

