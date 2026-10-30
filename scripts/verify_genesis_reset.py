"""Verify isolated original-DOS Genesis/reset witnesses and their bounded claims."""
import argparse
import gzip
import hashlib
import importlib.util
import json
import re
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = 'faf2c99341bcaceaa37770831d1548e5ebb066642ed146c2c665d679e27d65ca'
RECIPE_SHA = '64375d799047dde586c12c90b1ebe406ac42432624bcbacd3a2d9e2c9558e21c'
RECIPE = 'genesis-reset-v1'
KEEP = {'before.dat.gz','after.dat.gz','side-before.json.gz','sidefiles.json.gz','transcript.txt','game.log.gz','DOSDATE.LOG','DOSTIME.LOG','RETURN.LOG','KEYS.TXT','dosbox.log'}
BINS = ('YT.EXE','RMT-INIT.EXE','YTMAINT.EXE','BRUN30.EXE','LOCAL.EXE','KEYFEED.COM')
NATIVE = {
 'yt.json':('YT.EXE',{'0x12728':312,'0x2b25e':120,'0x29941':36}),
 'rmt-init.json':('RMT-INIT.EXE',{'0x10044':294,'0x10702':232,'0x10888':92,'0x10918':326,'0x12831':543,'0x10bc4':419,'0x11cf4':265,'0x11dfd':92,'0x12017':610,'0x12279':192}),
}
# Independent exact witnesses cover uninterpreted native zero mantissa bytes and
# the broader first-maintenance computation. Semantic checks run before these
# hashes, so rehashed negative controls must still fail the relevant rule.
WORLD_SHA = {
'owned-299':'443ca9f93112bf85fe714cc4513982e7447f0240c9ca4de01527a9f003fc4585',
'owned-300':'b47c73f3798f48640ddc1eabbd085631b1cdd28a2f37c503ef16c1e257643f07',
'owned-301':'b47c73f3798f48640ddc1eabbd085631b1cdd28a2f37c503ef16c1e257643f07',
'cancel-no':'7ca0c10c70c21070ab15eda44e6e5a3e6821fea57dd802da1f10123ae0309d32',
'cancel-blank':'7ca0c10c70c21070ab15eda44e6e5a3e6821fea57dd802da1f10123ae0309d32',
'cached-only':'b47c73f3798f48640ddc1eabbd085631b1cdd28a2f37c503ef16c1e257643f07',
'records-only':'7fa66984f413153b8a9231f56d75c846613b5e3628caba07981c24019aa09fcc',
'fallback-short':'6e7a2ca7dabfb09f5ced7f183f41b759faf4f907bde2a33231d9fd96cd92f989',
'fallback-200':'b14cf04b9446d690f05fc731b5cb36fc9843c16b16a3d6c2c40e5f741bcb9b3d',
'threshold-20':'7c863f4463713ad945975debe3dfc864f9d4c84f52039ad6ab34c56ddd4624e3',
'disabled-301':'2530022170bba77c0b074b3f4d2ced95c86378d66f95e3d25b0a2897f970c690',
'lottery-zero':'3ec9c0a500524194db77c80025b42e84536187abff8d94365f65a3c53171769f',
'cargo-low':'6f86a513214813893625915942b66987f55ff265e75b4758ce76436b381138d3',
'cargo-high':'6f86a513214813893625915942b66987f55ff265e75b4758ce76436b381138d3',
'custom-defaults':'657a46eb1ff274af6dfadab422f1614978b144b8a4d1b856b0bf76243b3ef8bc',
'winner-mapping':'b47c73f3798f48640ddc1eabbd085631b1cdd28a2f37c503ef16c1e257643f07',
'standalone-no':'14889076bdb047c04c29ba8d65a0d40d04c55aeb456d075bff480a2c8ad61930',
'standalone-blank':'14889076bdb047c04c29ba8d65a0d40d04c55aeb456d075bff480a2c8ad61930',
'standalone-yes':'21e8501ffa8a894e4fa7137c9b45982285bd0489ee1edd28feeeb7ffd6f26688',
'standalone-threshold-high':'0920942d0943cdb1cfda5ce520236f5ca9d50a9cac17e12a2c6804c2870b13b4',
'missing-initializer':'14889076bdb047c04c29ba8d65a0d40d04c55aeb456d075bff480a2c8ad61930',
'malformed-marker':'14889076bdb047c04c29ba8d65a0d40d04c55aeb456d075bff480a2c8ad61930',
'marker-resume':'21e8501ffa8a894e4fa7137c9b45982285bd0489ee1edd28feeeb7ffd6f26688',
'first-maintenance':'0b5e9e8c7c501c41a064613a3422872767c89587bdcbb9d884a9373e5e3fb6a5',
}


