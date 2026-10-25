"""Export compact golden snapshots from the preserved original-DOS experiment tree."""
from pathlib import Path
import argparse,sys,hashlib,json,datetime
parser=argparse.ArgumentParser();parser.add_argument('archive',type=Path);args=parser.parse_args()
sys.path.insert(0,str(args.archive/'analysis/yt-maint'));from experiments import get
base=args.archive/'analysis/yt-combat/experiments';epoch=datetime.datetime(2026,10,24,tzinfo=datetime.timezone.utc)
def stamp(b,rec):return (epoch+datetime.timedelta(days=get(b,rec,41)-297,minutes=get(b,rec,89))).isoformat().replace('+00:00','Z')
def player(b,rec):
 return {'ID':rec,'Identity':f'dos:{rec}','Alias':'Q' if rec==2 else 'Enemy','Sector':int(get(b,rec,57)),'Credits':int(get(b,rec,81)),'Turns':int(get(b,rec,49)),'Holds':max(10,int(get(b,rec,65))),'Fighters':int(get(b,rec,61)),'Ground':int(get(b,rec,121)),'Shields':int(get(b,rec,53)),'Cargo':[int(get(b,rec,o)) for o in [69,73,77]],'Missiles':int(get(b,rec,97)),'Mines':int(get(b,rec,129)),'Plasma':int(get(b,rec,113)),'Team':int(get(b,rec,89))}
def planet(b,rec):
 p=(rec-1)*137
 return {'ID':rec-4051,'Sector':100,'Owner':int(get(b,rec,73)),'Name':b[p:p+41].decode('cp437').strip(),'Updated':stamp(b,rec),'Production':[get(b,rec,o) for o in [45,49,53]],'Cargo':[get(b,rec,o) for o in [57,61,65]],**{name:get(b,rec,off) if name not in ['Bank','Ground'] else int(get(b,rec,off)) for name,off in [('Bank',117),('Ground',77),('Fighters',129),('Missiles',69),('Mines',125),('Plasma',113)]}}
names=['takeall','transfer-cargo','transfer-weapons','create','poor','full','bank-deposit','bank-withdraw','bank-negative','bank-over','bank-halfday','invest1','invest251','foreign','team-bank','unguarded-bank','lazy-production','bank-large','bank-large-relogin']
out=[]
for n in names:
 d=base/('planet-'+n);a=(d/'before.dat').read_bytes();b=(d/'YTDATA.DAT').read_bytes();rec=4051+int(get(b,151,93)) if n=='create' else 4053
 out.append({'name':n,'source':str(d.relative_to(args.archive)),'before_sha256':hashlib.sha256(a).hexdigest(),'after_sha256':hashlib.sha256(b).hexdigest(),'now':stamp(b,rec),'player':player(a,2),'other':player(a,3),'before':planet(a,4053),'after':planet(b,rec),'player_after':player(b,2)})
target=Path(__file__).resolve().parents[1]/'internal/game/testdata/dos-planets.json';target.write_text(json.dumps(out,indent=2)+'\n');print(f'Exported {len(out)} original DOS snapshots into {target.name}.')
