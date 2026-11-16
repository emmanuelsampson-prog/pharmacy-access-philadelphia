"""Download public inputs, preserving original bytes and SHA-256 provenance."""
from __future__ import annotations
import argparse
import hashlib
import json
import io
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
import requests
import pandas as pd
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[1]
ESTIMATES = [
    "B01003_001E", "B19013_001E", "B17001_001E", "B17001_002E",
    "B08201_001E", "B08201_002E", "B03002_001E", "B03002_003E",
    "B03002_004E", "B03002_012E",
] + [f"B01001_{i:03d}E" for i in [20,21,22,23,24,25,44,45,46,47,48,49]]

def specs():
    variables = ["NAME"] + ESTIMATES + [s[:-1]+"M" for s in ESTIMATES]
    query = urlencode({"get": ",".join(variables), "for": "tract:*", "in": "state:42 county:101"})
    return [
        dict(id="pa_pharmacies", file="pa_pharmacies.csv", format="csv",
             url="https://data.pa.gov/api/views/ysdx-4vmi/rows.csv?accessType=DOWNLOAD",
             source_page="https://data.pa.gov/Opioid-Related/ysdx-4vmi/about_data",
             vintage="Portal reports last updated 2025-07-01; license listing, not operating history",
             license="Portal labels Public Domain U.S. Government",
             limitations="May include nonretail/closed sites and approximate geocodes. No closure dates."),
        dict(id="acs_2022", file="acs_2022_philadelphia.json", format="json",
             url="https://api.census.gov/data/2022/acs/acs5?"+query,
             source_page="https://www.census.gov/data/developers/data-sets/acs-5year/2022.html",
             vintage="2018-2022 ACS five-year estimates; 2022 geography", license="US Census public data",
             limitations="Survey estimates with margins of error; not annual household trajectories."),
        dict(id="tract_boundaries", file="cb_2022_42_tract_500k.zip", format="zip",
             url="https://www2.census.gov/geo/tiger/GENZ2022/shp/cb_2022_42_tract_500k.zip",
             source_page="https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.html",
             vintage="2022 cartographic boundaries, 1:500,000", license="US Census public data",
             limitations="Simplified shapes; centroids are not residential or population-weighted origins."),
        dict(id="nj_county_boundaries", file="cb_2022_us_county_500k.zip", format="zip",
             url="https://www2.census.gov/geo/tiger/GENZ2022/shp/cb_2022_us_county_500k.zip",
             source_page="https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.html",
             vintage="2022 cartographic US counties; select New Jersey", license="US Census public data",
             limitations="Used only to flag origins within 2 km of NJ; no NJ pharmacy inventory included."),
        dict(id="closure_notice_2025", file="rite_aid_closure_notice_2025.pdf", format="pdf",
             url="https://www.amerihealthcaritaschc.com/content/dam/amerihealth-caritas/acpchc/pdf/provider/resources/communications/2025/20250605-rite-aid-pharmacy-closure-notice.pdf.coredownload.inline.pdf",
             source_page="https://www.amerihealthcaritaschc.com/", vintage="Notice issued 2025-06-05",
             license="Public notice; third-party copyright; not included in public repository",
             limitations="Closure or imminent closure; NOT store-specific final operating dates."),
    ]

def fetch(item, refresh=False):
    out = ROOT / "data/raw" / item["file"]
    out.parent.mkdir(parents=True, exist_ok=True)
    sidecar = out.with_suffix(out.suffix+".provenance.json")
    if out.exists() and sidecar.exists() and not refresh:
        previous = json.loads(sidecar.read_text())
        if hashlib.sha256(out.read_bytes()).hexdigest() != previous["sha256"]:
            raise ValueError(f"Cached input changed: {out}. Use --refresh to redownload.")
        return previous
    session = requests.Session()
    session.headers["User-Agent"] = "PharmacyAccessResearch/0.1 academic research"
    retry = Retry(total=2, backoff_factor=1, status_forcelist=[429,500,502,503,504])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    response = session.get(item["url"], timeout=(15,60))
    response.raise_for_status()
    content = response.content
    if item["format"] == "json": json.loads(content)
    if item["format"] == "zip" and not content.startswith(b"PK"): raise ValueError("Expected ZIP")
    if item["format"] == "pdf" and not content.startswith(b"%PDF"): raise ValueError("Expected PDF")
    if item["format"] == "csv" and not content.startswith(b"License Number,"): raise ValueError("Unexpected pharmacy schema")
    temp = out.with_suffix(out.suffix+".part")
    temp.write_bytes(content)
    temp.replace(out)
    record = dict(item, retrieved_at_utc=datetime.now(timezone.utc).isoformat(),
                  bytes=len(content), sha256=hashlib.sha256(content).hexdigest(),
                  status="downloaded", local_path=str(out.relative_to(ROOT)))
    sidecar.write_text(json.dumps(record, indent=2)+"\n")
    return record

