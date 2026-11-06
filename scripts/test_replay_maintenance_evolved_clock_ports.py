"""Independent full-block checks and admission controls for evolved port clocks."""
import builtins
import gzip
import unittest
from pathlib import Path
from unittest.mock import patch

from replay_qb_graph import mbf
from test_replay_maintenance_evolved_ports import source_clocks
import replay_maintenance_evolved_clock_ports as model

CORPUS=Path(__file__).resolve().parents[1]/'research/yt-maint/evolved-clock-controls'

class ClockPorts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.samples={}
        for folder in sorted(CORPUS.glob('*/child-*')):
            d=folder/'observed-a'
            b=gzip.decompress((d/'before-YTDATA.DAT.gz').read_bytes())
            a=gzip.decompress((d/'after-YTDATA.DAT.gz').read_bytes())[3051*137:4051*137]
            cls.samples[(folder.parent.name,folder.name)]=(b,a,source_clocks(d/'host-time.json.gz'))

    def test_all_24_observed_source_clocks_match_full_native_blocks(self):
        for key,(before,expected,_)in self.samples.items():
            for mode in('observed-a','observed-b','observed-c'):
                with self.subTest(profile=key,mode=mode):
                    clocks=source_clocks(CORPUS/key[0]/key[1]/mode/'host-time.json.gz')
                    actual,stats=model.replay_ports(before,*clocks)
                    self.assertEqual(actual,expected)
                    self.assertEqual((stats['ports'],stats['rng_draws']),(1000,0))

    def test_core_reads_no_files_and_input_is_immutable(self):
        before,expected,clocks=self.samples['noon','child-2'];saved=bytes(before)
        with patch.object(builtins,'open',side_effect=AssertionError('core file access')),patch.object(Path,'read_bytes',side_effect=AssertionError('core file access')):
            actual,_=model.replay_ports(before,*clocks)
        self.assertEqual(actual,expected);self.assertEqual(before,saved)

    def test_half_day_and_ten_day_cap_are_derived(self):
        _,_,c=self.samples['noon','child-2'];b=self.samples['noon','child-2'][0]
        _,s=model.replay_ports(b,*c);self.assertGreater(s['elapsed_min'],.499);self.assertLess(s['elapsed_max'],.501)
        for name in('catchup-eleven','new-year'):
            b,_,c=self.samples[name,'child-1'];_,s=model.replay_ports(b,*c)
            self.assertEqual((s['elapsed_min'],s['elapsed_max']),(10,10))

    def test_year_boundary_uses_base_year_serial_and_large_retained_rates(self):
        b,expected,c=self.samples['new-year','child-2'];actual,s=model.replay_ports(b,*c)
        self.assertEqual(s['day'],367);self.assertEqual(actual,expected)
        self.assertGreater(max(mbf.get(b,r,o)for r in range(3052,4052)for o in(61,65,69)),40000)

    def test_unknown_date_timer_and_mutable_inputs_rejected(self):
        b,_,(days,timers)=self.samples['second-two','child-1']
        invalid=[(bytearray(b),days,timers),(b,list(days),timers),(b,(309,)*1000,timers),(b,days,list(timers)),(b,days,(mbf.enc(300),)*1000)]
        for args in invalid:
            with self.subTest(args_type=type(args[0]),day=args[1][0]),self.assertRaises(ValueError):model.replay_ports(*args)

    def test_unsupported_treasury_nonfull_stock_and_rate_contexts_rejected(self):
        b,_,c=self.samples['second-two','child-1']
        for off,value in((89,1),(97,1),(49,1),(61,100000),(45,305)):
            w=bytearray(b);mbf.put(w,3052,off,value)
            with self.subTest(offset=off),self.assertRaises(ValueError):model.replay_ports(bytes(w),*c)

if __name__=='__main__':unittest.main()
