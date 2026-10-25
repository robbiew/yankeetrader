"""Package recovery notes and compact original-DOS planet evidence, excluding EXEs."""
from pathlib import Path
import argparse,shutil,gzip,json,hashlib
p=argparse.ArgumentParser();p.add_argument('archive',type=Path);a=p.parse_args().archive
root=Path(__file__).resolve().parents[1];out=root/'research';out.mkdir(exist_ok=True)
for folder in ['yt-init','yt-maint','yt-combat','yt-missiles','yt-ships','yt-trade','yt-genesis','yt-planets','yt-teams','ytcalc','dos-validation']:
 src=a/'analysis'/folder
 for name in ['RECOVERY.md','RESULTS.md','FINDINGS.md','recovered_rules.py','recovered-genesis.bas','recovered-management.txt','scenarios.json']:
  if (src/name).exists():
   dest=out/folder/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src/name,dest)
for name in ['ISSUES_AND_EXPLOITS.md','RECONSTRUCTION_PLAN.md','executable-inventory.json']:
 text=(a/'analysis'/name).read_text();(out/name).write_text(text.replace('../modern/','../'))
for module in ['main','sub','sub2']:
 dest=out/'yt-combat'/module/'qb-annotated.txt';dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(a/'analysis/yt-combat'/module/'qb-annotated.txt',dest)
manifest={}
for name in json.loads((a/'analysis/yt-planets/scenarios.json').read_text())['validated']:
 src=a/'analysis/yt-combat/experiments'/name;dest=out/'yt-combat/experiments'/name;dest.mkdir(parents=True,exist_ok=True)
 for filename in ['before.dat','YTDATA.DAT','GAME.LOG','KEYS.TXT']:
  data=(src/filename).read_bytes();compressed=dest/(filename+'.gz');compressed.write_bytes(gzip.compress(data,mtime=0));manifest[str(compressed.relative_to(out))]={'sha256':hashlib.sha256(data).hexdigest(),'uncompressed_bytes':len(data)}
(out/'planet-snapshots.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(f'Packaged {len(manifest)} compressed evidence files; archival executables remain in Downloads.')
