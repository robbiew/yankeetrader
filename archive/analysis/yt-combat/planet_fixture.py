from pathlib import Path
import shutil,sys
sys.path.insert(0,str(Path('analysis/yt-maint').resolve()))
from experiments import put
ROOT=Path('analysis/yt-combat').resolve()
d=ROOT/'experiments/fixture-planet';shutil.copytree(ROOT/'experiments/fixture-plasma',d)
b=bytearray((d/'YTDATA.DAT').read_bytes());put(b,152,81,0);put(b,152,85,0);put(b,152,93,1)
r=4052;b[(r-1)*137:r*137]=bytes(137);b[(r-1)*137:(r-1)*137+41]=b'Target '+b' '*34
for off,v in {41:297,45:10000,49:10000,53:10000,73:3,77:5000,85:7,89:0}.items():put(b,r,off,v)
(d/'YTDATA.DAT').write_bytes(b);(d/'before.dat').write_bytes(b)
