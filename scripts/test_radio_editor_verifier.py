"""Reject rehashed corruption of original editor outcomes and provenance."""
import contextlib,gzip,importlib.util,io,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('v',ROOT/'scripts/verify_radio_editor.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class Controls(unittest.TestCase):
 def test_preserved(self):
  with contextlib.redirect_stdout(io.StringIO()):v.check()
 def test_corruption(self):
  modes=('root','actor','keys','resource','fraction-to','fraction-flag','second-match','rejected-edit','continue-newline','missing20','extra21','padding','abort-send','public-missing','private-news','incomplete')
  names={'second-match':'edit-accept','rejected-edit':'edit-reject','missing20':'limit','extra21':'limit','abort-send':'abort','public-missing':'public-two'}
  for mode in modes:
   with self.subTest(mode=mode),tempfile.TemporaryDirectory()as temp:
    path=Path(temp)/'dos';shutil.copytree(ROOT/'research/yt-radio-editor/dos',path)
    summary=json.loads((path/'results.json').read_text());name=names.get(mode,'list-continue');r=next(x for x in summary['scenarios']if x['name']==name);d=path/name
    if mode=='incomplete':r['complete']=False
    elif mode=='keys':(d/'KEYS.TXT').write_bytes(b'wrong')
    elif mode=='actor':
     p=d/'transcript.txt';s=p.read_text();assert 'Welcome Tester!'in s;p.write_text(s.replace('Welcome Tester!','Welcome Enemy!'))
    elif mode=='resource':
     p=d/'after.dat.gz';b=bytearray(gzip.decompress(p.read_bytes()));v.mbf.put(b,2,81,999);p.write_bytes(gzip.compress(b))
    else:
     p=d/'sidefiles.json.gz';side=json.loads(gzip.decompress(p.read_bytes()));mail=bytearray.fromhex(side['YTRMSG.DAT']['hex']);old=bytes(mail)
     if mode=='root':
      f=d/'side-before.json.gz';raw=json.loads(gzip.decompress(f.read_bytes()));raw['YTRMSG.DAT']=mail.hex();side['YTRMSG.DAT']['before_sha256']=v.SHA(mail);f.write_bytes(gzip.compress(json.dumps(raw).encode()))
     elif mode=='fraction-to':v.mbf.put(mail,1,4,3.5)
     elif mode=='fraction-flag':v.mbf.put(mail,1,0,1.5)
     elif mode=='second-match':mail[12:86]=b'alpha BETA'.ljust(74,b' ')
     elif mode=='rejected-edit':mail[12:86]=b'BETA alpha'.ljust(74,b' ')
     elif mode=='continue-newline':
      mail[98:172]=b'SECOND'.ljust(74,b' ');extra=bytearray(mail[:86]);extra[12:86]=b'THIRD'.ljust(74,b' ');mail+=extra
     elif mode=='missing20':mail=mail[:-86]
     elif mode=='extra21':mail+=mail[:86]
     elif mode=='padding':mail[85]=9
     elif mode=='abort-send':
      other=json.loads(gzip.decompress((path/'list-continue/sidefiles.json.gz').read_bytes()));mail=bytearray.fromhex(other['YTRMSG.DAT']['hex'])[:86]
     elif mode in ('public-missing','private-news'):
      news=bytes.fromhex(side['YTNEWS.DAT']['hex']);changed=news.replace(b'PUBLIC SECOND',b'OMITTED')if mode=='public-missing'else news+b'  -  FIRST\r\n';assert changed!=news
      side['YTNEWS.DAT'].update(hex=changed.hex(),after_sha256=v.SHA(changed))
     else:raise AssertionError('unknown corruption')
     if mode not in ('root','public-missing','private-news'):assert bytes(mail)!=old
     side['YTRMSG.DAT'].update(hex=mail.hex(),after_sha256=v.SHA(mail));p.write_bytes(gzip.compress(json.dumps(side).encode()))
    for f in r['files']:r['files'][f]=v.SHA((d/f).read_bytes())
    (d/'result.json').write_text(json.dumps(r));(path/'results.json').write_text(json.dumps(summary))
    with self.assertRaises((AssertionError,KeyError)),contextlib.redirect_stdout(io.StringIO()):v.check(path)
if __name__=='__main__':unittest.main()
