"""Verify hostility memory, reconnect, planet and RNG-advancement DOS controls."""
import argparse,gzip,hashlib,json,math,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--evidence',type=Path,default=ROOT/'research/yt-mercenaries/hostility-dos');args=parser.parse_args()
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
source=(ROOT/'archive/analysis/yt-combat/experiments/fixture-team-captain/YTDATA.DAT').read_bytes()
exe=(ROOT/'archive/dos-original/YT.EXE').read_bytes();feeder=(ROOT/'archive/analysis/yt-combat/KEYFEED.COM').read_bytes()
assert sha(exe)=='c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037'
base_graph={100:[101,102,103,104,105,106],101:[107],102:[108],103:[100],104:[100],105:[100],106:[100],107:[109],108:[109],109:[110],110:[100]}
commands={
 'partial':'M;101\r~~A;10\r~~~~B\r~~50000','fresh':'M;101\r~~B\r~~50000',
 'cross-merc':'M;101\r~~A;2000\r~~~~M;107\r~~B\r~~50000',
 'cross-human':'M;101\r~~A;2000\r~~~~Y\r~~~~M;107\r~~B\r~~50000',
 'neutral-planet':'M;101\r~~B','foreign-planet':'M;101\r~~B',
 'stop-after-partial':'M;101\r~~A;10','reconnect':'B\r~~50000',
 **{f'clock-{h:02d}':'M;101\r~~B\r~~50000' for h in range(1,9)},
 **{f'scan-{i:02d}':'S;'*i+'M;101\r~~B\r~~50000' for i in range(1,9)},
}
cases=json.loads((args.evidence/'results.json').read_text())['scenarios']
assert len(cases)==len(commands) and {c['name'] for c in cases}=={'npc-hostility-'+s for s in commands}
by_name={c['name']:c for c in cases}
for c in cases:
 name=c['name'];short=name.removeprefix('npc-hostility-');d=args.evidence/name
 assert c==json.loads((d/'result.json').read_text()) and c['command']==commands[short],name
 assert c['executable_sha256']==sha(exe) and c['keyfeed_sha256']==sha(feeder),name
 for key,file in [('keys','KEYS.TXT'),('transcript','transcript.txt'),('dosbox_log','dosbox.log')]:assert sha((d/file).read_bytes())==c[key+'_sha256'],(name,file)
 assert (d/'KEYS.TXT').read_bytes()==b'\r~~~~~\r~'+c['command'].encode()+b'\r~~~~'+b'\rQ;Y\r~~'*24,name
 before=gzip.decompress((d/'before.dat.gz').read_bytes());after=gzip.decompress((d/'after.dat.gz').read_bytes())
 for label,data in [('before',before),('after',after)]:
  assert len(data)==568687 and sha(data)==c[label+'_sha256'],(name,label)
  assert n(data,2,57)==c['sector_'+label] and n(data,2,49)==c['turns_'+label],name
 if short=='reconnect':
  parent='npc-hostility-stop-after-partial';prior=gzip.decompress((args.evidence/parent/'after.dat.gz').read_bytes())
  assert before==prior and c['source_sha256']==sha(prior) and c['patches']==[],name
 else:
  assert c['source_sha256']==sha(source),name
  graph={**base_graph,100:[101,103]} if short.startswith('scan-') else base_graph
  assert c['graph']=={str(k):v for k,v in graph.items()},name
  expected={(2,93):0,(2,61):2000,(152,81):100,(152,85):-2}
  if short in ('partial','fresh','stop-after-partial'):expected[(152,81)]=1000
  if short.startswith('cross-'):expected.update({(158,81):100,(158,85):-2})
  if short=='cross-human':expected[(152,85)]=3
  if short.endswith('-planet'):expected.update({(152,93):2,(4053,73):0 if short=='neutral-planet' else 3})
  if short.startswith(('clock-','scan-')):expected[(2,61)]=10
  if short.startswith('scan-'):expected[(3,125)]=.5
  assert {(p['record'],p['offset']):p['value'] for p in c['patches']}==expected,name
  rebuilt=bytearray(source)
  for sector,warps in graph.items():
   r=51+sector;rebuilt[(r-1)*137:r*137]=bytes(137)
   for o,target in zip(range(41,65,4),warps):put(rebuilt,r,o,target)
  defaults=[(2,{45:0,49:500,57:100,89:0,105:0,125:0}),(3,{45:0,57:103,61:42,53:7,89:0,125:0}),(152,{65:2}),(3053,{93:101}),(153,{93:2}),(4053,{73:0,77:12})]
  for r,fields in defaults:
   for o,v in fields.items():put(rebuilt,r,o,v)
  for (r,o),v in expected.items():put(rebuilt,r,o,v)
  assert bytes(rebuilt)==before,(name,'undeclared fixture change')
 time=f'{int(short[-2:]):02d}:00:00' if short.startswith('clock-') else '00:00:00'
 assert c['dos_time']==time,name
 text=(d/'transcript.txt').read_text();assert 'Returning to Yankee Trader Local Logon Program' in text,name
 accepted='Good Deal! We join up with you!' in text;hostile='We just want your miserable life' in text
 if short in ('partial','cross-merc'):assert hostile and not accepted,name
 elif short.endswith('-planet'):assert 'This planet is OURS!' in text and not accepted and not hostile,name
 elif short=='stop-after-partial':assert not accepted and not hostile and n(after,152,81)>0,name
 else:assert accepted or hostile,(name,'bribe command never reached negotiation')
 assert n(after,2,81)==n(before,2,81)-(50000 if accepted else 0),name
 losses=sum(map(int,re.findall(r'You lost (\d+) fighter\(s\)',text)))
 surrendered=sum(map(int,re.findall(r'(\d+) fighters surrendered!',text)))
 recruited=0
 if accepted:recruited=n(before,152 if short!='cross-human' else 158,81)
 assert n(after,2,61)==n(before,2,61)-losses+surrendered+recruited,(name,'fighter conservation')
 spent=0 if short=='reconnect' else 2 if short.startswith('cross-') else 1
 assert n(after,2,49)==n(before,2,49)-spent,name
 if short in ('partial','cross-merc','fresh','cross-human','reconnect') or accepted:
  target=158 if short.startswith('cross-') else 152
  assert n(after,target,81)==n(after,target,85)==0,name
 if short=='stop-after-partial':assert n(after,152,81)==n(before,152,81)-sum(map(int,re.findall(r'You destroyed (\d+) enemy fighters\.',text))),name
 if short.startswith('cross-'):assert n(after,152,81)==n(after,152,85)==0,name
 assert n(after,2,45)==0,name
