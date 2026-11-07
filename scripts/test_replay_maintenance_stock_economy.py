"""Before-only positive-stock economy from complete modeled November4 parents."""
import builtins
import copy
from fractions import Fraction
import gzip
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import replay_maintenance_evolved_combat_records as prefix
import replay_maintenance_gateway_ports as ports
import replay_maintenance_gateway_planets as historical_planets
import replay_maintenance_stock_planets as planets
from replay_qb_graph import mbf,QB3
from test_replay_maintenance_evolved_ports import source_clocks
from test_replay_maintenance_gateway_planets import source_planet_clocks
import verify_maintenance_stock_conversion as evidence

ROOT=Path(__file__).resolve().parents[1]/'research/yt-maint/stock-conversion-controls'
MODES=('observed-a','observed-b','observed-c')
PARENT='route-mercenary-100000'


def load_observation(path):return json.loads(gzip.decompress(path.read_bytes()))


def fixture(parent,stock):
    """Test-side declared transform over modeled bytes; no captured child input."""
    world=bytearray(parent['YTDATA.DAT'])
    def put(record,offset,value):
        at=(record-1)*137+offset;world[at:at+4]=evidence.encode(value)
    for offset in range(41,65,4):put(2419,offset,3000)
    for sector,offset in((2996,45),(2998,49),(2999,53)):put(51+sector,offset,2368)
    at=(4054-1)*137;world[at:at+137]=b'Gateway Cache'.ljust(41,b' ')+bytes(96)
    for offset,value in((41,308),(73,0),(77,500000),(85,13),(89,0),(117,0),(129,stock)):put(4054,offset,value)
    for offset,value in((81,0),(85,0),(93,3),(129,0)):put(3051,offset,value)
    put(2419,81,97337)
    return bytes(world)


def raw(world,record,offset):
    at=(record-1)*137+offset;return bytes(world[at:at+4])


def run(world,seed,rows):
    work=bytearray(world);stats=planets.maintain(work,SimpleNamespace(rng=QB3(seed)),rows);return bytes(work),stats


class StockEconomyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parents={};cls.samples={};cls.before={}
        original=prefix.initial_before(PARENT)
        for mode in MODES:
            paths=(prefix.PARENT/PARENT/mode/'host-time.json.gz',)+tuple(prefix.DEFAULT/PARENT/f'child-{i}'/mode/'host-time.json.gz'for i in(1,2))
            observations=tuple(load_observation(p)for p in paths)
            outputs,stats=prefix.synthesize_chain(original,tuple(prefix.inputs_from_observation(o)for o in observations));cls.parents[mode]=outputs[-1]
        for case,recipe in evidence.CASES.items():
            for mode in MODES:
                folder=ROOT/case/'child-1'/mode;ob=load_observation(folder/'host-time.json.gz');seed,rows=source_planet_clocks(ob)
                cls.before[case,mode]=fixture(cls.parents[mode],Fraction(*recipe['stock']))
                cls.samples[case,mode]=(folder,ob,seed,rows)

    def test_all36_planet_economies_from_modeled_parent_match_native_writer_fields(self):
        for key,(folder,ob,seed,rows)in self.samples.items():
            work,stats=run(self.before[key],seed,rows)
            # Expected files are first opened after this case's complete economy.
            expected=gzip.decompress((folder/'after-YTDATA.DAT.gz').read_bytes())
            for record,day,timer in rows:
                at=(record-1)*137;omit={77}if record in(4052,4150,4151)else{129}
                indices=[n for n in range(137)if not any(offset<=n<offset+4 for offset in omit)]
                with self.subTest(case=key[0],mode=key[1],record=record):self.assertEqual(bytes(work[at+n]for n in indices),bytes(expected[at+n]for n in indices))
            self.assertEqual(stats['rng_draws'],12)

    def test_all36_port_clock_sets_predict_all1000_complete_raw_records(self):
        for key,(folder,ob,seed,rows)in self.samples.items():
            calendars,timers=source_clocks(folder/'host-time.json.gz');block,stats=ports.replay_ports(self.before[key],calendars,timers)
            expected=gzip.decompress((folder/'after-YTDATA.DAT.gz').read_bytes())[3051*137:4051*137]
            with self.subTest(case=key[0],mode=key[1]):self.assertEqual(block,expected)
            self.assertEqual((stats['ports'],stats['rng_draws']),(1000,0));self.assertEqual(tuple(block[i*137+101:i*137+105]for i in range(1000)),timers)

    def test_input_world_is_constructed_from_the_complete_modeled_prefix(self):
        for key,world in self.before.items():
            self.assertEqual(mbf.get(self.parents[key[1]]['YTDATA.DAT'],1,81),308)
            self.assertEqual(mbf.get(self.parents[key[1]]['YTDATA.DAT'],4054,85),0)
            self.assertEqual(mbf.get(world,4054,85),13)
            self.assertEqual(raw(world,4054,129),evidence.encode(Fraction(*evidence.CASES[key[0]]['stock'])))
            untouched=self.parents[key[1]]['YTDATA.DAT'][3051*137:4051*137]
            self.assertEqual(world[3051*137:4051*137],untouched)

    def test_positive_fraction_raw_stock_is_preserved_before_separate_pickup(self):
        for key,world in self.before.items():
            folder,ob,seed,rows=self.samples[key];work,stats=run(world,seed,rows)
            self.assertEqual(raw(work,4054,129),raw(world,4054,129))
            self.assertEqual(Fraction.from_float(mbf.get(work,4054,129)),Fraction(*evidence.CASES[key[0]]['stock']))
            self.assertEqual(mbf.get(work,3051,81),0)
            self.assertEqual(mbf.get(work,2419,81),97337)

    def test_zero_rates_add_no_stock_then_clamp_to_one(self):
        for key,world in self.before.items():
            folder,ob,seed,rows=self.samples[key];work,stats=run(world,seed,rows)
            self.assertEqual([mbf.get(world,4054,o)for o in(45,49,53)],[0,0,0])
            self.assertEqual([mbf.get(work,4054,o)for o in(45,49,53)],[1,1,1])
            self.assertEqual([mbf.get(work,4054,o)for o in(57,61,65,69,113,125)],[0]*6)
            self.assertEqual(raw(work,4054,129),raw(world,4054,129))

    def test_ground_and_actual_source_timestamp_are_derived(self):
        for key,world in self.before.items():
            folder,ob,seed,rows=self.samples[key];work,stats=run(world,seed,rows)
            row=next(r for r in rows if r[0]==4054)
            self.assertEqual(mbf.get(work,4054,77),505000);self.assertEqual(mbf.get(work,4054,117),0)
            self.assertEqual(mbf.get(work,4054,41),309);self.assertEqual(raw(work,4054,89),row[2])
            self.assertEqual(mbf.get(work,4054,73),0)

    def test_core_opens_no_files_and_does_not_mutate_world_or_clock_inputs(self):
        key=('large-above','observed-a');world=self.before[key];folder,ob,seed,rows=self.samples[key];calendars,timers=source_clocks(folder/'host-time.json.gz');saved=copy.deepcopy((world,rows,calendars,timers))
        with patch.object(builtins,'open',side_effect=AssertionError('core file read')),patch.object(Path,'read_bytes',side_effect=AssertionError('core byte read')),patch.object(Path,'read_text',side_effect=AssertionError('core text read')):
            result=run(world,seed,rows);block,stats=ports.replay_ports(world,calendars,timers)
        self.assertEqual((world,rows,calendars,timers),saved);self.assertEqual(raw(result[0],4054,129),raw(world,4054,129));self.assertEqual(len(block),137000)

    def test_captured_rng_witness_bytes_cannot_change_core_inputs_or_economy(self):
        key=('odd-half','observed-a');world=self.before[key];folder,ob,seed,rows=self.samples[key];poisoned=copy.deepcopy(ob)
        for event in poisoned['events']:
            for side in('before','after'):event[side]['rng_raw']='ffffffff'
        self.assertEqual(source_planet_clocks(poisoned),(seed,rows));self.assertEqual(run(world,*source_planet_clocks(poisoned)),run(world,seed,rows))

    def test_unmeasured_stock_bank_rate_ground_or_link_rejected_atomically(self):
        key=('odd-half','observed-a');folder,ob,seed,rows=self.samples[key]
        for record,offset,value in((4054,129,0),(4054,129,37),(4054,129,.875),(4054,117,1),(4054,45,1),(4054,77,500001),(4054,73,-1),(3049,93,3)):
            world=bytearray(self.before[key]);mbf.put(world,record,offset,value);saved=bytes(world)
            with self.subTest(record=record,offset=offset,value=value),self.assertRaises(ValueError):planets.maintain(world,SimpleNamespace(rng=QB3(seed)),rows)
            self.assertEqual(bytes(world),saved)

    def test_mutable_reordered_noon_and_other_date_clocks_are_rejected(self):
        key=('half','observed-a');world=self.before[key];folder,ob,seed,rows=self.samples[key]
        for changed in(list(rows),rows[::-1],tuple((r,310,t)for r,d,t in rows),tuple((r,d,mbf.enc(720))for r,d,t in rows)):
            with self.assertRaises(ValueError):run(world,seed,changed)
        changed=bytearray(world);mbf.put(changed,1,81,309)
        with self.assertRaises(ValueError):run(bytes(changed),seed,tuple((r,310,t)for r,d,t in rows))

    def test_historical_gateway_planet_admission_remains_strict(self):
        key=('three-quarter','observed-a');world=bytearray(self.before[key]);folder,ob,seed,rows=self.samples[key];saved=bytes(world)
        with self.assertRaises(ValueError):historical_planets.maintain(world,SimpleNamespace(rng=QB3(seed)),rows)
        self.assertEqual(bytes(world),saved)

if __name__=='__main__':unittest.main()
