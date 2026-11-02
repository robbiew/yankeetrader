"""Rehashed semantic/provenance controls for the spy-trigger evidence verifier."""
import contextlib
import gzip
import importlib.util
import io
import json
import re
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'research/yt-spies/triggers'
spec = importlib.util.spec_from_file_location('spy_trigger_verifier', ROOT/'scripts/verify_spy_triggers.py')
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


def write_json(path, value):
    raw = (json.dumps(value, indent=2)+'\n').encode()
    Path(path).write_bytes(gzip.compress(raw, mtime=0) if Path(path).suffix == '.gz' else raw)


class NativeCorruptionControls(unittest.TestCase):
    def test_preserved_native(self):
        self.assertEqual(v.verify_native(SOURCE), 20)

    def test_native_corruptions(self):
        modes = {
            'bytes': 'native bytes', 'requested-length': 'incomplete native bytes',
            'read-target': 'native target identity', 'profile': 'native analysis profile',
            'read-parameters': 'native read parameters', 'read-count': 'native observation count',
            'search-complete': 'incomplete native search', 'search-boundary': 'native search boundary',
            'search-pattern': 'native search parameters', 'search-count': 'native trigger search evidence',
            'search-file-offset': 'native trigger search evidence',
            'relocation': 'native relocation bytes', 'mapping': 'native mapped bytes',
            'source': 'native source digests', 'load-operation': 'native load-image operation',
        }
        with tempfile.TemporaryDirectory(prefix='yt-spy-native-negative-') as temp:
            root = Path(temp)
            original = (SOURCE/'rea.json').read_bytes()
            for mode, reason in modes.items():
                with self.subTest(mode=mode):
                    dossier = json.loads(original)
                    read = dossier['byte_evidence'][0]
                    search = dossier['search_evidence'][0]
                    load = dossier['load_image_evidence']
                    if mode == 'bytes':
                        raw = bytearray.fromhex(read['normalized_result']['bytes_hex'])
                        raw[0] ^= 1
                        read['normalized_result']['bytes_hex'] = raw.hex()
                    elif mode == 'requested-length': read['normalized_result']['requested_bytes'] += 1
                    elif mode == 'read-target': read['subject']['digest']['sha256'] = '0'*64
                    elif mode == 'profile': read['analysis_profile']['digest'] = '0'*64
                    elif mode == 'read-parameters': read['parameters']['address'] = '0x10000'
                    elif mode == 'read-count': dossier['byte_evidence'].pop()
                    elif mode == 'search-complete': search['normalized_result']['complete'] = False
                    elif mode == 'search-boundary': search['normalized_result']['searched']['blocks'][0]['start'] = '0x10001'
                    elif mode == 'search-pattern': search['parameters']['pattern'] = 'cd 3f 58 e2 a6'
                    elif mode == 'search-count': search['normalized_result']['matches'].pop()
                    elif mode == 'search-file-offset': search['normalized_result']['matches'][0]['file_offset'] += 1
                    elif mode == 'relocation': load['normalized_result']['observations']['relocations'][0]['memory_bytes_hex'] = '0000'
                    elif mode == 'mapping': next(m for m in load['normalized_result']['observations']['mappings'] if m['initialized'])['sha256'] = '0'*64
                    elif mode == 'source': load['normalized_result']['observations']['source_files'][0]['modified_sha256'] = '0'*64
                    elif mode == 'load-operation': load['operation'] = 'search_bytes'
                    else: raise AssertionError(mode)
                    write_json(root/'rea.json', dossier)
                    with self.assertRaisesRegex(AssertionError, reason):
                        v.verify_native(root)
        print(f'Rejected {len(modes)} spy native byte/load/search corruptions.')


