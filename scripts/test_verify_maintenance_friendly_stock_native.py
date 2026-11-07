"""Corruption and read-isolation controls for friendly-stock source evidence."""
import copy
import json
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

import verify_maintenance_friendly_stock_native as native


class FriendlyStockNative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet = (native.ROOT/native.PACKET).read_bytes()
        cls.binary = (native.ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes()
        cls.record = native.select_record(cls.packet)

    def test_original_packet_and_conditional_source_order(self):
        result = native.verify()
        self.assertEqual((result['reused_native_packets'], result['reused_native_reads'], result['retained_read_bytes']), (1, 1, 3462))
        self.assertEqual(result['entering_force_cache'], '7b90')
        self.assertTrue(result['pickup_precedes_plain_merge'])
        self.assertFalse(result['planet_governor_is_pickup_gate'])
        self.assertEqual(result['taking_stamp'], 'actor + entering physical force')
        self.assertIn('equals zero', result['capture_gate'])
        self.assertIn('positive', result['taking_gate'])
        self.assertIn('eager', result['hold_gate'])
        self.assertIn('no assertion that a local group held', result['scope'])

    def test_complete_packet_and_original_binary_are_pinned(self):
        for value in (self.packet+b'\n', self.packet[:-1]):
            with self.assertRaisesRegex(AssertionError, 'immutable complete'): native.select_record(value)
        with self.assertRaisesRegex(AssertionError, 'immutable original'): native.verify_record(self.record, self.binary+b'\0')
        with self.assertRaisesRegex(AssertionError, 'immutable original'): native.verify_paths(self.binary+b'\0')

    def test_unique_evidence_record_even_if_whole_packet_gate_is_bypassed(self):
        value = json.loads(self.packet)
        for rows in ([], value['records']+value['records']):
            changed = json.dumps(dict(records=rows)).encode()
            real = native.SHA
            with patch.object(native, 'SHA', side_effect=lambda b: native.PACKET_SHA if b == changed else real(b)):
                with self.assertRaisesRegex(AssertionError, 'one exact'): native.select_record(changed)

    def test_exact_identity_operation_subject_and_read_parameters(self):
        for key, value in (('evidence_id', 'ev_wrong'), ('operation', 'analyze_function'), ('parameters', dict(address='0x149f1', length=71))):
            row = copy.deepcopy(self.record); row[key] = value
            with self.subTest(key=key), self.assertRaises(AssertionError): native.verify_record(row, self.binary)
        row = copy.deepcopy(self.record); row['subject']['digest']['sha256'] = '0'*64
        with self.assertRaises(AssertionError): native.verify_record(row, self.binary)

    def test_truncated_shifted_or_altered_native_read_rejected(self):
        for key, value in (('address', '0x14601'), ('complete', False), ('returned_bytes', 3461), ('requested_bytes', 3461)):
            row = copy.deepcopy(self.record); row['normalized_result'][key] = value
            with self.subTest(key=key), self.assertRaises(AssertionError): native.verify_record(row, self.binary)
        row = copy.deepcopy(self.record)
        code = bytearray.fromhex(row['normalized_result']['bytes_hex']); code[0x4a01-0x4600] ^= 1
        row['normalized_result']['bytes_hex'] = code.hex()
        with self.assertRaisesRegex(AssertionError, 'relocated MZ'): native.verify_record(row, self.binary)

    def test_each_independent_source_contract_rejects_a_semantic_change(self):
        # Bypass only the hash in this negative control. Each mutated source
        # range still independently fails its declared call/order contract.
        head = struct.unpack_from('<H', self.binary, 8)[0]*16
        for name, (offset, expected) in native.SPANS.items():
            changed = bytearray(self.binary); changed[head+offset] ^= 1; changed = bytes(changed)
            real = native.SHA
            with self.subTest(contract=name), patch.object(native, 'SHA', side_effect=lambda b: native.BINARY_SHA if b == changed else real(b)):
                with self.assertRaisesRegex(AssertionError, 'original source contract: '+name): native.verify_paths(changed)

    def test_precise_force_gate_addition_and_receipt_mutations_are_rejected(self):
        # These touch operands/branches, not merely the first byte of a range:
        # descriptor1890, cache7b90, sector owner18ec, eager RND, stock/actor/
        # entering sum, zero-force capture test, taking amount, skip-merge jump.
        changes = ((0x4a02, 0x94), (0x4a0f, 0x92), (0x4c83, 0xee),
                   (0x485c, 0x35), (0x4d7d, 0x20), (0x4dc8, 0x00),
                   (0x4e35, 0xfa), (0x4ec1, 0x70), (0x4f60, 0xd1))
        head = struct.unpack_from('<H', self.binary, 8)[0]*16
        real = native.SHA
        for offset, value in changes:
            changed = bytearray(self.binary); self.assertNotEqual(changed[head+offset], value)
            changed[head+offset] = value; changed = bytes(changed)
            with self.subTest(offset=hex(offset)), patch.object(native, 'SHA', side_effect=lambda b: native.BINARY_SHA if b == changed else real(b)):
                with self.assertRaisesRegex(AssertionError, 'original source contract'): native.verify_paths(changed)

    def test_source_literals_keep_zero_encodings_and_single_hold_threshold(self):
        real = native.SHA
        for offset in native.LITERALS:
            changed = bytearray(self.binary); changed[offset+0xfd0+2] ^= 1; changed = bytes(changed)
            with self.subTest(literal=hex(offset)), patch.object(native, 'SHA', side_effect=lambda b: native.BINARY_SHA if b == changed else real(b)):
                with self.assertRaisesRegex(AssertionError, 'original source literal'): native.verify_paths(changed)
        self.assertNotEqual(native.LITERALS[0x8472], native.LITERALS[0x859e])

    def test_only_retained_packet_and_original_binary_are_opened(self):
        allowed = {native.ROOT/native.PACKET, native.ROOT/'archive/dos-original/YTMAINT.EXE'}
        read = Path.read_bytes; seen = []
        def guarded(path):
            self.assertIn(path, allowed); seen.append(path); return read(path)
        with patch.object(Path, 'read_bytes', guarded): native.verify()
        self.assertEqual(set(seen), allowed); self.assertEqual(len(seen), 2)


if __name__ == '__main__': unittest.main()
