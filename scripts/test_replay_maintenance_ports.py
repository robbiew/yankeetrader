"""Independent bounded-port model properties; no observed after-world templates."""
import builtins
from pathlib import Path
import unittest
from unittest.mock import patch
import replay_maintenance_ports as replay

mbf=replay.graph.mbf


def fixture(rates=(1000,2000,3000),coefficients=(11,-12,13)):
    data=bytearray(4151*137)
    for ident in range(1,1001):
        at=(3050+ident)*137
        data[at:at+41]=(f'Input port{ident}').encode().ljust(41,b' ')
        for off,value in [(41,2),(45,296)]+list(zip((61,65,69),rates))+list(zip((73,77,81),coefficients))+[(117,849),(121,1000),(125,6324)]:
            data[at+off:at+off+4]=mbf.enc(value)
    return bytes(data)


class PortReplayProperties(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before=fixture();cls.clock=[bytes.fromhex('00004800')]*1000

    def run_model(self,before=None,clock=None,day=306):
        return replay.replay_ports(self.before if before is None else before,day,self.clock if clock is None else clock)

    def test_ten_day_stock_class_and_signed_coefficients(self):
        block,stats=self.run_model();self.assertEqual(stats['class_counts'],[1000,0,0])
        for ident in (1,17,1000):
            record=block[(ident-1)*137:ident*137]
            self.assertEqual([mbf.dec(record[o:o+4])for o in (41,45,49,53,57,73,77,81)],[1,306,10000,20000,30000,-11,-12,13])

    def test_first_maximum_wins_ties(self):
        block,_=self.run_model(fixture((3000,3000,1000)))
        self.assertEqual(mbf.dec(block[41:45]),3)
        self.assertEqual([mbf.dec(block[o:o+4])for o in (73,77,81)],[11,-12,-13])

    def test_raw_zero_residue_is_preserved(self):
        block,_=self.run_model()
        self.assertEqual(block[101:105],bytes.fromhex('00004800'))
        self.assertNotEqual(block[101:105],bytes(4))

    def test_independent_raw_clock_epochs(self):
        raw='0e745a76';clock=replay.timer_epochs([(1,'00004800'),(600,raw)])
        self.assertEqual(len(clock),1000)
        block,_=self.run_model(clock=clock)
        self.assertEqual(block[598*137+101:598*137+105],bytes.fromhex('00004800'))
        self.assertEqual(block[599*137+101:599*137+105],bytes.fromhex(raw))

    def test_unrelated_input_bytes_and_names_survive(self):
        block,_=self.run_model()
        changed=set(range(41,61))|set(range(73,85))|set(range(101,105))
        for ident in (1,500,1000):
            original=self.before[(3050+ident)*137:(3051+ident)*137]
            actual=block[(ident-1)*137:ident*137]
            self.assertTrue(all(original[o]==actual[o]for o in range(137)if o not in changed))

    def test_synthesis_opens_no_target_or_other_file(self):
        with patch.object(builtins,'open',side_effect=AssertionError('unexpected file read')),patch.object(Path,'open',side_effect=AssertionError('unexpected path read')):
            block,_=self.run_model()
        self.assertEqual(len(block),137000)

    def test_rejects_noninitial_world_economic_inputs(self):
        for off,value in [(45,297),(49,1),(53,1),(57,1),(89,1),(97,1),(101,1),(61,0),(65,32767),(69,1.5),(73,0),(77,101)]:
            with self.subTest(off=off,value=value):
                b=bytearray(self.before);at=3051*137+off;b[at:at+4]=mbf.enc(value)
                with self.assertRaises(ValueError):self.run_model(bytes(b))

    def test_rejects_missing_malformed_or_backward_clock(self):
        for clock in [[],self.clock[:-1],[bytes(3)]*1000,[bytearray(4)]*1000,[mbf.enc(-1)]*1000,[mbf.enc(1440)]*1000,[mbf.enc(1)]+self.clock[1:]]:
            with self.subTest(first=clock[:1],length=len(clock)):
                with self.assertRaises(ValueError):self.run_model(clock=clock)

    def test_rejects_wrong_extent_and_calendar_bounds(self):
        with self.assertRaises(ValueError):self.run_model(self.before[:-1])
        for day in (0,367,True,306.5):
            with self.subTest(day=day):
                with self.assertRaises(ValueError):self.run_model(day=day)

    def test_rejects_unordered_or_unbounded_clock_epochs(self):
        for epochs in [[],[(0,'00004800')],[(2,'00004800')],[(1,'00004800'),(1,'00004800')],[(1,'00004800'),(1001,'00004800')],[(1,'00')]]:
            with self.subTest(epochs=epochs):
                with self.assertRaises(ValueError):replay.timer_epochs(epochs)


if __name__=='__main__':unittest.main()
