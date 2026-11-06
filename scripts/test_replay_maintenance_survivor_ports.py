"""Strict Nov5/6 port clocks and complete native block comparison."""
import builtins
import gzip
import unittest
from pathlib import Path
from unittest.mock import patch
from test_replay_maintenance_evolved_ports import source_clocks
from replay_qb_graph import mbf
import replay_maintenance_survivor_ports as model
ROOT=Path(__file__).resolve().parents[1]/'research/yt-maint/survivor-chain-controls'
class SurvivorPorts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.folders=list(ROOT.glob('*/child-*/observed-a'))
    def test_all24_source_clock_sets_predict_all_native_port_bytes(self):
        for p in self.folders:
            b=gzip.decompress((p/'before-YTDATA.DAT.gz').read_bytes());expected=gzip.decompress((p/'after-YTDATA.DAT.gz').read_bytes())[3051*137:4051*137]
            for mode in('observed-a','observed-b','observed-c'):
                c=source_clocks(p.parent/mode/'host-time.json.gz');out,stats=model.replay_ports(b,*c)
                with self.subTest(case=p.parent.parent.name,child=p.parent.name,mode=mode):self.assertEqual(out,expected)
                self.assertEqual(stats['rng_draws'],0)
    def test_core_reads_no_files_and_keeps_before_input(self):
        p=self.folders[0];b=gzip.decompress((p/'before-YTDATA.DAT.gz').read_bytes());c=source_clocks(p/'host-time.json.gz')
        with patch.object(builtins,'open',side_effect=AssertionError('corefile')),patch.object(Path,'read_bytes',side_effect=AssertionError('corefile')):out,s=model.replay_ports(b,*c)
        self.assertEqual(len(out),137000);self.assertEqual(type(b),bytes)
    def test_other_date_pairs_and_noon_are_rejected(self):
        p=self.folders[0];b=gzip.decompress((p/'before-YTDATA.DAT.gz').read_bytes());days,t=source_clocks(p/'host-time.json.gz')
        for d,ts in(((308,)*1000,t),(days,(mbf.enc(720),)*1000),(list(days),t)):
            with self.assertRaises(ValueError):model.replay_ports(b,d,ts)
        w=bytearray(b);mbf.put(w,3052,45,307)
        with self.assertRaises(ValueError):model.replay_ports(bytes(w),days,t)
    def test_economy_and_money_branches_remain_bounded(self):
        p=self.folders[0];b=gzip.decompress((p/'before-YTDATA.DAT.gz').read_bytes());c=source_clocks(p/'host-time.json.gz')
        for o,v in((89,1),(97,1),(61,70001),(49,1)):
            w=bytearray(b);mbf.put(w,3052,o,v)
            with self.subTest(offset=o),self.assertRaises(ValueError):model.replay_ports(bytes(w),*c)
if __name__=='__main__':unittest.main()
