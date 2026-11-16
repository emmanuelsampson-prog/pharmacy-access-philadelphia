"""Export the academic Word report to PDF using LibreOffice.

The original PDF filename is retained to preserve published links. Install
LibreOffice and place soffice/libreoffice on PATH, or pass --office PATH.
"""
from pathlib import Path
import argparse
import shutil
import subprocess
import tempfile
from report_content import OUT

parser=argparse.ArgumentParser()
parser.add_argument('--office',default=shutil.which('libreoffice') or shutil.which('soffice'))
args=parser.parse_args()
if not args.office:
    raise SystemExit('LibreOffice is required for PDF export. Install it or use --office PATH.')
source=OUT/'Pharmacy_Access_Research_Report.docx'
if not source.exists():
    raise SystemExit('Build the Word report first with python scripts/build_submission.py')
with tempfile.TemporaryDirectory(prefix='pharmacy-report-') as tmp:
    tmp=Path(tmp)
    command=[args.office,'-env:UserInstallation='+str((tmp/'profile').as_uri()),'--headless','--convert-to','pdf','--outdir',str(tmp),str(source)]
    result=subprocess.run(command,capture_output=True,text=True,timeout=120)
    pdf=tmp/(source.stem+'.pdf')
    if result.returncode or not pdf.exists():raise RuntimeError(result.stderr or result.stdout)
    target=OUT/'Pharmacy_Access_Project_Brief.pdf'
    shutil.copyfile(pdf,target)
    print(target)
