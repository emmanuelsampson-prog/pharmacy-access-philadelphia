"""Build an accessible, self-contained transfer map for the public report."""
import json
from html import escape
import pandas as pd
import geopandas as gpd
from report_content import ROOT, OUT


def build_explorer():
    pairs = pd.read_csv(ROOT / 'data/processed/philadelphia_transfer_pairs_2025.csv', dtype={'store_number': str})
    results = pd.read_csv(OUT / 'before_after_by_event.csv', dtype={'store_number': str}).set_index('store_number')
    tracts = gpd.read_file(ROOT / 'data/processed/tract_scenarios.geojson').to_crs(26918)
    boundary = tracts.geometry.union_all()
    origins = pd.read_csv(ROOT / 'data/processed/before_after_access_origins.csv', dtype={'GEOID': str, 'store_number': str})
    assigned = origins.loc[origins.main_included].set_index('GEOID').store_number.to_dict()
    old = gpd.GeoSeries(gpd.points_from_xy(pairs.old_longitude, pairs.old_latitude), crs=4326).to_crs(26918)
    new = gpd.GeoSeries(gpd.points_from_xy(pairs.receiving_longitude, pairs.receiving_latitude), crs=4326).to_crs(26918)
    xmin, ymin, xmax, ymax = boundary.bounds
    scale = min(530 / (xmax - xmin), 530 / (ymax - ymin))
    def xy(p):
        return [round(35 + (p.x - xmin) * scale, 2), round(565 - (p.y - ymin) * scale, 2)]
    paths = []
    geoms = list(boundary.geoms) if hasattr(boundary, 'geoms') else [boundary]
    from shapely.geometry import Point
    for geom in geoms:
        coords = [xy(Point(x, y)) for x, y in geom.exterior.coords]
        paths.append('M' + ' L'.join(f'{x},{y}' for x, y in coords) + ' Z')
    features, dots, options = [], [], []
    for i, row in pairs.iterrows():
        address = row.old_address.replace('STREETPA SUITE 1', 'STREET').replace('AVENUEPA SUITE', 'AVENUE').title()
        r = results.loc[row.store_number]
        n = None if pd.isna(r.tracts) else int(r.tracts)
        d = {'id': row.store_number, 'old': address, 'recipient': row.receiving_name.title(),
             'new': row.receiving_address.title().rstrip(',') + ', ' + row.receiving_city.title(),
             'date': pd.Timestamp(row.pharmacy_last_open_date).strftime('%B %d, %Y'),
             'a': xy(old.iloc[i]), 'b': xy(new.iloc[i]), 'n': n,
             'before': None if n is None else round(r.weighted_walk_before_minutes, 1),
             'after': None if n is None else round(r.weighted_walk_after_minutes, 1),
             'change': None if n is None else round(r.weighted_walk_delta_minutes, 1),
             'same': bool(row.same_address_transfer)}
        features.append(d)
        x, y = d['a']
        dots.append(f'<circle cx="{x}" cy="{y}" r="4" fill="#a5b6b7"><title>{escape(address)}</title></circle>')
        options.append(f'<option value="{row.store_number}">{escape(address)}</option>')
    polygons = ''.join(f'<path d="{p}" fill="#edf0ed" stroke="#8c9d9d" stroke-width="1"/>' for p in paths)
    tract_paths = []
    for row in tracts.itertuples():
        parts = list(row.geometry.geoms) if hasattr(row.geometry, 'geoms') else [row.geometry]
        subpaths = []
        for part in parts:
            for ring in [part.exterior, *part.interiors]:
                coords = [xy(Point(x, y)) for x, y in ring.coords]
                subpaths.append('M' + ' L'.join(f'{x},{y}' for x, y in coords) + ' Z')
        store = assigned.get(row.GEOID, '')
        tract_paths.append(f'<path d="{" ".join(subpaths)}" fill="#edf0ed" fill-rule="evenodd" stroke="#ccd5d6" stroke-width="0.45" data-tract-store="{store}"><title>Census tract {escape(row.GEOID)}</title></path>')
    polygons += ''.join(tract_paths)
    html = f'''<div class="explorer" id="explorer"><h3>Explore a documented transfer</h3><p>Select a former pharmacy to see its designated recipient and the modeled walking comparison for nearby included tract centers.</p><label for="transfer-select">Former Rite Aid address</label><select id="transfer-select">{''.join(options)}</select><div class="explorer-grid"><svg viewBox="0 0 600 610" role="img" aria-labelledby="map-title map-description"><title id="map-title">Selected pharmacy transfer in Philadelphia</title><desc id="map-description">Gray dots mark former pharmacies. Shaded tracts identify the included origins assigned to the selected transfer. An orange circle marks the selected former pharmacy and a teal square its designated recipient. The connecting line is not a street route.</desc>{polygons}{''.join(dots)}<line id="transfer-link" stroke="#627f86" stroke-width="2" stroke-dasharray="5 4"/><circle id="transfer-old" r="8" fill="#ba663e" stroke="white" stroke-width="2"/><rect id="transfer-new" width="13" height="13" fill="#137c86" stroke="white" stroke-width="2"/><text x="545" y="42" fill="#344b55" font-size="16">N ↑</text><path d="M35,590 h{5000 * scale:.2f}" stroke="#344b55" stroke-width="2"/><text x="35" y="580" font-size="12" fill="#344b55">5 km</text></svg><div id="transfer-detail" aria-live="polite"></div></div><p class="mini">Shaded tracts: included origins for the selected transfer · Orange circle: former pharmacy · Teal square: designated recipient. Tract shading shows sample membership, not uniform exposure or travel time. Lines connect addresses, not observed trips or mapped routes. Population weights describe neighborhood context, not customer counts. Source: company transfer table, PA coordinates and Census boundaries.</p><noscript><p>Enable JavaScript to explore individual records. The complete static map and location chart above remain available without it.</p></noscript></div>'''
    script = '''(()=>{const data=TRANSFER_DATA; const select=document.getElementById('transfer-select');
const set=(id,attrs)=>{const e=document.getElementById(id);for(const [k,v] of Object.entries(attrs))e.setAttribute(k,v)};
const update=()=>{const d=data.find(x=>x.id===select.value);document.querySelectorAll('[data-tract-store]').forEach(e=>{const selected=e.getAttribute('data-tract-store')===d.id;e.setAttribute('fill',selected?'#f3d0ad':'#edf0ed');e.setAttribute('stroke',selected?'#bb8b63':'#ccd5d6')});set('transfer-link',{x1:d.a[0],y1:d.a[1],x2:d.b[0],y2:d.b[1]});set('transfer-old',{cx:d.a[0],cy:d.a[1]});set('transfer-new',{x:d.b[0]-6.5,y:d.b[1]-6.5});
const out=document.getElementById('transfer-detail');out.replaceChildren();
const add=(tag,text,cls)=>{const e=document.createElement(tag);e.textContent=text;if(cls)e.className=cls;out.append(e)};
add('h4',d.old);add('p','Reported last pharmacy day: '+d.date);add('p','Designated recipient: '+d.recipient+', '+d.new);
if(d.n===null){add('p',d.id==='1956'?'Excluded from the primary calculation: insurer and company addresses disagree.':'No tract center falls within the main 800 m catchment. No estimate is available.','notice')}
else{add('div',d.before.toFixed(1)+' → '+d.after.toFixed(1)+' min','route-number');add('p','Population-weighted modeled one-way walk across '+d.n+' included tract origins.');add('p','Change: '+(d.change>0?'+':'')+d.change.toFixed(1)+' minutes.');}
if(d.same)add('p','Same-address transfer. Identical modeled distance does not prove uninterrupted pharmacy service.');
};select.addEventListener('change',update);update();})();'''.replace('TRANSFER_DATA', json.dumps(features, allow_nan=False).replace('</', '<\\/'))
    return html, script
