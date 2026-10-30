"""Rehashed semantic corruption controls for cloak-equipment research evidence."""
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

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'research/yt-cloak-equipment'
spec=importlib.util.spec_from_file_location('mbf',ROOT/'archive/analysis/yt-maint/experiments.py')
mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)
sha=lambda b:hashlib.sha256(b).hexdigest()


class SemanticCorruption(unittest.TestCase):
    def test_rehashed_controls(self):
        cases=[
            ('energy-ten','before',[(2,81,1000001)],'undeclared setup'),
            ('energy-ten','after',[(2,81,990001)],'exact credit debit'),
            ('energy-ten','after',[(2,125,.11)],'cloak result'),
            ('anti-own-full','after',[(3,125,0)],'undeclared world effect'),
            ('anti-own-full','after',[(2,125,0)],'cloak result'),
            ('anti-decay','after',[(2,125,.99)],'cloak result'),
            ('anti-repeat','after',[(2,81,500000)],'exact credit debit'),
            ('anti-boundary-reconnect','after',[(2,125,1)],'cloak result'),
            ('control-look','after',[(2,49,499)],'turn debit'),
            ('anti-empty','after',[(4053,117,1)],'undeclared world effect'),
            ('energy-ten','after',[(2,109,10880251)],'unexpected cloak/device score bonus'),
            ('anti-own-full','activation',[],'activation count'),
            ('anti-own-full','confirmation',[],'activation confirmation'),
            ('anti-own-full','display',[],'active display'),
            ('energy-overfill','overfull',[],'overfull rejection'),
            ('anti-exact','keys',[],'exact input stream'),
            ('anti-reconnect','side',[],'auxiliary input chain'),
            ('energy-one-exact','incomplete',[],'incomplete session'),
            ('energy-ten','native',[],'native bytes'),
            ('energy-ten','recipe',[],'frozen declarations'),
            ('anti-reconnect','sensor-add',[],'concealed scan'),
            ('anti-own-full','sensor-remove',[],'revealed scan'),
            ('anti-empty','fake-reveal',[],'unexpected empty reveal'),
        ]
        with tempfile.TemporaryDirectory(prefix='yt-cloak-negative-')as temp:
            root=Path(temp)/'research';shutil.copytree(SOURCE,root)
            for name,kind,patches,reason in cases:
                with self.subTest(name=name,kind=kind):
                    d=root/'dos'/name;c=json.loads((d/'result.json').read_text());files=[]
                    if kind in ('before','after'):
                        file=kind+'.dat.gz';b=bytearray(gzip.decompress((d/file).read_bytes()))
                        for rec,off,value in patches:mbf.put(b,rec,off,value)
                        (d/file).write_bytes(gzip.compress(b,mtime=0));files.append(file)
                    elif kind=='native':
                        path=root/'rea/yt.json';bundle=json.loads(path.read_text());v=bundle['records'][0]['normalized_result'];b=bytearray.fromhex(v['bytes_hex']);b[0]^=1;v['bytes_hex']=b.hex();path.write_text(json.dumps(bundle)+'\n')
                    elif kind=='recipe':
                        path=root/'dos/recipe.json';path.write_bytes(path.read_bytes()+b' ')
                    elif kind=='incomplete':c['complete']=False
                    elif kind=='side':
                        file='side-before.json.gz';values=json.loads(gzip.decompress((d/file).read_bytes()));values['YTRMSG.DAT']='01';(d/file).write_bytes(gzip.compress(json.dumps(values).encode(),mtime=0));files.append(file)
                    elif kind=='keys':
                        file='KEYS.TXT';b=(d/file).read_bytes();assert b'Y' in b;(d/file).write_bytes(b.replace(b'Y',b'N',1));files.append(file)
                    elif kind in ('sensor-add','sensor-remove','fake-reveal'):
                        file='transcript.txt';text=(d/file).read_text()
                        if kind=='fake-reveal':text+='\nEnemy  is uncloaked!\n'
                        else:
                            start=text.index('[ Sensors Activated ]');end=text.index('[ End Sensor Scan ]',start)
                            scan=text[start:end];ship='Enemy  - Fighters: 42 - Shields: 7'
                            if kind=='sensor-remove':
                                assert ship in scan;scan=scan.replace(ship,'REMOVED')
                            else:scan+='\n'+ship+'\n'
                            text=text[:start]+scan+text[end:]
                        (d/file).write_text(text);files.append(file)
                    else:
                        file='transcript.txt';text=(d/file).read_text()
                        old,new={
                            'activation':('Anti-Cloaking device activated!','REMOVED'),
                            'confirmation':('Anti-Cloaking Device works for this logon only. Buy one? [y/N]','REMOVED'),
                            'display':('Cloak Energy. : FAIL','Cloak Energy. : 100%'),
                            'overfull':("You can't have over 100% cloak!",'REMOVED'),
                        }[kind]
                        assert old in text;text=text.replace(old,new);(d/file).write_text(text);files.append(file)
                    for file in files:c['files'][file]=sha((d/file).read_bytes())
                    if files or kind=='incomplete':
                        (d/'result.json').write_text(json.dumps(c,indent=2)+'\n');path=root/'dos/results.json';manifest=json.loads(path.read_text());manifest['scenarios']=[c if v['name']==name else v for v in manifest['scenarios']];path.write_text(json.dumps(manifest,indent=2)+'\n')
                    try:
                        result=subprocess.run([sys.executable,str(ROOT/'scripts/verify_cloak_equipment.py'),'--research',str(root)],capture_output=True,text=True,timeout=20)
                        self.assertNotEqual(result.returncode,0,result.stdout);self.assertIn('AssertionError',result.stderr);self.assertIn(reason,result.stderr)
                    finally:
                        shutil.rmtree(d);shutil.copytree(SOURCE/'dos'/name,d);shutil.copy2(SOURCE/'dos/results.json',root/'dos/results.json');shutil.copy2(SOURCE/'dos/recipe.json',root/'dos/recipe.json');shutil.copy2(SOURCE/'rea/yt.json',root/'rea/yt.json')


if __name__=='__main__':unittest.main()
