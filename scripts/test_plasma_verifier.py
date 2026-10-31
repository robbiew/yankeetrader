"""Rehashed semantic and provenance corruption controls for retained plasma evidence."""
import contextlib
import gzip
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
SOURCE=ROOT/'research/yt-plasma'
spec=importlib.util.spec_from_file_location('plasma_verifier',ROOT/'scripts/verify_plasma.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
# A separate preexisting encoder changes fixtures; the verifier decodes independently.
spec=importlib.util.spec_from_file_location('fixture_mbf',ROOT/'archive/analysis/yt-maint/experiments.py');mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)

def write_json(path,value):
    data=(json.dumps(value,indent=2)+'\n').encode();path.write_bytes(gzip.compress(data,mtime=0) if path.suffix=='.gz' else data)

def target(root,name,rows):
    declarations={r['name']:r for r in v.read(root/'dos/recipe.json')['scenarios']}
    worlds={};aux={}
    parent=rows[name].get('parent')
    if parent:
        worlds[parent]=v.zipped(root/'dos'/parent/'after.dat.gz')
        aux[parent]={n:bytes.fromhex(r['hex']) for n,r in v.read(root/'dos'/parent/'sidefiles.json').items()}
    return v.verify_control(root/'dos',declarations[name],rows[name],v.zipped(root/'dos/baseline.dat.gz'),worlds,aux)

