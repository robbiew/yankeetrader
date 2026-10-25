from pathlib import Path
import sys,shutil
sys.path.insert(0,'analysis/yt-maint');from experiments import put
r=Path('analysis/yt-combat/experiments')
for name in ['takeall','transfer','bank-deposit','bank-withdraw','bank-negative','bank-over','invest1','invest251','foreign','team','unguarded','create','poor']:
 d=r/('fixture-planet-'+name);shutil.copytree(r/'fixture-trade-high',d);b=bytearray((d/'YTDATA.DAT').read_bytes())
 for o,v in {57:100,65:100,69:10,73:20,77:30,81:100000,89:0,97:7,113:9,121:15,129:8}.items():put(b,2,o,v)
 put(b,151,93,2);put(b,151,81,0);put(b,151,85,0)
 rec=4053;p=(rec-1)*137;b[p:p+137]=bytes(137);b[p:p+41]=b'Test Planet'.ljust(41,b' ')
 vals={41:297,45:10,49:20,53:30,57:100,61:200,65:300,69:70,73:2,77:100,85:11,89:0,113:90,117:0,125:80,129:600}
 if name.startswith('bank-'):vals[117]=10000
 if name in ['foreign','team','unguarded']:vals[73]=3
 if name=='unguarded':vals[77]=0
 if name=='team':put(b,2,89,1);put(b,3,89,1)
 for o,v in vals.items():put(b,rec,o,v)
 if name in ['create','poor']:
  put(b,151,93,0)
  if name=='poor':put(b,2,81,24999)
 (d/'YTDATA.DAT').write_bytes(b);(d/'before.dat').write_bytes(b)
for name,src in [('bank-halfday','bank-withdraw'),('unguarded-bank','unguarded'),('team-bank','team'),('move-collision','transfer'),('full','create')]:
 d=r/('fixture-planet-'+name);shutil.copytree(r/('fixture-planet-'+src),d);b=bytearray((d/'YTDATA.DAT').read_bytes())
 if name in ['bank-halfday','unguarded-bank','team-bank']:put(b,4053,117,1000000 if name=='bank-halfday' else 10000)
 if name=='bank-halfday':put(b,4053,41,296);put(b,4053,89,720)
 if name=='move-collision':b[(4054-1)*137:4054*137]=b[(4053-1)*137:4053*137];put(b,152,93,3)
 if name=='full':
  for p in range(4053,4152):put(b,p,85,1)
 (d/'YTDATA.DAT').write_bytes(b);(d/'before.dat').write_bytes(b)
for name,src in [('bank-large','bank-deposit'),('lazy-production','transfer')]:
 d=r/('fixture-planet-'+name);shutil.copytree(r/('fixture-planet-'+src),d);b=bytearray((d/'YTDATA.DAT').read_bytes())
 if name=='bank-large':put(b,2,81,100000000);put(b,4053,117,0)
 else:
  for o,v in {41:296,89:720,45:1000,49:2000,53:3000,57:0,61:0,65:0,69:0,125:0,113:0,129:0}.items():put(b,4053,o,v)
 (d/'YTDATA.DAT').write_bytes(b);(d/'before.dat').write_bytes(b)
