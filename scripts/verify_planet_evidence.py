"""Verify packaged original-DOS snapshot hashes and golden-file provenance."""
from pathlib import Path
import gzip,json,hashlib
root=Path(__file__).resolve().parents[1];research=root/'research'
manifest=json.loads((research/'planet-snapshots.json').read_text())
for name,entry in manifest.items():
 raw=gzip.decompress((research/name).read_bytes())
 assert len(raw)==entry['uncompressed_bytes'],name
 assert hashlib.sha256(raw).hexdigest()==entry['sha256'],name
for case in json.loads((root/'internal/game/testdata/dos-planets.json').read_text()):
 path='yt-combat/experiments/planet-'+case['name']+'/'
 assert manifest[path+'before.dat.gz']['sha256']==case['before_sha256']
 assert manifest[path+'YTDATA.DAT.gz']['sha256']==case['after_sha256']
print(f'Verified {len(manifest)} packaged evidence files and provenance for 19 planet golden scenarios.')
