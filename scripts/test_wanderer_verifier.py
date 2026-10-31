"""Rehashed semantic/provenance corruption controls for original Wanderer evidence."""
import contextlib
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'research/yt-wanderer'
spec=importlib.util.spec_from_file_location('wanderer_verifier',ROOT/'scripts/verify_wanderer.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
spec=importlib.util.spec_from_file_location('independent_fixture_mbf',ROOT/'archive/analysis/yt-maint/experiments.py')
mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)
sha=lambda data:hashlib.sha256(data).hexdigest()


def physical(path):
    return path if path.exists()else path.with_suffix(path.suffix+'.gz')


def write_json(path,value):
    actual=physical(path);data=(json.dumps(value,indent=2)+'\n').encode()
    actual.write_bytes(gzip.compress(data,mtime=0)if actual.suffix=='.gz'else data)


class SemanticCorruption(unittest.TestCase):
 def test_rehashed_controls(self):
  controls=[
   ('maint-linked','before',[(2,49,499)],'undeclared setup'),
   ('maint-linked','after',[(4052,73,2)],'maintenance governor reset'),
   ('maint-linked','after',[(4052,117,1235)],'linked bank settlement'),
   ('maint-zero-bank','after',[(4052,117,0)],'linked bank settlement'),
   ('maint-one-bank','after',[(4052,117,250000)],'linked bank settlement'),
   ('maint-inactive-linked','after',[(4052,85,12)],'linked name/activity preservation'),
   ('maint-duplicate-links','after',[(152,93,0)],'first-link-only relocation'),
   ('maint-missing-link','after',[(4052,117,1234)],'regenerated Wanderer fields'),
   ('maint-missing-link','after',[(4052,125,43)],'regenerated Wanderer fields'),
   ('maint-missing-link','after',[(4052,113,0)],'regeneration retained weapon stock'),
   ('maint-missing-stale-tail','after',[(4052,93,0)],'regeneration stale tail preservation'),
   ('maint-inactive-missing','after',[(4052,129,48)],'inactive regeneration weapon preservation'),
   ('maint-inactive-missing','after',[(4052,89,1)],'inactive regeneration clock preservation'),
   ('maint-only-earth','candidate',None,'candidate planet admission'),
   ('maint-same-day','after',[(4052,117,1)],'linked bank settlement'),
   ('reset-defaults','after',[(151,93,1)],'reset Wanderer remains inactive'),
   ('reset-defaults','after',[(4052,85,12)],'reset Wanderer remains inactive'),
   ('init-defaults','after',[(4052,85,0)],'initializer Wanderer fields'),
   ('transport-two','after',[(2,49,480)],'game ship turn/location settlement'),
   ('transport-two','after',[(2,57,2368)],'game ship turn/location settlement'),
   ('transport-two','after',[(2,125,0)],'transport cloak preservation'),
   ('transport-cancel','after',[(2,49,490)],'game ship turn/location settlement'),
   ('transport-nine','after',[(2,49,0)],'game ship turn/location settlement'),
   ('transport-zero-fighters','after',[(2,61,1)],'collision fighter bounds'),
   ('transport-occupied-planned','planet-name',None,'collision Wanderer deletion'),
   ('land-foreign-unguarded','after',[(4052,73,2)],'game governor/ground preservation'),
   ('land-owned','after',[(4052,45,999)],'planet production growth bound'),
   ('land-neutral','after',[(4052,77,24)],'adoption unrest bound'),
   ('land-team','after',[(52,77,1)],'team member recount'),
   ('bank-owned','after',[(2,81,100000)],'bank transfer conservation'),
   ('transfer-owned','after',[(2,61,9878)],'fighter transfer conservation'),
   ('transport-two','cargo',[(2,69,11)],'unrelated world mutation'),
   ('transport-two','zero-mantissa',None,'frozen complete world witness'),
   ('rename-renamed-slot','rename-name',None,'game planet name preservation'),
   ('transport-two','vanish',None,'Wanderer transport notices'),
   ('transport-two','privacy',None,'hidden transport destination'),
   ('maint-missing-link','regeneration-notice',None,'regeneration device notice'),
   ('land-neutral','unrest-notice',None,'adoption unrest receipt'),
   ('transport-two','normal-return',None,'normal quit'),
   ('maint-missing-link','news',None,'public regeneration event'),
   ('land-owned','score',None,'public scoreboard points'),
   ('land-owned','aux',None,'unrelated auxiliary effect'),
   ('land-owned','aux-input',None,'auxiliary input chain'),
   ('transport-two','keys',None,'exact input stream'),
   ('land-owned','date',None,'DOS date'),
   ('land-owned','clock',None,'DOS clock mismatch'),
   ('land-owned','return',None,'DOS return marker'),
   ('land-owned','incomplete',None,'incomplete DOS control'),
   ('land-owned','recipe',None,'frozen declarations'),
   ('land-owned','native',None,'native bytes'),
   ('land-owned','relocation',None,'native relocation'),
  ]
  with tempfile.TemporaryDirectory(prefix='yt-wanderer-negative-')as temp:
   root=Path(temp)/'research';shutil.copytree(SOURCE,root)
   for name,kind,patches,reason in controls:
    with self.subTest(name=name,kind=kind):
     directory=root/'dos'/name;case=v.read(directory/'result.json');changed=[]
     if kind in {'before','after','cargo','candidate','planet-name','rename-name','zero-mantissa'}:
      label='before'if kind=='before'else'after';file=label+'.dat.gz'
      world=bytearray(gzip.decompress((directory/file).read_bytes()))
      for record,offset,value in patches or():mbf.put(world,record,offset,value)
      if kind=='cargo':mbf.put(world,2,109,v.public_score(world,2))
      if kind=='candidate':mbf.put(world,52,93,2);mbf.put(world,3051,93,1)
      if kind=='planet-name':world[4051*137+4]=65
      if kind=='rename-name':world[4051*137:4051*137+41]=b'Forged'.ljust(41,b' ')
      if kind=='zero-mantissa':
       at=150*137+93;assert world[at+3]==0;world[at]^=1
      (directory/file).write_bytes(gzip.compress(world,mtime=0));changed.append(file)
     elif kind in {'vanish','privacy','regeneration-notice','unrest-notice','normal-return'}:
      file='game.log.gz';raw=gzip.decompress((directory/file).read_bytes())
      old,new={
       'vanish':(b'The Wanderer vanishes from your sensors!',b'REMOVED'),
       'privacy':(b'The Wanderer vanishes from your sensors!',b'The Wanderer vanishes from your sensors! Destination2368'),
       'regeneration-notice':(b'The Wanderer regenerated with P.H.O.E.N.I.X. device!',b'REMOVED'),
       'unrest-notice':(b'ground forces have been reduced to 2 from 23!',b'ground forces have been reduced to 3 from 23!'),
       'normal-return':(b'Returning to Yankee Trader Local Logon Program...',b'REMOVED'),
      }[kind]
      assert old in raw,kind;raw=raw.replace(old,new)
      (directory/file).write_bytes(gzip.compress(raw,mtime=0));(directory/'transcript.txt').write_text(raw.decode('cp437').replace('\r\n','\n'));changed.extend([file,'transcript.txt'])
     elif kind in {'news','score','aux'}:
      file='sidefiles.json.gz';side=json.loads(gzip.decompress((directory/file).read_bytes()))
      target={'news':'YTNEWS.DAT','score':'YTSCORE.ASC','aux':'YTNAME.DAT'}[kind];value=bytes.fromhex(side[target]['hex'])
      if kind=='news':assert b'P.H.O.E.N.I.X.'in value;value=value.replace(b'P.H.O.E.N.I.X.',b'FORGED')
      elif kind=='score':assert b'11,629,000'in value;value=value.replace(b'11,629,000',b'11,629,001')
      else:value+=b'FORGED'
      side[target]['hex']=value.hex();side[target]['after_sha256']=sha(value)
      (directory/file).write_bytes(gzip.compress(json.dumps(side).encode(),mtime=0));changed.append(file)
     elif kind=='aux-input':
      file='side-before.json.gz';side=json.loads(gzip.decompress((directory/file).read_bytes()));side['YTNAME.DAT']='00';(directory/file).write_bytes(gzip.compress(json.dumps(side).encode(),mtime=0));changed.append(file)
     elif kind=='keys':
      file='KEYS.TXT';raw=(directory/file).read_bytes();assert b'102'in raw;(directory/file).write_bytes(raw.replace(b'102',b'103'));changed.append(file)
     elif kind=='date':
      file='DOSDATE.LOG';raw=(directory/file).read_bytes();assert b'10/24/2026'in raw;(directory/file).write_bytes(raw.replace(b'10/24/2026',b'10/25/2026'));changed.append(file)
     elif kind=='clock':
      file='DOSTIME.LOG';raw=(directory/file).read_bytes();assert b'0:00:00.'in raw;(directory/file).write_bytes(raw.replace(b'0:00:00.',b'1:00:00.'));changed.append(file)
     elif kind=='return':file='RETURN.LOG';(directory/file).write_bytes(b'');changed.append(file)
     elif kind=='incomplete':case['complete']=False
     elif kind=='recipe':path=root/'dos/recipe.json';path.write_bytes(path.read_bytes()+b' ')
     elif kind in {'native','relocation'}:
      path=root/'rea/ytmaint.json';bundle=json.loads(path.read_text())
      if kind=='native':
       row=next(r for r in bundle['records']if r['operation']=='read_bytes')['normalized_result'];raw=bytearray.fromhex(row['bytes_hex']);raw[0]^=1;row['bytes_hex']=raw.hex()
      else:
       row=next(r for r in bundle['records']if r['operation']=='inspect_native_load_image')['normalized_result'];row['observations']['relocations'][0]['memory_bytes_hex']='0000'
      path.write_text(json.dumps(bundle)+'\n')
     else:raise AssertionError(kind)
     for file in changed:case['files'][file]=sha((directory/file).read_bytes())
     if changed or kind=='incomplete':
      write_json(directory/'result.json',case);path=root/'dos/results.json';manifest=v.read(path);manifest['scenarios']=[case if r['name']==name else r for r in manifest['scenarios']];write_json(path,manifest)
     try:
      with contextlib.redirect_stdout(io.StringIO()):
       with self.assertRaisesRegex(AssertionError,reason):v.verify(root)
     finally:
      shutil.rmtree(directory);shutil.copytree(SOURCE/'dos'/name,directory)
      for file in('dos/results.json','dos/recipe.json','rea/ytmaint.json'):
       original=physical(SOURCE/file);target=physical(root/file);shutil.copy2(original,target)
  print(f'Rejected {len(controls)} rehashed Wanderer semantic and provenance corruptions.')

 def test_rehashed_diagnostics(self):
  controls=[
   ('no-vacancy','completion','bounded diagnostic timeout/nonreturn'),
   ('no-vacancy','optimism','optimistic timeout notice/noncompletion'),
   ('later-npc-interference','aftermath','later NPC destruction outcome'),
   ('later-npc-interference','order','later NPC destruction phase order'),
  ]
  with tempfile.TemporaryDirectory(prefix='yt-wanderer-diagnostic-negative-')as temp:
   root=Path(temp)/'research';shutil.copytree(SOURCE,root)
   for label,kind,reason in controls:
    with self.subTest(label=label,kind=kind):
     relative=('exploratory/no-vacancy/maint-no-vacancy'if label=='no-vacancy'else'exploratory/later-npc-interference/transport-maintenance')
     d=root/relative;case=v.read(d/'result.json');changed=[]
     if kind=='completion':case['complete']=True
     elif kind=='aftermath':
      file='after.dat.gz';world=bytearray(gzip.decompress((d/file).read_bytes()));mbf.put(world,4052,85,12);(d/file).write_bytes(gzip.compress(world,mtime=0));changed.append(file)
     else:
      file='game.log.gz';raw=gzip.decompress((d/file).read_bytes())
      old=(b'Wanderer has successfully warped!'if kind=='optimism'else b'Planet "The Wanderer" destroyed!');assert old in raw
      raw=raw.replace(old,b'REMOVED');(d/file).write_bytes(gzip.compress(raw,mtime=0));(d/'transcript.txt').write_text(raw.decode('cp437').replace('\r\n','\n'));changed.extend([file,'transcript.txt'])
     for file in changed:case['files'][file]=sha((d/file).read_bytes())
     write_json(d/'result.json',case)
     if label=='no-vacancy':
      manifest=v.read(d.parent/'results.json');manifest['scenarios']=[case];write_json(d.parent/'results.json',manifest)
     try:
      with contextlib.redirect_stdout(io.StringIO()):
       with self.assertRaisesRegex(AssertionError,reason):v.verify(root)
     finally:
      shutil.rmtree(d);shutil.copytree(SOURCE/relative,d)
      if label=='no-vacancy':shutil.copy2(physical(SOURCE/'exploratory/no-vacancy/results.json'),physical(d.parent/'results.json'))
  print('Rejected 4 rehashed timeout/interference diagnostic corruptions.')


if __name__=='__main__':unittest.main()
