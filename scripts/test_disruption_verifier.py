"""Rehashed semantic/provenance corruption controls for disruption arrival evidence."""
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
SOURCE=ROOT/'research/yt-disruption'
spec=importlib.util.spec_from_file_location('disruption_verifier',ROOT/'scripts/verify_disruption.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
# Negative fixtures use a separate preexisting MBF encoder, not the validator's.
spec=importlib.util.spec_from_file_location('fixture_mbf',ROOT/'archive/analysis/yt-maint/experiments.py')
mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)


def write_json(path,value):
    data=(json.dumps(value,indent=2)+'\n').encode()
    path.write_bytes(gzip.compress(data,mtime=0) if path.suffix=='.gz' else data)


class SemanticCorruption(unittest.TestCase):
 def test_rehashed_controls(self):
  controls=[
   ('ordinary-arrival','after',[(2,49,374)],'saved turns'),
   ('ordinary-arrival','after',[(2,57,2)],'arrival/warp footprint'),
   ('startup-zero-turns','after',[(2,49,1)],'saved turns'),
   ('thruster-ten-turns','after',[(2,49,1)],'saved turns'),
   ('ordinary-arrival','after',[(2,81,100001)],'transport credits preserved'),
   ('startup-arrival','after',[(2,125,.9)],'forced warp cloak preservation'),
   ('arrival-zero-turns','after',[(2,125,1)],'forced warp cloak preservation'),
   ('startup-hole-mines','after',[(53,129,0)],'preserves physical hazards'),
   ('startup-hole-fighters','after',[(53,81,99)],'preserves physical hazards'),
   ('startup-hole-both','after',[(53,85,2)],'preserves physical hazards'),
   ('startup-landing-mines','after',[(54,129,1)],'safe landing mine damage'),
   ('startup-landing-both','after',[(2,53,8420)],'safe landing mine damage'),
   ('startup-landing-lethal','after',[(2,45,3)],'death attribution'),
   ('startup-landing-lethal','after',[(2,97,1)],'death cleared ship equipment'),
   ('startup-landing-lethal','after',[(54,129,26)],'lethal mine aftermath'),
   ('thruster-final','after',[(53,93,0)],'planetary destination/link identity'),
   ('thruster-intermediate','after',[(53,93,2)],'planetary destination/link identity'),
   ('normal-width-wanderer-hole','after',[(2419,93,0)],'planetary destination/link identity'),
   ('thruster-final-collision','after',[(57,85,0)],'preserves stationary planet'),
   ('thruster-final-collision','after',[(2,61,10000)],'collision fighter loss'),
   ('thruster-final','after',[(56,85,12)],'planet identity survives'),
   ('wanderer-final','after',[(55,45,13)],'bounded lazy planetary growth'),
   ('wanderer-final','after',[(55,89,999)],'planet access clock bound'),
   ('wanderer-final','after',[(55,117,1240)],'planet lazy integer clock'),
   ('quiet-origin','after',[(2,69,11)],'unrelated world mutation'),
   ('upper-raw-133','after',[(54,133,0)],'unrelated world mutation'),
   ('ordinary-arrival','before',[(2,61,9999)],'undeclared setup'),
   ('ordinary-reconnect','before',[(2,49,372)],'broken world chain'),
   ('wanderer-reconnect','aux-input',None,'auxiliary input chain'),
   ('eight-sector-reconnect','aux-input',None,'auxiliary input chain'),
   ('normal-width-reconnect','aux-input',None,'auxiliary input chain'),
   ('startup-zero-turns','zero-mantissa',None,'frozen complete world witness'),
   ('ordinary-arrival','score-cache',None,'saved score arithmetic'),
   ('ordinary-arrival','keys',None,'exact input stream'),
   ('ordinary-arrival','date',None,'DOS date'),
   ('ordinary-arrival','clock',None,'DOS clock mismatch'),
   ('ordinary-arrival','return',None,'DOS return marker'),
   ('ordinary-arrival','incomplete',None,'incomplete DOS control'),
   ('ordinary-arrival','timeout',None,'capture timeout declaration'),
   ('ordinary-arrival','binary',None,'binary identity'),
   ('ordinary-arrival','patches',None,'declared patch list'),
   ('ordinary-arrival','recipe',None,'frozen declarations'),
   ('ordinary-arrival','raw-only',None,'raw transcript identity'),
   ('ordinary-arrival','text-only',None,'raw transcript identity'),
   ('ordinary-arrival','receipt-cost',None,'heat/recharge relationship'),
   ('startup-clock-01','receipt-heat',None,'heat/recharge relationship'),
   ('ordinary-arrival','receipt-hole',None,'arrival/warp footprint'),
   ('wanderer-final','vanish',None,'Wanderer transport receipt'),
   ('wanderer-final','receipt-privacy',None,'Wanderer destination privacy'),
   ('normal-width-sensors','sensor',None,'sensor hazard candidates'),
   ('normal-width-sensors-repeat','sensor-repeat',None,'sensor scan count'),
   ('eight-sector-reconnect','sensor',None,'sensor hazard candidates'),
   ('ordinary-arrival','news',None,'public event settlement'),
   ('ordinary-arrival','public-score',None,'public scoreboard points'),
   ('ordinary-arrival','aux',None,'unrelated auxiliary mutation'),
   ('ordinary-arrival','native',None,'native bytes'),
   ('ordinary-arrival','relocation',None,'native relocation bytes'),
   ('ordinary-arrival','native-mapping',None,'native mapped bytes'),
  ]
  with tempfile.TemporaryDirectory(prefix='yt-disruption-negative-') as temp:
   root=Path(temp)/'research';shutil.copytree(SOURCE,root)
   for name,kind,patches,reason in controls:
    with self.subTest(name=name,kind=kind):
     directory=root/'dos'/name;case=v.read(directory/'result.json');changed=[]
     if kind in {'before','after','zero-mantissa','score-cache'}:
      file=('before' if kind=='before' else 'after')+'.dat.gz'
      world=bytearray(gzip.decompress((directory/file).read_bytes()))
      for record,offset,value in patches or ():mbf.put(world,record,offset,value)
      if kind=='after':
       for player in (2,3):mbf.put(world,player,109,v.public_score(world,player))
      if kind=='zero-mantissa':
       at=137+49;assert world[at+3]==0;world[at]^=1
      if kind=='score-cache':mbf.put(world,2,109,1)
      (directory/file).write_bytes(gzip.compress(world,mtime=0));changed.append(file)
     elif kind in {'aux-input','news','public-score','aux'}:
      file='side-before.json.gz' if kind=='aux-input' else 'sidefiles.json.gz'
      data=json.loads(gzip.decompress((directory/file).read_bytes()))
      if kind=='aux-input':data['YTNAME.DAT']='00'
      else:
       key={'news':'YTNEWS.DAT','public-score':'YTSCORE.ASC','aux':'YTNAME.DAT'}[kind]
       raw=bytes.fromhex(data[key]['hex'])
       if kind=='news':raw=raw.rstrip(b'\x1a')+b'The Wanderer moved to sector 2368!\r\n\x1a'
       elif kind=='public-score':
        assert b'11,629,000' in raw;raw=raw.replace(b'11,629,000',b'11,629,001')
       else:raw+=b'FORGED'
       data[key]['hex']=raw.hex();data[key]['after_sha256']=v.sha(raw)
      write_json(directory/file,data);changed.append(file)
     elif kind in {'raw-only','text-only','receipt-cost','receipt-heat','receipt-hole','vanish','receipt-privacy','sensor','sensor-repeat'}:
      raw=gzip.decompress((directory/'game.log.gz').read_bytes())
      if kind=='text-only':(directory/'transcript.txt').write_text((directory/'transcript.txt').read_text()+'FORGED');changed.append('transcript.txt')
      else:
       old,new={
        'raw-only':(b'BLACK HOLE',b'FORGED HOLE'),
        'receipt-cost':(b'55 turns to recharge',b'999 turns to recharge'),
        'receipt-heat':(b'================================\r\n[\r\n',b'================================\r\n[*****\r\n'),
        'receipt-hole':(b'A *-BLACK HOLE-* grabs you!',b'REMOVED'),
        'vanish':(b'The Wanderer vanishes from your sensors!',b'REMOVED'),
        'receipt-privacy':(b'The Wanderer vanishes from your sensors!',b'The Wanderer vanishes from your sensors! successfully warped to2368'),
        'sensor':(b'** Space-time disruption detected! **',b'NO DISRUPTION'),
        'sensor-repeat':(b'[ Sensors Activated ]',b'[ Forged ]'),
       }[kind]
       assert old in raw,kind;raw=raw.replace(old,new,1)
       (directory/'game.log.gz').write_bytes(gzip.compress(raw,mtime=0));changed.append('game.log.gz')
       if kind!='raw-only':(directory/'transcript.txt').write_text(raw.decode('cp437').replace('\r\n','\n'));changed.append('transcript.txt')
     elif kind in {'keys','date','clock','return'}:
      file={'keys':'KEYS.TXT','date':'DOSDATE.LOG','clock':'DOSTIME.LOG','return':'RETURN.LOG'}[kind]
      raw=(directory/file).read_bytes()
      if kind=='keys':raw=raw.replace(b'M;2',b'M;3')
      elif kind=='date':raw=raw.replace(b'10/24/2026',b'10/25/2026')
      elif kind=='clock':raw=raw.replace(b'0:00:00.',b'1:00:00.')
      else:raw=b''
      (directory/file).write_bytes(raw);changed.append(file)
     elif kind=='incomplete':case['complete']=False
     elif kind=='timeout':case['timeout_seconds']=45
     elif kind=='binary':case['binaries']['YT.EXE']='0'*64
     elif kind=='patches':case['applied_patches']=case['applied_patches'][:-1]
     elif kind=='recipe':p=root/'dos/recipe.json';p.write_bytes(p.read_bytes()+b' ')
     elif kind in {'native','relocation','native-mapping'}:
      p=root/'rea/yt.json';bundle=json.loads(p.read_text())
      if kind=='native':
       row=next(r for r in bundle['records'] if r['operation']=='read_bytes')['normalized_result'];raw=bytearray.fromhex(row['bytes_hex']);raw[0]^=1;row['bytes_hex']=raw.hex()
      else:
       row=next(r for r in bundle['records'] if r['operation']=='inspect_native_load_image')['normalized_result']['observations']
       if kind=='relocation':row['relocations'][0]['memory_bytes_hex']='0000'
       else:next(m for m in row['mappings'] if m['initialized'])['sha256']='0'*64
      write_json(p,bundle)
     else:raise AssertionError(kind)
     for file in changed:case['files'][file]=v.sha((directory/file).read_bytes())
     if changed or kind in {'incomplete','timeout','binary','patches'}:
      write_json(directory/'result.json.gz',case);p=root/'dos/results.json.gz';manifest=v.read(root/'dos/results.json');manifest['scenarios']=[case if r['name']==name else r for r in manifest['scenarios']];write_json(p,manifest)
     try:
      with contextlib.redirect_stdout(io.StringIO()):
       with self.assertRaisesRegex(AssertionError,reason):v.verify(root)
     finally:
      shutil.rmtree(directory);shutil.copytree(SOURCE/'dos'/name,directory)
      for file in ('dos/results.json.gz','dos/recipe.json','rea/yt.json'):shutil.copy2(SOURCE/file,root/file)
  print(f'Rejected {len(controls)} rehashed disruption semantic and provenance corruptions.')

 def test_rehashed_diagnostic(self):
  controls=['complete','marker','geometry','reentry','world','aux','recipe']
  with tempfile.TemporaryDirectory(prefix='yt-disruption-diagnostic-negative-') as temp:
   root=Path(temp)/'research';shutil.copytree(SOURCE,root)
   for kind in controls:
    with self.subTest(kind=kind):
     d=root/'diagnostics/one-sector-loop';case=v.read(d/'result.json');changed=[]
     reason={'complete':'diagnostic classification','marker':'DOS return marker','geometry':'frozen declarations','reentry':'repeated native arrival','world':'frozen incomplete diagnostic witness','aux':'frozen incomplete diagnostic witness','recipe':'diagnostic frozen declarations'}[kind]
     if kind=='complete':case['complete']=True
     elif kind=='marker':(d/'RETURN.LOG').write_bytes(b'DISRUPTION_PROGRAM_RETURNED\r\n');changed.append('RETURN.LOG')
     elif kind in {'geometry','recipe'}:
      p=root/'diagnostics/recipe.json'
      if kind=='geometry':r=json.loads(p.read_text());r['scenarios'][0]['sectors']=2;write_json(p,r)
      else:p.write_bytes(p.read_bytes()+b' ')
     elif kind=='reentry':
      raw=gzip.decompress((d/'game.log.gz').read_bytes()).replace(b'A *-BLACK HOLE-* grabs you!',b'REMOVED');(d/'game.log.gz').write_bytes(gzip.compress(raw,mtime=0));(d/'transcript.txt').write_text(raw.decode('cp437').replace('\r\n','\n'));changed+=['game.log.gz','transcript.txt']
     elif kind=='world':
      data=bytearray(gzip.decompress((d/'after.dat.gz').read_bytes()));mbf.put(data,2,81,99999);(d/'after.dat.gz').write_bytes(gzip.compress(data,mtime=0));changed.append('after.dat.gz')
     elif kind=='aux':
      p=d/'sidefiles.json.gz';data=json.loads(gzip.decompress(p.read_bytes()));raw=bytes.fromhex(data['YTNEWS.DAT']['hex'])+b'FORGED';data['YTNEWS.DAT']['hex']=raw.hex();data['YTNEWS.DAT']['after_sha256']=v.sha(raw);write_json(p,data);changed.append(p.name)
     for file in changed:case['files'][file]=v.sha((d/file).read_bytes())
     if changed or kind=='complete':
      write_json(d/'result.json.gz',case);manifest=v.read(root/'diagnostics/results.json');manifest['scenarios']=[case];write_json(root/'diagnostics/results.json.gz',manifest)
     try:
      with contextlib.redirect_stdout(io.StringIO()):
       with self.assertRaisesRegex(AssertionError,reason):v.verify(root)
     finally:
      shutil.rmtree(root/'diagnostics');shutil.copytree(SOURCE/'diagnostics',root/'diagnostics')
  print(f'Rejected {len(controls)} separately rehashed incomplete-diagnostic corruptions.')


if __name__=='__main__':unittest.main()
