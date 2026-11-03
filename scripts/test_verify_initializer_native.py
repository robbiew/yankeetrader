"""Corruption controls for bounded original initializer byte contracts."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from verify_initializer_native import ROOT,CONTRACTS,verify
SOURCE=ROOT/'research/yt-initializer-replay/native-contracts.json'

class InitializerNativeTests(unittest.TestCase):
    def rejects(self,meta):
        with tempfile.TemporaryDirectory()as tmp:
            p=Path(tmp)/'contracts.json';p.write_text(json.dumps(meta))
            with self.assertRaises(AssertionError):verify(p)

    def test_original_contracts(self):self.assertEqual(verify(),23)

    def test_missing_duplicate_and_extra_reads(self):
        original=json.loads(SOURCE.read_text())
        for mode in ('missing','duplicate','extra'):
            with self.subTest(mode=mode):
                meta=copy.deepcopy(original)
                if mode=='missing':meta['contracts'].pop()
                elif mode=='duplicate':meta['contracts'][-1]=meta['contracts'][0]
                else:meta['contracts'].append(meta['contracts'][0])
                self.rejects(meta)

    def test_every_contract_rejects_changed_coordinates_bytes_and_truncation(self):
        original=json.loads(SOURCE.read_text())
        for i,c in enumerate(original['contracts']):
            for mode in ('offset','length','bytes','truncated','empty','binary'):
                with self.subTest(name=c['name'],mode=mode):
                    meta=copy.deepcopy(original);item=meta['contracts'][i]
                    if mode=='offset':item['file_offset']+=1
                    elif mode=='length':item['length']-=1
                    elif mode=='bytes':item['bytes_hex']=bytes([int(item['bytes_hex'][:2],16)^1]).hex()+item['bytes_hex'][2:]
                    elif mode=='truncated':item['bytes_hex']=item['bytes_hex'][:-2]
                    elif mode=='empty':item['bytes_hex']=''
                    else:item['binary']='unrelated.exe'
                    self.rejects(meta)

    def test_changed_authority_listing_or_format(self):
        for field in ('authority','listing_sha256','format'):
            with self.subTest(field=field):
                meta=json.loads(SOURCE.read_text());meta[field]='changed';self.rejects(meta)

if __name__=='__main__':unittest.main()
