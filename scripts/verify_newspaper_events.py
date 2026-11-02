"""Verify newspaper action scopes against copied DOS worlds and native bytes."""
import argparse
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import struct
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
RESEARCH=ROOT/'research/yt-newspaper/events'
SOURCE=ROOT/'archive/analysis/yt-combat/experiments/fixture-team-captain'
BASE_SHA='04eaf42c54d4f35c3412737e27fa968b5abcd22eb295cb5d8b45ab8045fcd0ec'
RECIPE='newspaper-creation-acquisition-v1'
BINS={
 'BRUN30.EXE':'3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8',
 'KEYFEED.COM':'06dd2b9fcb91502185f6f4a2123ad7fdac144f47f5170df203760b86db127596',
 'LOCAL.EXE':'bb970c43eb29fb80e7252f3968884f1c43543a5e39c6714b209ffca7dbf2d93a',
 'YT.EXE':'c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037'}
KEEP={'before.dat.gz','after.dat.gz','side-before.json.gz','sidefiles.json.gz','transcript.txt','game.log.gz','DOSDATE.LOG','DOSTIME.LOG','RETURN.LOG','KEYS.TXT','dosbox.log'}
GRAPH={1:[100,101],100:[1,101],101:[100,102],102:[101]}
RANGES={
 'planet_success':('0x13927',46),'planet_gate_poor':('0x136a0',108),
 'planet_consent_capacity_name':('0x1370c',187),'planet_fee_news':('0x1390c',73),
 'port_gate_consent':('0x12341',410),'port_settlement_radio':('0x124db',360),
 'port_owner_fee_finish':('0x1263f',203),'port_rename':('0x1a9f0',323),
 'news_append':('0x20ebb',59),'radio_packet':('0x21981',174),
 'planet_name_helper':('0x15464',140),'radio_open':('0x21479',75),
 'radio_packet_return':('0x21a2e',3),'planet_text':('0x33f72',15),
 'port_text':('0x33682',17),'newspaper_file':('0x36aa2',10),
 'planet_name_confirmation':('0x154e9',208),'radio_file':('0x36b1a',10),
 'port_success_complete':('0x12341',971),'port_rename_return':('0x1ab32',3),
 'planet_name_write_return':('0x155b9',29)}
SEARCHES={
 'no_public_append_in_purchase':('9a9b1a421f','0x12341','0x1270b'),
 'private_writer_in_purchase':('9a6125421f','0x12341','0x1270b'),
 'no_public_append_in_rename':('9a9b1a421f','0x1a9f0','0x1ab34'),
 'public_append_in_planet_creation':('9a9b1a421f','0x136a0','0x139b0')}
# Share only primitive MZ reconstruction/relocation validation, never the capture writer.
spec=importlib.util.spec_from_file_location('native_primitives',ROOT/'scripts/verify_spy_triggers.py')
primitive=importlib.util.module_from_spec(spec);spec.loader.exec_module(primitive)
sha=primitive.sha
get=primitive.get
put=primitive.put
read=primitive.read
zipped=primitive.zipped
FROZEN=read(RESEARCH/'expected.json')
DECLARATIONS={c['name']:c for c in FROZEN['recipe']['scenarios']}
EXPECTED=FROZEN['semantics']


def setup(declaration,baseline):
 b=bytearray(baseline)
 for sector,warps in GRAPH.items():
  start=(51+sector-1)*137;b[start:start+137]=bytes(137)
  for off,value in zip(range(41,65,4),warps):put(b,51+sector,off,value)
 patches=[[2,o,v]for o,v in {45:0,49:500,57:1,89:0,93:0,105:0,125:0}.items()]
 patches += [[3,o,v]for o,v in {45:0,57:2,61:42,53:7,89:0,125:1}.items()]
 patches += [[52,65,1],[152,65,2],[3053,93,101],[153,93,2],[4053,73,0],[4053,77,12]]
 patches += declaration['patches']
 for record,off,value in patches:put(b,record,off,value)
 return bytes(b),patches


def bytes_at(b,rec,off=0,n=137):return b[(rec-1)*137+off:(rec-1)*137+off+n]

