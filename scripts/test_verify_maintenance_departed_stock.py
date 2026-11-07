"""Corruption controls for departed-garrison acquisition, not replay acceptance."""
import copy
import gzip
import json
from pathlib import Path
import tempfile
import unittest
import verify_maintenance_departed_stock as v

class DepartedStockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=v.ROOT/'research/yt-maint/departed-stock-controls'
        cls.summary=v.verify(cls.root)

    def test_full_supplement(self):
        self.assertEqual(len(v.verify(v.ROOT/'research/yt-maint/departed-stock-zero-controls')),2)

    def test_departed_and_held_controls(self):
        self.assertTrue(self.summary['second-four-whole']['composition']['departed'])
        self.assertFalse(self.summary['second-two-whole']['composition']['departed'])

    def reject_stats(self,case,mutate):
        stats=copy.deepcopy(self.summary[case]);mutate(stats)
        with self.assertRaises(AssertionError):v.qualify_composition(case,stats)

    def test_combined_actor_rejected(self):
        self.reject_stats('second-four-whole',lambda s:s['taking_receipts'][0].update(actor=97374))

    def test_missing_capture_rejected(self):
        self.reject_stats('second-four-owned',lambda s:s.update(captures=[]))

    def test_missing_reactivation_rejected(self):
        self.reject_stats('second-four-whole',lambda s:s['mercenary_moves'].pop())

    def test_missing_second_reactivation_rejected(self):
        self.reject_stats('second-eight-whole',lambda s:s['mercenary_moves'].pop())

    def test_double_count_rejected(self):
        self.reject_stats('second-four-whole',lambda s:s['final_physical'].__setitem__(-2,97448))

    def test_fractional_receipt_rejected(self):
        self.reject_stats('second-two-half',lambda s:s.update(taking_receipts=[dict(actor=97374,amount=1)]))

    def test_lost_departed_group_rejected(self):
        self.reject_stats('second-four-whole',lambda s:s.update(final_mercenary_sectors=[3000]))

    def test_uncleared_stock_rejected(self):
        self.reject_stats('second-four-whole',lambda s:s.update(stock_cleared=False))

    def test_raw_output_corruption_rejected(self):
        profile='second-four-whole';folder=self.root/profile/'child-1/unobserved-a'
        before={n:gzip.decompress((folder/('before-'+n+'.gz')).read_bytes()) for n in v.FILES}
        after={n:gzip.decompress((folder/('after-'+n+'.gz')).read_bytes()) for n in v.FILES}
        after['YTNEWS.DAT']=b''
        with self.assertRaises(AssertionError):v.verify_semantics(profile,before,after,(folder/'TRACE.BIN').read_bytes())

    def test_manifest_corruption_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/self.root.name;root.mkdir();(root/'pins.json').write_text('{}')
            with self.assertRaises(AssertionError):v.verify(root)

if __name__=='__main__':unittest.main()
