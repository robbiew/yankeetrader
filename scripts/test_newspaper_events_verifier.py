"""Rehashed corruption controls for public creation and private acquisition evidence."""
import contextlib
import copy
import gzip
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'research/yt-newspaper/events'
DOS=Path(os.environ.get('YT_NEWSPAPER_EVENTS_DOS',SOURCE/'dos'))
spec=importlib.util.spec_from_file_location('newspaper_event_verifier',ROOT/'scripts/verify_newspaper_events.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)


def write_json(path,value):
 p=Path(path);b=(json.dumps(value,indent=2)+'\n').encode()
 p.write_bytes(gzip.compress(b,mtime=0)if p.suffix=='.gz'else b)


def update_text(d,text,case,changed):
 (d/'transcript.txt').write_text(text);changed.append('transcript.txt')
 (d/'game.log.gz').write_bytes(gzip.compress(text.replace('\n','\r\n').encode('cp437'),mtime=0));changed.append('game.log.gz')


class NativeControls(unittest.TestCase):
 def test_native_preserved(self):self.assertEqual(v.verify_native(SOURCE),21)
 def test_native_corruptions(self):
  modes={
   'byte':'native bytes','length':'incomplete native bytes','target':'native target identity',
   'profile':'native analysis profile','provider':'native provider identity',
   'read-parameters':'native read parameters','read-set':'native observation set',
   'search-complete':'incomplete native search','search-boundary':'native search boundary',
   'search-parameters':'native search parameters','search-matches':'native bounded matches',
   'search-set':'native search set','relocation':'native relocation bytes',
   'mapping':'native mapped bytes','source':'native source digests','load-operation':'native load-image operation'}
  with tempfile.TemporaryDirectory(prefix='yt-news-event-native-')as tmp:
   root=Path(tmp);original=v.read(SOURCE/'rea.json')
   for mode,reason in modes.items():
    with self.subTest(mode=mode):
     x=copy.deepcopy(original);e=x['byte_evidence'][0];search=x['search_evidence'][0];load=x['load_image_evidence']
     if mode=='byte':e['normalized_result']['bytes_hex']='00'+e['normalized_result']['bytes_hex'][2:]
     elif mode=='length':e['normalized_result']['returned_bytes']-=1
     elif mode=='target':e['subject']['digest']['sha256']='0'*64
     elif mode=='profile':e['analysis_profile']['digest']='0'*64
     elif mode=='provider':e['provider']['version']='0'
     elif mode=='read-parameters':e['parameters']['address']='0x10000'
     elif mode=='read-set':x['byte_evidence'].pop()
     elif mode=='search-complete':search['normalized_result']['complete']=False
     elif mode=='search-boundary':search['normalized_result']['searched']['bytes']-=1
     elif mode=='search-parameters':search['parameters']['end']='0x12400'
     elif mode=='search-matches':search['normalized_result']['matches'].append(dict(address='0x12341',segment='CODE_0',file_offset=12609,procedure=None))
     elif mode=='search-set':x['search_evidence'].pop()
     elif mode=='relocation':load['normalized_result']['observations']['relocations'][0]['memory_bytes_hex']='0000'
     elif mode=='mapping':next(m for m in load['normalized_result']['observations']['mappings']if m['initialized'])['sha256']='0'*64
     elif mode=='source':load['normalized_result']['observations']['source_files'][0]['modified_sha256']='0'*64
     elif mode=='load-operation':load['operation']='read_bytes'
     else:raise AssertionError(mode)
     write_json(root/'rea.json',x)
     with self.assertRaisesRegex(AssertionError,reason):v.verify_native(root)
  print(f'Rejected {len(modes)} native byte/load/search corruptions.')


class RuntimeControls(unittest.TestCase):
 def test_preserved(self):
  with contextlib.redirect_stdout(io.StringIO()):v.check(DOS)
 def test_rehashed_corruptions(self):
  controls=[
   ('planet-create','incomplete','incomplete DOS control'),
   ('planet-create','binary','binary/session identity'),
   ('planet-create','patches','declared patch list'),
   ('planet-create','before','undeclared setup or broken world chain'),
   ('port-seller-reload','before','undeclared setup or broken world chain'),
   ('port-seller-reload','aux-input','auxiliary input chain'),
   ('planet-create','keys','exact input stream'),
   ('planet-create','date','DOS date'),
   ('planet-create','clock','DOS clock mismatch'),
   ('planet-create','return','DOS return marker'),
   ('planet-create','raw-only','raw transcript identity'),
   ('planet-create','text-only','raw transcript identity'),
   ('planet-create','identity','login identity'),
   ('planet-create','alias','login alias'),
   ('planet-create','credits','account resource settlement'),
   ('planet-create','turn','account resource settlement'),
   ('planet-create','planet-owner','planet identity/owner/ground'),
   ('planet-create','planet-name','accepted planet name'),
   ('planet-create','planet-production','bounded initial production'),
   ('planet-create','planet-bank','new planet empty private inventory'),
   ('planet-create','event-name','only declared public event append'),
   ('planet-decline','forged-created-news','only declared public event append'),
   ('port-buyout-keep','public-sale','only declared public event append'),
   ('port-buyout-keep','buyer-credit','account resource settlement'),
   ('port-buyout-keep','seller-credit','account resource settlement'),
   ('port-buyout-keep','treasury','port owner/treasury settlement'),
   ('port-buyout-keep','port-owner','port owner/treasury settlement'),
   ('port-buyout-rename','port-name','accepted port name'),
   ('port-buyout-rename','packet-old-name','exact private seller notice'),
   ('port-buyout-keep','packet-price','exact private seller notice'),
   ('port-buyout-keep','packet-recipient','seller packet routing'),
   ('port-buyout-keep','packet-sender','seller packet routing'),
   ('port-unowned','packet-extra','unexpected private mail change'),
   ('port-seller-reload','packet-counter','seller automatic delivery counter'),
   ('port-buyer-reload','buyer-sees-seller','seller notice not buyer history'),
   ('port-seller-reload','door-identity','actor door identity'),
   ('planet-create','unrelated','unrelated world mutation'),
  ]
  with tempfile.TemporaryDirectory(prefix='yt-news-events-runtime-')as tmp:
   root=Path(tmp)
   for name,mode,reason in controls:
    with self.subTest(name=name,mode=mode):
     d=root/name;shutil.copytree(DOS/name,d);case=v.read(d/'result.json');changed=[]
     if mode=='incomplete':case['complete']=False
     elif mode=='binary':case['binaries']['YT.EXE']='0'*64
     elif mode=='patches':case['applied_patches'].pop()
     elif mode in {'before','credits','turn','planet-owner','planet-name','planet-production','planet-bank','buyer-credit','seller-credit','treasury','port-owner','port-name','unrelated'}:
      filename='before.dat.gz'if mode=='before'else'after.dat.gz';raw=bytearray(v.zipped(d/filename))
      values={'before':(2,53,123),'credits':(2,81,74999),'turn':(2,49,499),'planet-owner':(4054,73,3),'planet-production':(4054,45,100),'planet-bank':(4054,117,1),'buyer-credit':(2,81,99968),'seller-credit':(3,81,2809),'treasury':(3053,89,1),'port-owner':(3053,97,3),'unrelated':(151,129,1)}
      if mode in {'planet-name','port-name'}:
       at=(4054-1)*137 if mode=='planet-name'else(3053-1)*137;raw[at]=ord('X')
      else:v.put(raw,*values[mode])
      (d/filename).write_bytes(gzip.compress(raw,mtime=0));changed.append(filename)
     elif mode=='aux-input':
      filename='side-before.json.gz';x=json.loads(gzip.decompress((d/filename).read_bytes()));x['YTRMSG.DAT']='00';write_json(d/filename,x);changed.append(filename)
     elif mode in {'keys','date','clock','return'}:
      filename={'keys':'KEYS.TXT','date':'DOSDATE.LOG','clock':'DOSTIME.LOG','return':'RETURN.LOG'}[mode];raw=(d/filename).read_bytes()
      if mode=='keys':raw=raw.replace(b'L\r',b'I\r',1)
      elif mode=='date':raw=raw.replace(b'10/24/2026',b'10/25/2026')
      elif mode=='clock':raw=raw.replace(b'0:00:00.',b'1:00:00.')
      else:raw=b''
      (d/filename).write_bytes(raw);changed.append(filename)
     elif mode in {'event-name','forged-created-news','public-sale','packet-old-name','packet-price','packet-recipient','packet-sender','packet-extra','packet-counter','door-identity'}:
      filename='sidefiles.json.gz';x=json.loads(gzip.decompress((d/filename).read_bytes()));key='YTNEWS.DAT'if mode in {'event-name','forged-created-news','public-sale'}else'DORINFO1.DEF'if mode=='door-identity'else'YTRMSG.DAT';raw=bytearray.fromhex(x[key]['hex'])
      if mode=='event-name':raw=raw.replace(b'made a planet: New Eden',b'made a planet: Other')
      elif mode=='forged-created-news':raw=raw[:-1]+b'  -  Q  made a planet: New Eden\r\n\x1a'
      elif mode=='public-sale':raw=raw[:-1]+b'Q bought your port for 31 credits\r\n\x1a'
      elif mode=='packet-old-name':raw=raw[:12]+b'Q  bought your port "News Harbor" in 101 for 31 credits'.ljust(74,b' ')
      elif mode=='packet-price':raw=raw[:12]+b'Q  bought your port "Test Port" in 101 for 310 credits'.ljust(74,b' ')
      elif mode=='packet-recipient':v.put(raw,1,4,2)
      elif mode=='packet-sender':v.put(raw,1,8,2)
      elif mode=='packet-extra':raw=b'FORGED SELLER NOTICE'
      elif mode=='packet-counter':v.put(raw,1,0,1)
      elif mode=='door-identity':raw=raw.replace(b'ENEMY',b'TESTER')
      x[key].update(hex=raw.hex(),after_sha256=v.sha(raw));write_json(d/filename,x);changed.append(filename)
     else:
      text=(d/'transcript.txt').read_text()
      if mode=='identity':text=text.replace('Welcome Tester!','Welcome Other!')
      elif mode=='alias':text=re.sub(r'^Name  : Q ', 'Name  : Other ',text,flags=re.M)
      elif mode=='buyer-sees-seller':text+='\nQ  bought your port "Test Port" in 101 for 31 credits\n'
      elif mode in {'raw-only','text-only'}:text+='\nRAW/TEXT DIVERGENCE\n'
      else:raise AssertionError(mode)
      if mode=='raw-only':(d/'game.log.gz').write_bytes(gzip.compress(text.replace('\n','\r\n').encode('cp437'),mtime=0));changed.append('game.log.gz')
      elif mode=='text-only':(d/'transcript.txt').write_text(text);changed.append('transcript.txt')
      else:update_text(d,text,case,changed)
     for filename in changed:case['files'][filename]=v.sha((d/filename).read_bytes())
     write_json(d/'result.json',case)
     parent=case.get('parent');worlds={};aux={}
     if parent:
      worlds[parent]=v.zipped(DOS/parent/'after.dat.gz');aux[parent]={n:bytes.fromhex(r['hex'])for n,r in v.read(DOS/parent/'sidefiles.json').items()}
     try:
      with self.assertRaisesRegex(AssertionError,reason):v.verify_control(root,v.DECLARATIONS[name],case,v.zipped(DOS/'baseline.dat.gz'),worlds,aux)
     finally:shutil.rmtree(d)
  print(f'Rejected {len(controls)} rehashed runtime semantic/provenance corruptions.')
 def test_elapsed_display_positive(self):
  with tempfile.TemporaryDirectory(prefix='yt-news-event-elapsed-')as tmp:
   root=Path(tmp);name='planet-create';d=root/name;shutil.copytree(DOS/name,d);case=v.read(d/'result.json');changed=[]
   text,count=re.subn(r'Time: 179:[0-9]{2}','Time: 178:59',(d/'transcript.txt').read_text());self.assertGreater(count,0)
   update_text(d,text,case,changed)
   for filename in changed:case['files'][filename]=v.sha((d/filename).read_bytes())
   write_json(d/'result.json',case)
   v.verify_control(root,v.DECLARATIONS[name],case,v.zipped(DOS/'baseline.dat.gz'),{},{})
 def test_frozen_recipe(self):
  with tempfile.TemporaryDirectory(prefix='yt-news-event-recipe-')as tmp:
   root=Path(tmp);shutil.copy2(DOS/'baseline.dat.gz',root/'baseline.dat.gz');(root/'recipe.json').write_bytes((DOS/'recipe.json').read_bytes()+b' ')
   with self.assertRaisesRegex(AssertionError,'frozen declarations'):v.check(root)


if __name__=='__main__':unittest.main()
