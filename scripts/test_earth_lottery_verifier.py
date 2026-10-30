"""Rehashed semantic corruption controls for paid Earth lottery evidence."""
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

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'research/yt-earth-lottery'
spec = importlib.util.spec_from_file_location('mbf', ROOT/'archive/analysis/yt-maint/experiments.py')
mbf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mbf)
sha = lambda b:hashlib.sha256(b).hexdigest()


class SemanticCorruption(unittest.TestCase):
    def test_rehashed_controls(self):
        cases = [
            ('tier-1','before',[(2,81,100001)],'undeclared setup'),
            ('tier-1','after',[(2,81,100094)],'credit settlement'),
            ('tier-1','after',[(2,105,0)],'daily play counter'),
            ('tier-1','after',[(2,49,498)],'turn debit'),
            ('tier-1','after',[(3,81,1)],'undeclared world effect'),
            ('tier-1','after',[(4053,117,1)],'undeclared world effect'),
            ('tier-1','after',[(2,109,9990346)],'score credit contribution'),
            ('tier-1','after',[(3,109,367051)],'other score cache'),
            ('tier-6','after',[(2,81,100100000)],'credit settlement'),
            ('large-loss-27','after',[(2,81,134217720)],'credit settlement'),
            ('next-day-reset','after',[(2,105,2)],'daily play counter'),
            ('tier-6','receipt',None,'payout receipt'),
            ('tier-0','loss',None,'losing receipt'),
            ('input-letter','invalid',None,'invalid input rejection'),
            ('limit-reached','limit',None,'daily limit refusal'),
            ('tier-6','keys',None,'exact input stream'),
            ('tier-6','date',None,'DOS date'),
            ('tier-6','clock',None,'declared clock'),
            ('same-day-reconnect','side-input',None,'auxiliary input chain'),
            ('tier-6','news-award',None,'public news scope'),
            ('tier-3','news-extra',None,'public news scope'),
            ('tier-4','news-missing',None,'public news scope'),
            ('tier-6','board',None,'scoreboard value'),
            ('tier-1','side-output',None,'unrelated auxiliary effect'),
            ('tier-1','native',None,'native bytes'),
            ('tier-1','recipe',None,'frozen declarations'),
            ('tier-1','incomplete',None,'incomplete session'),
        ]
        with tempfile.TemporaryDirectory(prefix='yt-lottery-negative-') as temp:
            root = Path(temp)/'research'
            shutil.copytree(SOURCE, root)
            for name,kind,patches,reason in cases:
                with self.subTest(name=name,kind=kind):
                    directory = root/'dos'/name
                    result = json.loads((directory/'result.json').read_text())
                    changed = []
                    if kind in {'before','after'}:
                        file = kind+'.dat.gz'
                        world = bytearray(gzip.decompress((directory/file).read_bytes()))
                        for record,offset,value in patches:mbf.put(world,record,offset,value)
                        (directory/file).write_bytes(gzip.compress(world,mtime=0))
                        changed.append(file)
                    elif kind=='native':
                        path = root/'rea/yt.json'
                        bundle = json.loads(path.read_text())
                        record = bundle['records'][0]['normalized_result']
                        value = bytearray.fromhex(record['bytes_hex'])
                        value[0] ^= 1
                        record['bytes_hex'] = value.hex()
                        path.write_text(json.dumps(bundle)+'\n')
                    elif kind=='recipe':
                        path = root/'dos/recipe.json'
                        path.write_bytes(path.read_bytes()+b' ')
                    elif kind=='incomplete':result['complete']=False
                    elif kind=='keys':
                        file = 'KEYS.TXT'
                        value = (directory/file).read_bytes()
                        assert b'126788' in value
                        (directory/file).write_bytes(value.replace(b'126788',b'000000',1))
                        changed.append(file)
                    elif kind=='date':
                        file = 'DOSDATE.LOG'
                        value = (directory/file).read_bytes()
                        assert b'10/24/2026' in value
                        (directory/file).write_bytes(value.replace(b'10/24/2026',b'10/25/2026'))
                        changed.append(file)
                    elif kind=='clock':
                        file='DOSTIME.LOG'
                        value=(directory/file).read_bytes()
                        assert b'0:00:00.' in value
                        result['time']='01:00:00'
                        (directory/file).write_bytes(value.replace(b'0:00:00.',b'1:00:00.'))
                        changed.append(file)
                    elif kind=='side-input':
                        file = 'side-before.json.gz'
                        values = json.loads(gzip.decompress((directory/file).read_bytes()))
                        values['YTRMSG.DAT']='01'
                        (directory/file).write_bytes(gzip.compress(json.dumps(values).encode(),mtime=0))
                        changed.append(file)
                    elif kind in {'news-award','news-extra','news-missing','board','side-output'}:
                        file = 'sidefiles.json.gz'
                        values = json.loads(gzip.decompress((directory/file).read_bytes()))
                        target = 'YTSCORE.ASC' if kind=='board' else ('YTRMSG.DAT' if kind=='side-output' else 'YTNEWS.DAT')
                        value = bytes.fromhex(values[target]['hex'])
                        if kind=='news-award':
                            assert b'Q  won 100000000 credits' in value
                            value = value.replace(b'Q  won 100000000 credits',b'Q  won 1 credits')
                        elif kind=='news-extra':value=value[:-1]+b'Q  won 10000 credits in the lottery!\r\n\x1a'
                        elif kind=='news-missing':
                            assert b'Q  won 100000 credits in the lottery!\r\n' in value
                            value=value.replace(b'Q  won 100000 credits in the lottery!\r\n',b'')
                        elif kind=='board':
                            assert b'109,990,240' in value
                            value=value.replace(b'109,990,240',b'109,990,241')
                        else:value+=b'\x01'
                        values[target]['hex']=value.hex()
                        values[target]['after_sha256']=sha(value)
                        (directory/file).write_bytes(gzip.compress(json.dumps(values).encode(),mtime=0))
                        changed.append(file)
                    else:
                        file='transcript.txt'
                        text=(directory/file).read_text()
                        old,new={
                            'receipt':('You matched 6 digits and won 100000000 credits!','You matched 5 digits and won 1000000 credits!'),
                            'loss':("Sorry, you didn't win this time.",'REMOVED'),
                            'invalid':('Please enter NUMBERS only!','REMOVED'),
                            'limit':('You will be allowed to play again tomorrow.','REMOVED'),
                        }[kind]
                        assert old in text
                        (directory/file).write_text(text.replace(old,new))
                        changed.append(file)
                    for file in changed:result['files'][file]=sha((directory/file).read_bytes())
                    if changed or kind=='incomplete':
                        (directory/'result.json').write_text(json.dumps(result,indent=2)+'\n')
                        path=root/'dos/results.json'
                        manifest=json.loads(path.read_text())
                        manifest['scenarios']=[result if row['name']==name else row for row in manifest['scenarios']]
                        path.write_text(json.dumps(manifest,indent=2)+'\n')
                    try:
                        check=subprocess.run([sys.executable,str(ROOT/'scripts/verify_earth_lottery.py'),'--research',str(root)],capture_output=True,text=True,timeout=30)
                        self.assertNotEqual(check.returncode,0,check.stdout)
                        self.assertIn('AssertionError',check.stderr)
                        self.assertIn(reason,check.stderr)
                    finally:
                        shutil.rmtree(directory)
                        shutil.copytree(SOURCE/'dos'/name,directory)
                        for file in ['dos/results.json','dos/recipe.json','rea/yt.json']:
                            shutil.copy2(SOURCE/file,root/file)


if __name__=='__main__':unittest.main()