def field_mask(masked,before,record,offsets):
 for offset in offsets:
  start=(record-1)*137+offset;masked[start:start+4]=before[start:start+4]


def verify_native(root=RESEARCH):
 dossier=read(Path(root)/'rea.json');binary=(ROOT/'archive/dos-original/YT.EXE').read_bytes()
 assert sha(binary)==BINS['YT.EXE'],'native binary identity'
 image=primitive.loaded(binary);reads=dossier['byte_evidence'];searches=dossier['search_evidence'];load=dossier['load_image_evidence']
 assert len(reads)==len(RANGES) and {e['label']for e in reads}==set(RANGES),'native observation set'
 assert len(searches)==len(SEARCHES) and {e['label']for e in searches}==set(SEARCHES),'native search set'
 for e in reads+searches+[load]:
  assert e['subject']['digest']['sha256']==sha(binary),'native target identity'
  assert e['analysis_profile']['digest']=='92fec87c3e8c374652fd603898f727129f4c0cecccf8cee1c17c98a90aced029','native analysis profile'
  assert e['provider']['id']=='ghidra'and e['provider']['version']=='12.1.4','native provider identity'
 for e in reads:
  address,length=RANGES[e['label']];v=e['normalized_result'];at=int(address,16)-65536
  assert e['operation']=='read_bytes'and e['parameters']==dict(address=address,length=length),'native read parameters'
  assert v['address']==address and v['complete']and v['requested_bytes']==v['returned_bytes']==length,'incomplete native bytes'
  assert bytes.fromhex(v['bytes_hex'])==image[at:at+length],'native bytes'
 assert load['operation']=='inspect_native_load_image','native load-image operation'
 primitive.verify_load_image(load,binary,image)
 header=struct.unpack_from('<H',binary,8)[0]*16
 for e in searches:
  pattern,start,end=SEARCHES[e['label']];v=e['normalized_result'];lo=int(start,16);hi=int(end,16);size=hi-lo+1
  assert e['operation']=='search_bytes'and e['parameters']==dict(pattern=pattern,start=start,end=end,limit=25),'native search parameters'
  assert v['complete']and v['next_cursor']is None,'incomplete native search'
  assert v['searched']==dict(blocks=[dict(segment='CODE_0',start=start,end=end,bytes=size)],bytes=size,skipped_uninitialized=[],skipped_not_loaded=[]),'native search boundary'
  needle=bytes.fromhex(pattern)
  matches=[dict(address=hex(at),segment='CODE_0',file_offset=header+at-65536,procedure=None)for at in range(lo,hi-len(needle)+2)if image[at-65536:at-65536+len(needle)]==needle]
  assert v['matches']==matches,'native bounded matches'
 return len(reads)