class RuntimeCorruptionControls(unittest.TestCase):
    def test_preserved(self):
        with contextlib.redirect_stdout(io.StringIO()):
            v.verify(SOURCE)

    def test_runtime_corruptions(self):
        controls = [
            ('list-only','incomplete','incomplete DOS control'),
            ('list-only','binary','binary/session identity'),
            ('list-only','patches','declared patch list'),
            ('list-only','before','undeclared setup or broken world chain'),
            ('partial-reveal-target','before','undeclared setup or broken world chain'),
            ('partial-reveal-target','aux-input','auxiliary input chain'),
            ('list-only','keys','exact input stream'),
            ('list-only','date','DOS date'),
            ('list-only','clock','DOS clock mismatch'),
            ('list-only','return','DOS return marker'),
            ('list-only','raw-only','raw transcript identity'),
            ('list-only','text-only','raw transcript identity'),
            ('list-only','identity','login identity'),
            ('list-only','alias','login alias'),
            ('list-only','credits','account resources'),
            ('partial-reveal','cloak','account resources'),
            ('fighters-five','fighters','account resources'),
            ('missile-one','missile','account resources'),
            ('move','report-sector','complete ordered spy report headers'),
            ('list-only','extra-header','complete ordered spy report headers'),
            ('three-spies','second-spy-location','complete ordered spy locations'),
            ('partial-reveal','ship-shield','complete ordered ship records'),
            ('partial-reveal','mail','no deferred radio notification'),
            ('partial-reveal-target','mail','no deferred radio notification'),
            ('partial-reveal','public-warning','only declared ordinary newspaper append'),
            ('partial-reveal-target','door-identity','actor door identity'),
        ]
        with tempfile.TemporaryDirectory(prefix='yt-spy-runtime-negative-') as temp:
            root = Path(temp)/'research'
            shutil.copytree(SOURCE,root)
            for name,mode,reason in controls:
                with self.subTest(name=name,mode=mode):
                    d = root/'dos'/name
                    case = v.read(d/'result.json')
                    changed = []
                    if mode == 'incomplete': case['complete'] = False
                    elif mode == 'binary': case['binaries']['YT.EXE'] = '0'*64
                    elif mode == 'patches': case['applied_patches'] = case['applied_patches'][:-1]
                    elif mode in {'before','credits','cloak','fighters','missile'}:
                        filename = 'before.dat.gz' if mode=='before' else 'after.dat.gz'
                        raw = bytearray(v.zipped(d/filename))
                        record,offset,value = {'before':(2,53,123),'credits':(2,81,123),'cloak':(3,125,.25),'fighters':(2,61,1000),'missile':(2,97,7)}[mode]
                        v.put(raw,record,offset,value)
                        (d/filename).write_bytes(gzip.compress(raw,mtime=0))
                        changed.append(filename)
                    elif mode == 'aux-input':
                        filename='side-before.json.gz';initial=v.read(d/'side-before.json')
                        initial['YTRMSG.DAT']='00';write_json(d/filename,initial);changed.append(filename)
                    elif mode in {'keys','date','clock','return'}:
                        filename={'keys':'KEYS.TXT','date':'DOSDATE.LOG','clock':'DOSTIME.LOG','return':'RETURN.LOG'}[mode]
                        raw=(d/filename).read_bytes()
                        if mode=='keys': raw=raw.replace(b'P;9',b'P;8')
                        elif mode=='date': raw=raw.replace(b'10/24/2026',b'10/25/2026')
                        elif mode=='clock': raw=raw.replace(b'0:00:00.',b'1:00:00.')
                        else: raw=b''
                        (d/filename).write_bytes(raw);changed.append(filename)
                    elif mode in {'mail','public-warning','door-identity'}:
                        filename='sidefiles.json.gz';aux=v.read(d/'sidefiles.json')
                        key='YTRMSG.DAT' if mode=='mail' else 'YTNEWS.DAT' if mode=='public-warning' else 'DORINFO1.DEF'
                        raw=bytes.fromhex(aux[key]['hex'])
                        if mode=='mail': raw=b'FORGED SPY WARNING'
                        elif mode=='public-warning': raw+=b'YOU WERE FOUND BY A SPY\r\n'
                        else: raw=raw.replace(b'ENEMY',b'TESTER')
                        aux[key].update(hex=raw.hex(),after_sha256=v.sha(raw))
                        write_json(d/filename,aux);changed.append(filename)
                    else:
                        text=(d/'transcript.txt').read_text()
                        if mode=='identity': text=text.replace('Welcome Tester!','Welcome Other!')
                        elif mode=='alias': text=text.replace('Name  : Q ','Name  : Other ')
                        elif mode=='report-sector': text=text.replace('following was found in sector 101:','following was found in sector 102:')
                        elif mode=='extra-header': text+='\n*** RADIO MESSAGE FROM SPY #1! The following was found in sector 101:\n'
                        elif mode=='second-spy-location': text=text.replace('Spy # 2 will hunt in sector 101.','Spy # 2 will hunt in sector 104.',1)
                        elif mode=='ship-shield': text=text.replace('Fighters: 42 - Shields: 7','Fighters: 42 - Shields: 70')
                        elif mode in {'raw-only','text-only'}: text+='FORGED RAW/TEXT DIVERGENCE'
                        else: raise AssertionError(mode)
                        if mode!='raw-only': (d/'transcript.txt').write_text(text);changed.append('transcript.txt')
                        if mode!='text-only':
                            raw=text.replace('\n','\r\n').encode('cp437')
                            (d/'game.log.gz').write_bytes(gzip.compress(raw,mtime=0));changed.append('game.log.gz')
                    for filename in changed: case['files'][filename]=v.sha((d/filename).read_bytes())
                    write_json(d/'result.json',case)
                    parent=case.get('parent');worlds={};auxiliaries={}
                    if parent:
                        worlds[parent]=v.zipped(root/'dos'/parent/'after.dat.gz')
                        auxiliaries[parent]={n:bytes.fromhex(r['hex']) for n,r in v.read(root/'dos'/parent/'sidefiles.json').items()}
                    try:
                        with self.assertRaisesRegex(AssertionError,reason):
                            v.verify_control(root/'dos',v.DECLARATIONS[name],case,v.zipped(root/'dos/baseline.dat.gz'),worlds,auxiliaries)
                    finally:
                        shutil.rmtree(d);shutil.copytree(SOURCE/'dos'/name,d)
        print(f'Rejected {len(controls)} rehashed spy semantic/provenance corruptions.')

    def test_elapsed_display_is_not_a_golden_hash(self):
        with tempfile.TemporaryDirectory(prefix='yt-spy-elapsed-control-') as temp:
            root=Path(temp)/'research';shutil.copytree(SOURCE,root)
            d=root/'dos/list-only';case=v.read(d/'result.json')
            original=(d/'transcript.txt').read_text()
            changed,count=re.subn(r'Time: 179:[0-9]{2}', 'Time: 178:59', original)
            self.assertGreater(count,0)
            (d/'transcript.txt').write_text(changed)
            (d/'game.log.gz').write_bytes(gzip.compress(changed.replace('\n','\r\n').encode('cp437'),mtime=0))
            for filename in ('transcript.txt','game.log.gz'):
                case['files'][filename]=v.sha((d/filename).read_bytes())
            write_json(d/'result.json',case)
            # Captured elapsed display may vary; starting clocks, actions,
            # resources, complete reports and parent identities remain exact.
            v.verify_control(root/'dos',v.DECLARATIONS['list-only'],case,v.zipped(root/'dos/baseline.dat.gz'),{}, {})

    def test_declaration_corruption(self):
        with tempfile.TemporaryDirectory(prefix='yt-spy-recipe-negative-') as temp:
            root=Path(temp)/'research';shutil.copytree(SOURCE,root)
            p=root/'dos/recipe.json';p.write_bytes(p.read_bytes()+b' ')
            with self.assertRaisesRegex(AssertionError,'frozen declarations'):
                v.verify(root)


if __name__ == '__main__':
    unittest.main()
