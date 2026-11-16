"""Render the public research report and conditional emissions calculator."""
from pathlib import Path
import base64
from html import escape
import json
from report_content import ROOT, OUT, TITLE, SUBTITLE, AUTHOR, DATE, REPO, get_sections, REFERENCES

s=json.loads((OUT/'before_after_summary.json').read_text())
from transfer_explorer import build_explorer
explorer_html, explorer_script = build_explorer()
def block(b):
    kind=b['type']
    if kind=='p': return '<p>'+escape(b['text'])+'</p>'
    if kind=='h3': return '<h3>'+escape(b['text'])+'</h3>'
    if kind=='list': return '<ol>'+''.join('<li>'+escape(x)+'</li>' for x in b['items'])+'</ol>'
    if kind=='table':
        return '<div class="table-scroll"><table><caption>'+escape(b['caption'])+'</caption><thead><tr>'+''.join('<th scope="col">'+escape(x)+'</th>' for x in b['headers'])+'</tr></thead><tbody>'+''.join('<tr>'+''.join(('<th scope="row">' if i==0 else '<td>')+escape(str(x))+('</th>' if i==0 else '</td>') for i,x in enumerate(row))+'</tr>' for row in b['rows'])+'</tbody></table></div>'
    if kind=='figure':
        data=base64.b64encode((OUT/b['file']).read_bytes()).decode()
        return '<figure class="wide"><a href="outputs/public/'+escape(b['file'])+'" title="Open full-size figure"><img src="data:image/png;base64,'+data+'" alt="'+escape(b['alt'])+'"></a><figcaption>'+escape(b['caption'])+'</figcaption></figure>'
    raise ValueError(kind)

sections=[]
for i,sec in enumerate(get_sections(),1):
    body=''.join(block(b) for b in sec['blocks'])
    if sec['id']=='travel': body+=(ROOT/'scripts/calculator.html').read_text().replace('DEFAULT_CO2', f"{s['conditional_kg_per_1000_at_half_car']:.2f}")
    if sec['id']=='results': body+=explorer_html
    sections.append(f'<section id="{sec["id"]}" class="section"><div class="report-section"><div class="section-label">{i:02d} / Research report</div><h2>{escape(sec["title"])}</h2>{body}</div></section>')
