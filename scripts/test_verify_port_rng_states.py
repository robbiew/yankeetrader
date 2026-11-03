"""Rehashed corruption tests for non-RNG initializer state hooks."""
import gzip
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from verify_port_rng_states import ROOT,SHA,verify
SOURCE=ROOT/'research/yt-port-replay/state-dos'

class PortRNGStateTests(unittest.TestCase):
    def copy(self,tmp):
        target=Path(tmp)/'states';shutil.copytree(SOURCE,target);return target

    def corrupt(self,filename,change,metadata=None):
        with tempfile.TemporaryDirectory()as tmp:
            root=self.copy(tmp);d=root/'midnight-ports-end';p=d/filename
            p.write_bytes(change(p.read_bytes()))
            path=d/'result.json';meta=json.loads(path.read_text());meta['files'][filename]=SHA(p.read_bytes())
            if metadata:metadata(meta)
            path.write_text(json.dumps(meta))
            with self.assertRaises(AssertionError):verify(root)

    def test_retained_controls(self):
        outcomes=verify(SOURCE);self.assertEqual(len(outcomes),12)
        self.assertEqual(outcomes['midnight-graph-end'],0xc3cfff)

    def test_rehashed_raw_state_and_completion(self):
        def state_change(raw):
            raw=bytearray(raw);raw[raw.index(b'\0RS!')+4]^=1;return raw
        cases=(state_change,lambda raw:raw.replace(b'\0RS!',b'\0XX!'),
               lambda raw:raw+b'\0RS!'+bytes(4),
               lambda raw:raw.replace(b'<YT-INIT Normal Termination>',b'<abnormal termination>'))
        for change in cases:
            with self.subTest(change=change):self.corrupt('INIT.LOG',change)

    def test_rehashed_state_with_updated_metadata(self):
        def change(raw):
            raw=bytearray(raw);raw[raw.index(b'\0RS!')+4]^=1;return raw
        self.corrupt('INIT.LOG',change,lambda meta:meta.update(state=meta['state']^1))

    def test_rehashed_world_corruption(self):
        def change(raw):
            world=bytearray(gzip.decompress(raw));world[0]^=1;return gzip.compress(world,mtime=0)
        self.corrupt('before-maint.dat.gz',change)

    def test_rehashed_shell_controls(self):
        for filename,before,after in [('ANSWERS.TXT',b'Y',b'N'),('COMMANDS.TXT',b'time 00:00:00',b'time 00:00:01'),('INITRET.LOG',b'INITIALIZER_RETURNED',b'NOT_RETURNED'),('DOSDATE.LOG',b'11/02/2026',b'11/03/2026'),('DOSTIME.LOG',b'am',b'pm')]:
            with self.subTest(filename=filename):self.corrupt(filename,lambda raw:raw.replace(before,after))

    def test_payload_copy_identity_and_site(self):
        for field in ('payload_hex','initializer_copied_sha256','site_code_offset','cave_code_offset','baseline_world_sha256'):
            with self.subTest(field=field),tempfile.TemporaryDirectory()as tmp:
                root=self.copy(tmp);p=root/'midnight-ports-end/result.json';meta=json.loads(p.read_text());meta[field]=meta[field]+1 if isinstance(meta[field],int)else'00'+meta[field];p.write_text(json.dumps(meta))
                with self.assertRaises(AssertionError):verify(root)

    def test_case_coverage(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=self.copy(tmp);shutil.rmtree(root/'later-ports-end')
            with self.assertRaises(AssertionError):verify(root)

if __name__=='__main__':unittest.main()