def fetch_acs_table(table, refresh=False):
    """Stream the official national bulk file; retain Philadelphia tract rows.

    The public bulk route needs no API key. Full national response bytes are
    hashed while streaming but not kept; filtered raw lines preserve all cells.
    """
    folder=ROOT/"data/raw";folder.mkdir(parents=True,exist_ok=True)
    path=folder/f"acs2022_{table.lower()}_philadelphia.dat"
    sidecar=path.with_suffix(".provenance.json")
    if path.exists() and sidecar.exists() and not refresh:
        record=json.loads(sidecar.read_text())
        if hashlib.sha256(path.read_bytes()).hexdigest()!=record["sha256"]:raise ValueError("ACS subset checksum mismatch")
        return record
    url=f"https://www2.census.gov/programs-surveys/acs/summary_file/2022/table-based-SF/data/5YRData/acsdt5y2022-{table.lower()}.dat"
    response=requests.get(url,stream=True,timeout=(15,90))
    response.raise_for_status()
    digest=hashlib.sha256();remainder=b"";selected=[];header=None;total=0
    for chunk in response.iter_content(chunk_size=1024*1024):
        digest.update(chunk);total+=len(chunk)
        lines=(remainder+chunk).split(b"\n");remainder=lines.pop()
        for line in lines:
            if header is None:
                header=line
                if not header.startswith(b"GEO_ID|"):raise ValueError("Unexpected Census bulk schema")
                selected.append(line)
            elif line.startswith(b"1400000US42101"):selected.append(line)
    if remainder.startswith(b"1400000US42101"):selected.append(remainder)
    if len(selected)<300:raise ValueError(f"Incomplete Philadelphia tract extraction: {len(selected)-1}")
    content=b"\n".join(selected)+b"\n"
    path.write_bytes(content)
    record=dict(id=f"acs2022_{table}",file=path.name,url=url,
        source_page="https://www.census.gov/programs-surveys/acs/data/summary-file.2022.html",
        vintage="2018-2022 ACS five-year estimates",license="US Census public data",
        limitations="Survey estimates; geographic context, not individual behavior. Includes MOEs.",
        status="downloaded",extraction="GEO_ID starts with 1400000US42101",rows=len(selected)-1,
        retrieved_at_utc=datetime.now(timezone.utc).isoformat(),national_source_bytes=total,
        national_source_sha256=digest.hexdigest(),bytes=len(content),
        sha256=hashlib.sha256(content).hexdigest(),local_path=str(path.relative_to(ROOT)))
    sidecar.write_text(json.dumps(record,indent=2)+"\n")
    return record

def combine_acs():
    tables=[]
    for table in ["B01003","B19013","B17001","B08201","B03002","B01001"]:
        frame=pd.read_csv(ROOT/f"data/raw/acs2022_{table.lower()}_philadelphia.dat",sep="|",dtype=str)
        # Remove possible trailing delimiter column; retain exact E/M cells.
        frame=frame.loc[:,~frame.columns.str.startswith("Unnamed")]
        frame=frame.rename(columns={c:re.sub(r"_(E|M)(\d+)$",lambda m:"_"+m[2]+m[1],c) for c in frame.columns})
        tables.append(frame.set_index("GEO_ID"))
    merged=pd.concat(tables,axis=1,join="outer")
    if merged.index.duplicated().any() or merged.isna().any().any():raise ValueError("ACS table join incomplete")
    geoid=merged.index.str.replace("1400000US","",regex=False)
    merged["NAME"]=[f"Census tract {g[5:]}, Philadelphia County, Pennsylvania" for g in geoid]
    merged["state"]=geoid.str[:2];merged["county"]=geoid.str[2:5];merged["tract"]=geoid.str[5:]
    columns=["NAME"]+ESTIMATES+[s[:-1]+"M" for s in ESTIMATES]+["state","county","tract"]
    normalized=merged[columns]
    path=ROOT/"data/raw/acs_2022_philadelphia.json"
    path.write_text(json.dumps([columns]+normalized.values.tolist())+"\n")
    return dict(id="acs_2022_normalized",status="derived_from_downloaded_bulk_tables",rows=len(normalized),
        local_path=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    results=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[(item,pool.submit(fetch,item,args.refresh)) for item in specs() if item["id"]!="acs_2022"]
        futures += [(dict(id=f"acs2022_{table}"),pool.submit(fetch_acs_table,table,args.refresh))
                    for table in ["B01003","B19013","B17001","B08201","B03002","B01001"]]
        for item, future in futures:
            try: result=future.result()
            except Exception as exc: result=dict(item,status="failed",error=str(exc))
            results.append(result)
            print(result["id"], result["status"], result.get("bytes",result.get("error")), flush=True)
    if all(r["status"]=="downloaded" for r in results if r["id"].startswith("acs2022_")):
        results.append(combine_acs())
    (ROOT/"data").mkdir(exist_ok=True)
    (ROOT/"data/source_manifest.json").write_text(json.dumps(results,indent=2)+"\n")
    if any(r["status"] == "failed" for r in results): raise SystemExit(1)

if __name__ == "__main__": main()