def semantics(declaration,before,after,initial,final,text):
 name=declaration['name'];family=declaration['family'];gold=EXPECTED[name]
 actor=3 if declaration.get('actor')=='ENEMY'else 2
 identity='Enemy'if actor==3 else'Tester';alias=bytes_at(before,actor,n=41).decode('cp437').rstrip()
 assert re.findall(r'^Welcome ([^\n]+)!$',text,re.M)==[identity],'login identity'
 aliases=[a.rstrip()for a in re.findall(r'^Name[ \t]+:[ \t]+([^\n]+)$',text,re.M)]
 assert aliases and set(aliases)=={alias},'login alias'
 assert 'Entering a new player'not in text and 'Entering a new ship'not in text,'unexpected registration/replacement'
 assert text.count("Do you want to read [T]oday's or [Y]esterday's news? [T/Y] -=> ")==1,'newspaper selection path'
 news_before=initial['YTNEWS.DAT'];prefix=news_before.split(b'\x1a',1)[0];current=final['YTNEWS.DAT']
 assert news_before.endswith(b'\x1a')and current.startswith(prefix),'existing newspaper preservation'
 appended=current[len(prefix):]
 event=(b'  -  Q  made a planet: '+gold['planet_name'].encode('cp437')+b'\r\n')if gold['outcome']=='created'else b''
 login=rb'-=\*=- \d{2}:\d{2}:\d{2} '+re.escape(alias.encode('cp437'))+rb'  Logged on -=\*=-\r\n'
 assert re.fullmatch(login+re.escape(event)+rb'\x1a',appended),'only declared public event append'
 # Every retained line must actually be displayed by the selected reader, in order.
 section=text.rsplit("Do you want to read [T]oday's or [Y]esterday's news? [T/Y] -=> ",1)[1].split('Computer command (?=help)?',1)[0]
 at=0
 for line in current.split(b'\x1a',1)[0].decode('cp437').splitlines():
  index=section.find(line,at);assert index>=0,'complete selected newspaper output';at=index+len(line)
 assert final['YTYNEWS.DAT']==initial['YTYNEWS.DAT'],'yesterday changed during action/read'
 # Assert exact resources independently of whole-output snapshots; only explicit cash/count settlements differ.
 changes={}
 if gold['outcome']=='created':changes[(2,81)]=get(before,2,81)-25000
 if gold['outcome']=='bought':
  changes[(2,81)]=get(before,2,81)-31;changes[(2,117)]=get(before,2,117)+1
  if get(before,3053,97)!=0:
   changes[(3,81)]=get(before,3,81)+31+get(before,3053,89)
   changes[(3,117)]=get(before,3,117)-1
 for record in range(2,7):
  assert bytes_at(after,record,n=41)==bytes_at(before,record,n=41),'public/account identity mutation'
  for offset in (45,49,53,57,61,65,69,73,77,81,85,89,93,97,101,105,113,117,121,125,129,133):
   assert get(after,record,offset)==changes.get((record,offset),get(before,record,offset)),('account resource settlement',record,offset)
  assert math.isfinite(get(after,record,109))and get(after,record,109)>=0,'score cache bounds'
 masked=bytearray(after)
 for record in range(2,7):field_mask(masked,before,record,[109])
 for record,offset in changes:field_mask(masked,before,record,[offset])
 if gold['outcome']=='created':
  planet=gold['planet_name'];assert get(before,151,93)==0 and get(after,151,93)==3,'planet sector link'
  assert bytes_at(after,4054,n=41)==planet.encode('cp437').ljust(41,b' '),'accepted planet name'
  assert get(after,4054,85)==len(planet)and get(after,4054,73)==2 and get(after,4054,77)==1,'planet identity/owner/ground'
  assert get(after,4054,41)==297 and 0<=get(after,4054,89)<10,'planet creation clock'
  for offset in (69,113,117,125):assert get(after,4054,offset)==0,'new planet empty private inventory'
  rates=[get(after,4054,o)for o in (45,49,53)];stocks=[get(after,4054,o)for o in (57,61,65)]
  assert rates[0]==rates[1]==rates[2]and 1<=rates[0]<1.01,'bounded initial production'
  assert stocks[0]==stocks[1]==stocks[2]and math.isclose(stocks[0],10*rates[0],rel_tol=1e-6),'bounded initial warehouse'
  assert math.isclose(get(after,4054,129),30*rates[0],rel_tol=1e-6),'bounded initial fighters'
  field_mask(masked,before,151,[93]);start=(4054-1)*137;masked[start:start+41]=before[start:start+41]
  field_mask(masked,before,4054,[41,45,49,53,57,61,65,69,73,77,85,89,113,117,125,129])
  assert text.count('created with Genesis Device!')==1,'single completed creation receipt'
 else:assert 'created with Genesis Device!'not in text,'unexpected creation receipt'
 if name=='port-teammate':
  assert get(after,52,77)==2,'team scoreboard member count'
  field_mask(masked,before,52,[77])
 if name=='planet-creator-reload':
  for offset in (45,49,53,57,61,65,129):
   assert get(before,4054,offset)<=get(after,4054,offset)<=get(before,4054,offset)*1.01,'bounded creator reload projection'
  assert 10<=get(after,4054,89)<20,'creator reload update clock'
  for offset in (113,117):assert get(before,4054,offset)==get(after,4054,offset)==0,'creator reload empty inventories'
  field_mask(masked,before,4054,[45,49,53,57,61,65,89,113,117,129])
 if name=='planet-existing':
  for offset in (45,49,53,57,61,65,69,125,129):
   assert get(before,4053,offset)<=get(after,4053,offset)<=get(before,4053,offset)*1.01,'bounded existing planet projection'
  assert 0<=get(after,4053,89)<10,'existing planet update clock'
  field_mask(masked,before,4053,[45,49,53,57,61,65,69,89,125,129])
 if family=='port':
  bought=gold['outcome']=='bought'
  for offset in (49,53,57,61,65,69):
   value=get(after,3053,offset);start=get(before,3053,offset)
   assert math.isfinite(value)and start<=value<=start*1.01,'bounded lazy commerce update'
  assert 0<=get(after,3053,101)<10,'port update clock'
  field_mask(masked,before,3053,[49,53,57,61,65,69,101])
  if bought:
   assert get(after,3053,97)==2 and get(after,3053,89)==0,'port owner/treasury settlement'
   port=gold['port_name'];assert bytes_at(after,3053,n=41)==port.encode().ljust(41,b' '),'accepted port name'
   assert get(after,3053,85)==len(port),'port name length'
   start=(3053-1)*137;masked[start:start+41]=before[start:start+41];field_mask(masked,before,3053,[85,89,97])
  assert text.count('Sold!')==int(bought),'single purchase settlement receipt'
 assert bytes(masked)==before,'unrelated world mutation'
 # Seller notice is an 86-byte system packet with old name, not a public purchase event.
 expected_mail=initial.get('YTRMSG.DAT',b'')
 notice=b'Q  bought your port "Test Port" in 101 for 31 credits'
 if family=='port'and gold['outcome']=='bought'and get(before,3053,97)!=0:
  assert expected_mail==b'','source mailbox isolation'
  packet=final['YTRMSG.DAT'];assert len(packet)==86,'single seller notice packet'
  assert get(packet,1,0)==1 and get(packet,1,4)==3 and get(packet,1,8)==-2,'seller packet routing'
  assert packet[12:]==notice.ljust(74,b' '),'exact private seller notice'
 elif name in {'port-seller-reload','port-renamed-seller-reload'}:
  packet=final['YTRMSG.DAT'];assert len(packet)==86 and packet[4:]==expected_mail[4:],'seller notice preserved body/routing'
  assert get(packet,1,0)==0,'seller automatic delivery counter'
  assert notice.decode()in text,'seller actually receives notice'
 else:assert final.get('YTRMSG.DAT',b'')==expected_mail,'unexpected private mail change'
 if name=='port-buyer-reload':assert notice.decode()not in text,'seller notice not buyer history'
 assert set(final)==set(initial),'auxiliary file set'
 for filename in set(initial)-{'YTNEWS.DAT','YTRMSG.DAT','YTSCORE.ASC','DORINFO1.DEF'}:
  assert final[filename]==initial[filename],'unrelated auxiliary mutation: '+filename
 lines=initial['DORINFO1.DEF'].split(b'\r\n');assert len(lines)>6,'source door identity';lines[6]=declaration.get('actor','TESTER').encode()
 assert final['DORINFO1.DEF']==b'\r\n'.join(lines),'actor door identity'
 required={
  'planet-poor':"You're too poor to buy one.",'planet-slots-full':"I'm sorry, but all planets are taken.",
  'planet-existing':'<Land/Create planet>','port-no-port':'No port here!',
  'port-self':'You already OWN this port','port-poor':"Come back when you can afford it!"}
 if name in required:assert required[name]in text,'required negative branch: '+name
 if name.startswith('planet-reserved-'):assert 'made a planet:'not in section[len(prefix.decode('cp437')):]and 'What do you want to name this planet?'in text,'reserved-name branch'
 if name=='planet-name-retry':assert text.count('What do you want to name this planet?')==2 and 'Final World'in text,'planet rename retry'
 if name=='port-rename-retry':assert text.count('Please enter a NAME for your port.')==2 and 'Final Harbor'in text,'port rename retry'


