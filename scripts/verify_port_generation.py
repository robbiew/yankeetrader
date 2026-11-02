"""Verify retained, pristine DOS port generation and its maintenance transition."""
import argparse, gzip, hashlib, json, math, re, struct
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SHA = lambda b: hashlib.sha256(b).hexdigest()
BINS = {"YT-INIT.EXE":"601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2", "BRUN30.EXE":"3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8"}
MAINT = "8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6"
def get(b, record, offset):
 raw=b[(record-1)*137+offset:(record-1)*137+offset+4]
 assert len(raw)==4
 if raw[3]==0:return 0
 m=int.from_bytes(raw[:3], 'little')
 return (-1 if m&0x800000 else 1)*math.ldexp(1+(m&0x7fffff)/2**23,raw[3]-129)
def verify_native(root):
 contracts={
  "initializer-rea.json":("YT-INIT.EXE",{"0x1196e":210,"0x11b28":260,"0x11c07":140}),
  "initializer-names-rea.json":("YT-INIT.EXE",{"0x1004f":40,"0x11c88":544,"0x123e4":546,"0x131b0":4966}),
  "runtime-rea.json":("BRUN30.EXE",{"0x1b2c2":110,"0x2002c":12}),
  "pricing-rea.json":("YT.EXE",{"0x10030":140})}
 for filename,(binary,reads) in contracts.items():
  raw=(ROOT/"archive/dos-original"/binary).read_bytes()
  image=bytearray(raw[struct.unpack_from("<H",raw,8)[0]*16:])
  table=struct.unpack_from("<H",raw,24)[0]
  for i in range(struct.unpack_from("<H",raw,6)[0]):
   off,seg=struct.unpack_from("<HH",raw,table+4*i);at=seg*16+off
   struct.pack_into("<H",image,at,(struct.unpack_from("<H",image,at)[0]+0x1000)&0xffff)
  records=json.loads((root/filename).read_text())["records"];seen=set()
  assert len(records)==len(reads)
  for r in records:
   n=r["normalized_result"];address=n["address"]
   assert r["operation"]=="read_bytes" and r["subject"]["digest"]["sha256"]==SHA(raw)
   assert address in reads and address not in seen
   size=reads[address];assert r["parameters"]=={"address":address,"length":size}
   assert n["complete"] and n["requested_bytes"]==n["returned_bytes"]==size
   at=int(address,16)-0x10000;assert bytes.fromhex(n["bytes_hex"])==image[at:at+size]
   seen.add(address)
  assert seen==set(reads)
 # Independent extraction checks the908 weighted tokens actually shipped.
 binary=(ROOT/"archive/dos-original/YT-INIT.EXE").read_bytes()
 rows=re.findall(rb"[\x06-\x49]\x26 ([^\x00]+)\x00",binary[0x33a0:0x4720])
 tokens=b",".join(row for row in rows if row!=b'"***"').split(b",")
 assert len(tokens)==908 and SHA(b",".join(tokens))=="8a59a909d232084d89a82db77339f680475c3187aef96ef0ce6444bd0b4002b7"

def verify(directory):
 worlds={}; summaries={}
 for name,clock in [("midnight","00:00:00"),("repeat","00:00:00"),("later","12:34:00")]:
  d=directory/name;m=json.loads((d/"result.json").read_text())
  assert m["name"]==name and m["date"]=="11/02/2026" and m["time"]==clock
  assert m["recipe"]=="dos-port-generation-v1" and m["maintenance_child"]=="declared-exit-stub"
  assert m["binaries"]=={**BINS,"YTMAINT.EXE":SHA(bytes.fromhex("b8004ccd21"))}
  assert m["actual_maintenance_sha256"]==MAINT
  assert set(m["files"])=={"before-maint.dat.gz","after-maint.dat.gz","INIT.LOG","MAINT.LOG","INITRET.LOG","MAINTRET.LOG","ANSWERS.TXT","init-dosbox.log","maint-dosbox.log"}
  for f,h in m["files"].items():assert SHA((d/f).read_bytes())==h,(name,f)
  assert (d/"ANSWERS.TXT").read_bytes()==b"Y\r\n\r\n"
  assert b"<YT-INIT Normal Termination>" in (d/"INIT.LOG").read_bytes()
  assert b"INITIALIZER_RETURNED" in (d/"INITRET.LOG").read_bytes()
  assert b"MAINTENANCE_RETURNED" in (d/"MAINTRET.LOG").read_bytes()
  assert b"Daily Maintenance Completed OK" in (d/"MAINT.LOG").read_bytes()
  before=gzip.decompress((d/"before-maint.dat.gz").read_bytes());after=gzip.decompress((d/"after-maint.dat.gz").read_bytes())
  assert len(before)==len(after)==4151*137
  assert get(before,1,57)==3051 and get(before,1,61)==4051
  rates=[];locations=[]
  for port in range(1,1001):
   r=3051+port;at=(r-1)*137
   namebytes=before[at:at+41].rstrip(b" ")
   assert namebytes and all(32<=c<=126 for c in namebytes)
   assert namebytes==after[at:at+41].rstrip(b" ")
   assert port!=1 or namebytes==b"Earth"
   sector=get(before,r,93);assert sector==int(sector) and 1<=sector<=3000
   locations.append(int(sector))
   assert get(after,r,93)==sector
   for source in (before,after):
    c=[get(source,r,o) for o in (73,77,81)]
    assert all(v==int(v) and 1<=abs(v)<=100 for v in c)
    assert sum(v>0 for v in c)==1
    assert c[3-int(get(source,r,41))]>0
   for o in (49,53,57):
    p=get(before,r,o+12);rates.append(p)
    assert p==int(p) and 1000<=p<=32766
    assert get(before,r,o)==0
    assert get(after,r,o+12)==p and get(after,r,o)==10*p
    assert abs(get(before,r,o+24))==abs(get(after,r,o+24))
   assert get(before,r,45)==296 and get(after,r,45)==306
  assert locations[:4]==[1,3,5,7]
  # Original initialization marks1..4 rather than1,3,5,7. Preserve and expose
  # overwritten records instead of silently asserting a repaired modern layout.
  expected_links={sector:port for port,sector in enumerate(locations,1)}
  for stage,source in (("before",before),("after",after)):
   for sector in range(1,3001):
    assert get(source,51+sector,65)==expected_links.get(sector,0), (name,stage,sector,"sector port link")
  duplicates=len(locations)-len(set(locations))
  assert 0<=duplicates<=2
  summaries[m["name"]]={"ports":1000,"distinct_locations":len(set(locations)),"overwritten_ports":duplicates,"production_min":min(rates),"production_max":max(rates),"initial_stock":0,"maintenance_stock_days":10}
  worlds[m["name"]]=before
 assert worlds["midnight"]==worlds["repeat"]
 assert worlds["midnight"]!=worlds["later"]
 for f,h in BINS.items():assert SHA((ROOT/"archive/dos-original"/f).read_bytes())==h
 assert SHA((ROOT/"archive/dos-original/YTMAINT.EXE").read_bytes())==MAINT
 return summaries
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("directory",nargs="?",type=Path,default=ROOT/"research/yt-port-generation/dos");a=p.parse_args();verify_native(a.directory.parent);print(json.dumps(verify(a.directory),indent=2))
