"""Rehashed semantic/provenance controls for broadcast shared lifetime evidence."""
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
SOURCE=ROOT/'research/yt-broadcast-radio/extended'
spec=importlib.util.spec_from_file_location('broadcast_verifier',ROOT/'scripts/verify_broadcast_lifetime.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
spec=importlib.util.spec_from_file_location('fixture_mbf',ROOT/'archive/analysis/yt-maint/experiments.py');mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)

def write_json(path,value):
    data=(json.dumps(value,indent=2)+'\n').encode();path.write_bytes(gzip.compress(data,mtime=0) if path.suffix=='.gz' else data)

def target(root,name,case):
    worlds={};aux={};parent=case.get('parent')
    if parent:
        worlds[parent]=v.zipped(root/'dos'/parent/'after.dat.gz')
        aux[parent]={n:bytes.fromhex(r['hex']) for n,r in v.read(root/'dos'/parent/'sidefiles.json').items()}
    return v.verify_control(root/'dos',v.DECLARATIONS[name],case,v.zipped(root/'dos/baseline.dat.gz'),worlds,aux)

class RehashedControls(unittest.TestCase):
    def test_semantics_and_provenance(self):
        controls=[
            ('broadcast-send','mail',[(0,31)],'broadcast packet semantics'),
            ('broadcast-send','mail',[(4,3)],'broadcast packet semantics'),
            ('broadcast-send','mail',[(8,3)],'broadcast packet semantics'),
            ('broadcast-send','mail',[(0,29.5)],'integer radio fields'),
            ('broadcast-send','mail',[(4,-2.5)],'integer radio fields'),
            ('broadcast-send','mail',[(8,2.5)],'integer radio fields'),
            ('recipient-read','mail',[(0,30)],'broadcast packet semantics'),
            ('sender-read','mail',[(0,30)],'broadcast packet semantics'),
            ('recipient-repeat','mail',[(0,28)],'broadcast packet semantics'),
            ('sender-after-recipient','mail',[(0,28)],'broadcast packet semantics'),
            ('budget-two','mail',[(0,2)],'broadcast packet semantics'),
            ('budget-one','mail',[(0,0)],'broadcast packet semantics'),
            ('budget-zero','mail',[(0,1)],'broadcast packet semantics'),
            ('budget-negative-one','mail',[(0,0)],'broadcast packet semantics'),
            ('broadcast-send','mail-body',None,'broadcast packet semantics'),
            ('two-lines','missing-line',None,'broadcast packet semantics'),
            ('broadcast-send','after',[(2,81,123)],'conserved resources'),
            ('broadcast-zero-turns','after',[(2,49,1)],'conserved resources'),
            ('recipient-read','after',[(3,93,0)],'conserved resources'),
            ('broadcast-send','after',[(3,125,0)],'conserved resources'),
            ('broadcast-send','before',[(2,53,1)],'undeclared setup'),
            ('recipient-read','before',[(2,113,0)],'broken world chain'),
            ('recipient-read','aux-input',None,'auxiliary input chain'),
            ('broadcast-send','news-body',None,'broadcast newspaper publication'),
            ('broadcast-send','news-header',None,'broadcast newspaper publication'),
            ('broadcast-send','keys',None,'exact input stream'),
            ('broadcast-send','date',None,'DOS date'),
            ('broadcast-send','clock',None,'DOS clock mismatch'),
            ('broadcast-send','return',None,'DOS return marker'),
            ('broadcast-send','incomplete',None,'incomplete DOS control'),
            ('broadcast-send','binary',None,'binary/session identity'),
            ('broadcast-send','patches',None,'declared patch list'),
            ('broadcast-send','raw-only',None,'raw transcript identity'),
            ('broadcast-send','text-only',None,'raw transcript identity'),
        ]
        with tempfile.TemporaryDirectory(prefix='yt-broadcast-negative-') as temp:
            root=Path(temp)/'research';shutil.copytree(SOURCE,root)
            for name,kind,patches,reason in controls:
                with self.subTest(name=name,kind=kind):
                    d=root/'dos'/name;case=v.read(d/'result.json');changed=[]
                    if kind in {'before','after'}:
                        f=kind+'.dat.gz';b=bytearray(v.zipped(d/f))
                        for record,offset,value in patches:mbf.put(b,record,offset,value)
                        (d/f).write_bytes(gzip.compress(b,mtime=0));changed.append(f)
                    elif kind in {'mail','mail-body','missing-line','news-body','news-header'}:
                        f='sidefiles.json.gz';a=v.read(d/'sidefiles.json');key='YTNEWS.DAT' if kind.startswith('news-') else 'YTRMSG.DAT';b=bytearray.fromhex(a[key]['hex'])
                        if kind=='mail':
                            for offset,value in patches:mbf.put(b,1,offset,value)
                        elif kind=='mail-body':b[12:13]=b'X'
                        elif kind=='missing-line':b=b[:86]
                        elif kind=='news-body':b=bytearray(bytes(b).replace(b'YT BROADCAST PROBE',b'FORGED RADIO BODY'))
                        else:b=bytearray(bytes(b).replace(b'Message from: Q ',b'Message from: X '))
                        a[key].update(hex=b.hex(),after_sha256=v.sha(b));write_json(d/f,a);changed.append(f)
                    elif kind=='aux-input':
                        f='side-before.json.gz';a=v.read(d/'side-before.json');a['YTRMSG.DAT']='00';write_json(d/f,a);changed.append(f)
                    elif kind in {'keys','date','clock','return'}:
                        f={'keys':'KEYS.TXT','date':'DOSDATE.LOG','clock':'DOSTIME.LOG','return':'RETURN.LOG'}[kind];b=(d/f).read_bytes()
                        if kind=='keys':b=b.replace(b'ALL',b'TEAM')
                        elif kind=='date':b=b.replace(b'10/24/2026',b'10/25/2026')
                        elif kind=='clock':b=b.replace(b'0:00:00.',b'1:00:00.')
                        else:b=b''
                        (d/f).write_bytes(b);changed.append(f)
                    elif kind=='incomplete':case['complete']=False
                    elif kind=='binary':case['binaries']['YT.EXE']='0'*64
                    elif kind=='patches':case['applied_patches']=case['applied_patches'][:-1]
                    elif kind=='text-only':
                        f='transcript.txt';(d/f).write_text((d/f).read_text()+'FORGED');changed.append(f)
                    elif kind=='raw-only':
                        f='game.log.gz';b=v.zipped(d/f).replace(b'YT BROADCAST PROBE',b'FORGED RADIO BODY');(d/f).write_bytes(gzip.compress(b,mtime=0));changed.append(f)
                    else:raise AssertionError(kind)
                    for f in changed:case['files'][f]=v.sha((d/f).read_bytes())
                    write_json(d/'result.json',case)
                    try:
                        with self.assertRaisesRegex(AssertionError,reason):target(root,name,case)
                    finally:shutil.rmtree(d);shutil.copytree(SOURCE/'dos'/name,d)
        print(f'Rejected {len(controls)} rehashed broadcast semantic/provenance corruptions.')

    def test_native_and_declarations(self):
        controls=['recipe','yt-bytes','maint-bytes','yt-relocation','maint-relocation','mapping','yt-ledger','maint-ledger','profile']
        with tempfile.TemporaryDirectory(prefix='yt-broadcast-native-negative-') as temp:
            root=Path(temp)/'research';shutil.copytree(SOURCE,root)
            for kind in controls:
                with self.subTest(kind=kind):
                    if kind=='recipe':p=root/'dos/recipe.json';p.write_bytes(p.read_bytes()+b' ');reason='frozen declarations'
                    elif kind.endswith('ledger'):
                        p=root/'rea'/('maint-ledger.json' if kind=='maint-ledger' else 'ledger.json');p.write_bytes(p.read_bytes()+b' ');reason='native ledger identity'
                    else:
                        p=root/'rea'/('maint.json' if kind.startswith('maint-') else 'yt.json');b=v.read(p)
                        if kind=='profile':next(r for r in b['records'] if r['operation']=='read_bytes')['analysis_profile']['digest']='0'*64;reason='native analysis profile'
                        elif kind.endswith('bytes'):
                            r=next(r for r in b['records'] if r['operation']=='read_bytes')['normalized_result'];raw=bytearray.fromhex(r['bytes_hex']);raw[0]^=1;r['bytes_hex']=raw.hex();reason='native bytes'
                        else:
                            r=next(r for r in b['records'] if r['operation']=='inspect_native_load_image')['normalized_result']['observations']
                            if kind.endswith('relocation'):r['relocations'][0]['memory_bytes_hex']='0000';reason='native relocation bytes'
                            else:next(m for m in r['mappings'] if m['initialized'])['sha256']='0'*64;reason='native mapped bytes'
                        write_json(p,b)
                    try:
                        with self.assertRaisesRegex(AssertionError,reason):
                            if kind=='recipe':
                                with contextlib.redirect_stdout(io.StringIO()):v.verify(root)
                            else:v.verify_native(root)
                    finally:shutil.copy2(SOURCE/p.relative_to(root),p)
        print(f'Rejected {len(controls)} broadcast native/declaration corruptions.')

if __name__=='__main__':unittest.main()
