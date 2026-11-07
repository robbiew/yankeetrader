"""Independent corruption checks for the retained stock INT source contracts."""
import copy
import json
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

import verify_maintenance_stock_conversion_native as native


class StockConversionNative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packets={key:(native.ROOT/path).read_bytes()for key,(path,_,_)in native.PACKETS.items()}
        cls.binaries={name:(native.ROOT/'archive/dos-original'/name).read_bytes()for name in native.BINARIES}
        cls.records=native.select_records(cls.packets)

    def test_all_existing_packets_reads_and_original_paths_verify(self):
        result=native.verify()
        self.assertEqual((result['reused_native_packets'],result['reused_native_reads'],result['retained_read_bytes']),(3,4,3932))
        self.assertTrue(result['overlapping_reads']);self.assertEqual(result['single_INT_entry'],'0x1acb2')
        self.assertEqual(result['positive_mask_helper'],'0x1ad17');self.assertEqual(result['source_stock_clear'],'00008000')
        self.assertEqual(set(self.records),{'pickup','dispatch','positive-entry','floor'})

    def test_complete_packet_bytes_are_pinned_not_just_selected_rows(self):
        for key,raw in self.packets.items():
            broken=dict(self.packets);broken[key]=raw+b'\n'
            with self.subTest(packet=key),self.assertRaisesRegex(AssertionError,'immutable complete native packet'):native.select_records(broken)
        with self.assertRaises(AssertionError):native.select_records({})

    def test_exact_evidence_subject_operation_and_parameters_are_required(self):
        for name,row in self.records.items():
            binary=self.binaries[native.CONTRACTS[name][2]]
            for key,value in(('evidence_id','ev_unrelated'),('operation','analyze_function'),('parameters',{'address':'0x10000','length':1})):
                broken=copy.deepcopy(row);broken[key]=value
                with self.subTest(read=name,key=key),self.assertRaises(AssertionError):native.verify_record(broken,binary,name)
            broken=copy.deepcopy(row);broken['subject']['digest']['sha256']='0'*64
            with self.subTest(read=name,key='subject'),self.assertRaises(AssertionError):native.verify_record(broken,binary,name)

    def test_truncated_wrong_address_and_mutated_native_bytes_are_rejected(self):
        for name,row in self.records.items():
            binary=self.binaries[native.CONTRACTS[name][2]]
            for key,value in(('complete',False),('address','0x10000'),('returned_bytes',1),('requested_bytes',1)):
                broken=copy.deepcopy(row);broken['normalized_result'][key]=value
                with self.subTest(read=name,key=key),self.assertRaises(AssertionError):native.verify_record(broken,binary,name)
            broken=copy.deepcopy(row);data=bytearray.fromhex(broken['normalized_result']['bytes_hex']);data[0]^=1;broken['normalized_result']['bytes_hex']=data.hex()
            with self.subTest(read=name,key='bytes'),self.assertRaisesRegex(AssertionError,'relocated MZ'):native.verify_record(broken,binary,name)

    def test_unique_retained_evidence_ids_are_checked_even_if_packet_hash_gate_is_bypassed(self):
        key='pickup';_,digest,_=native.PACKETS[key];value=json.loads(self.packets[key]);value['records'].append(copy.deepcopy(value['records'][0]))
        changed=json.dumps(value).encode();broken=dict(self.packets);broken[key]=changed;real=native.SHA
        with patch.object(native,'SHA',side_effect=lambda b:digest if b==changed else real(b)):
            with self.assertRaisesRegex(AssertionError,'one exact independently declared evidence ID'):native.select_records(broken)
        value['records']=[];changed=json.dumps(value).encode();broken[key]=changed
        with patch.object(native,'SHA',side_effect=lambda b:digest if b==changed else real(b)):
            with self.assertRaisesRegex(AssertionError,'one exact independently declared evidence ID'):native.select_records(broken)

    def test_original_binary_identity_cannot_be_replaced_by_a_matching_packet(self):
        for name,row in self.records.items():
            subject=native.CONTRACTS[name][2];binary=self.binaries[subject]
            with self.subTest(read=name),self.assertRaisesRegex(AssertionError,'immutable original subject'):native.verify_record(row,binary+b'\0',name)
        with self.assertRaises(AssertionError):native.verify_paths(self.binaries['YTMAINT.EXE']+b'\0',self.binaries['BRUN30.EXE'])

    def test_semantic_source_contracts_remain_independent_of_the_hash_gate(self):
        # Each change keeps the input extent but violates a distinct original
        # call/order/raw-zero contract. Production never bypasses these hashes.
        cases=(('YTMAINT.EXE',0x4cdd,0x04),('BRUN30.EXE',0x171+3*2,0x92),
               ('BRUN30.EXE',0xacce,0xcf),('BRUN30.EXE',0xad3a,0x08),('BRUN30.EXE',0xad4b,0x01),
               ('YTMAINT.EXE',0x4d0a,0x74),('YTMAINT.EXE',0x4d36,0x26),('YTMAINT.EXE',0x4d69,0xfa),
               ('YTMAINT.EXE',0x4e35,0xc4))
        real=native.SHA
        for subject,offset,value in cases:
            original=self.binaries[subject];changed=bytearray(original);head=struct.unpack_from('<H',original,8)[0]*16;changed[head+offset]=value;changed=bytes(changed)
            bins=dict(self.binaries);bins[subject]=changed
            with self.subTest(subject=subject,offset=hex(offset)),patch.object(native,'SHA',side_effect=lambda b:native.BINARIES[subject]if b==changed else real(b)):
                with self.assertRaises(AssertionError):native.verify_paths(bins['YTMAINT.EXE'],bins['BRUN30.EXE'])
        subject='YTMAINT.EXE';original=self.binaries[subject];changed=bytearray(original);changed[0x8472+0xfd0+2]=0;changed=bytes(changed)
        with patch.object(native,'SHA',side_effect=lambda b:native.BINARIES[subject]if b==changed else real(b)):
            with self.assertRaisesRegex(AssertionError,'exact original source literal8472'):native.verify_paths(changed,self.binaries['BRUN30.EXE'])

    def test_only_existing_three_packets_and_two_originals_are_opened(self):
        allowed={native.ROOT/path for path,_,_ in native.PACKETS.values()}|{native.ROOT/'archive/dos-original'/name for name in native.BINARIES}
        read=Path.read_bytes;seen=[]
        def guarded(path):
            self.assertIn(path,allowed);seen.append(path);return read(path)
        with patch.object(Path,'read_bytes',guarded):native.verify()
        self.assertEqual(set(seen),allowed);self.assertEqual(len(seen),5)

if __name__=='__main__':unittest.main()
