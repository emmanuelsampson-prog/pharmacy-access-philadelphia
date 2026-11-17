# Figure style

All main and supplementary Python figures use the shared settings in
`src/figure_style.py`. Their physical width is 10.6 inches and their raster
resolution is 240 dpi. Keeping the export width constant prevents the website
and report from enlarging the type by different amounts. Exports retain their
canvas; tight cropping is deliberately avoided.

| Element | Setting |
|---|---|
| Typeface | DejaVu Sans |
| Figure and panel titles | 12 pt, regular weight, black |
| Axis label and tick | 10 pt, black |
| Legend | 9 pt |
| Subtitle | 9 pt |
| Source and explanatory note | 8 pt |
| Before / former pharmacy | Matplotlib blue, `#1f77b4` |
| After / designated recipient | Matplotlib orange, `#ff7f0e` |
| Longer / shorter access | Orange / blue, respectively |
| Other or unanalysed tracts | Gray, `#eeeeee` |

Colors must be read with the legend. A time-period category and the direction
of an access change are different encodings. Walking-time maps use Matplotlib's
sequential viridis scale; change maps use a diverging blue-to-orange scale
centered on unchanged access. The same walking-time intervals and colorbar are
used before and after. The excluded tract remains hatched. The supplementary
distance-increase map also uses viridis; household vehicle availability uses
the sequential Blues scale with its own units.

The paired scatterplots are descriptive before-and-after comparisons. Their
dashed diagonals represent equal values, not fitted regression lines. They use
ordinary blue circular markers. Chart axes, framed legends and regular-weight
titles follow the standard Matplotlib notebook appearance. There are no
decorative headings inside the figures.

The website displays the same exported Python timeline as the notebook and
reports. A collapsible selector below it provides the dated source records.
The selector and transfer explorer use DejaVu Sans, packaged from Matplotlib
with `python scripts/build_figure_fonts.py`. The font license is included beside
the web-font files. The website builder embeds those fonts.
Report body text and tables retain the academic Times New Roman style.
SVG downloads outline the glyphs and PDF downloads embed the font, preserving
the typography on computers without DejaVu Sans installed.

These presentation settings do not change the source records, coordinates,
projection, route calculations, model estimates or analytical tables.
