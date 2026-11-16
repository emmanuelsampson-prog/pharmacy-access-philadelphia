"""Create a compact, evidence-labeled PDF from the executed pilot outputs."""
from pathlib import Path
import json
from xml.sax.saxutils import escape
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"outputs/public"
summary=json.loads((OUT/"summary.json").read_text())
metrics=pd.read_csv(OUT/"ml_metrics.csv")
font=Path('/usr/share/fonts/truetype/dejavu')
pdfmetrics.registerFont(TTFont('DVS',str(font/'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('DVS-Bold',str(font/'DejaVuSans-Bold.ttf')))
pdfmetrics.registerFontFamily('DVS',normal='DVS',bold='DVS-Bold',italic='DVS',boldItalic='DVS-Bold')
navy=colors.HexColor('#172d45');teal=colors.HexColor('#087e8b');orange=colors.HexColor('#b9532d')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleX',fontName='DVS-Bold',fontSize=28,leading=33,textColor=navy,spaceAfter=12))
styles.add(ParagraphStyle(name='SubX',fontName='DVS',fontSize=14,leading=20,textColor=teal,spaceAfter=16))
styles.add(ParagraphStyle(name='H1X',fontName='DVS-Bold',fontSize=17,leading=22,textColor=navy,spaceAfter=13))
styles.add(ParagraphStyle(name='H2X',fontName='DVS-Bold',fontSize=11,leading=15,textColor=teal,spaceBefore=10,spaceAfter=6))
styles.add(ParagraphStyle(name='BodyX',fontName='DVS',fontSize=9.4,leading=14,spaceAfter=9))
styles.add(ParagraphStyle(name='SmallX',fontName='DVS',fontSize=8,leading=11,spaceAfter=7,textColor=colors.HexColor('#475569')))
styles.add(ParagraphStyle(name='LabelX',fontName='DVS-Bold',fontSize=9,leading=13,textColor=orange,spaceAfter=10))
styles.add(ParagraphStyle(name='CellX',fontName='DVS',fontSize=8,leading=11))
W=499
story=[]
def p(text,style='BodyX'):return Paragraph(text,styles[style])
def add(text,style='BodyX'):story.append(p(text,style))
def table(rows,widths):
    data=[[p(str(v),'CellX') for v in row] for row in rows]
    t=Table(data,colWidths=widths,hAlign='LEFT',repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e4f0f1')),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.6,teal),
        ('LINEBELOW',(0,1),(-1,-1),.25,colors.HexColor('#d8e2e7')),
        ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
        ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    story.append(t);story.append(Spacer(1,12))
def newpage(title):story.append(PageBreak());add(title,'H1X')

add('When Pharmacies<br/>Disappear','TitleX')
add('Accessibility, travel and equity<br/>in Philadelphia','SubX')
add('Emmanuel Amissah Sampson | University of Pennsylvania<br/>AI in Urban Studies final-project development | 16 November 2026','SmallX')
story.append(Spacer(1,12))
add('EXECUTED PUBLIC-DATA PILOT - EMPIRICAL STUDY PENDING','LabelX')
add('The project asks how pharmacy closures change the geography of everyday destinations, redistribute visits and create unequal access burdens. The proposed empirical case is Philadelphia and the 2023-2025 Rite Aid closures, using 2022 as a preperiod.')
add('The main deliverable is an executed Jupyter notebook, supported by reusable code, downloaded public inputs, a source manifest, a closure-verification ledger and a companion notebook for the future mobility study. This brief summarizes what has actually been completed.')
table([['Completed now','Still required for a final causal study'],
    ['Public-data download and provenance; tract access scenario; spatial AI benchmark; emissions sensitivity; method tests','Verified historical operating dates; authorized mobility panel; historical routing and NJ alternatives; defensible comparison groups; course rubric and deadline']], [W/2,W/2])
add('A focused semester project','H2X')
add('Study pharmacies first. Keep other retail openings, closures and relocations as the research agenda. Observed mode changes require data beyond aggregate foot traffic; without those data, travel modes and emissions must remain explicitly modeled scenarios.')
add('Read first','H2X')
add('notebooks/01_public_data_pilot.ipynb<br/>docs/research_protocol.md<br/>docs/data_access.md','SmallX')
add('Repository: github.com/emmanuelsampson-prog/pharmacy-access-philadelphia<br/>Web report: emmanuelsampson-prog.github.io/pharmacy-access-philadelphia/','SmallX')

newpage('1 | What the public pilot shows')
add('A scenario, not a historical effect','LabelX')
add('The calculation removes every Rite Aid-labelled entry from a Pennsylvania licensed-pharmacy roster and compares the nearest remaining destination from each tract centroid. The roster is not a verified operating network. Distances are straight-line meters, not routes or observed journeys.')
story.append(Image(str(OUT/'access_equity_map.png'),width=W,height=W*1313/1910))
story.append(Spacer(1,10))
table([['Run record','Result'],
    ['Philadelphia tracts / populated tracts',f"{summary['tracts_total']} / {summary['tracts_populated']}"],
    ['Rite Aid-labelled entries in the PA study buffer',str(summary['rite_aid_labelled_buffer_sites'])+' unverified candidates'],
    ['Population-weighted increment: all-listed scenario',f"{summary['population_weighted_increment_m']:.1f} meters"],
    ['Population-weighted increment: chain-name scenario',f"{summary['population_weighted_chain_inventory_increment_m']:.1f} meters"]],[365,134])
add('The large difference between inventory definitions makes operating-status validation essential. These two scenarios are not formal bounds, and neither value estimates the actual effects of the 2023-2025 closures.','SmallX')

newpage('2 | AI results and emissions assumptions')
add('The simple baseline wins on average absolute error','H2X')
add('Models use five contiguous geographic holdouts with a 1 km training exclusion buffer. Imputation and scaling occur inside each fold. The target is a mechanically calculated scenario, so predictive performance does not establish causality or historical validity.')
rows=[['Model','MAE (m)','RMSE (m)','R-squared']]
for _,r in metrics.sort_values('mae_m').iterrows():rows.append([r.model,f'{r.mae_m:.1f}',f'{r.rmse_m:.1f}',f'{r.r2:.3f}'])
table(rows,[220,93,93,93])
story.append(Image(str(OUT/'model_and_equity.png'),width=W,height=W*862/2174))
story.append(Spacer(1,9))
add('Random forest does not improve MAE over the median baseline. Its small RMSE improvement and near-zero R-squared do not establish useful generalization. These negative results are retained; the held-out folds should not be reused as an untouched test after further tuning.','SmallX')
add('Emissions remain conditional scenarios','H2X')
add('The code varies car share, route-detour factor and the share of journeys producing additional travel. It applies the EPA typical gasoline-vehicle factor of about 400 g CO2 per vehicle-mile to 1,000 hypothetical person round trips, assuming one traveler per vehicle. No actual mode shares or citywide annual emissions are estimated.')
add('Equity tables describe neighborhoods using ACS population and household weights. They do not identify individual experience or causal subgroup effects; ACS margins of error are retained but not propagated in this pilot.','SmallX')

newpage('3 | The empirical design to complete')
table([['Element','Specification'],
    ['Unit and period','Philadelphia home-origin area by week/month; separate surviving-pharmacy panel. Observe 2022-2025.'],
    ['Events','Verified last pharmacy-open and first pharmacy-closed dates, front-store date, receiving pharmacy and same-site replacement. Preserve date uncertainty.'],
    ['Outcomes','Origin-to-POI distance proxy and normalized category activity; receiving-store redistribution; routed access measures. No mode claim from counts alone.'],
    ['Exposure and spillovers','Starting specification: direct exposure within 800 m; indirect exposure 800-1,600 m. Test other thresholds and preperiod catchments.'],
    ['Comparisons','Never- or not-yet-exposed areas beyond the anticipation window; exclude separately flagged spillovers and handle overlapping events.'],
    ['Estimator','Cohort-time contrasts; avoid already-treated controls. Python code is unadjusted. Optional R did extension adds baseline covariates and a more restrictive clean sample.'],
    ['Inference','Event support, pretrends, placebo checks, date/radius sensitivity and spatial uncertainty. Bootstrap intervals in Python are pointwise.']],[115,384])
add('Key identification risk','H2X')
add('Bankruptcy does not randomize which pharmacies close or when. Demand decline, leases, staffing and neighborhood change may select locations. Parallel trends and clean comparisons require evidence. Nearby surviving stores may receive displaced visits and therefore belong in the spillover analysis, not the control group.')
add('The code rejects missing panel outcomes, unverified event dates and insufficient comparison support. A successful software run is not evidence that the identifying assumptions hold. If clean controls are too scarce, narrow the estimand or retain a descriptive/scenario project.','SmallX')

newpage('4 | Next inputs, records and references')
add('Complete the empirical work in four stages','H2X')
table([['Stage','Deliverable'],
    ['1. Scope and access','Course rubric/deadline, Penn/Dewey product access, verified event and operating-history ledger.'],
    ['2. Build panels','Coverage-audited origin/POI panels, geography crosswalks, historical routing and border alternatives.'],
    ['3. Estimate and challenge','AI validation, causal contrasts, clean-control support, pretrends and robustness checks.'],
    ['4. Write and publish','Complete empirical notebooks and interpretation; publish only permitted aggregates; update the GitHub web report.']],[115,384])
add('Reproducibility record','H2X')
add('The package contains two Jupyter notebooks, Python source modules, an optional unexecuted R extension, public inputs, hashes, figures, data dictionaries and publication instructions. Eleven Python method checks passed in the initial verification. The companion notebook explicitly reports that the required empirical inputs are absent.')
add('Selected references','H2X')
for label,url in [
('PA licensed pharmacy roster','https://data.pa.gov/Opioid-Related/ysdx-4vmi/about_data'),
('Census 2022 ACS Summary File','https://www.census.gov/programs-surveys/acs/data/summary-file.2022.html'),
('Penn Libraries: Dewey access','https://www.library.upenn.edu/lippincott/datapoints/data-access-dewey-2025'),
('Callaway and Sant\'Anna: multiple-period DiD','https://bcallaway11.github.io/did/articles/multi-period-did.html'),
('Butts: DiD with spatial spillovers','https://arxiv.org/abs/2105.03737'),
('EPA: typical passenger-vehicle emissions','https://www.epa.gov/greenvehicles/greenhouse-gas-emissions-typical-passenger-vehicle')]:
    add(f'<link href="{url}" color="#087e8b">{escape(label)}</link>','SmallX')
add('Full source details and retrieval provenance are in docs/references.md and data/source_manifest.json. Original code and documentation were developed with AI assistance and require author review. Follow the course AI-use rules before submission.','SmallX')
add('No human-mobility dataset or individual travel records were obtained. No historical causal effect, observed mode change or observed emissions effect has been claimed.','LabelX')

def footer(c,doc):
    c.setStrokeColor(colors.HexColor('#d7e2e7'));c.line(48,43,547,43)
    c.setFont('DVS',7.5);c.setFillColor(colors.HexColor('#506273'))
    c.drawString(48,29,'PHARMACY ACCESS | Public-data feasibility pilot')
    c.drawRightString(547,29,str(doc.page))

doc=SimpleDocTemplate(str(OUT/'Pharmacy_Access_Project_Brief.pdf'),pagesize=(595,842),
    leftMargin=48,rightMargin=48,topMargin=47,bottomMargin=58,
    title='When Pharmacies Disappear - Project Brief',author='Emmanuel Amissah Sampson')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(OUT/'Pharmacy_Access_Project_Brief.pdf')
