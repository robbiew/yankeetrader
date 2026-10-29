"""Rehashed negative controls must fail semantic verification, not just checksums."""
import gzip
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'research/yt-xannor-mobile/dos'
spec = importlib.util.spec_from_file_location('mbf',ROOT/'archive/analysis/yt-maint/experiments.py')
mbf = importlib.util.module_from_spec(spec); spec.loader.exec_module(mbf)
sha = lambda b: hashlib.sha256(b).hexdigest()


class SemanticControls(unittest.TestCase):
    def test_rehashed_semantic_corruption(self):
        controls = [
            ('mines-origin','after',[(153,81,1),(153,85,-1)],'friendly force lost/created'),
            ('mines-hop-small','after',[(152,129,1)],'fatal-mine accounting'),
            ('planet-xannor','after',[(4053,129,0),(1165,81,138)],'route endpoint/force'),
            ('path-unreachable','after',[(53,105,1114),(151,81,0),(151,85,0),(1165,81,101)],'route endpoint/force'),
            ('split-score-2001','text',[],'allocation threshold/bound'),
            ('top-threshold-below','after',[(56,105,250)],'sticky pursuit result'),
            ('return-next-day','before',[(3053,89,1)],'broken exact-world chain'),
            ('protected-mines','after',[(58,129,3)],'early Union mine cleanup'),
            ('return-empty','clock',[],'captured DOS clock'),
        ]
        with tempfile.TemporaryDirectory(prefix='yt-mobile-negative-') as temp:
            evidence = Path(temp)/'dos'; shutil.copytree(SOURCE,evidence)
            for name,kind,patches,reason in controls:
                with self.subTest(case=name,kind=kind):
                    manifest = json.loads((SOURCE/'results.json').read_text())
                    d=evidence/name; shutil.rmtree(d); shutil.copytree(SOURCE/name,d)
                    result=json.loads((d/'result.json').read_text())
                    if kind in ('before','after'):
                        file=kind+'.dat.gz';data=bytearray(gzip.decompress((d/file).read_bytes()))
                        for record,offset,value in patches:mbf.put(data,record,offset,value)
                        result[kind+'_sha256']=sha(data)
                        (d/file).write_bytes(gzip.compress(data,mtime=0))
                    elif kind=='text':
                        file='transcript.txt';text=(d/file).read_text()
                        text=text.replace('Mercenary Maintenance...', '  -  Group: 3               Size: 1 \n\nMercenary Maintenance...')
                        (d/file).write_text(text)
                    else:
                        file='DOSTIME.LOG';text=(d/file).read_text()
                        (d/file).write_text(re.sub(r'Current time: [^\n]+','Current time: 00:00:20.00am',text))
                    result['files'][file]=sha((d/file).read_bytes())
                    (d/'result.json').write_text(json.dumps(result,indent=2)+'\n')
                    manifest['scenarios']=[result if c['name']==name else c for c in manifest['scenarios']]
                    (evidence/'results.json').write_text(json.dumps(manifest,indent=2)+'\n')
                    proc=subprocess.run([sys.executable,str(ROOT/'scripts/verify_xannor_mobile.py'),'--evidence',str(evidence)],capture_output=True,text=True,timeout=15)
                    try:
                        self.assertNotEqual(proc.returncode,0,proc.stdout)
                        self.assertIn('AssertionError',proc.stderr)
                        self.assertIn(reason,proc.stderr)
                    finally:
                        # Each control starts from exact original evidence again.
                        shutil.rmtree(d);shutil.copytree(SOURCE/name,d)


if __name__=='__main__':
    unittest.main()
