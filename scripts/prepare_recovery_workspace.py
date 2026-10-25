"""Copy the immutable archive into the layout expected by historical tools."""
import argparse
from pathlib import Path
import shutil

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('destination', type=Path)
args = parser.parse_args()
archive = Path(__file__).resolve().parents[1] / 'archive'
args.destination = args.destination.resolve()
if args.destination.is_relative_to(archive.resolve()):
    parser.error('choose a destination outside the preserved archive')
args.destination.mkdir(parents=True, exist_ok=False)
shutil.copytree(archive / 'analysis', args.destination / 'analysis')
for source in (archive / 'dos-original').iterdir():
    shutil.copy2(source, args.destination / source.name)
shutil.copy2(archive / 'references/ytcalc.xls', args.destination / 'ytcalc.xls')
print(f'Prepared recovery workspace at {args.destination.resolve()}')
