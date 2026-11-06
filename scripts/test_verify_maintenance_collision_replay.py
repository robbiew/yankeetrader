"""Independent byte/provenance corruption checks for the new source packet."""
import copy
import json
import tempfile
from pathlib import Path
import unittest

import verify_maintenance_collision_replay as v


class NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record=json.loads(v.PACKET.read_text())['records'][0]
        cls.original=(v.ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes()
    def test_complete_native_evidence(self):self.assertEqual(v.verify()['complete_bytes'],3462)
    def test_immutable_packet_cannot_be_rehashed(self):
        with tempfile.TemporaryDirectory()as name:
            p=Path(name)/'packet.json';p.write_text(json.dumps({'records':[]}))
            with self.assertRaises(AssertionError):v.verify(p)
    def test_wrong_original_is_rejected(self):
        original=bytearray(self.original);original[-1]^=1
        with self.assertRaises(ValueError):v.verify_record(self.record,bytes(original))


def mutation(name,change):
    def test(self):
        record=copy.deepcopy(self.record);change(record)
        with self.assertRaises((AssertionError,ValueError)):v.verify_record(record,self.original)
    setattr(NativeTests,'test_reject_'+name,test)

mutation('zero_length',lambda r:r['parameters'].update(length=0))
mutation('shifted_address',lambda r:r['parameters'].update(address='0x14601'))
mutation('truncated_data',lambda r:r['normalized_result'].update(bytes_hex=r['normalized_result']['bytes_hex'][:-2]))
mutation('false_returned_extent',lambda r:r['normalized_result'].update(returned_bytes=3461))
mutation('incomplete_read',lambda r:r['normalized_result'].update(complete=False))
mutation('changed_native_byte',lambda r:r['normalized_result'].update(bytes_hex='00'+r['normalized_result']['bytes_hex'][2:]))
mutation('wrong_subject',lambda r:r['subject']['digest'].update(sha256='0'*64))
mutation('wrong_operation',lambda r:r.update(operation='trace_native_values'))

if __name__=='__main__':unittest.main()
