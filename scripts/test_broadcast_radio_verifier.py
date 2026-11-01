"""Corruption controls for original broadcast-radio evidence verification."""
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
spec=importlib.util.spec_from_file_location('verify',ROOT/'scripts/verify_broadcast_radio.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

class Controls(unittest.TestCase):
 def test_preserved(self):
  with contextlib.redirect_stdout(io.StringIO()):v.check()
 def test_corruptions(self):
  modes=('missing','binary','incomplete','keys','date','time','scanner','fraction-counter','fraction-destination','fraction-sender','mail-text','transition','repeat-transition','chain','header','startup','root-mailbox','sender-actor','repeat-actor')
  for mode in modes:
   with self.subTest(mode=mode),tempfile.TemporaryDirectory()as temp:
    path=Path(temp)/'dos';shutil.copytree(ROOT/'research/yt-broadcast-radio/dos',path)
    summary=json.loads((path/'results.json').read_text())
    name={'repeat-transition':'recipient-again','repeat-actor':'recipient-again','sender-actor':'sender-read',
          'scanner':'recipient-read','transition':'recipient-read','chain':'recipient-read','header':'recipient-read','startup':'recipient-read'}.get(mode,'broadcast-send')
    r=next(r for r in summary['scenarios']if r['name']==name);d=path/name
    if mode=='missing':summary['scenarios'].pop()
    elif mode=='binary':r['binaries']['YT.EXE']='0'*64
    elif mode=='incomplete':r['complete']=False
    elif mode=='root-mailbox':
     f=d/'side-before.json.gz';raw=json.loads(gzip.decompress(f.read_bytes()));g=d/'sidefiles.json.gz';side=json.loads(gzip.decompress(g.read_bytes()))
     raw['YTRMSG.DAT']=side['YTRMSG.DAT']['hex'];side['YTRMSG.DAT']['before_sha256']=v.SHA(bytes.fromhex(raw['YTRMSG.DAT']))
     f.write_bytes(gzip.compress(json.dumps(raw).encode()));g.write_bytes(gzip.compress(json.dumps(side).encode()))
    elif mode in ('sender-actor','repeat-actor'):
     other=path/('recipient-read'if mode=='sender-actor'else 'sender-after-recipient')/'transcript.txt'
     (d/'transcript.txt').write_bytes(other.read_bytes())
    elif mode=='keys':(d/'KEYS.TXT').write_bytes(b'wrong')
    elif mode in ('date','time'):
     f=d/('DOSDATE.LOG'if mode=='date'else 'DOSTIME.LOG');f.write_bytes(b'Current date: Sun 10/25/2026\r\n'if mode=='date'else b'Current time: 1:00:00.00am\r\n')
    elif mode=='scanner':
     f=d/'after.dat.gz';b=bytearray(gzip.decompress(f.read_bytes()));v.mbf.put(b,3,93,0);f.write_bytes(gzip.compress(b))
    elif mode in ('fraction-counter','fraction-destination','fraction-sender','mail-text','transition','repeat-transition'):
     f=d/'sidefiles.json.gz';side=json.loads(gzip.decompress(f.read_bytes()));b=bytearray.fromhex(side['YTRMSG.DAT']['hex'])
     if mode=='mail-text':b[12]=ord('X')
     elif mode=='fraction-counter':v.mbf.put(b,1,0,30.5)
     elif mode=='fraction-destination':v.mbf.put(b,1,4,-2.5)
     elif mode=='fraction-sender':v.mbf.put(b,1,8,2.5)
     elif mode=='transition':v.mbf.put(b,1,0,30)
     else:v.mbf.put(b,1,0,28)
     side['YTRMSG.DAT'].update(hex=b.hex(),after_sha256=v.SHA(b));f.write_bytes(gzip.compress(json.dumps(side).encode()))
    elif mode=='chain':
     f=d/'side-before.json.gz';raw=json.loads(gzip.decompress(f.read_bytes()));raw['YTRMSG.DAT']='00';f.write_bytes(gzip.compress(json.dumps(raw).encode()))
     f=d/'sidefiles.json.gz';side=json.loads(gzip.decompress(f.read_bytes()));side['YTRMSG.DAT']['before_sha256']=v.SHA(b'\0');f.write_bytes(gzip.compress(json.dumps(side).encode()))
    else:
     f=d/'transcript.txt';s=f.read_text()
     if mode=='header':s=s.replace('Message to: All * From: Q','Message to: Someone * From: Q')
     else:
      # Keep the total body count while moving startup delivery into history.
      first=s.index('YT BROADCAST PROBE');s=s[:first]+s[first:].replace('YT BROADCAST PROBE','MISSING STARTUP',1);s+='\nYT BROADCAST PROBE\n'
     f.write_text(s)
    for f in r['files']:r['files'][f]=v.SHA((d/f).read_bytes())
    (d/'result.json').write_text(json.dumps(r));(path/'results.json').write_text(json.dumps(summary))
    with self.assertRaises((AssertionError,KeyError)),contextlib.redirect_stdout(io.StringIO()):v.check(path)

if __name__=='__main__':unittest.main()