# These exact auxiliary witnesses bound only the retained first-maintenance run.
# They preserve the observed complete news and score files, not a general
# maintenance news/score generation formula.
MAINTENANCE_AUX_SHA = {
 'YTNEWS.DAT':'4273f696b1d6d5aa5449edd39779c77d52a63a9f39b840c0f2b2596cee61be6f',
 'YTSCORE.ASC':'43d1518020dde4abe8bfef563e768ff781f55049e414ba9bab9b49f704f300da',
}


def sha(value):return hashlib.sha256(value).hexdigest()
def read(path):return json.loads(path.read_text())
def zipped(path):return gzip.decompress(path.read_bytes())
def side(path):return json.loads(zipped(path))
def record(data,n):return data[(n-1)*137:n*137]
def field(data,n,off):return data[(n-1)*137+off:(n-1)*137+off+4]


def loaded(data):
 header=struct.unpack_from('<H',data,8)[0]*16
 image=bytearray(data[header:]);table=struct.unpack_from('<H',data,24)[0]
 for i in range(struct.unpack_from('<H',data,6)[0]):
  off,seg=struct.unpack_from('<HH',data,table+4*i);at=seg*16+off
  struct.pack_into('<H',image,at,(struct.unpack_from('<H',image,at)[0]+0x1000)&0xffff)
 return image


def verify_native(root):
 for file,(binary,ranges)in NATIVE.items():
  raw=(ROOT/'archive/dos-original'/binary).read_bytes();image=loaded(raw);records=read(root/'rea'/file)['records'];seen=set()
  assert len(records)==len(ranges),'native observation count'
  for e in records:
   value=e['normalized_result'];address=value['address']
   assert address in ranges and address not in seen,'native address set';seen.add(address)
   assert e['operation']=='read_bytes'and e['subject']['digest']['sha256']==sha(raw),'native target identity'
   assert value['complete']and value['requested_bytes']==value['returned_bytes']==ranges[address],'incomplete native bytes'
   at=int(address,16)-0x10000
   assert bytes.fromhex(value['bytes_hex'])==image[at:at+ranges[address]],'native bytes'


