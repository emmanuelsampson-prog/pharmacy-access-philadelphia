# Figure style

All main and supplementary Python figures use the shared settings in
`src/figure_style.py`. Their physical width is 10.6 inches and their raster
resolution is 240 dpi. Keeping the export width constant prevents the website
and report from enlarging the type by different amounts. Exports retain their
canvas; tight cropping is deliberately avoided.

| Element | Setting |
|---|---|
| Typeface | DejaVu Sans |
| Figure title | 19 pt, bold, dark ink |
| Panel title | 13 pt, bold, dark ink |
| Axis label | 12 pt |
| Tick and legend | 11 pt |
| Source and explanatory note | 10 pt |
| Before / former pharmacy | Rust, `#b45130` |
| After / designated recipient | Teal, `#187b80` |
| Longer / shorter access | Rust / teal, respectively |
| Other or unanalysed tracts | Gray, `#e5e8e9` |

Colors must be read with the legend. A time-period category and the direction
of an access change are different encodings. Walking-time maps use a sequential
warm scale; change maps use a diverging teal-to-rust scale centered on unchanged
access. The same walking-time intervals are used before and after. Colors alone
do not replace labels: paired scatterplots also distinguish directions with
marker shapes, and the excluded tract remains hatched.
The supplementary distance-increase map uses the same warm color family;
household vehicle availability uses a sequential teal scale with its own units.

The paired scatterplots are descriptive before-and-after comparisons. Their
dashed diagonals represent equal values, not fitted regression lines.

The interactive timeline uses the same DejaVu Sans font, packaged from
Matplotlib with `python scripts/build_figure_fonts.py`. The font license is
included beside the web-font files. The website builder embeds those fonts so
the interactive chart does not depend on the reader having them installed.
Report body text and tables retain the academic Times New Roman style.
SVG downloads outline the glyphs and PDF downloads embed the font, preserving
the typography on computers without DejaVu Sans installed.

These presentation settings do not change the source records, coordinates,
projection, route calculations, model estimates or analytical tables.
