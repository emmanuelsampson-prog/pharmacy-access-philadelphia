"""Responsive weekly chart with keyboard-accessible record inspection."""
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
    ceiling = max(4, int((weekly.records.max() + 2) // 2 * 2))
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
    buttons = []
    for i, row in weekly.iterrows():
        if row.week_start.month == row.week_end.month:
            label = f'{row.week_start:%-d}–{row.week_end:%-d %B}'
        else:
            label = f'{row.week_start:%-d %B}–{row.week_end:%-d %B}'
        key = str(row.week_start.date())
        week_data.append({'key': key, 'label': label, 'count': int(row.records)})
        height = row.records / ceiling * 220
        buttons.append(f'''<button type="button" class="timeline-week{' peak' if i == peak else ''}" data-timeline-week="{key}" aria-pressed="{'true' if i == peak else 'false'}" aria-controls="timeline-records" aria-label="{escape(label)} 2025: {int(row.records)} records" style="--bar-height:{height:.2f}px"><span class="timeline-count" aria-hidden="true">{int(row.records)}</span><span class="timeline-bar{' zero' if row.records == 0 else ''}" aria-hidden="true"></span><span class="timeline-week-label" aria-hidden="true">{row.week_start:%-d}<br>{row.week_start:%b}</span></button>''')
    ticks = ''.join(f'<span style="bottom:{64 + n / ceiling * 220:.2f}px">{n}</span>' for n in range(0, ceiling + 1, 2))
    grid = ''.join(f'<i style="bottom:{64 + n / ceiling * 220:.2f}px"></i>' for n in range(0, ceiling + 1, 2))
    def record_html(d):
        flag = '<span class="timeline-flag">Address conflict under review</span>' if d['disputed'] else ('<span class="timeline-flag">Same-address transfer</span>' if d['same'] else '')
        return f'<li><time datetime="{d["iso"]}">{escape(d["date"])}</time><strong>{escape(d["address"])}</strong><span>Recipient: {escape(d["recipient"])}, {escape(d["recipient_address"])}</span>{flag}</li>'
    selected = week_data[peak]
    rows = ''.join(record_html(d) for d in data if d['week'] == selected['key'])
    monthly = records.groupby(records.date.dt.to_period('M')).size()
    busiest_month = monthly.idxmax()
    share = int(monthly.max()) / len(records)
    month_labels = ''.join(f'<span><b>{int(count)}</b> {month.start_time:%B}</span>' for month,count in monthly.items())
    html = f'''<div class="timeline-card">
<div class="timeline-kicker">Philadelphia · Rite Aid transfer records · 2025</div>
<h3>{share:.0%} of documented transfers fell in {busiest_month.start_time:%B}</h3>
<p class="timeline-deck">{len(records)} locations · {len(daily)} reported dates · {records.date.min():%-d %B}–{records.date.max():%-d %B %Y}</p>
<div class="timeline-months" aria-label="Monthly record totals">{month_labels}</div>
<div class="timeline-chart-heading"><strong>Records per week</strong><span>Monday–Sunday · Select a bar to inspect the records</span></div>
<div class="timeline-chart-scroll" tabindex="0" role="region" aria-label="Weekly transfer chart; scroll horizontally on small screens">
<div class="timeline-chart"><div class="timeline-yaxis" aria-hidden="true">{ticks}</div><div class="timeline-plot"><div class="timeline-grid" aria-hidden="true">{grid}</div><div class="timeline-bars" role="group" aria-label="Select a week">{''.join(buttons)}</div></div></div></div>
<div class="timeline-axis-note">Week starting <span><i></i>Busiest week: {escape(selected['label'])} · {selected['count']} records ({selected['count']/len(records):.0%})</span></div>
<div class="timeline-record-header"><div><div class="timeline-kicker">Inspect the source records</div><h4 id="timeline-selected-title">{escape(selected['label'])} 2025</h4><p id="timeline-selected-summary" role="status" aria-live="polite">{selected['count']} of {len(records)} documented locations</p></div><button type="button" id="timeline-show-all">Show all {len(records)} records</button></div>
<ul class="timeline-records" id="timeline-records">{rows}</ul>
<p class="timeline-source">Dates are company-reported last pharmacy-business days. Zero bars mean no records in this table, not zero closures citywide. Patient travel is not measured.</p>
<div class="timeline-downloads"><a href="outputs/public/transfer_timeline.svg">Download vector figure ↗</a><a href="outputs/public/transfer_timeline.png">Open print figure ↗</a><a href="outputs/public/transfer_timeline_weekly.csv" download>Weekly counts ↓</a><a href="data/processed/philadelphia_transfer_pairs_2025.csv" download>All source records ↓</a></div>
<noscript><p>The chart and busiest-week records are shown without JavaScript. Download all source records to inspect the full table.</p></noscript></div>'''
    script = '''(()=>{const records=TIMELINE_RECORDS, weeks=TIMELINE_WEEKS;
const buttons=[...document.querySelectorAll('[data-timeline-week]')], all=document.getElementById('timeline-show-all');
const list=document.getElementById('timeline-records'), title=document.getElementById('timeline-selected-title'), status=document.getElementById('timeline-selected-summary');
function update(key){const chosen=key===null?records:records.filter(d=>d.week===key);const week=weeks.find(w=>w.key===key);
buttons.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.timelineWeek===key)));all.setAttribute('aria-pressed',String(key===null));
title.textContent=key===null?'All documented locations':week.label+' 2025';status.textContent=chosen.length+' of '+records.length+' documented locations';list.replaceChildren();
if(!chosen.length){const li=document.createElement('li');li.className='timeline-empty';li.textContent='No locations in the source table have a reported last pharmacy day in this week. This is not evidence that no pharmacies closed elsewhere in Philadelphia.';list.append(li);}
for(const d of chosen){const li=document.createElement('li');const add=(tag,text,cls)=>{const e=document.createElement(tag);e.textContent=text;if(cls)e.className=cls;li.append(e);return e;};add('time',d.date).dateTime=d.iso;add('strong',d.address);add('span','Recipient: '+d.recipient+', '+d.recipient_address);if(d.disputed)add('span','Address conflict under review','timeline-flag');if(d.same)add('span','Same-address transfer','timeline-flag');list.append(li);}}
buttons.forEach(b=>b.addEventListener('click',()=>update(b.dataset.timelineWeek)));all.addEventListener('click',()=>update(null));})();'''
    script = script.replace('TIMELINE_RECORDS', json.dumps(data).replace('</','<\\/')).replace('TIMELINE_WEEKS',json.dumps(week_data))
    return html, script
