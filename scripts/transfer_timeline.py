"""Source-record selector accompanying the Python-generated timeline figure."""
import json
from html import escape
import pandas as pd
from report_content import ROOT


def build_timeline():
    # scripts/ is on sys.path for the site builder; add the repository for src/.
    import sys
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from src.timeline import timeline_data
    pairs = pd.read_csv(ROOT / 'data/processed/philadelphia_transfer_pairs_2025.csv', dtype={'store_number': str})
    records, weekly, daily, summary = timeline_data(pairs)
    peak = int(weekly.records.idxmax())
    data = []
    for row in records.itertuples():
        start = row.date - pd.Timedelta(days=row.date.day_of_week)
        address = row.old_address.replace('STREETPA SUITE 1', 'STREET').replace('AVENUEPA SUITE', 'AVENUE').title()
        data.append({'id': row.store_number, 'address': address,
                     'date': row.date.strftime('%-d %B %Y'), 'iso': str(row.date.date()),
                     'week': str(start.date()), 'recipient': row.receiving_name.title(),
                     'recipient_address': row.receiving_address.title().rstrip(',') + ', ' + row.receiving_city.title(),
                     'same': bool(row.same_address_transfer), 'disputed': row.store_number == '1956'})
    week_data = []
    for i, row in weekly.iterrows():
        if row.week_start.month == row.week_end.month:
            label = f'{row.week_start:%-d}–{row.week_end:%-d %B}'
        else:
            label = f'{row.week_start:%-d %B}–{row.week_end:%-d %B}'
        key = str(row.week_start.date())
        week_data.append({'key': key, 'label': label, 'count': int(row.records)})
    def record_html(d):
        flag = '<span class="timeline-flag">Address conflict under review</span>' if d['disputed'] else ('<span class="timeline-flag">Same-address transfer</span>' if d['same'] else '')
        return f'<li><time datetime="{d["iso"]}">{escape(d["date"])}</time><strong>{escape(d["address"])}</strong><span>Recipient: {escape(d["recipient"])}, {escape(d["recipient_address"])}</span>{flag}</li>'
    selected = week_data[peak]
    rows = ''.join(record_html(d) for d in data if d['week'] == selected['key'])
    options = '<option value="all">All 24 records</option>' + ''.join(
        f'<option value="{w["key"]}"{" selected" if w["key"] == selected["key"] else ""}>'
        f'{escape(w["label"])} 2025 ({w["count"]} records)</option>' for w in week_data)
    html = f'''<details class="timeline-record-view"><summary>View the dated source records</summary>
<label for="timeline-week-select">Reported last pharmacy day (Monday–Sunday week)</label>
<select id="timeline-week-select" aria-controls="timeline-records">{options}</select>
<p id="timeline-selected-summary" role="status" aria-live="polite">{selected['count']} of {len(records)} documented locations</p>
<ul class="timeline-records" id="timeline-records">{rows}</ul>
<p>Dates are company-reported last pharmacy-business days. These are selected records, not all Philadelphia closures.</p>
<div class="timeline-downloads"><a href="outputs/public/transfer_timeline.svg">Vector figure (SVG)</a><a href="outputs/public/transfer_timeline.pdf">Figure (PDF)</a><a href="outputs/public/transfer_timeline_weekly.csv" download>Weekly counts (CSV)</a><a href="data/processed/philadelphia_transfer_pairs_2025.csv" download>All source records (CSV)</a></div>
<noscript><p>The busiest-week records are shown without JavaScript. Download the CSV to inspect all records.</p></noscript></details>'''
    script = '''(()=>{const records=TIMELINE_RECORDS, weeks=TIMELINE_WEEKS;
const select=document.getElementById('timeline-week-select'), list=document.getElementById('timeline-records'), status=document.getElementById('timeline-selected-summary');
function update(){const key=select.value;const chosen=key==='all'?records:records.filter(d=>d.week===key);
status.textContent=chosen.length+' of '+records.length+' documented locations';list.replaceChildren();
if(!chosen.length){const li=document.createElement('li');li.className='timeline-empty';li.textContent='No locations in this source table have a reported last pharmacy day in this week. This does not imply that no pharmacies closed elsewhere in Philadelphia.';list.append(li);}
for(const d of chosen){const li=document.createElement('li');const add=(tag,text,cls)=>{const e=document.createElement(tag);e.textContent=text;if(cls)e.className=cls;li.append(e);return e;};add('time',d.date).dateTime=d.iso;add('strong',d.address);add('span','Recipient: '+d.recipient+', '+d.recipient_address);if(d.disputed)add('span','Address conflict under review','timeline-flag');if(d.same)add('span','Same-address transfer','timeline-flag');list.append(li);}}
select.addEventListener('change',update);})();'''
    script = script.replace('TIMELINE_RECORDS', json.dumps(data).replace('</','<\\/')).replace('TIMELINE_WEEKS',json.dumps(week_data))
    return html, script