records=json.loads((ROOT/'research/yt-mercenaries/rea/hostility-path.json').read_text())['records'];assert len(records)==3
header=struct.unpack_from('<H',exe,8)[0]*16
for r in records:
 v=r['normalized_result'];start=header+int(v['address'],16)-0x10000
 assert r['subject']['digest']['sha256']==sha(exe) and v['complete'] and bytes.fromhex(v['bytes_hex'])==exe[start:start+v['requested_bytes']]
print(f'Verified {len(cases)} DOS hostility sessions, exact reconnect chain, faction memory, planet controls and three REA observations.')
runtime=(ROOT/'archive/dos-original/BRUN30.EXE').read_bytes()
proof=json.loads((ROOT/'research/yt-mercenaries/rea/runtime-dispatch.json').read_text())
assert proof['executable_sha256']==sha(runtime) and proof['dispatch_table_file_offset']==0x58d
assert {r['opcode'] for r in proof['fragments']}=={0x72,0x82,0x92,0xa0,0xa1,0xa2,0xa6,0xae}
for r in proof['fragments']:
 address=struct.unpack_from('<H',runtime,0x58d+2*r['opcode'])[0]
 assert r['runtime_cs_offset']==address and r['file_offset']==0x200+address
 assert bytes.fromhex(r['bytes_hex'])==runtime[0x200+address:0x200+address+85]
# DS constant pool is mapped in the archived annotator at file 0x23240 for DS:6190.
for offset,value in ((0x69c4,.33),(0x69ec,.05),(0x69f0,.9)):
 raw=exe[0x23240+offset-0x6190:0x23240+offset-0x6190+4]
 m=int.from_bytes(raw[:3],'little');decoded=(-1 if m&0x800000 else 1)*(1+(m&0x7fffff)/2**23)*2.0**(raw[3]-129)
 assert abs(decoded-value)<1e-7,(hex(offset),decoded)
