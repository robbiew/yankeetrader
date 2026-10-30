"""Rehashed semantic corruption controls for the isolated Genesis/reset corpus."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'research/yt-genesis'
spec=importlib.util.spec_from_file_location('mbf',ROOT/'archive/analysis/yt-maint/experiments.py');mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)
sha=lambda value:hashlib.sha256(value).hexdigest()


class SemanticCorruption(unittest.TestCase):
 def test_rehashed_controls(self):
  cases=[
   ('owned-300','before',[(2,117,299)],'undeclared setup'),
   ('owned-300','after',[(2,81,1)],'cleared human record'),
   ('owned-300','after',[(3053,97,2)],'cleared port ownership/treasury'),
   ('owned-300','after',[(3053,89,1)],'cleared port ownership/treasury'),
   ('owned-300','after',[(1,49,501)],'reset configuration carryover'),
   ('lottery-zero','after',[(1,101,0)],'reset configuration carryover'),
   ('cargo-low','after',[(1,121,4)],'reset configuration carryover'),
   ('owned-300','after',[(1,125,7000)],'reset configuration carryover'),
   ('owned-300','after',[(1,81,297)],'reset configuration carryover'),
   ('owned-300','after',[(3052,49,1)],'reset port stocks'),
   ('owned-300','after',[(52,65,17)],'Earth reset links'),
   ('owned-300','after',[(53,41,2)],'warp destination bounds'),
   ('owned-300','after',[(53,69,1)],'reset sector residue'),
   ('owned-300','after',[(3053,61,0)],'reset port production'),
   ('owned-300','after',[(4053,85,1)],'inactive planet buffer pattern'),
   ('records-only','after',[(2,117,300)],'nonreset world conservation'),
   ('owned-299','after',[(2,109,20002500)],'nonreset world conservation'),
   ('missing-initializer','after',[(2,81,0)],'nonreset world conservation'),
   ('first-maintenance','after',[(3052,49,0)],'initial maintenance port stocks'),
   ('first-maintenance','after',[(1,81,296)],'first maintenance date'),
   ('first-maintenance','home-name',None,'initial maintenance faction homes'),
   ('first-maintenance','maintenance-score',None,'frozen maintenance auxiliary witness'),
   ('first-maintenance','maintenance-news',None,'frozen maintenance auxiliary witness'),
   ('owned-300','zero-mantissa',None,'frozen complete world witness'),
   ('owned-300','completion',None,'reset completion message'),
   ('winner-mapping','winner-display',None,'reset winner display'),
   ('marker-resume','confirmation',None,'reset confirmation mode'),
   ('owned-300','side-output',None,'unrelated auxiliary effect'),
   ('winner-mapping','scoreboard',None,'stale scoreboard preserved'),
   ('owned-300','winner-news',None,'reset public winner'),
   ('owned-300','winner-radio',None,'reset radio winner'),
   ('owned-300','alias',None,'reset aliases'),
   ('missing-initializer','handoff',None,'preserved handoff marker'),
   ('malformed-marker','marker-return',None,'auxiliary file set'),
   ('marker-resume','side-input',None,'auxiliary input chain'),
   ('standalone-yes','keys',None,'exact input stream'),
   ('owned-300','date',None,'DOS date'),
   ('owned-300','clock',None,'declared clock'),
   ('owned-300','return',None,'DOS return marker'),
   ('owned-300','incomplete',None,'incomplete DOS control'),
   ('owned-300','native',None,'native bytes'),
   ('owned-300','recipe',None,'frozen declarations'),
  ]
  with tempfile.TemporaryDirectory(prefix='yt-genesis-negative-')as temp:
   root=Path(temp)/'research';shutil.copytree(SOURCE,root)
   for name,kind,patches,reason in cases:
    with self.subTest(name=name,kind=kind):
     d=root/'dos'/name;c=json.loads((d/'result.json').read_text());changed=[]
     if kind in('before','after','home-name','zero-mantissa'):
      label=kind if kind in('before','after')else'after';file=label+'.dat.gz';world=bytearray(gzip.decompress((d/file).read_bytes()))
      for rec,off,value in patches or():mbf.put(world,rec,off,value)
      if kind=='home-name':world[(4052-1)*137:(4052-1)*137+41]=b'Missing'.ljust(41,b' ')
      if kind=='zero-mantissa':
       at=(53-1)*137+53;assert world[at+3]==0;world[at]^=1
      (d/file).write_bytes(gzip.compress(world,mtime=0));changed.append(file)
     elif kind in('completion','winner-display','confirmation'):
      file='game.log.gz';raw=gzip.decompress((d/file).read_bytes())
      old,new={
       'completion':(b'Initialization completed sucessfully!',b'REMOVED'),
       'winner-display':(b'Congratulations ! You have fulfilled the prophesy!!',b'Congratulations Q! You have fulfilled the prophesy!!'),
       'confirmation':(b'Initializing ports...',b'Do you wish to re-init Y.T. using your old default values?\r\nInitializing ports...'),
      }[kind]
      assert old in raw;raw=raw.replace(old,new)
      (d/file).write_bytes(gzip.compress(raw,mtime=0));(d/'transcript.txt').write_text(raw.decode('cp437').replace('\r\n','\n'));changed.extend([file,'transcript.txt'])
     elif kind in('side-output','scoreboard','winner-news','winner-radio','alias','handoff','marker-return','maintenance-score','maintenance-news'):
      file='sidefiles.json.gz';values=json.loads(gzip.decompress((d/file).read_bytes()));initial=json.loads(gzip.decompress((d/'side-before.json.gz').read_bytes()))
      target={'side-output':'KEEPME.DAT','scoreboard':'YTSCORE.ASC','winner-news':'YTNEWS.DAT','winner-radio':'YTRMSG.DAT','alias':'YTNAME.DAT','handoff':'RMTINIT.TMP','marker-return':'RMTINIT.TMP','maintenance-score':'YTSCORE.ASC','maintenance-news':'YTNEWS.DAT'}[kind]
      value=bytes.fromhex(values[target]['hex'])if target in values else b''
      if kind=='scoreboard':value=b'Empty new scoreboard\r\n'
      elif kind in('winner-news','winner-radio'):
       assert b'fulfilled by !!'in value;value=value.replace(b'fulfilled by !!',b'fulfilled by Q!!')
      elif kind=='alias':value=b'Dummy,Dummy,Dummy,Dummy\r\nTester,,Q,\r\n\x1a'
      elif kind=='handoff':value=b'OTHER.DEF\r\n\x1a'
      elif kind=='marker-return':value=b'MISSING.DEF\r\n\x1a'
      elif kind in('maintenance-score','maintenance-news'):value+=b'FORGED MAINTENANCE AUXILIARY DATA\r\n'
      else:value+=b'\x01'
      values[target]=dict(hex=value.hex(),after_sha256=sha(value),before_sha256=sha(bytes.fromhex(initial[target]))if target in initial else None)
      (d/file).write_bytes(gzip.compress(json.dumps(values).encode(),mtime=0));changed.append(file)
     elif kind=='side-input':
      file='side-before.json.gz';values=json.loads(gzip.decompress((d/file).read_bytes()));values['KEEPME.DAT']='01';(d/file).write_bytes(gzip.compress(json.dumps(values).encode(),mtime=0));changed.append(file)
     elif kind=='keys':
      file='KEYS.TXT';value=(d/file).read_bytes();assert b'Y'in value;(d/file).write_bytes(value.replace(b'Y',b'N',1));changed.append(file)
     elif kind=='date':
      file='DOSDATE.LOG';value=(d/file).read_bytes();assert b'10/24/2026'in value;(d/file).write_bytes(value.replace(b'10/24/2026',b'10/25/2026'));changed.append(file)
     elif kind=='clock':
      file='DOSTIME.LOG';value=(d/file).read_bytes();assert b'0:00:00.'in value;c['time']='01:00:00';(d/file).write_bytes(value.replace(b'0:00:00.',b'1:00:00.'));changed.append(file)
     elif kind=='return':file='RETURN.LOG';(d/file).write_bytes(b'');changed.append(file)
     elif kind=='incomplete':c['complete']=False
     elif kind=='recipe':path=root/'dos/recipe.json';path.write_bytes(path.read_bytes()+b' ')
     elif kind=='native':
      path=root/'rea/rmt-init.json';bundle=json.loads(path.read_text());v=bundle['records'][0]['normalized_result'];value=bytearray.fromhex(v['bytes_hex']);value[0]^=1;v['bytes_hex']=value.hex();path.write_text(json.dumps(bundle)+'\n')
     else:raise AssertionError(kind)
     for file in changed:c['files'][file]=sha((d/file).read_bytes())
     if changed or kind=='incomplete':
      (d/'result.json').write_text(json.dumps(c,indent=2)+'\n');path=root/'dos/results.json';manifest=json.loads(path.read_text());manifest['scenarios']=[c if v['name']==name else v for v in manifest['scenarios']];path.write_text(json.dumps(manifest,indent=2)+'\n')
     try:
      result=subprocess.run([sys.executable,str(ROOT/'scripts/verify_genesis_reset.py'),'--research',str(root)],capture_output=True,text=True,timeout=30)
      self.assertNotEqual(result.returncode,0,result.stdout);self.assertIn('AssertionError',result.stderr);self.assertIn(reason,result.stderr)
     finally:
      shutil.rmtree(d);shutil.copytree(SOURCE/'dos'/name,d)
      for file in('dos/results.json','dos/recipe.json','rea/yt.json','rea/rmt-init.json'):shutil.copy2(SOURCE/file,root/file)
  print('Rejected 42 rehashed Genesis semantic/provenance corruptions.')


if __name__=='__main__':unittest.main()
