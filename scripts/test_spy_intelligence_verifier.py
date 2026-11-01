"""Ensure spy evidence verification rejects corrupted provenance and outcomes."""
import contextlib
import gzip
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('verify',ROOT/'scripts/verify_spy_intelligence.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

class CorruptionControls(unittest.TestCase):
 def test_preserved(self):
  with contextlib.redirect_stdout(io.StringIO()):v.check()
 def test_corruptions(self):
  for mode in ('missing-case','incomplete','binary','keys','source','clock','cloak','ship-fields','shimmer','disruption','caller-report','snapshot'):
   with self.subTest(mode=mode),tempfile.TemporaryDirectory()as temp:
    path=Path(temp)/'dos';shutil.copytree(ROOT/'research/yt-spies/intelligence/dos',path)
    summary=json.loads((path/'results.json').read_text());results=summary['scenarios']
    name={'disruption':'disruption','caller-report':'caller-only','shimmer':'partial-cloak'}.get(mode,'visible')
    r=next(r for r in results if r['name']==name);d=path/name
    if mode=='missing-case':results.pop()
    elif mode=='incomplete':r['complete']=False
    elif mode=='binary':r['executable_sha256']='0'*64
    elif mode=='source':r['source_sha256']='0'*64
    elif mode=='clock':r['dos_time']='12:00:00'
    elif mode=='keys':(d/'KEYS.TXT').write_bytes(b'wrong');r['files']['KEYS.TXT']=v.SHA(b'wrong')
    elif mode in ('cloak','snapshot'):
     b=bytearray(gzip.decompress((d/'after.dat.gz').read_bytes()))
     v.mbf.put(b,3 if mode=='cloak'else 2,125 if mode=='cloak'else 81,.25 if mode=='cloak'else 999)
     (d/'after.dat.gz').write_bytes(gzip.compress(b));r['after_sha256']=v.SHA(b)
    else:
     p=d/'transcript.txt';s=p.read_text()
     if mode=='ship-fields':s=s.replace('Fighters: 1000 - Shields: 10','Fighters: 999 - Shields: 10')
     elif mode=='shimmer':s=s.replace('The spy detected the shimmering','Removed shimmering')
     elif mode=='disruption':s=s.replace('** Space-time disruption detected! **','Removed disruption')
     elif mode=='caller-report':s+='\n*** RADIO MESSAGE FROM SPY #1!\n'
     p.write_text(s);r['files']['transcript.txt']=v.SHA(p.read_bytes())
    (d/'result.json').write_text(json.dumps(r));(path/'results.json').write_text(json.dumps(summary))
    with self.assertRaises((AssertionError,KeyError)),contextlib.redirect_stdout(io.StringIO()):v.check(path)

if __name__=='__main__':unittest.main()