def verify_reset(c,before,after,text,mbf):
 get=mbf.get;name=c['name'];hq=get(after,1,117)
 assert hq==int(hq)and 8<=hq<=3000,'reset HQ bounds'
 expected=bytearray(record(before,1))
 threshold=get(before,1,105);threshold=200 if threshold<20 or threshold>300 else threshold
 cargo=get(before,1,121);cargo=50 if cargo<5 or cargo>1000 else cargo
 lottery=max(1,get(before,1,101))
 for off,value in {81:296,101:lottery,105:threshold,117:hq,121:cargo,125:6324}.items():mbf.put(expected,1,off,value)
 assert record(after,1)==expected,'reset configuration carryover'
 for r in range(2,52):assert record(after,r)==b' '*41+bytes(96),'cleared human record'
 graph={}
 for sector in range(1,3001):
  r=51+sector;raw=record(after,r);assert raw[:41]==b' '*41,'sector name cleared'
  warps=[get(after,r,o)for o in range(41,65,4)]
  assert all(v==int(v)and 0<=v<=3000 and v!=sector for v in warps),'warp destination bounds'
  edges=[int(v)for v in warps if v]
  assert edges and len(edges)==len(set(edges)),'warp duplicate/empty group'
  graph[sector]=edges
  port=get(after,r,65);assert port==int(port)and 0<=port<=1000,'sector port bounds'
  allowed={81:10000 if sector==hq else 0,85:-1 if sector==hq else 0,105:hq if sector==1 else 0}
  for off in range(69,137,4):assert get(after,r,off)==allowed.get(off,0),'reset sector residue'
 assert graph[1]==[2,3,4,5,6,7]and get(after,52,65)==1,'Earth reset links'
 seen={1};todo=[1]
 while todo:
  for target in graph[todo.pop()]:
   if target not in seen:seen.add(target);todo.append(target)
 assert len(seen)==3000,'generated graph reachability'
 for port in range(1,1001):
  r=3051+port;raw=record(after,r);title=raw[:41].rstrip(b' ')
  assert title and re.fullmatch(rb'[A-Za-z ]+',title)and raw[:41]==title.ljust(41,b' '),'reset port name'
  kind=get(after,r,41);assert kind in(1,2,3),'reset port type'
  assert get(after,r,45)==287,'reset production watermark'
  assert all(get(after,r,o)==0 for o in(49,53,57)),'reset port stocks'
  assert all(get(after,r,o)==int(get(after,r,o))and 1000<=get(after,r,o)<=32767 for o in(61,65,69)),'reset port production'
  coefficients=[get(after,r,o)for o in(73,77,81)]
  assert all(v==int(v)and 1<=abs(v)<=100 for v in coefficients),'reset coefficient bounds'
  assert [v>0 for v in coefficients]==[i==3-kind for i in range(3)],'reset coefficient signs'
  assert get(after,r,85)==len(title),'reset port name length'
  assert get(after,r,89)==0 and get(after,r,97)==0,'cleared port ownership/treasury'
  sector=get(after,r,93);assert sector==int(sector)and 1<=sector<=3000,'port location bounds'
  for off in(101,105,109,113,117,121,125,129,133):
   value=({117:hq,121:cargo,125:6324}.get(off,0)if port==1 else 0)
   assert get(after,r,off)==value,'reset port residue'
 assert record(after,3052)[:41].rstrip()==b'Earth'and get(after,3052,93)==1,'Earth reset identity'
 inactive=bytearray(expected);mbf.put(inactive,1,85,0);mbf.put(inactive,1,89,0)
 for r in range(4052,4152):assert record(after,r)==inactive,'inactive planet buffer pattern'
 assert 'Initialization completed sucessfully!'in text,'reset completion message'
 if c['mode']=='game':assert 'Are you that Trader Q'in text,'in-game Genesis entry'
 standalone=c['mode']=='standalone'and not c.get('parent')
 assert ('Do you wish to re-init Y.T. using your old default values?'in text)==standalone,'reset confirmation mode'
 expected_winner='The Sysop'if standalone else''
 assert text.count('Congratulations '+expected_winner+'! You have fulfilled the prophesy!!')==(0 if standalone else 3),'reset winner display'
 return expected_winner


def verify_nonreset(c,before,after,text,mbf):
 get=mbf.get;expect=c['expect'];name=c['name']
 assert 'Initialization completed sucessfully!'not in text,'unexpected reset'
 expected=bytearray(before)
 if expect=='refusal':
  assert 'Are you that Trader Q'in text and 'Returning to Yankee Trader Local Logon Program...'in text,'normal refusal quit'
  if name.startswith('cancel-'):assert 'Alas, today'in text,'cancelled Genesis'
  elif name=='disabled-301':assert '*FUNCTION DISABLED*'in text,'disabled Genesis'
  else:
   threshold=200 if c['threshold']<20 else c['threshold']
   assert 'You are '+str(threshold-c['cached'])+' short of fulfilling the prophesy.'in text,'cached eligibility refusal'
  mbf.put(expected,2,117,c['cached']);mbf.put(expected,2,109,5002500+c['cached']*50000);mbf.put(expected,3,109,1265500)
 elif expect=='standalone-cancel':
  assert 'Running stand alone...'in text and 'Do you wish to re-init Y.T. using your old default values?'in text,'standalone confirmation'
 elif expect=='chain-error':assert 'ERR= 53'in text and 'Untrapped Error'in text,'missing initializer fault'
 elif expect=='marker-error':assert 'Path not found in module RMT-INIT'in text,'malformed marker fault'
 else:raise AssertionError('unknown nonreset outcome')
 assert after==expected,'nonreset world conservation'


