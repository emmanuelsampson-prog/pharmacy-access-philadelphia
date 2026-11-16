"""Build fixed 2025 street networks from Geofabrik's historical OSM extract.

The annual extract replaces timed-out historical Overpass requests. No observed
mobility data are used. Origins and destinations are held fixed within each pair.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import xml.etree.ElementTree as ET
import osmium
import osmnx as ox
import requests
import gc

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw/historical_network'
RAW.mkdir(parents=True, exist_ok=True)
URL = 'https://download.geofabrik.de/north-america/us/pennsylvania-250101.osm.pbf'
PBF = RAW / 'pennsylvania-250101.osm.pbf'
BBOX = (-75.31, 39.85, -74.94, 40.16)
COMMON_EXCLUDED = {'abandoned', 'construction', 'no', 'planned', 'platform', 'proposed', 'raceway', 'razed'}
WALK_EXCLUDED = COMMON_EXCLUDED | {'motorway', 'motorway_link', 'bus_guideway', 'cycleway', 'rest_area', 'services'}
DRIVE_EXCLUDED = COMMON_EXCLUDED | {'bridleway', 'bus_guideway', 'cycleway', 'elevator', 'escalator', 'footway', 'path', 'pedestrian', 'steps', 'track', 'corridor'}


def usable(tags, mode):
    if 'highway' not in tags or tags.get('area') == 'yes' or tags.get('access') in {'private', 'no'}:
        return False
    if tags['highway'] in (WALK_EXCLUDED if mode == 'walk' else DRIVE_EXCLUDED):
        return False
    if mode == 'walk':
        return tags.get('foot') not in {'no', 'private'}
    return tags.get('motor_vehicle') not in {'no', 'private'} and tags.get('motorcar') not in {'no', 'private'} and tags.get('service') != 'private'


class LocalWays(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.nodes = {}
        self.ways = []

    def node(self, node):
        if node.location.valid():
            x, y = node.location.lon, node.location.lat
            if BBOX[0] <= x <= BBOX[2] and BBOX[1] <= y <= BBOX[3]:
                self.nodes[node.id] = (x, y)

    def way(self, way):
        tags = dict(way.tags)
        if not any(usable(tags, mode) for mode in ['walk', 'drive']):
            return
        parts, current = [], []
        for node in way.nodes:
            if node.ref in self.nodes:
                current.append(node.ref)
            else:
                if len(current) >= 2:
                    parts.append(current)
                current = []
        if len(current) >= 2:
            parts.append(current)
        for part, refs in enumerate(parts):
            self.ways.append((way.id if part == 0 else -(way.id * 1000 + part), refs, tags))


def build():
    if not PBF.exists():
        with requests.get(URL, stream=True, timeout=(30, 180)) as response:
            response.raise_for_status()
            temporary = PBF.with_suffix('.part')
            with temporary.open('wb') as handle:
                for chunk in response.iter_content(4 * 1024 * 1024):
                    handle.write(chunk)
            temporary.replace(PBF)
    reader = osmium.io.Reader(str(PBF))
    snapshot = reader.header().get('osmosis_replication_timestamp')
    reader.close()
    if not snapshot.startswith('2025-01-01'):
        raise ValueError(f'Unexpected historical extract date: {snapshot}')
    print('Reading historical streets:', snapshot, flush=True)
    local = LocalWays()
    local.apply_file(str(PBF))
    print('Local nodes and way segments:', len(local.nodes), len(local.ways), flush=True)
    needed_all = {ref for _, refs, _ in local.ways for ref in refs}
    local.nodes = {node: point for node, point in local.nodes.items() if node in needed_all}
    del needed_all
    gc.collect()
    print('Street nodes retained:', len(local.nodes), flush=True)
    for mode in ['walk', 'drive']:
        selected = [w for w in local.ways if usable(w[2], mode)]
        needed = {ref for _, refs, _ in selected for ref in refs}
        xml = ET.Element('osm', version='0.6', generator='pharmacy-access-philadelphia')
        for node in sorted(needed):
            x, y = local.nodes[node]
            ET.SubElement(xml, 'node', id=str(node), lon=str(x), lat=str(y))
        for wid, refs, tags in selected:
            element = ET.SubElement(xml, 'way', id=str(wid))
            for node in refs:
                ET.SubElement(element, 'nd', ref=str(node))
            for key, value in tags.items():
                ET.SubElement(element, 'tag', k=key, v=value)
        xmlpath = RAW / f'{mode}_20250101.osm'
        ET.ElementTree(xml).write(xmlpath, encoding='utf-8', xml_declaration=True)
        del xml, selected, needed
        gc.collect()
        print('Wrote street XML:', mode, flush=True)
    del local
    gc.collect()
    records = []
    for mode in ['walk', 'drive']:
        xmlpath = RAW / f'{mode}_20250101.osm'
        graph = ox.graph_from_xml(xmlpath, bidirectional=(mode == 'walk'), simplify=False, retain_all=False)
        path = RAW / f'{mode}_20250101.graphml'
        ox.save_graphml(graph, path)
        records.append({'mode': mode, 'file': str(path.relative_to(ROOT)), 'nodes': len(graph),
                        'edges': graph.number_of_edges(), 'bytes': path.stat().st_size,
                        'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        print(f'Saved {mode}: {len(graph)} nodes and {graph.number_of_edges()} edges', flush=True)
        del graph
        gc.collect()
    manifest = {
        'source': 'OpenStreetMap contributors; historical Pennsylvania extract distributed by Geofabrik',
        'source_url': URL, 'source_pbf_bytes': PBF.stat().st_size,
        'source_pbf_sha256': hashlib.sha256(PBF.read_bytes()).hexdigest(),
        'license': 'ODbL 1.0; https://www.openstreetmap.org/copyright',
        'snapshot_utc': snapshot, 'retrieved_at_utc': datetime.now(timezone.utc).isoformat(),
        'bbox_west_south_east_north': BBOX, 'osmnx_version': ox.__version__,
        'simplified': False, 'retain_all': False,
        'walk_excluded_highways': sorted(WALK_EXCLUDED), 'drive_excluded_highways': sorted(DRIVE_EXCLUDED),
        'interpretation': 'Constant mapped network. Shortest distance routes; no traffic, delays, turn restrictions, conditional restrictions, complete node-barrier permissions or observed mode choice.',
        'geographic_limit': 'PA extract clipped to bounding box. Destinations and origins are in PA; NJ alternatives and routes are not assessed.',
        'files': records}
    (ROOT / 'data/historical_network_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    build()
