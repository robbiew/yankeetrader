"""Direct independent original-byte/provenance corruption controls."""
import copy
import json
from pathlib import Path
import unittest

import verify_maintenance_evolved_replay as v


class NativeReplayEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records=json.loads(v.PACKET.read_text())['records']
        cls.original=(v.ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes()

    def test_complete_packet_and_relocated_original(self):
        self.assertEqual(v.verify(),dict(native_reads=1,complete_bytes=153,production_save_version=35))

    def test_altered_original_rejected(self):
        b=bytearray(self.original);b[100]^=1
        with self.assertRaises(AssertionError):v.verify_records(self.records,bytes(b))

    def test_missing_duplicate_or_extra_read_rejected(self):
        for records in([],self.records+[self.records[0]],[self.records[0],self.records[0]]):
            with self.subTest(count=len(records)),self.assertRaises(AssertionError):v.verify_records(records,self.original)

    def test_wrong_subject_operation_or_range_rejected(self):
        mutations=[lambda r:r.update(operation='analyze_function'),lambda r:r['subject'].update(name='other.EXE'),lambda r:r['subject']['digest'].update(sha256='0'*64),lambda r:r['parameters'].update(address='0x14129')]
        for mutate in mutations:
            records=copy.deepcopy(self.records);mutate(records[0])
            with self.subTest(mutation=mutations.index(mutate)),self.assertRaises(AssertionError):v.verify_records(records,self.original)

    def test_incomplete_or_mismatched_lengths_rejected(self):
        for change in(dict(complete=False),dict(requested_bytes=152),dict(returned_bytes=152),dict(address='0x14129')):
            records=copy.deepcopy(self.records);records[0]['normalized_result'].update(change)
            with self.subTest(change=change),self.assertRaises(AssertionError):v.verify_records(records,self.original)

    def test_changed_or_truncated_native_bytes_rejected(self):
        for truncate in(False,True):
            records=copy.deepcopy(self.records);raw=bytearray.fromhex(records[0]['normalized_result']['bytes_hex'])
            if truncate:raw.pop()
            else:raw[50]^=1
            records[0]['normalized_result']['bytes_hex']=raw.hex()
            with self.subTest(truncate=truncate),self.assertRaises(AssertionError):v.verify_records(records,self.original)


if __name__=='__main__':unittest.main()