def board_frame(text):
 text=re.sub(r'^ *(\d+) +([0-9.]+)% +([0-9,]+) +None +[0-9]+ +(Q|Enemy) *\r?\n','',text,flags=re.M)
 text=re.sub(r'Last updated at: \d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}','Last updated at: CLOCK',text)
 return re.sub(r'^ +1,000,000 +[0-9.]+% +0 +0[.]00%\r?\n','NPC SCORES\r\n',text,flags=re.M)


def verify_aux(c,initial,final,text,mbf,winner=None):
 expect=c['expect'];name=c['name'];expected_names=set(initial)
 if expect in('reset','marker-error'):expected_names.discard('RMTINIT.TMP')
 if expect in('standalone-cancel','chain-error'):expected_names.add('RMTINIT.TMP')
 assert set(final)==expected_names,'auxiliary file set'
 changed={'YTNAME.DAT','YTNEWS.DAT','YTYNEWS.DAT','YTRMSG.DAT','YTSCORE.ASC'}if expect=='reset'else{'YTNEWS.DAT','YTSCORE.ASC'}if expect in('refusal','chain-error','maintenance')else set()
 if expect=='maintenance':changed.add('YTYNEWS.DAT')
 for file,value in initial.items():
  if file not in changed and file!='RMTINIT.TMP':assert final[file]==value,('unrelated auxiliary effect',name,file)
 if expect=='reset':
  assert final['YTSCORE.ASC']==initial['YTSCORE.ASC'],'stale scoreboard preserved'
  assert final['YTNAME.DAT']==b'Dummy,Dummy,Dummy,Dummy\r\n\x1a','reset aliases'
  assert final['YTYNEWS.DAT']==b"NO YESTERDAY'S NEWS TO READ!\r\n"*5+b'\x1a','reset yesterday news'
  notice=('** The Prophesy has been fulfilled by '+winner+'!! **').encode()
  raw=final['YTNEWS.DAT'];assert raw.startswith((notice+b'\r\n')*3),'reset public winner'
  suffix=raw[len((notice+b'\r\n')*3):]
  lines=suffix.decode('cp437').splitlines();assert len(lines)==8 and lines[-1]=='\x1a','reset initialization news'
  phrases=['**********************','**********************','**                  **','** Game Initialized **','**                  **','**********************','**********************']
  assert all(re.fullmatch(r'\d{2}:\d{2}:\d{2} 10-24-2026 '+re.escape(phrase),line)for line,phrase in zip(lines,phrases)),'reset initialization news'
  assert final['YTRMSG.DAT']==(mbf.enc(50)+mbf.enc(-2)+mbf.enc(-2)+notice.ljust(72,b' ')+bytes(2))*5,'reset radio winner'
 elif expect in('refusal','chain-error'):
  prefix=initial['YTNEWS.DAT'];assert prefix.endswith(b'\x1a')and final['YTNEWS.DAT'].startswith(prefix[:-1]),'login news prefix'
  tail=final['YTNEWS.DAT'][len(prefix)-1:].decode('cp437')
  assert re.fullmatch(r'-=\*=- \d{2}:\d{2}:\d{2} Q  Logged on -=\*=-\r\n\x1a',tail),'login-only news'
  if expect=='chain-error':
   assert final['RMTINIT.TMP']==b'DORINFO1.DEF\r\n\x1a','preserved handoff marker'
   assert final['YTSCORE.ASC']==initial['YTSCORE.ASC'],'fault scoreboard preserved'
  else:
   board=final['YTSCORE.ASC'].decode('cp437');rows=re.findall(r'^ *(\d+) +([0-9.]+)% +([0-9,]+) +None +([0-9]+) +(Q|Enemy) *\r?\n',board,re.M)
   score=5002500+c['cached']*50000
   assert len(rows)==2 and rows[0]==('1','100.00',f'{score:,}',str(c['cached']),'Q')and rows[1]==('2',f'{1265500/score*100:.2f}','1,265,500','0','Enemy'),'logout scoreboard values'
   assert board_frame(board)==board_frame(initial['YTSCORE.ASC'].decode('cp437')),'logout scoreboard scope'
 elif expect=='standalone-cancel':assert final['RMTINIT.TMP']==b'','empty standalone marker'
 elif expect=='maintenance':
  assert final['YTYNEWS.DAT']==initial['YTNEWS.DAT'],'maintenance news rotation'
  assert 'Maintenance Program Ran'in final['YTNEWS.DAT'].decode('cp437'),'maintenance news'
  for phrase in('The Wanderer regenerated','The Xannor have made a Planet','Mercenaries have built a home base'):assert phrase in final['YTNEWS.DAT'].decode('cp437'),'maintenance faction news'
  assert name=='first-maintenance' and {file:sha(final[file])for file in MAINTENANCE_AUX_SHA}==MAINTENANCE_AUX_SHA,'frozen maintenance auxiliary witness'


