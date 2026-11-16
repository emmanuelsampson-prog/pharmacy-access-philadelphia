"""Package public research files and explicitly approved cached analytical inputs.

Run from any directory: python scripts/package_release.py /path/release.zip
Third-party articles, court PDFs, insurer PDFs, the statewide PBF and intermediate
OSM XML are deliberately omitted. Their provenance is recorded in manifests.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def build(destination):
    names = set(subprocess.check_output(
        ['git', 'ls-files', '-co', '--exclude-standard', '-z'], cwd=ROOT
    ).decode().strip('\0').split('\0'))
    # Only this explicit list can add ignored raw inputs to the public archive.
    raw = ROOT / 'data/raw'
    cached = [
        raw / 'pa_pharmacies.csv', raw / 'cb_2022_42_tract_500k.zip',
        raw / 'cb_2022_us_county_500k.zip', raw / 'acs_2022_philadelphia.json',
        raw / 'cvs_knights_census_geocode.json',
        raw / 'historical_network/walk_20250101.graphml',
        raw / 'historical_network/drive_20250101.graphml',
    ]
    for table in ['b01001', 'b01003', 'b03002', 'b08201', 'b17001', 'b19013']:
        cached.append(raw / f'acs2022_{table}_philadelphia.dat')
    for path in list(cached):
        sidecar = path.with_name(path.name + '.provenance.json')
        if sidecar.exists():
            cached.append(sidecar)
    names.update(str(path.relative_to(ROOT)) for path in cached)
    paths = [ROOT / name for name in sorted(names) if name]
    missing = [str(path.relative_to(ROOT)) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f'Missing release inputs: {missing}')
    prohibited = [path for path in paths if
        ('data/restricted/' in str(path.relative_to(ROOT)) and path.name != '.gitkeep')
        or path.suffix in {'.pbf', '.osm'} or '__pycache__' in path.parts]
    if prohibited:
        raise ValueError(f'Unexpected release files: {prohibited}')
    manifest = [{'file': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size,
                 'sha256': sha256(path)} for path in paths]
    destination = Path(destination).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    prefix = 'pharmacy-access-philadelphia/'
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in paths:
            archive.write(path, prefix + str(path.relative_to(ROOT)))
        archive.writestr(prefix + 'release_file_manifest.json', json.dumps(manifest, indent=2))
    checksum = sha256(destination)
    destination.with_suffix('.sha256').write_text(f'{checksum}  {destination.name}\n')
    print(json.dumps({'archive': str(destination), 'files': len(paths) + 1,
                      'bytes': destination.stat().st_size, 'sha256': checksum}, indent=2))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python scripts/package_release.py OUTPUT.zip')
    build(sys.argv[1])