def verify_control(directory,declaration,case,baseline,worlds,auxiliaries):
 name=declaration['name'];assert re.fullmatch('[a-z0-9-]+',name),'scenario path';d=Path(directory)/name
 assert case==read(d/'result.json'),'manifest/result mismatch'
 assert all(case[k]==v for k,v in declaration.items()),'manifest/declaration mismatch'
 assert case['recipe']==RECIPE and case['baseline_sha256']==BASE_SHA and case['binaries']==BINS,'binary/session identity'
 assert case['date']=='10/24/2026'and case['time']==declaration.get('time','00:00:00'),'declared clock identity'
 assert case['timeout_seconds']==150 and case['complete']and case['program_returned']and not case['timed_out'],'incomplete DOS control'
 assert set(case['files'])==KEEP and {p.name for p in d.iterdir()}==KEEP|{'result.json'},'retained file set'
 for filename,digest in case['files'].items():assert sha((d/filename).read_bytes())==digest,('file hash',name,filename)
 primitive.clock(d,case)
 assert (d/'RETURN.LOG').read_bytes()==b'BROADCAST_PROGRAM_RETURNED\r\n','DOS return marker'
 before,after=zipped(d/'before.dat.gz'),zipped(d/'after.dat.gz');assert len(before)==len(after)==568687,'world size'
 if declaration.get('parent'):
  parent=declaration['parent'];assert parent in worlds,'parent ordering';expected=worlds[parent];patches=[];initial=auxiliaries[parent]
  assert declaration['patches']==[],'read-only exact parent chain'
 else:
  expected,patches=setup(declaration,baseline)
  initial={p.name:p.read_bytes()for p in SOURCE.iterdir()if p.suffix.upper()in('.DAT','.ASC','.DEF','.TMP')and p.name!='YTDATA.DAT'}
 assert case['applied_patches']==patches,'declared patch list'
 assert before==expected,'undeclared setup or broken world chain'
 assert {n:bytes.fromhex(v)for n,v in read(d/'side-before.json').items()}==initial,'auxiliary input chain'
 rows=read(d/'sidefiles.json');final={n:bytes.fromhex(v['hex'])for n,v in rows.items()}
 assert all(v['after_sha256']==sha(final[n])and v['before_sha256']==(sha(initial[n])if n in initial else None)for n,v in rows.items()),'auxiliary identity'
 assert (d/'KEYS.TXT').read_bytes()==('\r~~~~~\r~'+declaration['command']+'\r~~~~'+'\rQ;Y\r~~'*24).encode(),'exact input stream'
 text=(d/'transcript.txt').read_text();assert zipped(d/'game.log.gz').decode('cp437').replace('\r\n','\n')==text,'raw transcript identity'
 assert 'Returning to Yankee Trader Local Logon Program...'in text,'normal program return'
 semantics(declaration,before,after,initial,final,text)
 return after,final