def verify_maintenance(before,after,text,mbf):
 get=mbf.get
 assert 'Daily Maintenance Completed OK'in text,'first maintenance completion'
 assert get(before,1,81)==296 and get(after,1,81)==297,'first maintenance date'
 head=bytearray(record(before,1));mbf.put(head,1,81,297);assert record(after,1)==head,'maintenance configuration conservation'
 human=b' '*41+bytes(96);human=bytearray(human);mbf.put(human,1,109,-1)
 for r in range(2,52):assert record(after,r)==human,'maintenance empty humans'
 for r in range(3052,4052):
  for stock,production in((49,61),(53,65),(57,69)):assert get(after,r,stock)==10*get(before,r,production),'initial maintenance port stocks'
  assert get(after,r,45)==297 and get(after,r,89)==get(after,r,97)==0,'maintenance port ownership/watermark'
  for off in(61,65,69,85,93,105,109,113,117,121,125,129,133):assert field(after,r,off)==field(before,r,off),'maintenance port conservation'
  assert record(after,r)[:41]==record(before,r)[:41],'maintenance port names'
 for r,title in((4052,b'The Wanderer'),(4150,b'Mercenary Base'),(4151,b'Xannoron')):
  assert record(after,r)[:41]==title.ljust(41,b' ')and get(after,r,85)==len(title),'initial maintenance faction homes'
  assert get(after,r,45)==(5000 if r==4052 else 100000),'initial maintenance home production'
 for r in range(4053,4150):assert record(after,r)==record(before,r),'maintenance inactive planets'
 for r in range(52,3052):
  assert record(after,r)[:41]==record(before,r)[:41],'maintenance sector names'
  for off in(41,45,49,53,57,61,65,69,73,77,89,97,101,109,113,117,121,125,133):assert field(after,r,off)==field(before,r,off),'maintenance topology conservation'
 for slot in(1,99,100):assert sum(get(after,r,93)==slot for r in range(52,3052))==1,'maintenance home sector links'


