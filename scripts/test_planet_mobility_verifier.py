"""Rehashed negative controls for DOS planetary thrusters and forced landing."""
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
SOURCE=ROOT/'research/yt-planet-mobility'
spec=importlib.util.spec_from_file_location('mobility_verifier',ROOT/'scripts/verify_planet_mobility.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
spec=importlib.util.spec_from_file_location('independent_fixture_mbf',ROOT/'archive/analysis/yt-maint/experiments.py')
mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)
sha=lambda data:hashlib.sha256(data).hexdigest()


class SemanticCorruption(unittest.TestCase):
 def test_rehashed_controls(self):
  controls=[
   ('move-one','before',[(2,49,499)],'undeclared setup'),
   ('move-one','after',[(2,49,491)],'turn debit'),
   ('move-two','after',[(2,57,101)],'final ship sector'),
   ('move-two','after',[(152,93,2)],'planet sector links'),
   ('move-cloak-boundary','after',[(2,125,0)],'thruster cloak preservation'),
   ('move-one','after',[(4053,45,999)],'planet production growth bound'),
   ('move-one','after',[(4053,117,0)],'planet bank preservation'),
   ('move-one','after',[(4053,69,0)],'planet weapon preservation'),
   ('move-one','cargo',[(2,69,11)],'unrelated world mutation'),
   ('collision-first','after',[(4054,77,1)],'collision target preservation'),
   ('collision-first','after',[(2,45,1)],'ship death preservation'),
   ('collision-later','after',[(2,49,480)],'turn debit'),
   ('collision-zero-fighters','after',[(2,61,1)],'explosion fighter bounds'),
   ('collision-first','planet-name',None,'moving planet deletion'),
   ('move-wanderer','after',[(2,57,305)],'final ship sector'),
   ('move-mines','after',[(2,53,8860)],'mine aftermath settlement'),
   ('move-mines','after',[(152,129,1)],'arrival mines consumed'),
   ('force-partial','after',[(2,121,899)],'committed ground debit'),
   ('force-partial','after',[(4053,77,93)],'captured ownership/garrison'),
   ('force-loss','after',[(4053,73,2)],'failed assault preservation'),
   ('force-fraction','after',[(2,121,998)],'committed ground debit'),
   ('land-fractional-defender','after',[(4053,77,1)],'fractional defender floor'),
   ('land-teammate','after',[(52,77,1)],'team member recount'),
   ('force-invalid','after',[(4053,73,2)],'planet ownership/ground settlement'),
   ('force-no-ship-defenses','after',[(2,53,1)],'public score arithmetic'),
   ('move-one','zero-mantissa',None,'frozen complete world witness'),
   ('move-one','completion',None,'move completion notice'),
   ('force-partial','ground-trace',None,'attacker casualty bound'),
   ('move-one','normal-return',None,'normal quit'),
   ('move-mines','news',None,'exact public event settlement'),
   ('force-partial','score',None,'public scoreboard points'),
   ('move-one','aux',None,'unrelated auxiliary effect'),
   ('move-one','aux-input',None,'auxiliary input chain'),
   ('move-one','keys',None,'exact input stream'),
   ('move-one','date',None,'DOS date'),
   ('move-one','clock',None,'DOS clock mismatch'),
   ('move-one','return',None,'DOS return marker'),
   ('move-one','incomplete',None,'incomplete DOS control'),
   ('move-one','recipe',None,'frozen declarations'),
   ('move-one','native',None,'native bytes'),
   ('move-one','relocation',None,'native relocation'),
  ]
  with tempfile.TemporaryDirectory(prefix='yt-mobility-negative-')as temp:
   root=Path(temp)/'research';shutil.copytree(SOURCE,root)
   for name,kind,patches,reason in controls:
    with self.subTest(name=name,kind=kind):
     directory=root/'dos'/name;case=json.loads((directory/'result.json').read_text());changed=[]
     if kind in {'before','after','cargo','planet-name','zero-mantissa'}:
      label='before'if kind=='before'else'after';file=label+'.dat.gz'
      world=bytearray(gzip.decompress((directory/file).read_bytes()))
      for record,offset,value in patches or():mbf.put(world,record,offset,value)
      if kind=='cargo':mbf.put(world,2,109,v.public_score(world,2))
      if kind=='planet-name':world[(4053-1)*137+4]=65
      if kind=='zero-mantissa':
       at=(151-1)*137+93;assert world[at+3]==0;world[at]^=1
      (directory/file).write_bytes(gzip.compress(world,mtime=0));changed.append(file)
     elif kind in {'completion','ground-trace','normal-return'}:
      file='game.log.gz';raw=gzip.decompress((directory/file).read_bytes())
      old,new={
       'completion':(b'Test Planet moved! (Xannoron Movers, we move anyTHING, anyWHERE!)',b'REMOVED'),
       'ground-trace':(b'Your forces remaining  : 92!',b'Your forces remaining  : 1!'),
       'normal-return':(b'Returning to Yankee Trader Local Logon Program...',b'REMOVED'),
      }[kind]
      assert old in raw,(kind,raw);raw=raw.replace(old,new)
      (directory/file).write_bytes(gzip.compress(raw,mtime=0));(directory/'transcript.txt').write_text(raw.decode('cp437').replace('\r\n','\n'));changed.extend([file,'transcript.txt'])
     elif kind in {'news','score','aux'}:
      file='sidefiles.json.gz';side=json.loads(gzip.decompress((directory/file).read_bytes()))
      target={'news':'YTNEWS.DAT','score':'YTSCORE.ASC','aux':'YTNAME.DAT'}[kind];value=bytes.fromhex(side[target]['hex'])
      if kind=='news':assert b'Shields reduced to 8859'in value;value=value.replace(b'Shields reduced to 8859',b'Shields reduced to 8860')
      elif kind=='score':assert b'11,554,000'in value;value=value.replace(b'11,554,000',b'11,554,001')
      else:value+=b'FORGED'
      side[target]['hex']=value.hex();side[target]['after_sha256']=sha(value)
      (directory/file).write_bytes(gzip.compress(json.dumps(side).encode(),mtime=0));changed.append(file)
     elif kind=='aux-input':
      file='side-before.json.gz';side=json.loads(gzip.decompress((directory/file).read_bytes()));side['YTNAME.DAT']='00';(directory/file).write_bytes(gzip.compress(json.dumps(side).encode(),mtime=0));changed.append(file)
     elif kind=='keys':
      file='KEYS.TXT';raw=(directory/file).read_bytes();assert b'101'in raw;(directory/file).write_bytes(raw.replace(b'101',b'102'));changed.append(file)
     elif kind=='date':
      file='DOSDATE.LOG';raw=(directory/file).read_bytes();assert b'10/24/2026'in raw;(directory/file).write_bytes(raw.replace(b'10/24/2026',b'10/25/2026'));changed.append(file)
     elif kind=='clock':
      file='DOSTIME.LOG';raw=(directory/file).read_bytes();assert b'0:00:00.'in raw;(directory/file).write_bytes(raw.replace(b'0:00:00.',b'1:00:00.'));changed.append(file)
     elif kind=='return':file='RETURN.LOG';(directory/file).write_bytes(b'');changed.append(file)
     elif kind=='incomplete':case['complete']=False
     elif kind=='recipe':path=root/'dos/recipe.json';path.write_bytes(path.read_bytes()+b' ')
     elif kind in {'native','relocation'}:
      path=root/'rea/yt.json';bundle=json.loads(path.read_text())
      if kind=='native':
       row=next(r for r in bundle['records']if r['operation']=='read_bytes')['normalized_result'];raw=bytearray.fromhex(row['bytes_hex']);raw[0]^=1;row['bytes_hex']=raw.hex()
      else:
       row=next(r for r in bundle['records']if r['operation']=='inspect_native_load_image')['normalized_result'];row['observations']['relocations'][0]['memory_bytes_hex']='0000'
      path.write_text(json.dumps(bundle)+'\n')
     else:raise AssertionError(kind)
     for file in changed:case['files'][file]=sha((directory/file).read_bytes())
     if changed or kind=='incomplete':
      (directory/'result.json').write_text(json.dumps(case,indent=2)+'\n');path=root/'dos/results.json';manifest=json.loads(path.read_text());manifest['scenarios']=[case if r['name']==name else r for r in manifest['scenarios']];path.write_text(json.dumps(manifest,indent=2)+'\n')
     try:
      with contextlib.redirect_stdout(io.StringIO()):
       with self.assertRaisesRegex(AssertionError,reason):v.verify(root)
     finally:
      shutil.rmtree(directory);shutil.copytree(SOURCE/'dos'/name,directory)
      for file in('dos/results.json','dos/recipe.json','rea/yt.json'):shutil.copy2(SOURCE/file,root/file)
  print(f'Rejected {len(controls)} rehashed planetary mobility/landing semantic and provenance corruptions.')


if __name__=='__main__':unittest.main()
