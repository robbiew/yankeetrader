"""Rehashed semantic/provenance corruption controls for the acquisition evidence."""
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
SOURCE=ROOT/'research/yt-mercenary-plasma'
spec=importlib.util.spec_from_file_location('sales_verifier',ROOT/'scripts/verify_mercenary_plasma.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
# The independently maintained fixture encoder is deliberately not the verifier's.
spec=importlib.util.spec_from_file_location('fixture_mbf',ROOT/'archive/analysis/yt-maint/experiments.py')
mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)

def write_json(path,value):
    raw=(json.dumps(value,indent=2)+'\n').encode()
    path.write_bytes(gzip.compress(raw,mtime=0) if path.suffix=='.gz' else raw)

def target(root,name,rows):
    declarations={r['name']:r for r in v.read(root/'dos/recipe.json')['scenarios']}
    worlds={};aux={};parent=rows[name].get('parent')
    if parent:
        worlds[parent]=v.zipped(root/'dos'/parent/'after.dat.gz')
        aux[parent]={n:bytes.fromhex(r['hex']) for n,r in v.read(root/'dos'/parent/'sidefiles.json').items()}
    return v.verify_control(root/'dos',declarations[name],rows[name],v.zipped(root/'dos/baseline.dat.gz'),worlds,aux)