def check(path=None,research=RESEARCH):
 root=Path(research);directory=Path(path)if path is not None else root/'dos'
 baseline=(SOURCE/'YTDATA.DAT').read_bytes();assert sha(baseline)==BASE_SHA and zipped(directory/'baseline.dat.gz')==baseline,'baseline identity'
 expected_recipe=(json.dumps(FROZEN['recipe'],indent=2)+'\n').encode()
 assert (directory/'recipe.json').read_bytes()==expected_recipe,'frozen declarations'
 manifest=read(directory/'results.json');assert manifest['recipe']==RECIPE,'recipe identity';rows={c['name']:c for c in manifest['scenarios']}
 assert len(rows)==len(manifest['scenarios'])==len(DECLARATIONS)and set(rows)==set(DECLARATIONS)==set(EXPECTED),'scenario set'
 binaries={n:(ROOT/('archive/analysis/yt-combat'if n=='KEYFEED.COM'else'archive/dos-original')/n).read_bytes()for n in BINS}
 assert {n:sha(v)for n,v in binaries.items()}==BINS,'archived binary identity'
 worlds={};auxiliaries={}
 for name,declaration in DECLARATIONS.items():
  try:worlds[name],auxiliaries[name]=verify_control(directory,declaration,rows[name],baseline,worlds,auxiliaries)
  except AssertionError as e:raise AssertionError(f'{name}: {e}')from e
 native=verify_native(root)
 print(f'Verified {len(rows)} returned newspaper controls, {sum(bool(c.get("parent"))for c in DECLARATIONS.values())} exact world/auxiliary chains and {native} native observations.')


if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('path',nargs='?',type=Path);p.add_argument('--research',type=Path,default=RESEARCH);a=p.parse_args();check(a.path,a.research)