refs=''.join(f'<li>{escape(label)} <a href="{escape(url)}">Read source ↗</a></li>' for label,url in REFERENCES)
css=(ROOT/'scripts/site_style.css').read_text()
page=f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{TITLE} | Emmanuel Sampson</title><meta name="description" content="Research report on pharmacy access in Philadelphia, with findings, methodology, discussion, recommendations, limitations and a reproducible Jupyter notebook.">
<style>{css}</style></head><body>
<a class="skip" href="#main">Skip to research</a><header class="nav"><a class="brand" href="#">EMMANUEL SAMPSON / URBAN RESEARCH</a><nav aria-label="Sections"><a href="#period">Study period</a><a href="#evidence">Evidence</a><a href="#results">Access</a><a href="#equity">Equity</a><a href="#travel">Emissions</a><a href="#records">Downloads</a></nav></header>
<main id="main" class="wrap"><section class="hero"><div><div class="eyebrow">Philadelphia · Historical investigation 2023–2025</div><h1>{TITLE}</h1><p class="lede">{SUBTITLE}.</p><p class="byline">{AUTHOR}<br>University of Pennsylvania<br>{DATE}</p><div class="actions"><a class="button" href="outputs/public/Pharmacy_Access_Research_Report.docx">Download the Word report ↓</a><a class="button alt" href="#results">Read the results ↓</a></div></div><aside class="hero-side" aria-label="Main findings"><div><strong>41 locations</strong><p>Selected historical evidence across 2023–2025</p></div><div><strong>{s['weighted_walk_before_minutes']:.1f} → {s['weighted_walk_after_minutes']:.1f} min</strong><p>Modeled one-way walking time<br>Before and after designated 2025 transfers</p></div><p class="scope-note">{s['tracts']} tract origins · Fixed population weights<br>Calculated access, not observed travel behavior</p></aside></section>
<div class="story-guide" aria-label="Follow the findings"><a href="#evidence"><strong>1. Follow the closures</strong>See where events were documented and how the sources corroborate them.</a><a href="#results"><strong>2. Compare access</strong>Follow prescription destinations and examine walking and driving routes.</a><a href="#travel"><strong>3. Assess the implications</strong>Explore neighborhood differences, conditional emissions and the remaining evidence needs.</a></div>
{''.join(sections)}
<section id="references" class="section"><div class="report-section references"><h2>References</h2><p class="mini">Numbers in the text refer to these sources. Source details were checked on {DATE}.</p><ol>{refs}</ol><p>Additional data and software references appear in <a href="{REPO}/blob/main/docs/references.md">the repository source notes</a>.</p></div></section>
<section id="records" class="section"><div class="report-section"><h2>Research records and downloads</h2><p>The website and academic Word report present nine figures, including maps, location comparisons and emissions sensitivities. Start with notebook 04 for the executed historical evidence and before-and-after route analysis. The earlier inventory-removal exercise remains a separate supplement. The mobility notebook states which observed inputs are still needed for causal estimates.</p><div class="actions"><a class="button" href="outputs/public/Pharmacy_Access_Research_Report.docx">Word report ↓</a><a class="button alt" href="outputs/public/Pharmacy_Access_Project_Brief.pdf">PDF report ↗</a><a class="button alt" href="{REPO}">GitHub repository ↗</a></div><ul><li><a href="{REPO}/blob/main/notebooks/04_before_after_transfer_access.ipynb">Main executed Jupyter notebook: historical evidence and before/after access</a></li><li><a href="{REPO}/blob/main/notebooks/01_public_data_pilot.ipynb">Supplementary inventory-removal notebook</a></li><li><a href="{REPO}/blob/main/notebooks/02_mobility_event_study.ipynb">Mobility and event-study notebook</a></li><li><a href="{REPO}/blob/main/notebooks/03_closure_evidence_audit.ipynb">Court records and inventory audit notebook</a></li><li><a href="{REPO}/blob/main/docs/before_after_methods.md">Before-and-after methods and interpretation</a></li><li><a href="{REPO}/blob/main/data/processed/historical_evidence_2023_2025.csv">2023–2025 historical evidence ledger</a></li><li><a href="{REPO}/blob/main/data/processed/transfer_corroboration_2025.csv">Transfer corroboration and address review</a></li><li><a href="{REPO}/releases/latest">Download the reproducible project package</a></li><li><a href="{REPO}/blob/main/docs/research_protocol.md">Detailed protocol for the historical study</a></li><li><a href="{REPO}/blob/main/data/source_manifest.json">Data sources and file checksums</a></li><li><a href="{REPO}/blob/main/docs/data_dictionary.md">Data dictionary</a></li></ul><p class="mini">The release package contains cached public analytical inputs and historical street graphs. A Git clone can retrieve sources with the documented downloaders. Restricted mobility data are not included. Maps use Census boundaries and pharmacy coordinates; routes use © OpenStreetMap contributors, ODbL 1.0, via Geofabrik.</p></div></section>
</main><footer class="footer"><div class="footer-inner"><strong>{AUTHOR} · University of Pennsylvania</strong><p><a href="{REPO}">Research code and reproducibility record</a></p></div></footer>
<script>
(()=>{{const fields=['car','additional','trips'].map(id=>document.getElementById(id));const update=()=>{{const [car,additional,trips]=fields.map(e=>Number(e.value));const output=document.getElementById('co2');if(!Number.isFinite(trips)||trips<0||trips>1000000||fields[2].value===''){{output.textContent='Enter 0–1,000,000 trips';return;}}const kg=trips*{s['weighted_drive_delta_roundtrip_km']}*car*additional*400/1.609344/1000;output.textContent=kg.toLocaleString(undefined,{{minimumFractionDigits:2,maximumFractionDigits:2}})+' kg CO₂';}};fields.forEach(e=>e.addEventListener('input',update));update();}})();
{explorer_script}
</script></body></html>'''
(ROOT/'index.html').write_text(page)
print('Built index.html from the shared research narrative')
