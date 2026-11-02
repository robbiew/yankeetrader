"""Check saved DOS turn changes, announcements and native arithmetic evidence."""
import gzip,hashlib,importlib.util,json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-xannor-turn-bonus'
SHA=lambda b:hashlib.sha256(b).hexdigest()
spec=importlib.util.spec_from_file_location('turn_primitives',ROOT/'scripts/verify_spy_triggers.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
CASES={'kills-199':(199,100,0),'kills-200':(200,100,1),'kills-399':(399,100,1),'kills-400':(400,100,2),'cap-one':(1000,499,1),'at-cap':(1000,500,0),'mercenary':(400,100,0),'player-defense':(400,100,0),'partial-escape':(100000,100,7),'missiles':(400,100,0),'plasma':(400,100,0)}

def check(root=DEFAULT):
 root=Path(root);binary=(ROOT/'archive/dos-original/YT.EXE').read_bytes()
 assert SHA(binary)=='c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037'
 image=v.loaded(binary);bundle=json.loads((root/'rea.json').read_text());observed=set()
 reads={'0x11028':390,'0x32ba8':8,'0x168f8':8}
 assert len(bundle['records'])==len(reads), 'native observation count'
 for r in bundle['records']:
  assert r['operation']=='read_bytes' and r['subject']['digest']['sha256']==SHA(binary)
  n=r['normalized_result'];offset=int(n['address'],16)-0x10000
  assert n['address'] in reads and n['address'] not in observed, 'unexpected or duplicate native read'
  length=reads[n['address']]
  assert r['parameters']=={'address':n['address'],'length':length}, 'native read contract'
  assert n['complete'] and n['returned_bytes']==n['requested_bytes']==length, 'truncated native read'
  assert bytes.fromhex(n['bytes_hex'])==image[offset:offset+n['returned_bytes']]
  observed.add(n['address'])
 assert set(reads)==observed
 assert image[0x22ba8:0x22bb0]==bytes.fromhex('0000000000004888') # MBF64 200
 for name,(count,turns,award) in CASES.items():
  case=root/'dos'/name;r=json.loads((case/'result.json').read_text())
  assert r['complete'] and r['program_returned'] and not r['timed_out']
  assert (case/'RETURN.LOG').read_bytes()==b'BROADCAST_PROGRAM_RETURNED\r\n', 'missing shell return marker'
  raw=gzip.decompress((case/'game.log.gz').read_bytes()).decode('cp437').replace('\r\n','\n')
  assert raw==(case/'transcript.txt').read_text()
  assert 'Returning to Yankee Trader Local Logon Program...' in raw, 'missing normal program return'
  assert r['binaries']['YT.EXE']==SHA(binary)
  for file,digest in r['files'].items():assert SHA((case/file).read_bytes())==digest
  before=gzip.decompress((case/'before.dat.gz').read_bytes());after=gzip.decompress((case/'after.dat.gz').read_bytes())
  assert v.get(before,2,49)==turns and v.get(before,2,57)==100
  target=152 if name in ['missiles','plasma'] else 151
  owner=-2 if name=='mercenary' else 3 if name=='player-defense' else -1
  assert v.get(before,target,81)==count and v.get(before,target,85)==owner
  side_before=json.loads(gzip.decompress((case/'side-before.json.gz').read_bytes()));side_after=json.loads(gzip.decompress((case/'sidefiles.json.gz').read_bytes()))
  key=next(k for k in side_before if k.upper()=='YTNEWS.DAT')
  old=bytes.fromhex(side_before[key]).rstrip(b'\x1a');new=bytes.fromhex(side_after[key]['hex']).rstrip(b'\x1a');assert new.startswith(old)
  suffix=new[len(old):]
  # DOS lines have CRLF, so strip the CR before exact line matching.
  bonuses=re.findall(rb'^Q  collected ([0-9]+) turns bonus for destroying ([0-9]+) Xannor!!$',suffix.replace(b'\r',b''),re.M)
  if name in ['missiles','plasma']:
   assert v.get(after,2,49)==turns-1 and not bonuses
   assert v.get(after,target,81)==0 and b'destroyed 400 fighters in sector 101!' in suffix
  else:
   casualties=1504 if name=='partial-escape' else count
   owner_name='The Xannor' if owner==-1 else 'Mercenaries' if owner==-2 else 'Enemy'
   reports=[line.rstrip() for line in suffix.splitlines() if b' fighters belonging to ' in line]
   assert reports==[f'Q  destroyed {casualties} fighters belonging to {owner_name}'.encode()]
   assert b'surrendered to' not in suffix
   if name!='partial-escape':assert v.get(after,target,81)==0 and v.get(after,2,61)<=v.get(before,2,61)
   assert v.get(after,2,49)==turns+award
   assert bonuses==([(str(award).encode(),str(casualties).encode())] if award else [])
   if name=='partial-escape':
    assert casualties<count and v.get(after,2,61)==0 and v.get(after,2,53)==11069
   elif owner==-1:assert award==min(casualties//200,500-turns)
 return len(CASES)
if __name__=='__main__':print(f'Xannor turn-bonus evidence passed: {check(Path(sys.argv[1]) if len(sys.argv)>1 else DEFAULT)} normally returned DOS controls.')