def verify(root):
 droot=root/'dos';source=ROOT/'archive/analysis/yt-combat/experiments/fixture-trade-earth';base=(source/'YTDATA.DAT').read_bytes()
 assert sha(base)==BASE_SHA and zipped(droot/'baseline.dat.gz')==base,'baseline identity'
 raw=(droot/'recipe.json').read_bytes();assert sha(raw)==RECIPE_SHA,'frozen declarations'
 recipe=json.loads(raw);manifest=read(droot/'results.json');assert recipe['recipe']==manifest['recipe']==RECIPE,'recipe identity'
 specs={r['name']:r for r in recipe['scenarios']};rows=manifest['scenarios'];assert len(specs)==len(rows)==24 and len({r['name']for r in rows})==24 and set(specs)==set(WORLD_SHA)=={r['name']for r in rows},'scenario identity'
 spec=importlib.util.spec_from_file_location('mbf',ROOT/'archive/analysis/yt-maint/experiments.py');mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)
 binaries={n:(ROOT/'archive/dos-original'/n).read_bytes()for n in BINS if n!='KEYFEED.COM'};binaries['KEYFEED.COM']=(ROOT/'archive/analysis/yt-combat/KEYFEED.COM').read_bytes()
 worlds={};sides={}
 for c in rows:
  name=c['name'];directory=droot/name;decl=specs[name]
  assert re.fullmatch(r'[a-z0-9-]+',name),'scenario path'
  assert c==read(directory/'result.json')and all(c[k]==v for k,v in decl.items()),'manifest/declaration mismatch'
  assert c['recipe']==RECIPE and c['baseline_sha256']==BASE_SHA,'session identity'
  assert c['complete']and c['program_returned']and not c['timed_out']and c['timeout_seconds']==120,'incomplete DOS control'
  assert c['binaries']=={n:sha(v)for n,v in binaries.items()if n not in decl.get('omit',[])},'binary identity'
  assert set(c['files'])==KEEP and {p.name for p in directory.iterdir()}==KEEP|{'result.json'},'retained file set'
  for file,digest in c['files'].items():assert sha((directory/file).read_bytes())==digest,('file hash',name,file)
  assert c['date']=='10/24/2026'and '10/24/2026'in(directory/'DOSDATE.LOG').read_text(),'DOS date'
  assert c['time']=='00:00:00','declared clock'
  m=re.search(r'Current time: (\d+):(\d+):(\d+)\.(\d+)(am|pm)',(directory/'DOSTIME.LOG').read_text());assert m,'DOS clock'
  h,minute,second,fraction,ampm=m.groups();observed=(int(h)%12+(12 if ampm=='pm'else 0))*3600+int(minute)*60+int(second)+int(fraction)/10**len(fraction)
  assert 0<=observed<=.06,'DOS clock mismatch'
  assert(directory/'RETURN.LOG').read_bytes()==b'GENESIS_PROGRAM_RETURNED\r\n','DOS return marker'
  before=zipped(directory/'before.dat.gz');after=zipped(directory/'after.dat.gz');assert len(before)==len(after)==568687,'world size'
  if c.get('parent'):
   assert c['parent']in worlds,'parent ordering'
   expected=bytearray(worlds[c['parent']]);initial=sides[c['parent']]
  else:
   expected=bytearray(base);mbf.put(expected,1,105,decl['threshold']);mbf.put(expected,2,117,decl['cached'])
   for port in range(1,1001):mbf.put(expected,3051+port,97,2 if 2<=port<=decl['owned']+1 else 0)
   initial={p.name:p.read_bytes()for p in source.iterdir()if p.suffix.upper()in('.DAT','.ASC','.DEF')and p.name!='YTDATA.DAT'}
   initial['KEEPME.DAT']=b'Unrelated file: do not overwrite.\r\n'
   if decl.get('alias_case_pair'):initial['YTNAME.DAT']=initial['YTNAME.DAT'].rstrip(b'\x1a')+b'TESTER,,Q,\r\n\x1a'
   if decl.get('score_sentinel'):initial['YTSCORE.ASC']=b'PRIOR SEASON SCOREBOARD SENTINEL\r\n'
   if'marker'in decl:initial['RMTINIT.TMP']=decl['marker'].encode()
   for rec,off,value in decl.get('patches',[]):mbf.put(expected,rec,off,value)
  assert before==expected,'undeclared setup or broken world chain'
  assert {n:bytes.fromhex(v)for n,v in side(directory/'side-before.json.gz').items()}==initial,'auxiliary input chain'
  aux=side(directory/'sidefiles.json.gz');final={n:bytes.fromhex(v['hex'])for n,v in aux.items()}
  assert all(v['after_sha256']==sha(final[n])and v['before_sha256']==(sha(initial[n])if n in initial else None)for n,v in aux.items()),'auxiliary identity'
  if c['mode']=='game':keys='\r~~~~~\r~G\r~~'+c['reply']+'\r~~~~Q;Y\r'+'~~\r'*12
  elif c['mode']=='standalone':keys='~~~~'+c['reply']+'\r'+'~~\r'*12
  else:keys='~~~~\r'
  assert(directory/'KEYS.TXT').read_bytes()==keys.encode(),'exact input stream'
  text=(directory/'transcript.txt').read_text();assert zipped(directory/'game.log.gz').decode('cp437').replace('\r\n','\n')==text,'raw transcript identity'
  winner=None
  if c['expect']=='reset':winner=verify_reset(c,before,after,text,mbf)
  elif c['expect']=='maintenance':verify_maintenance(before,after,text,mbf)
  else:verify_nonreset(c,before,after,text,mbf)
  verify_aux(c,initial,final,text,mbf,winner)
  assert sha(after)==WORLD_SHA[name],'frozen complete world witness'
  worlds[name],sides[name]=after,final
 verify_native(root)
 print('Verified 24 normally returned Genesis controls, exact world/auxiliary chains, bounded reset semantics, frozen full worlds and 13 native byte observations.')


if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--research',type=Path,default=ROOT/'research/yt-genesis');verify(p.parse_args().research)