class SemanticCorruption(unittest.TestCase):
 def test_rehashed_controls(self):
  controls=[
   ('empty-adjacent','after',[(2,113,9)],'saved plasma debit'),
   ('empty-adjacent','after',[(2,49,500)],'saved launch turns'),
   ('one-turn','after',[(2,49,1)],'saved launch turns'),
   ('no-bolts','after',[(2,49,499)],'saved launch turns'),
   ('negative-count','after',[(2,113,8)],'saved plasma debit'),
   ('oversized-count','after',[(2,113,0)],'saved plasma debit'),
   ('empty-adjacent','after',[(2,57,101)],'launcher sector preserved'),
   ('own-sector','after',[(2,53,1000000)],'self-target damage'),
   ('own-sector-cloaked','after',[(2,61,10000)],'self-target damage'),
   ('enemy-ship','after',[(3,53,1000000)],'indiscriminate ship damage'),
   ('cloaked-ship','after',[(3,53,1000000)],'indiscriminate ship damage'),
   ('team-ship','after',[(3,53,1000000)],'indiscriminate ship damage'),
   ('fighters-enemy','after',[(152,81,1000000)],'sector fighter casualty receipt'),
   ('fighters-self','after',[(152,81,1000000)],'sector fighter casualty receipt'),
   ('hole-target-defenses','after',[(643,81,999999)],'hole before defenses'),
   ('mines-only','after',[(152,129,10000)],'sector mine casualty receipt'),
   ('planet-small','after',[(152,93,2)],'planet destruction link cleanup'),
   ('planet-zero','after',[(4053,73,3)],'planet destruction link cleanup'),
   ('planet-small','after',[(4053,57,1)],'planet destruction resources'),
   ('planet-productive','after',[(4053,77,5000)],'surviving planet damage'),
   ('lethal-ship','after',[(3,45,3)],'ship death attribution'),
   ('lethal-ship','after',[(2,81,100000)],'salvage saved receipt'),
   ('two-ships','after',[(4,53,999999)],'ordered shared ship energy'),
   ('quiet-origin','after',[(2,69,11)],'unrelated world mutation'),
   ('empty-adjacent','score',[(2,109,1)],'saved score arithmetic'),
   ('empty-adjacent','before',[(2,53,999999)],'undeclared setup'),
   ('volley-reload','before',[(2,113,9)],'broken world chain'),
   ('planet-reload','aux-input',None,'auxiliary input chain'),
   ('empty-adjacent','keys',None,'exact input stream'),
   ('empty-adjacent','date',None,'DOS date'),
   ('empty-adjacent','clock',None,'DOS clock mismatch'),
   ('empty-adjacent','return',None,'DOS return marker'),
   ('empty-adjacent','incomplete',None,'incomplete DOS control'),
   ('empty-adjacent','timeout',None,'capture timeout declaration'),
   ('empty-adjacent','binary',None,'binary/session identity'),
   ('empty-adjacent','patches',None,'declared patch list'),
   ('empty-adjacent','raw-only',None,'raw transcript identity'),
   ('empty-adjacent','text-only',None,'raw transcript identity'),
   ('two-hop','attenuation',None,'two-hop fixed attenuation'),
   ('three-hop','attenuation',None,'three-hop fixed attenuation'),
   ('range-exhaustion','attenuation',None,'finite attenuation range'),
   ('mixed-defense','mixed-order',None,'mixed absorption and wreck order'),
   ('planet-small','planet-destroyed',None,'planet destruction link cleanup'),
   ('empty-adjacent','energy',None,'launch energy arithmetic'),
   ('empty-adjacent','turn-receipt',None,'launch turn receipt count'),
   ('hole-592','deflection',None,'hole deflection receipt'),
   ('empty-adjacent','aux',None,'frozen complete auxiliary witness'),
  ]
  with tempfile.TemporaryDirectory(prefix='yt-plasma-negative-') as tmp:
   root=Path(tmp)/'research';shutil.copytree(SOURCE,root)
   original_rows={r['name']:r for r in v.read(SOURCE/'dos/results.json')['scenarios']}
   for name,kind,patches,reason in controls:
    with self.subTest(name=name,kind=kind):
     d=root/'dos'/name;case=v.read(d/'result.json');changed=[]
     if kind in {'before','after','score'}:
      file=('before' if kind=='before' else 'after')+'.dat.gz';world=bytearray(v.zipped(d/file))
      for r,o,value in patches:mbf.put(world,r,o,value)
      if kind=='after':
       for r in (2,3,4):
        if v.get(world,r,109)>=0:mbf.put(world,r,109,v.public_score(world,r))
      (d/file).write_bytes(gzip.compress(world,mtime=0));changed.append(file)
     elif kind in {'aux-input','aux'}:
      file='side-before.json.gz' if kind=='aux-input' else 'sidefiles.json.gz';a=json.loads(v.zipped(d/file))
      if kind=='aux-input':a['YTNAME.DAT']='00'
      else:
       key='YTNAME.DAT';raw=bytes.fromhex(a[key]['hex'])+b'FORGED';a[key]['hex']=raw.hex();a[key]['after_sha256']=v.sha(raw)
      write_json(d/file,a);changed.append(file)
     elif kind in {'keys','date','clock','return'}:
      file={'keys':'KEYS.TXT','date':'DOSDATE.LOG','clock':'DOSTIME.LOG','return':'RETURN.LOG'}[kind];raw=(d/file).read_bytes()
      if kind=='keys':raw=raw.replace(b'+;101;1',b'+;102;1')
      elif kind=='date':raw=raw.replace(b'10/24/2026',b'10/25/2026')
      elif kind=='clock':raw=raw.replace(b'0:00:00.',b'1:00:00.')
      else:raw=b''
      (d/file).write_bytes(raw);changed.append(file)
     elif kind=='incomplete':case['complete']=False
     elif kind=='timeout':case['timeout_seconds']=45
     elif kind=='binary':case['binaries']['YT.EXE']='0'*64
     elif kind=='patches':case['applied_patches']=case['applied_patches'][:-1]
     elif kind in {'raw-only','text-only','attenuation','energy','turn-receipt','deflection','mixed-order','planet-destroyed'}:
      raw=v.zipped(d/'game.log.gz')
      if kind=='text-only':(d/'transcript.txt').write_text((d/'transcript.txt').read_text()+'FORGED');changed.append('transcript.txt')
      else:
       old,new={
        'raw-only':(b'2500000 Megawatts',b'2400000 Megawatts'),
        'attenuation':(b'2450000 Megawatts',b'2449999 Megawatts'),
        'energy':(b'firing 2500000 megawatts!',b'firing 2500001 megawatts!'),
        'turn-receipt':(b'One Turn Deducted,',b'No Turn Deducted,'),
        'deflection':(b'The plasma bolt is deflected by a black hole',b'The plasma bolt silently passes a black hole'),
        'mixed-order':(b'destroyed 1 mines in sector 101!',b'destroyed 0 mines in sector 101!'),
        'planet-destroyed':(b'The planet was destroyed!!',b'The planet was spared!!'),
       }[kind]
       assert old in raw,kind;raw=raw.replace(old,new,1);(d/'game.log.gz').write_bytes(gzip.compress(raw,mtime=0));changed.append('game.log.gz')
       if kind!='raw-only':(d/'transcript.txt').write_text(raw.decode('cp437').replace('\r\n','\n'));changed.append('transcript.txt')
     else:raise AssertionError(kind)
     for file in changed:case['files'][file]=v.sha((d/file).read_bytes())
     if changed or kind in {'incomplete','timeout','binary','patches'}:
      write_json(d/'result.json.gz',case)
     try:
      # Mirror the rewritten manifest row in memory: unrelated 62-row patch
      # metadata need not be reparsed for each independently rehashed case.
      rows={**original_rows,name:case}
      with self.assertRaisesRegex(AssertionError,reason):target(root,name,rows)
     finally:
      shutil.rmtree(d);shutil.copytree(SOURCE/'dos'/name,d)
  print(f'Rejected {len(controls)} rehashed plasma control corruptions.')

 def test_native_and_declarations(self):
  controls=['recipe','native-bytes','relocation','mapping','ledger','profile']
  with tempfile.TemporaryDirectory(prefix='yt-plasma-native-negative-') as tmp:
   root=Path(tmp)/'research';shutil.copytree(SOURCE,root)
   for kind in controls:
    with self.subTest(kind=kind):
     if kind=='recipe':p=root/'dos/recipe.json';p.write_bytes(p.read_bytes()+b' ');reason='frozen declarations'
     elif kind=='ledger':p=root/'rea/ledger.json';p.write_bytes(p.read_bytes()+b' ');reason='native ledger identity'
     else:
      p=root/'rea/yt.json';b=v.read(p)
      if kind=='profile':
       next(r for r in b['records'] if r['operation']=='read_bytes')['analysis_profile']['digest']='0'*64;reason='native analysis profile'
      elif kind=='native-bytes':
       row=next(r for r in b['records'] if r['operation']=='read_bytes')['normalized_result'];raw=bytearray.fromhex(row['bytes_hex']);raw[0]^=1;row['bytes_hex']=raw.hex();reason='native bytes'
      else:
       row=next(r for r in b['records'] if r['operation']=='inspect_native_load_image')['normalized_result']['observations']
       if kind=='relocation':row['relocations'][0]['memory_bytes_hex']='0000';reason='native relocation bytes'
       else:next(m for m in row['mappings'] if m['initialized'])['sha256']='0'*64;reason='native mapped bytes'
      write_json(p,b)
     try:
      with contextlib.redirect_stdout(io.StringIO()):
       with self.assertRaisesRegex(AssertionError,reason):v.verify(root) if kind=='recipe' else v.verify_native(root)
     finally:
      shutil.copy2(SOURCE/'dos/recipe.json',root/'dos/recipe.json');shutil.copy2(SOURCE/'rea/yt.json',root/'rea/yt.json');shutil.copy2(SOURCE/'rea/ledger.json',root/'rea/ledger.json')
  print(f'Rejected {len(controls)} plasma native/declaration corruptions.')

if __name__=='__main__':unittest.main()
