"""Preserve the distinction between startup observations and later-call claims."""
import json,shutil,tempfile,unittest,struct
from pathlib import Path
import audit_mode_selector_bytes as scan
import verify_mode_selector_startup as audit
from recover_mode_selector_startup import payload


class SelectorAdmission(unittest.TestCase):
    def test_complete_native_static_and_source_audit(self):
        result=audit.verify();self.assertEqual(len(result['startup_snapshots']),7);self.assertEqual(result['byte_inventory_programs'],8)
        self.assertEqual(result['decision'],'no-mode4-replay-migration-admitted')

    def test_payload_is_independently_reconstructed(self):self.assertEqual(payload(),audit.expected_payload())

    def test_loader_relocation_overlap_cannot_corrupt_probe(self):
        for offset in (0x39,0x3a,0x6c,0x6d):
            original=bytearray(64);struct.pack_into('<H',original,6,1);struct.pack_into('<H',original,24,28);struct.pack_into('<HH',original,28,offset,0)
            with self.assertRaises(AssertionError):audit.verify_relocations(original,len(payload()))
        original=bytearray(64);struct.pack_into('<H',original,6,1);struct.pack_into('<H',original,24,28);struct.pack_into('<HH',original,28,0x33,0)
        audit.verify_relocations(original,len(payload())) # Preserved startup-call relocation is allowed.

    def test_changed_snapshot_selector_is_not_admitted(self):
        for name in audit.PROGRAMS:
            trace=bytearray((audit.DEFAULT/name.lower()/'TRACE.BIN').read_bytes());trace[35]=4
            with self.assertRaises(AssertionError):audit.verify_trace(bytes(trace))

    def test_truncated_or_unframed_snapshot_rejected(self):
        t=(audit.DEFAULT/'yt.exe/TRACE.BIN').read_bytes()
        for bad in (t[:-1],t+b'x',b'XXXX'+t[4:],t[:35]):
            with self.assertRaises(AssertionError):audit.verify_trace(bad)

    def test_absolute_byte_and_overlapping_word_stores_detected(self):
        for signature in ('c6061f0004','a21f00','881e1f00','c7061e000004','a31e00','8f061f00','80061f0004','83061e0004','d11e1e00','fe061f00'):
            result=scan.store_candidates(bytes.fromhex(signature),0)
            self.assertTrue(result,signature);self.assertEqual(result[0]['file_offset'],0)

    def test_reads_relative_calls_and_cmp_are_not_stores(self):
        for raw in ('803e1f0004','e81f00','a01f00','a11e00','813e1e000004'):
            self.assertEqual(scan.store_candidates(bytes.fromhex(raw),0),[])

    def test_indirect_writes_remain_outside_signature_scope(self):
        # MOV byte [BX],4 can select a computed address. This inventory cannot
        # exclude it; an empty direct-store result must never become that claim.
        self.assertEqual(scan.store_candidates(bytes.fromhex('c60704'),0),[])
        self.assertTrue(any('Indirect writes' in s for s in scan.build()['limitations']))

    def test_empty_provider_xrefs_do_not_hide_positive_reads(self):
        report=audit.verify_static();self.assertEqual(len(report['programs'][0]['compare_mode4_offsets']),5)
        packet=json.loads((audit.ROOT/'research/yt-mbf-mode-selector/rea/selector-xrefs.json').read_text())
        self.assertEqual(packet['data']['normalized_result'],[])

    def test_source_or_capture_mutation_rejected_by_manifest(self):
        for changed in ('sources/recover_mode_selector_startup.py','yt.exe/TRACE.BIN'):
            with tempfile.TemporaryDirectory() as temp:
                root=Path(temp)/'native';shutil.copytree(audit.DEFAULT,root);(root/changed).write_bytes(b'changed')
                with self.assertRaises(AssertionError):audit.verify(root)

    def test_all_current_sector_ids_agree_in_both_numeric_modes(self):
        from replay_qb_initializer import sector_record
        from replay_qb_graph import mbf
        from verify_int16_single import expected_integer as nearest
        from verify_int16_mode4 import expected_integer as floor
        for sector in range(1,3001):
            raw=mbf.enc(sector);self.assertEqual(nearest(raw),sector);self.assertEqual(floor(raw),sector)
            fac=bytearray(mbf.enc(sector+51));fac[:2]=sector.to_bytes(2,'little');fac[3]=0
            record=sector_record(sector,[0]*6)
            self.assertEqual(record[41:65],bytes(fac)*6)

    def test_large_stock_INT_must_not_be_replaced_with_signed16(self):
        from replay_maintenance_stock_mercenary import positive_single_floor
        from replay_qb_graph import mbf
        from verify_int16_mode4 import expected_integer
        self.assertEqual(positive_single_floor(189529.5),189529)
        self.assertIsNone(expected_integer(mbf.enc(189529.5)))

if __name__=='__main__':unittest.main()
