"""Render the public research report and conditional emissions calculator."""
from pathlib import Path
import base64
from html import escape
import json
from report_content import ROOT, OUT, TITLE, SUBTITLE, AUTHOR, DATE, REPO, get_sections, REFERENCES

s=json.loads((OUT/'summary.json').read_text())
def block(b):
    kind=b['type']
    if kind=='p': return '<p>'+escape(b['text'])+'</p>'
    if kind=='h3': return '<h3>'+escape(b['text'])+'</h3>'
    if kind=='list': return '<ol>'+''.join('<li>'+escape(x)+'</li>' for x in b['items'])+'</ol>'
    if kind=='table':
        return '<div class="table-scroll"><table><caption>'+escape(b['caption'])+'</caption><thead><tr>'+''.join('<th scope="col">'+escape(x)+'</th>' for x in b['headers'])+'</tr></thead><tbody>'+''.join('<tr>'+''.join(('<th scope="row">' if i==0 else '<td>')+escape(str(x))+('</th>' if i==0 else '</td>') for i,x in enumerate(row))+'</tr>' for row in b['rows'])+'</tbody></table></div>'
    if kind=='figure':
        data=base64.b64encode((OUT/b['file']).read_bytes()).decode()
        return '<figure class="wide"><img src="data:image/png;base64,'+data+'" alt="'+escape(b['alt'])+'"><figcaption>'+escape(b['caption'])+'</figcaption></figure>'
    raise ValueError(kind)

sections=[]
for i,sec in enumerate(get_sections(),1):
    body=''.join(block(b) for b in sec['blocks'])
    if sec['id']=='travel': body+=(ROOT/'scripts/calculator.html').read_text()
    sections.append(f'<section id="{sec["id"]}" class="section"><div class="report-section"><div class="section-label">{i:02d} / Research report</div><h2>{escape(sec["title"])}</h2>{body}</div></section>')
refs=''.join(f'<li>{escape(label)} <a href="{escape(url)}">Read source ↗</a></li>' for label,url in REFERENCES)
css=(ROOT/'scripts/site_style.css').read_text()
page=f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{TITLE} | Emmanuel Sampson</title><meta name="description" content="Research report on pharmacy access in Philadelphia, with findings, methodology, discussion, recommendations, limitations and a reproducible Jupyter notebook.">
<style>{css}</style></head><body>
<a class="skip" href="#main">Skip to research</a><header class="nav"><a class="brand" href="#">EMMANUEL SAMPSON / URBAN RESEARCH</a><nav aria-label="Sections"><a href="#methodology">Methods</a><a href="#results">Results</a><a href="#travel">Travel and emissions</a><a href="#discussion">Discussion</a><a href="#records">Downloads</a></nav></header>
<main id="main" class="wrap"><section class="hero"><div><div class="eyebrow">Philadelphia · Urban accessibility</div><h1>{TITLE}</h1><p class="lede">{SUBTITLE}.</p><p class="byline">{AUTHOR}<br>University of Pennsylvania<br>{DATE}</p><div class="actions"><a class="button" href="outputs/public/Pharmacy_Access_Research_Report.docx">Download the Word report ↓</a><a class="button alt" href="#results">Read the results ↓</a></div></div><aside class="hero-side" aria-label="Main findings"><div><strong>32.4 m</strong><p>Population-weighted proximity increase<br>under the all-listed removal scenario</p></div><div><strong>67 of 391</strong><p>Populated tracts with a calculated increase</p></div><p>These are spatial scenario results. Actual changes in travel modes and emissions have not been measured.</p></aside></section>
{''.join(sections)}
<section id="references" class="section"><div class="report-section references"><h2>References</h2><p class="mini">Numbers in the text refer to these sources. Source details were checked on {DATE}.</p><ol>{refs}</ol><p>Additional data and software references appear in <a href="{REPO}/blob/main/docs/references.md">the repository source notes</a>.</p></div></section>
<section id="records" class="section"><div class="report-section"><h2>Research records and downloads</h2><p>The website, Word report and notebook share the same findings and interpretation. The first notebook contains the executed public analysis. The second documents the future mobility study and reports that the required historical inputs are missing.</p><div class="actions"><a class="button" href="outputs/public/Pharmacy_Access_Research_Report.docx">Word report ↓</a><a class="button alt" href="outputs/public/Pharmacy_Access_Project_Brief.pdf">PDF report ↗</a><a class="button alt" href="{REPO}">GitHub repository ↗</a></div><ul><li><a href="{REPO}/blob/main/notebooks/01_public_data_pilot.ipynb">Executed Jupyter notebook</a></li><li><a href="{REPO}/blob/main/notebooks/02_mobility_event_study.ipynb">Mobility and event-study notebook</a></li><li><a href="{REPO}/releases/latest">Download the reproducible project package</a></li><li><a href="{REPO}/blob/main/docs/research_protocol.md">Detailed protocol for the historical study</a></li><li><a href="{REPO}/blob/main/data/source_manifest.json">Data sources and file checksums</a></li><li><a href="{REPO}/blob/main/docs/data_dictionary.md">Data dictionary</a></li></ul><p class="mini">The project package contains cached public analytical inputs. A Git clone can retrieve them with the documented downloader. Restricted mobility data are not included.</p></div></section>
</main><footer class="footer"><div class="footer-inner"><strong>{AUTHOR} · University of Pennsylvania</strong><p><a href="{REPO}">Research code and reproducibility record</a></p></div></footer>
<script>
(()=>{{const fields=['car','detour','additional','trips'].map(id=>document.getElementById(id));const update=()=>{{const [car,detour,additional,trips]=fields.map(e=>Number(e.value));const output=document.getElementById('co2');if(!Number.isFinite(trips)||trips<0||trips>1000000||fields[3].value===''){{output.textContent='Enter 0–1,000,000 trips';return;}}const kg=trips*2*{s['population_weighted_increment_m']}*detour*car*additional*400/1609.344/1000;output.textContent=kg.toLocaleString(undefined,{{minimumFractionDigits:2,maximumFractionDigits:2}})+' kg CO₂';}};fields.forEach(e=>e.addEventListener('input',update));update();}})();
</script></body></html>'''
(ROOT/'index.html').write_text(page)
print('Built index.html from the shared research narrative')
