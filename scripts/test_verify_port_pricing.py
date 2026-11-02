"""Semantic corruption controls for the independent retained-pricing checker."""
import gzip
import hashlib
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('price_checker',ROOT/'scripts/verify_port_pricing.py')
checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
SOURCE=ROOT/'research/yt-port-generation/pricing-dos'


class PricingEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.capture=Path(self.temporary.name)/'capture'
        shutil.copytree(SOURCE,self.capture)

    def rehash(self,name,*files):
        case=self.capture/name
        metadata=json.loads((case/'result.json').read_text())
        for filename in files:
            metadata['files'][filename]=hashlib.sha256((case/filename).read_bytes()).hexdigest()
        (case/'result.json').write_text(json.dumps(metadata))

    def reject(self):
        with self.assertRaises((AssertionError,ValueError,KeyError)):
            checker.verify(self.capture)

    def test_original_controls_are_valid(self):
        observed=checker.verify(self.capture)
        self.assertEqual(len(observed),7)
        self.assertEqual(observed[0]['prices'],[20,29,41])
        self.assertEqual(observed[1]['prices'],[30,44,62])
        self.assertTrue(all(row['prices']==[2025,2960,4162]for row in observed[2:]))

    def test_recipe_and_coverage_are_pinned(self):
        path=self.capture/'recipe.json'
        recipe=json.loads(path.read_text());recipe['scenarios'].pop()
        path.write_text(json.dumps(recipe));self.reject()

    def test_rehashed_wrong_displayed_price(self):
        case=self.capture/'amplified-midnight'
        transcript=case/'transcript.txt'
        transcript.write_text(transcript.read_text().replace('2960','3000'))
        raw=gzip.decompress((case/'game.log.gz').read_bytes()).replace(b'2960',b'3000')
        (case/'game.log.gz').write_bytes(gzip.compress(raw,mtime=0))
        self.rehash(case.name,'transcript.txt','game.log.gz');self.reject()

    def test_rehashed_false_transcript(self):
        case=self.capture/'normal-midnight';path=case/'transcript.txt'
        path.write_text(path.read_text().replace('44','45'))
        self.rehash(case.name,'transcript.txt');self.reject()

    def test_rehashed_changed_keystrokes(self):
        case=self.capture/'normal-midnight';path=case/'KEYS.TXT'
        path.write_bytes(path.read_bytes().replace(b'P;0;0;0',b'P;1;0;0'))
        self.rehash(case.name,'KEYS.TXT');self.reject()

    def test_rehashed_missing_return_marker(self):
        case=self.capture/'normal-midnight'
        (case/'RETURN.LOG').write_bytes(b'PROGRAM_DID_NOT_RETURN')
        self.rehash(case.name,'RETURN.LOG');self.reject()

    def test_rehashed_undeclared_world_patch(self):
        case=self.capture/'amplified-midnight';path=case/'before.dat.gz'
        world=bytearray(gzip.decompress(path.read_bytes()));world[700]^=1
        path.write_bytes(gzip.compress(world,mtime=0))
        self.rehash(case.name,path.name);self.reject()

    def test_rehashed_world_reload_break(self):
        case=self.capture/'amplified-reload';path=case/'before.dat.gz'
        world=bytearray(gzip.decompress(path.read_bytes()));world[700]^=1
        path.write_bytes(gzip.compress(world,mtime=0))
        self.rehash(case.name,path.name);self.reject()

    def test_rehashed_auxiliary_reload_break(self):
        case=self.capture/'amplified-reload';path=case/'side-before.json.gz'
        side=json.loads(gzip.decompress(path.read_bytes()));side['YTNEWS.DAT']=''
        path.write_bytes(gzip.compress(json.dumps(side).encode(),mtime=0))
        self.rehash(case.name,path.name);self.reject()

    def test_rehashed_cash_mutation(self):
        case=self.capture/'normal-midnight';path=case/'after.dat.gz'
        world=bytearray(gzip.decompress(path.read_bytes()))
        checker.mbf.put(world,2,81,1000001)
        path.write_bytes(gzip.compress(world,mtime=0))
        self.rehash(case.name,path.name);self.reject()

    def test_changed_binary_identity(self):
        path=self.capture/'normal-midnight/result.json'
        metadata=json.loads(path.read_text());metadata['binaries']['BRUN30.EXE']='0'*64
        path.write_text(json.dumps(metadata));self.reject()

    def test_removed_hash_coverage(self):
        path=self.capture/'normal-midnight/result.json'
        metadata=json.loads(path.read_text());del metadata['files']['game.log.gz']
        path.write_text(json.dumps(metadata));self.reject()

    def test_incomplete_process_cannot_qualify(self):
        path=self.capture/'normal-midnight/result.json'
        metadata=json.loads(path.read_text());metadata['complete']=False
        path.write_text(json.dumps(metadata));self.reject()


if __name__=='__main__':unittest.main()
