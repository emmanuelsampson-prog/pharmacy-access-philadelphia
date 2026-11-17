"""Package the same open font used in the Python figures for the web chart."""
from pathlib import Path
import shutil
import matplotlib
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/public'
source = Path(matplotlib.get_data_path()) / 'fonts/ttf'
for name in ['DejaVuSans', 'DejaVuSans-Bold']:
    font = TTFont(source / f'{name}.ttf')
    font.flavor = 'woff'
    font.save(OUT / f'{name}.woff')
shutil.copyfile(source / 'LICENSE_DEJAVU', OUT / 'DejaVu-Font-License.txt')
print('Packaged DejaVu Sans web fonts and their license')
