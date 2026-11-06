"""All gateway port blocks and strict clock/input boundaries."""
import builtins
import gzip
from pathlib import Path
import unittest
from unittest.mock import patch
from test_replay_maintenance_evolved_ports import source_clocks
from replay_qb_graph import mbf
import replay_maintenance_gateway_ports as model
ROOT=Path(__file__).resolve().parents[1]/'research/yt-maint/gateway-hazard-controls'
class GatewayPorts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.folders=list(ROOT.glob('*/child-*/observed-a'))
    def test_all36_source_sets_predict_complete1000_port_records(self):
        for p in self.folders:
            b=gzip.decompress((p/'before-YTDATA.DAT.gz').read_bytes());expected=gzip.decompress((p/'after-YTDATA.DAT.gz').read_bytes())[3051*137:4051*137]
            for mode in('observed-a','observed-b','observed-c'):
                out,stats=model.replay_ports(b,*source_clocks(p.parent/mode/'host-time.json.gz'))
                with self.subTest(case=p.parent.parent.name,stage=p.parent.name,mode=mode):self.assertEqual(out,expected)
                self.assertEqual(stats['rng_draws'],0)
    def test_core_reads_no_files_and_does_not_mutate_inputs(self):
        p=self.folders[0];b=gzip.decompress((p/'before-YTDATA.DAT.gz').read_bytes());clocks=source_clocks(p/'host-time.json.gz');saved=(b,clocks)
        with patch.object(builtins,'open',side_effect=AssertionError('core open')),patch.object(Path,'read_bytes',side_effect=AssertionError('core read')):out,stats=model.replay_ports(b,*clocks)
        self.assertEqual((b,clocks),saved);self.assertEqual(len(out),137000)
    def test_wrong_gateway_identity_or_duplicate_link_is_rejected(self):
        p=self.folders[0];b=gzip.decompress((p/'before-YTDATA.DAT.gz').read_bytes());clocks=source_clocks(p/'host-time.json.gz')
        for r,o,v in((4054,73,-1),(4054,85,12),(3050,93,3),(3051,93,0)):
            w=bytearray(b);mbf.put(w,r,o,v)
            with self.subTest(record=r,offset=o),self.assertRaises(ValueError):model.replay_ports(bytes(w),*clocks)
    def test_wrong_source_dates_noon_mutable_clock_arrays_and_money_branches_rejected(self):
        p=self.folders[0];b=gzip.decompress((p/'before-YTDATA.DAT.gz').read_bytes());days,timers=source_clocks(p/'host-time.json.gz')
        for ds,ts in(((308,)*1000,timers),(days,(mbf.enc(720),)*1000),(list(days),timers),(days,list(timers))):
            with self.assertRaises(ValueError):model.replay_ports(b,ds,ts)
        for offset,value in((89,1),(97,1),(61,70001),(49,1)):
            w=bytearray(b);mbf.put(w,3052,offset,value)
            with self.assertRaises(ValueError):model.replay_ports(bytes(w),days,timers)
if __name__=='__main__':unittest.main()
