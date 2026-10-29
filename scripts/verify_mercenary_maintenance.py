"""Check original DOS maintenance provenance and Mercenary economic/action evidence."""
import argparse,gzip,hashlib,json,math,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--evidence',type=Path,default=ROOT/'research/yt-mercenary-maintenance/dos');args=parser.parse_args()
sha=lambda b:hashlib.sha256(b).hexdigest()
def n(data,r,o):
 raw=data[(r-1)*137+o:(r-1)*137+o+4];m=int.from_bytes(raw[:3],'little')
 return 0 if not raw[3] else (-1 if m&0x800000 else 1)*(1+(m&0x7fffff)/2**23)*2.0**(raw[3]-129)
def put(data,r,o,v):
 raw=bytes(4)
 if v:
  f,e=math.frexp(abs(v));m=round((f*2-1)*2**23)
  if m==2**23:m=0;e+=1
  raw=(m|(0x800000 if v<0 else 0)).to_bytes(3,'little')+bytes([e+128])
 a=(r-1)*137+o;data[a:a+4]=raw

def groups(data,owner=-2):return [(s,n(data,51+s,81)) for s in range(1,3001)if n(data,51+s,85)==owner and n(data,51+s,81)>0]
def total(data,owner=-2):return sum(v for _,v in groups(data,owner))

