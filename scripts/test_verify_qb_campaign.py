"""Rehashed semantic corruption must not pass campaign verification."""
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from verify_qb_campaign import verify

ROOT=Path(__file__).resolve().parents[1]/'evidence/qb-full-world'

class QBVerificationTests(unittest.TestCase):
    def test_retained_campaign(self):
        verify(ROOT)

    def test_rehashed_semantic_corruption(self):
        cases=[
            ('summary.json',lambda w:w.update(outcome='failed')),
            ('summary.json',lambda w:w.update(threshold=20)),
            ('summary.json',lambda w:w.update(days=0)),
            ('before-genesis.json.gz',lambda w:next(p for key,p in w['Ports'].items() if key!='1' and p['Owner']==1).update(Owner=0)),
            ('after-genesis.json.gz',lambda w:w['QBRecipe'].update(State=1)),
            ('after-genesis.json.gz',lambda w:w['SeasonResults'][0].update(Ports=20)),
            ('after-genesis.json.gz',lambda w:w['Ports']['2'].update(Name='Changed')),
            ('day-01-repeat.json.gz',lambda w:w['Players']['1'].update(Credits=1)),
            ('day-01-after.json.gz',lambda w:w['Players']['1'].update(Turns=499)),
            ('initial.json.gz',lambda w:w.update(GenesisPorts=0)),
            ('after-genesis.json.gz',lambda w:w['Sectors']['1'].update(Warps=[7])),
            ('after-genesis.json.gz',lambda w:w['Ports']['2'].update(Updated='2027-01-01T00:00:00Z')),
            ('reconnected.json.gz',lambda w:w['Players']['1'].update(Credits=999999)),
        ]
        for name,mutate in cases:
            with self.subTest(name=name),tempfile.TemporaryDirectory() as tmp:
                target=Path(tmp)/'evidence';shutil.copytree(ROOT,target)
                path=target/name;raw=path.read_bytes()
                data=json.loads(gzip.decompress(raw) if name.endswith('.gz') else raw)
                mutate(data);raw=json.dumps(data).encode()
                path.write_bytes(gzip.compress(raw,mtime=0) if name.endswith('.gz') else raw)
                manifest=json.loads((target/'manifest.json').read_text())
                manifest[name]=hashlib.sha256(path.read_bytes()).hexdigest()
                (target/'manifest.json').write_text(json.dumps(manifest))
                with self.assertRaises(AssertionError):verify(target)

    def test_rehashed_driver_or_action_receipt_corruption(self):
        for name in ('driver.go.txt','transcript.txt.gz','actions.json'):
            with self.subTest(name=name),tempfile.TemporaryDirectory() as tmp:
                target=Path(tmp)/'evidence';shutil.copytree(ROOT,target)
                path=target/name
                if name=='driver.go.txt':path.write_bytes(path.read_bytes()+b'\n// altered source\n')
                elif name.endswith('.gz'):
                    raw=gzip.decompress(path.read_bytes()).replace(b'1 short',b'0 short')
                    path.write_bytes(gzip.compress(raw,mtime=0))
                else:
                    actions=json.loads(path.read_text());actions.remove('GENESIS');path.write_text(json.dumps(actions))
                manifest=json.loads((target/'manifest.json').read_text())
                manifest[name]=hashlib.sha256(path.read_bytes()).hexdigest()
                (target/'manifest.json').write_text(json.dumps(manifest))
                with self.assertRaises(AssertionError):verify(target)

    def test_missing_or_unhashed_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'evidence';shutil.copytree(ROOT,target)
            path=target/'manifest.json';manifest=json.loads(path.read_text());manifest.pop('actions.json');path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(AssertionError,'manifest'):verify(target)

if __name__=='__main__':unittest.main()