class RehashedCorruption(unittest.TestCase):
    def test_controls(self):
        controls=[
            ('earth-menu','after',[(2,113,10)],'saved carried plasma'),
            ('earth-menu','after',[(2,81,15000000)],'saved credits'),
            ('earth-menu','after',[(2,49,500)],'saved turns'),
            ('base-land-refuse','after',[(2,113,10)],'saved carried plasma'),
            ('base-land-refuse','after',[(4150,73,2)],'planet ownership preserved'),
            ('captured-base-take','after',[(2,113,9)],'saved carried plasma'),
            ('captured-base-take','after',[(4150,113,20)],'saved planetary plasma'),
            ('ordinary-planet-take','after',[(2,81,15000000)],'saved credits'),
            ('ordinary-planet-take','after',[(4053,117,0)],'planet bank preserved'),
            ('ordinary-planet-take','after',[(2,49,499)],'saved turns'),
            ('ordinary-take-all','after',[(2,113,9)],'saved carried plasma'),
            ('ordinary-deposit','after',[(4053,113,20)],'saved planetary plasma'),
            ('take-zero','after',[(2,113,10)],'saved carried plasma'),
            ('quiet','after',[(2,69,11)],'unrelated world mutation'),
            ('quiet','before',[(2,53,999999)],'undeclared setup'),
            ('take-reload','before',[(2,113,9)],'broken world chain'),
            ('deposit-reload','aux-input',None,'auxiliary input chain'),
            ('earth-menu','keys',None,'exact input stream'),
            ('earth-menu','date',None,'DOS date'),
            ('earth-menu','clock',None,'DOS clock mismatch'),
            ('earth-menu','return',None,'DOS return marker'),
            ('earth-menu','incomplete',None,'incomplete DOS control'),
            ('earth-menu','timeout',None,'capture timeout declaration'),
            ('earth-menu','binary',None,'binary/session identity'),
            ('earth-menu','patches',None,'declared patch list'),
            ('earth-menu','raw-only',None,'raw transcript identity'),
            ('earth-menu','text-only',None,'raw transcript identity'),
            ('earth-menu','menu',None,'required acquisition receipt'),
            ('base-land-refuse','denial',None,'required acquisition receipt'),
            ('ordinary-planet-take','aux',None,'frozen complete auxiliary witness'),
        ]
        with tempfile.TemporaryDirectory(prefix='yt-mercenary-acquisition-negative-') as tmp:
            root=Path(tmp)/'research';shutil.copytree(SOURCE,root)
            original_rows={r['name']:r for r in v.read(SOURCE/'dos/results.json')['scenarios']}
            for name,kind,patches,reason in controls:
                with self.subTest(name=name,kind=kind):
                    d=root/'dos'/name;case=v.read(d/'result.json');changed=[]
                    if kind in {'before','after'}:
                        file=kind+'.dat.gz';world=bytearray(v.zipped(d/file))
                        for r,o,value in patches:mbf.put(world,r,o,value)
                        (d/file).write_bytes(gzip.compress(world,mtime=0));changed.append(file)
                    elif kind in {'aux-input','aux'}:
                        file='side-before.json.gz' if kind=='aux-input' else 'sidefiles.json.gz';a=json.loads(v.zipped(d/file))
                        if kind=='aux-input':a['YTNAME.DAT']='00'
                        else:
                            key='YTNAME.DAT';raw=bytes.fromhex(a[key]['hex'])+b'FORGED';a[key]['hex']=raw.hex();a[key]['after_sha256']=v.sha(raw)
                        write_json(d/file,a);changed.append(file)
                    elif kind in {'keys','date','clock','return'}:
                        file={'keys':'KEYS.TXT','date':'DOSDATE.LOG','clock':'DOSTIME.LOG','return':'RETURN.LOG'}[kind];raw=(d/file).read_bytes()
                        if kind=='keys':raw=raw.replace(b'P;0',b'P;1')
                        elif kind=='date':raw=raw.replace(b'10/24/2026',b'10/25/2026')
                        elif kind=='clock':raw=raw.replace(b'0:00:00.',b'1:00:00.')
                        else:raw=b''
                        (d/file).write_bytes(raw);changed.append(file)
                    elif kind=='incomplete':case['complete']=False
                    elif kind=='timeout':case['timeout_seconds']=45
                    elif kind=='binary':case['binaries']['YT.EXE']='0'*64
                    elif kind=='patches':case['applied_patches']=case['applied_patches'][:-1]
                    elif kind=='text-only':
                        (d/'transcript.txt').write_text((d/'transcript.txt').read_text()+'FORGED');changed.append('transcript.txt')
                    elif kind in {'raw-only','menu','denial'}:
                        raw=v.zipped(d/'game.log.gz')
                        old,new={
                            'raw-only':(b'Cloak Energy',b'Plasma Bolts'),
                            'menu':(b'[9] Hire Spies (Each)',b'[9] Plasma Bolt Shop'),
                            'denial':(b'Permission to land is DENIED!',b'Permission to land is GRANTED'),
                        }[kind]
                        assert old in raw,kind
                        raw=raw.replace(old,new,1);(d/'game.log.gz').write_bytes(gzip.compress(raw,mtime=0));changed.append('game.log.gz')
                        if kind!='raw-only':
                            (d/'transcript.txt').write_text(raw.decode('cp437').replace('\r\n','\n'));changed.append('transcript.txt')
                    else:raise AssertionError(kind)
                    for file in changed:case['files'][file]=v.sha((d/file).read_bytes())
                    write_json(d/'result.json.gz',case)
                    try:
                        rows={**original_rows,name:case}
                        with self.assertRaisesRegex(AssertionError,reason):target(root,name,rows)
                    finally:
                        shutil.rmtree(d);shutil.copytree(SOURCE/'dos'/name,d)
        print(f'Rejected {len(controls)} rehashed acquisition semantic/provenance corruptions.')

    def test_native_and_declarations(self):
        controls=['recipe','native-bytes','relocation','mapping','ledger','profile']
        with tempfile.TemporaryDirectory(prefix='yt-mercenary-native-negative-') as tmp:
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
                        with self.assertRaisesRegex(AssertionError,reason):
                            if kind=='recipe':
                                with contextlib.redirect_stdout(io.StringIO()):v.verify(root)
                            else:v.verify_native(root)
                    finally:shutil.copy2(SOURCE/p.relative_to(root),p)
        print(f'Rejected {len(controls)} acquisition native/declaration corruptions.')

    def test_document_chronology(self):
        changes=(ROOT/'archive/dos-original/CHANGES.TXT').read_bytes()
        manual=(ROOT/'archive/dos-original/YTINSTR.DOC').read_bytes()
        v.verify_history(changes,manual)
        with self.assertRaisesRegex(AssertionError,'change-log source identity'):
            v.verify_history(changes.replace(b'REMOVED the mercenary mother ship.',b'RETAINED the mercenary mother ship.'),manual)
        with self.assertRaisesRegex(AssertionError,'manual source identity'):
            v.verify_history(changes,manual.replace(b'You cannot buy them at Earth.',b'You can now buy them at Earth.'))
        print('Rejected two altered archived chronology/manual sources.')

if __name__=='__main__':unittest.main()
