"""Small shared map furniture for local, meter-based projected maps."""


def map_furniture(ax, bounds, scale_m=5000):
    xmin, ymin, xmax, ymax = bounds
    x = xmin + (xmax - xmin) * .06
    y = ymin + (ymax - ymin) * .015
    ax.plot([x, x + scale_m], [y, y], color='#344b55', linewidth=2)
    ax.text(x + scale_m / 2, y + 500, f'{scale_m / 1000:g} km',
            ha='center', fontsize=8, color='#344b55')
    ax.annotate('N', xy=(.92, .93), xytext=(.92, .84), xycoords='axes fraction',
                textcoords='axes fraction', ha='center', fontsize=9,
                arrowprops={'arrowstyle': '-|>', 'color': '#344b55'}, color='#344b55')

