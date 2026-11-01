"""Corruption controls for the independent DOS team-radio verifier."""
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
spec=importlib.util.spec_from_file_location('verify',ROOT/'scripts/verify_team_radio.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

class Controls(unittest.TestCase):
 def test_preserved(self):
  with contextlib.redirect_stdout(io.StringIO()):v.check()
 def test_corruptions(self):
  for mode in ('missing','binary','incomplete','roster','world','resources','destination','shared-read','outsider','late-join','chain','keys'):
   with self.subTest(mode=mode),tempfile.TemporaryDirectory()as temp:
    path=Path(temp)/'dos';shutil.copytree(ROOT/'research/yt-team-radio/dos',path)
    summary=json.loads((path/'results.json').read_text())
    name={'shared-read':'recipient-read','outsider':'outsider-read','late-join':'late-join','chain':'recipient-left'}.get(mode,'team-send')
    r=next(r for r in summary['scenarios']if r['name']==name);d=path/name
    if mode=='missing':summary['scenarios'].pop()
    elif mode=='binary':r['binaries']['YT.EXE']='0'*64
    elif mode=='incomplete':r['complete']=False
    elif mode=='roster':r['roster']=[2,3]
    elif mode in ('world','resources'):
     f='before.dat.gz'if mode=='world'else'after.dat.gz';b=bytearray(gzip.decompress((d/f).read_bytes()));v.mbf.put(b,2,81,123)
     (d/f).write_bytes(gzip.compress(b))
    elif mode in ('destination','shared-read','late-join'):
     f=d/'sidefiles.json.gz';side=json.loads(gzip.decompress(f.read_bytes()));b=bytearray.fromhex(side['YTRMSG.DAT']['hex'])
     if mode=='destination':v.mbf.put(b,1,4,5)
     elif mode=='shared-read':v.mbf.put(b,1,0,0)
     else:
      packet=bytearray(b[:86]);v.mbf.put(packet,1,4,3);b+=packet
     side['YTRMSG.DAT'].update(hex=b.hex(),after_sha256=v.SHA(b));f.write_bytes(gzip.compress(json.dumps(side).encode()))
    elif mode=='chain':
     f=d/'side-before.json.gz';raw=json.loads(gzip.decompress(f.read_bytes()));raw['YTRMSG.DAT']='00';f.write_bytes(gzip.compress(json.dumps(raw).encode()))
     f=d/'sidefiles.json.gz';side=json.loads(gzip.decompress(f.read_bytes()));side['YTRMSG.DAT']['before_sha256']=v.SHA(b'\0');f.write_bytes(gzip.compress(json.dumps(side).encode()))
    elif mode=='outsider':
     f=d/'transcript.txt';f.write_text(f.read_text()+'\nYT TEAM PROBE\n')
    elif mode=='keys':(d/'KEYS.TXT').write_bytes(b'wrong')
    # Rehash altered witnesses so semantic checks, rather than only hashes, reject them.
    for f in r['files']:r['files'][f]=v.SHA((d/f).read_bytes())
    (d/'result.json').write_text(json.dumps(r));(path/'results.json').write_text(json.dumps(summary))
    with self.assertRaises((AssertionError,KeyError)),contextlib.redirect_stdout(io.StringIO()):v.check(path)

if __name__=='__main__':unittest.main()