def hiring(tax):
 budget=tax//10
 return (0,0,0) if budget<1 else (1,budget,budget) if budget<10 else (10,budget//10,10*(budget//10))

original=(ROOT/'archive/analysis/dos-validation/evidence/YTDATA.DAT').read_bytes()
player_source=(ROOT/'archive/analysis/yt-combat/experiments/fixture-team-captain/YTDATA.DAT').read_bytes()
exe=(ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes();runtime=(ROOT/'archive/dos-original/BRUN30.EXE').read_bytes()
assert sha(exe)=='8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6'
assert sha(runtime)=='3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8'
base=bytearray(original)
for r in range(2,52):base[(r-1)*137:r*137]=bytes(137);put(base,r,109,-1)
for sector in range(1,3001):
 for o in (81,85,93,105,129):put(base,51+sector,o,0)
for port in range(3052,4052):put(base,port,89,0);put(base,port,97,0)
for r in range(4052,4152):base[(r-1)*137:r*137]=bytes(137)
for slot,label,owner in ((1,'The Wanderer',0),(2,'Probe Planet',0),(99,'Mercenary Base',-2),(100,'Xannoron',-1)):
 r=4051+slot;a=(r-1)*137;base[a:a+41]=label.encode().ljust(41,b' ')
 for o,v in ((41,298),(73,owner),(77,1),(85,len(label)),(89,0),(117,1)):put(base,r,o,v)
for r,o,v in ((2050,93,1),(2051,93,99),(1165,93,100),(1,117,1114),(52,105,1114)):put(base,r,o,v)
base=bytes(base)
assert gzip.decompress((args.evidence/'baseline.dat.gz').read_bytes())==base,'baseline recipe differs'
travel={(151,41):101,(151,45):0,(151,49):0,(151,53):0,(151,57):0,(151,61):0,(151,81):100,(151,85):-2}
expected={f'tax-{t}':{(3053,89):t*10}for t in (0,9,10,19,90,99,100,109,110,199,200,100112)}
expected.update({
 'tax-next-day':{},'split-tax-9':{(3053,89):95,(3054,89):5},'split-tax-10':{(3053,89):95,(3054,89):15},
 'union-only-spawn':{(1165,81):1,(1165,85):-1,(3053,89):100},'capacity-blocked':{(1165,81):1,(1165,85):-1,(3053,89):1000},
 'earth-tax-excluded':{(3052,89):1000000},'move-empty':travel,'move-zero-warp':{**travel,(151,41):0},
 'merge':{(152,41):100,(152,45):0,(152,49):0,(152,53):0,(152,57):0,(152,61):0,(151,81):100,(151,85):-2,(152,81):200,(152,85):-2},
 'mine-kill-remainder':{**travel,(152,129):3},'mine-one':{**travel,(152,129):1},'mine-large-force':{**travel,(151,81):100000,(152,129):3},
 'xannor-defense':{**travel,(152,81):50,(152,85):-1},'large-xannor-battle':{**travel,(151,81):20000,(152,81):15000,(152,85):-1},
 'human-defense':{**travel,(152,81):50,(152,85):2},'human-strong-defense':{**travel,(152,81):1000,(152,85):2},
 'desert-one':{(151,81):1,(151,85):2},'desert-hundred':{(151,81):100,(151,85):2},
 'planet-neutral':{**travel,(152,93):2,(4053,73):0,(4053,129):37},
 'planet-human':{**travel,(152,93):2,(4053,73):2,(4053,129):37},
 'planet-strong-ground':{**travel,(152,93):2,(4053,73):2,(4053,77):500000,(4053,129):37},
 'planet-human-guarded':{**travel,(152,93):2,(4053,73):2,(4053,129):37,(152,81):1000,(152,85):2},
 'planet-xannor-guarded':{**travel,(152,93):2,(4053,129):37,(152,81):50,(152,85):-1},
 'planet-held':{**travel,(151,93):2,(4053,73):-2,(4053,129):37},
 'planet-human-origin':{**travel,(151,93):2,(4053,73):2,(4053,129):37},
 'base-missing-reference':{(2051,93):0},'base-orphan-reference':{(4150,85):0},
 'base-captured':{(4150,73):2,(4150,77):123,(4150,117):1234},
 'base-zero-reserves':{(4150,77):0,(4150,117):0},'base-positive-reserves':{(4150,77):1,(4150,117):1},
})
human={'union-only-spawn','capacity-blocked','human-defense','human-strong-defense','desert-one','desert-hundred','planet-human','planet-strong-ground','planet-human-guarded','planet-human-origin','base-captured'}
manifest=json.loads((args.evidence/'results.json').read_text());cases=manifest['scenarios'];recipe='mercenary-maintenance-isolation-v1'
assert manifest['recipe']==recipe and len(cases)==len(expected) and {c['name'] for c in cases}==set(expected)
for c in cases:
 name=c['name'];d=args.evidence/name
 assert c==json.loads((d/'result.json').read_text()) and c['recipe']==recipe,name
 assert c['source_sha256']==sha(original) and c['baseline_sha256']==sha(base),name
 assert c['executable_sha256']==sha(exe) and c['runtime_sha256']==sha(runtime),name
 date='10/26/2026' if name=='tax-next-day' else '10/25/2026'
 assert c['date']==date and c['time']=='00:00:00',name
 assert set(c['files'])=={'before.dat.gz','after.dat.gz','transcript.txt','dosbox.log','DOSDATE.LOG','DOSTIME.LOG'},name
 for file,digest in c['files'].items():assert sha((d/file).read_bytes())==digest,(name,file)
 assert ('Current date: '+('Mon 'if name=='tax-next-day' else 'Sun ')+date) in (d/'DOSDATE.LOG').read_text(),name
 assert '0:00:00.00am' in (d/'DOSTIME.LOG').read_text(),name
 before=gzip.decompress((d/'before.dat.gz').read_bytes());after=gzip.decompress((d/'after.dat.gz').read_bytes())
 assert len(before)==len(after)==568687 and sha(before)==c['before_sha256'] and sha(after)==c['after_sha256'],name
 patches={(r,o):v for r,o,v in c['patches']}
 assert len(patches)==len(c['patches']) and patches==expected[name],(name,'unexpected fixture override')
 if name=='tax-next-day':
  assert c['parent']=='tax-199' and not c.get('human') and not c.get('dense_defense'),name
  rebuilt=bytearray(gzip.decompress((args.evidence/'tax-199/after.dat.gz').read_bytes()))
 else:
  assert not c.get('parent'),name;rebuilt=bytearray(base)
  assert bool(c.get('human'))==(name in human),name
  if name in human:
   rebuilt[137:274]=player_source[137:274]
   for o,v in ((41,297),(45,0),(57,7),(89,0),(109,0)):put(rebuilt,2,o,v)
  assert bool(c.get('dense_defense'))==(name in ('union-only-spawn','capacity-blocked')),name
  assert bool(c.get('empty_union'))==(name=='union-only-spawn'),name
  if c.get('dense_defense'):
   for sector in range(2,3001):put(rebuilt,51+sector,81,1000);put(rebuilt,51+sector,85,2)
  if name=='union-only-spawn':
   for sector in range(2,8):put(rebuilt,51+sector,81,0);put(rebuilt,51+sector,85,0)
 for (r,o),v in patches.items():put(rebuilt,r,o,v)
 assert bytes(rebuilt)==before,(name,'undeclared fixture mutation')
 text=(d/'transcript.txt').read_text();start=text.index('Mercenary Maintenance...')
 body=text[start:text.find('Running Super Planet Lottery') if 'Running Super Planet Lottery' in text else len(text)]
 blocked=name=='capacity-blocked'
 assert bool(c.get('expect_timeout'))==blocked and c['timed_out']==blocked and c['complete']==(not blocked),name
 assert c['timeout_seconds']==(8 if blocked else 45),name
 assert ('Daily Maintenance Completed OK' in text)==(not blocked),name
 if blocked:
  assert 'Checking for Mercenary Planet' in body and 'government has hired' not in body and n(after,3053,89)==900,name
  assert not groups(before) and not groups(after),name
  continue
 # Tax each ordinary port separately and exclude Earth. Later phases do not
 # spend port treasuries in these fixtures, so every debit is directly checkable.
 taxes=sum(math.floor(n(before,r,89)/10) for r in range(3053,4052))
 assert n(after,3052,89)==n(before,3052,89),name
 for r in range(3053,4052):assert n(after,r,89)==n(before,r,89)-math.floor(n(before,r,89)/10),(name,'port debit',r)
 reported=re.search(r'goverment has collected (\d+) credits tax',text)
 assert (int(reported[1]) if reported else 0)==taxes,name
 count,size,hires=hiring(taxes)
 report=re.search(r'government has hired (\d+) mercenaries',body)
 assert (int(report[1]) if report else 0)==hires,(name,'hiring/remainder')
 if name.startswith('tax-') or name.startswith('split-tax-'):
  battles=re.findall(r'\*\*\* (\d+) Mercenaries attacking (\d+) fighters[^\n]*\n\s*\*\*\* The Mercenaries (Won|Lost)!',body)
  assert all(result=='Lost' for _,_,result in battles),name
  assert 'captured planet' not in body and 'Mercenaries taking' not in body,name
  losses=sum(int(force)for force,_,_ in battles)
  assert total(after)==total(before)+hires-losses,(name,'hired strength versus later losses')
 if name=='tax-next-day':assert taxes==179 and hires==10,name
 if name=='union-only-spawn':
  origins=list(map(int,re.findall(r'1 Mercenaries moving from sector (\d+)',body)))
  assert origins and 2<=origins[0]<=7 and hires==1,name
 if name=='move-empty':
  assert total(after)==100 and n(after,151,81)==n(after,151,85)==0,name
  destination=groups(after)[0][0]
  assert destination not in [n(before,151,o)for o in range(41,65,4)],(name,'bounded multi-hop control')
 if name=='move-zero-warp':
  failed_goal=int(re.search(r'Sector path not found - from sector 100 to sector\s+(\d+)',body)[1])
  assert groups(after)==[(failed_goal,100)] and failed_goal!=100 and all(n(before,151,o)==0 for o in range(41,65,4)),(name,'unreachable-path teleport evidence')
 if name=='merge':assert len(groups(after))==1 and total(after)==300 and n(after,151,81)==n(after,152,81)==0,name
 if name=='mine-kill-remainder':
  assert total(after)==0 and n(after,152,129)==2 and 'mercenariers were killed!' in body,name
 if name in ('mine-one','mine-large-force'):
  assert n(after,152,129)==0 and 'hit sector mines in sector 101' in body,name
  if name=='mine-one':assert total(after)==0 and 'mercenariers were killed!' in body,name
  else:
   lost=int(re.search(r'Lost a total of (\d+) fighters',body)[1]);assert 0<lost<100000 and total(after)==100000-lost,name
 if name in ('xannor-defense','large-xannor-battle','planet-xannor-guarded'):
  assert 'beloning to The Xannor!' in body and 'The Mercenaries Won!' in body,name
  assert n(after,152,81)==n(after,152,85)==0 and 0<total(after)<total(before),name
 if name in ('human-strong-defense','planet-human-guarded'):
  assert total(after)==0 and n(after,152,85)==2 and n(after,152,81)==1100 and 'joined Q ' in body,name
 if name=='human-defense':assert total(after)==150 and '50 fighters in sector 101' in body and 'joined the mercs!' in body,name
 if name=='desert-one':assert total(after)==1 and '1 fighters in sector 100' in body and 'joined the mercs!' in body,name
 if name=='desert-hundred':assert total(after)==0 and n(after,151,81)==100 and n(after,151,85)==2 and 'joined the mercs!' not in body,name
 if name in ('planet-neutral','planet-human','planet-strong-ground'):
  assert groups(after)==[(101,137)] and 'captured planet Probe Planet!' in body and 'taking 37 fighters' in body,name
  assert n(after,4053,129)==0 and n(after,4053,73)==n(before,4053,73) and n(after,4053,77)==n(before,4053,77),(name,'title/ground versus capture wording')
 if name in ('planet-held','planet-human-origin'):
  assert groups(after)==[(100,100)] and n(after,4053,129)==37 and 'moving from sector 100' not in body,name
 if name in ('planet-human-guarded','planet-xannor-guarded'):assert n(after,4053,129)==37 and 'taking 37 fighters' not in body,name
 if name.startswith('base-'):
  assert n(after,4150,73)==-2,name
  if name in ('base-missing-reference','base-zero-reserves'):
   assert n(after,4150,77)==150000 and n(after,4150,117)==25000000,name
  if name=='base-missing-reference':
   assert n(after,4150,85)==14 and all(n(after,4150,o)==100000 for o in (45,49,53)) and 'built a home base' in body,name
   assert sum(n(after,51+s,93)==99 for s in range(1,3001))==1,name
  elif name=='base-orphan-reference':assert n(after,4150,85)==0 and 'built a home base' not in body,name
  elif name=='base-captured':assert n(after,4150,77)==123 and n(after,4150,117)==1234 and 'built a home base' not in body,name
  elif name=='base-positive-reserves':assert n(after,4150,77)==1 and n(after,4150,117)==1,name

# Reconstruct Ghidra's DOS load module including MZ segment fixups.
header=struct.unpack_from('<H',exe,8)[0]*16;image=bytearray(exe[header:])
relocations=struct.unpack_from('<H',exe,6)[0];table=struct.unpack_from('<H',exe,24)[0]
for i in range(relocations):
 offset,segment=struct.unpack_from('<HH',exe,table+4*i);at=16*segment+offset
 struct.pack_into('<H',image,at,(struct.unpack_from('<H',image,at)[0]+0x1000)&0xffff)
records=json.loads((ROOT/'research/yt-mercenary-maintenance/rea/phase-paths.json').read_text())['records']
ranges={'0x14478':145,'0x14534':182,'0x14804':117,'0x149d4':107,'0x14c7f':123,'0x14fb1':75,'0x1504e':175,'0x143e9':121,'0x15318':66,'0x17939':159,'0x14a78':83}
assert len(records)==len(ranges)
for r in records:
 v=r['normalized_result'];start=int(v['address'],16)-0x10000
 assert r['subject']['digest']['sha256']==sha(exe) and r['operation']=='read_bytes'
 assert v['complete'] and v['requested_bytes']==ranges[v['address']] and bytes.fromhex(v['bytes_hex'])==image[start:start+v['requested_bytes']]
for address,value in ((0x87de,.66),(0x88de,.95),(0x8520,.5),(0x891e,150)):
 raw=exe[0x8e30+address-0x7e60:0x8e30+address-0x7e60+4];mant=int.from_bytes(raw[:3],'little')
 observed=(-1 if mant&0x800000 else 1)*(1+(mant&0x7fffff)/2**23)*2.0**(raw[3]-129)
 assert abs(observed-value)<1e-6,(hex(address),observed)
raw=exe[0x8e30+0x8916-0x7e60:0x8e30+0x8916-0x7e60+8];mant=int.from_bytes(raw[:7],'little')
assert (1+(mant&((1<<55)-1))/2**55)*2.0**(raw[7]-129)==200
print(f'Verified {len(cases)-1} completed DOS Mercenary maintenance runs, one bounded hiring-capacity timeout, exact next-day chain, tax/action accounting and {len(records)} REA observations.')

# Derived-rule boundary checks are illustrative RNG controls, not DOS random replay.
import importlib.util
spec=importlib.util.spec_from_file_location('rules',ROOT/'research/yt-mercenary-maintenance/recovered_rules.py')
rules=importlib.util.module_from_spec(spec);spec.loader.exec_module(rules)
assert rules.mine_loss(100000,3,lambda:.5)==(92497,7503,3)
assert rules.mine_loss(100,3,lambda:.5)==(0,100,1)
assert rules.mine_loss(5,3,lambda:0)==(2,3,3)
assert rules.defense_battle(201,201,lambda:0)==(201,0,52)
assert rules.defense_battle(201,201,lambda:.5)==(0,201,52)
assert rules.defense_battle(200,201,lambda:0)==(200,0,201)
assert rules.defense_battle(201,200,lambda:0)==(201,0,200)
for tax in (0,9,10,19,90,99,100,109,110,199,200,100112):
 assert sum(rules.hire_plan(tax))==hiring(tax)[2]
for invalid in (-.1,1,float('nan')):
 try:rules.mine_loss(1,1,lambda:invalid)
 except ValueError:pass
 else:raise AssertionError('invalid RNG accepted')
