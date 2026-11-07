"""Independent provenance and owner-transfer/mine composition corruption checks."""
import copy
import gzip
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import verify_maintenance_neutral_owner_stock as v

class NeutralOwnerStockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary=v.verify();cls.observer=(v.DEFAULT/'sources/observe_maintenance_departure.js').read_text()

    def reject_stats(self,case,mutation):
        stats=copy.deepcopy(self.summary[case]);mutation(stats)
        with self.assertRaises(AssertionError):v.qualify_composition(case,stats)

    def corrupt_case(self,mutate,case='neutral-mine-whole',mode='observed-a'):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/mode;shutil.copytree(v.DEFAULT/case/'child-1'/mode,folder)
            meta=json.loads((folder/'capture.json').read_text());mutate(folder,meta)
            meta['files']={n:v.SHA((folder/n).read_bytes()) for n in meta['files']}
            (folder/'capture.json').write_text(json.dumps(meta))
            with self.assertRaises((AssertionError,ValueError,KeyError)):
                v.verify_case(folder,case,mode,self.observer)

    def test_complete_six_mode_inventory(self):
        self.assertEqual(len(self.summary),6)
        self.assertTrue(all(s['paired']['equal'] for s in self.summary.values()))

    def test_neutral_force_transfers_and_subunit_stock_is_not_a_fighter(self):
        self.assertEqual(self.summary['neutral-one-empty']['composition']['neutral_transferred'],1)
        self.assertEqual(self.summary['neutral-half']['composition']['receipt_actor'],97374)
        self.assertEqual(self.summary['neutral-half']['public_pickup'],0)

    def test_measured_mine_losses_and_separate_departed_group(self):
        self.assertEqual([self.summary[c]['quantified_mine_losses'] for c in ('neutral-mine-whole','friendly-mine-second-two','friendly-mine-second-four')],[381,159,4374])
        self.assertEqual(self.summary['friendly-mine-second-four']['final_mercenary_sectors'],[356,3000])
        self.assertEqual(self.summary['friendly-mine-second-four']['xannor_losses'],3673)

    def test_neutral_transfer_cannot_be_ignored(self):
        self.reject_stats('neutral-whole',lambda s:s.update(neutral_transfer=0))

    def test_neutral_group_cannot_be_duplicated(self):
        self.reject_stats('neutral-whole',lambda s:s['final_physical'].__setitem__(0,37))

    def test_pre_mine_actor_cannot_stamp_receipt(self):
        self.reject_stats('neutral-mine-whole',lambda s:s['taking_receipts'][0].update(actor=97374))

    def test_local_force_is_not_charged_as_incoming_mine_damage(self):
        self.reject_stats('friendly-mine-second-two',lambda s:s['mine_receipts'][0].update(actor=97374))

    def test_positive_entering_force_cannot_emit_capture(self):
        self.reject_stats('neutral-whole',lambda s:s['captures'].append(dict(actor=97374,title='Gateway Cache')))

    def test_departed_group_cannot_stamp_combined_receipt(self):
        self.reject_stats('friendly-mine-second-four',lambda s:s['taking_receipts'][0].update(actor=93000))

    def test_later_activation_cannot_disappear(self):
        self.reject_stats('friendly-mine-second-four',lambda s:s['mercenary_moves'].pop())

    def test_mine_receipt_must_precede_stock_receipt(self):
        self.reject_stats('neutral-mine-whole',lambda s:s['taking_receipts'][0].update(ordinal=1))

    def test_stock_cannot_remain_uncleared(self):
        self.reject_stats('neutral-half',lambda s:s.update(stock_cleared=False))

    def test_rehashed_error_log_is_rejected(self):
        self.corrupt_case(lambda f,m:(f/'ERROR.LOG').write_bytes(b'PROGRAM_ERROR\r\n'))

    def test_rehashed_missing_host_arguments_are_rejected(self):
        self.corrupt_case(lambda f,m:(f/'dosbox.stderr').write_bytes(b''))

    def test_changed_declared_clock_is_rejected(self):
        self.corrupt_case(lambda f,m:m.update(clock='00:00:04'))

    def test_rehashed_substituted_observer_is_rejected(self):
        self.corrupt_case(lambda f,m:(f/'loaded-observer.js').write_text('unrelated observer'))

    def test_rehashed_dos_command_change_is_rejected(self):
        self.corrupt_case(lambda f,m:(f/'COMMANDS.TXT').write_text('ytmaint\n'))

    def test_rehashed_neutral_owner_input_change_is_rejected(self):
        def mutate(folder,meta):
            path=folder/'before-YTDATA.DAT.gz';raw=bytearray(gzip.decompress(path.read_bytes()));at=3050*137+85
            raw[at:at+4]=v.encode(-2);path.write_bytes(gzip.compress(bytes(raw),mtime=0));meta['inputs']['YTDATA.DAT']=v.SHA(raw)
        self.corrupt_case(mutate)

    def test_missing_mode_and_frozen_source_corruption_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'controls';root.mkdir();(root/'pins.json').write_bytes((v.DEFAULT/'pins.json').read_bytes())
            with self.assertRaises(AssertionError):v.verify(root)

    def test_modified_manifest_cannot_admit_changed_observations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'pins.json').write_text('{"files":{}}')
            with self.assertRaises(AssertionError):v.verify(root)

if __name__=='__main__':unittest.main()
