"""Native observation corruption must be rejected, independently of RNG traces."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from verify_rng_native import ROOT,CONTRACTS,verify

class NativeRNGTests(unittest.TestCase):
    def test_retained(self):self.assertEqual(verify(ROOT/'research/yt-rng-seeding'),13)
    def test_missing_empty_truncated_or_changed_reads(self):
        for mode in ('missing','empty','truncated','bytes','target','parameters'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                for name in CONTRACTS:shutil.copy2(ROOT/'research/yt-rng-seeding'/name,root/name)
                p=root/'runtime-rea.json';bundle=json.loads(p.read_text())
                if mode=='missing':bundle['records'].pop()
                else:
                    r=bundle['records'][0];n=r['normalized_result']
                    if mode=='target':r['subject']['digest']['sha256']='0'*64
                    elif mode=='parameters':r['parameters']['length']=0
                    elif mode=='bytes':n['bytes_hex']='00'+n['bytes_hex'][2:]
                    else:
                        n['bytes_hex']='' if mode=='empty' else n['bytes_hex'][:-2]
                        n['returned_bytes']=len(n['bytes_hex'])//2
                p.write_text(json.dumps(bundle))
                with self.assertRaises(AssertionError):verify(root)
if __name__=='__main__':unittest.main()
