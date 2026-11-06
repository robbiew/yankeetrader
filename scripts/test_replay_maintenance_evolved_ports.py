"""Exact retained port blocks and independent narrow-profile properties."""
import builtins
import copy
import datetime
import gzip
import json
from pathlib import Path
from unittest.mock import patch
import unittest

from replay_qb_graph import mbf,F32
from verify_maintenance_clock_matrix import event_pair,CALENDAR_CALLERS
import replay_maintenance_evolved_ports as replay

ROOT=Path(__file__).resolve().parents[1]
CORPUS=ROOT/'research/yt-maint/convergence-chain-controls'


def source_clocks(path):
    observation=json.loads(gzip.decompress(path.read_bytes()));dates=[];timers=[]
    for event in observation['events']:
        for side in('before','after'):event[side].pop('rng_raw')
        pair=event_pair(event,event['ordinal'])
        if pair.get('kind')=='date'and pair.get('role')=='calendar'and CALENDAR_CALLERS[pair['nested_return_ip']]=='port':
            dates.append((pair['date']-datetime.date(2026,1,1)).days+1)
        if pair.get('kind')=='timer'and pair.get('role')=='port':timers.append(pair['minutes'])
    return tuple(dates),tuple(timers)


def put(world,record,offset,value):
    output=bytearray(world);mbf.put(output,record,offset,value);return bytes(output)


class EvolvedPortReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before={};cls.expected={};cls.clocks={}
        for stage in('day-1','day-2','day-3'):
            folder=CORPUS/stage/'observed-a'
            cls.before[stage]=gzip.decompress((folder/'before-YTDATA.DAT.gz').read_bytes())
            cls.expected[stage]=gzip.decompress((folder/'after-YTDATA.DAT.gz').read_bytes())[3051*137:4051*137]
            for mode in('observed-a','observed-b','observed-c'):
                cls.clocks[(stage,mode)]=source_clocks(CORPUS/stage/mode/'host-time.json.gz')

    def test_all_nine_observations_match_every_raw_port_byte(self):
        for (stage,mode),clocks in self.clocks.items():
            with self.subTest(stage=stage,mode=mode):
                actual,stats=replay.replay_ports(self.before[stage],*clocks)
                self.assertEqual(actual,self.expected[stage]);self.assertEqual(stats['ports'],1000);self.assertEqual(stats['rng_draws'],0)

    def test_three_day_port_chain_feeds_only_prior_modeled_port_bytes(self):
        world=self.before['day-1']
        for stage in('day-1','day-2','day-3'):
            block,stats=replay.replay_ports(world,*self.clocks[(stage,'observed-a')])
            self.assertEqual(block,self.expected[stage])
            world=world[:3051*137]+block+world[4051*137:]

    def test_core_never_reads_original_captures_or_targets(self):
        for stage in self.before:
            with self.subTest(stage=stage),patch.object(Path,'read_bytes',side_effect=AssertionError('no source/target reads')),patch.object(Path,'read_text',side_effect=AssertionError('no text reads')),patch.object(builtins,'open',side_effect=AssertionError('no open')):
                block,_=replay.replay_ports(self.before[stage],*self.clocks[(stage,'observed-a')])
            self.assertEqual(block,self.expected[stage])

    def test_input_world_and_source_clock_tuples_are_unchanged(self):
        before=self.before['day-2'];clocks=self.clocks[('day-2','observed-a')];saved=copy.deepcopy((before,clocks))
        replay.replay_ports(before,*clocks);self.assertEqual((before,clocks),saved)

    def test_fractional_elapsed_and_rate_promotions_are_derived(self):
        first,s1=replay.replay_ports(self.before['day-1'],*self.clocks[('day-1','observed-a')])
        second,s2=replay.replay_ports(self.before['day-2'],*self.clocks[('day-2','observed-a')])
        self.assertEqual((s1['rate_promotions'],s1['elapsed_min'],s1['elapsed_max']),(0,10,10))
        self.assertEqual(s2['rate_promotions'],3000);self.assertEqual(s2['elapsed_min'],1);self.assertGreater(s2['elapsed_max'],1)
        local=3657-3051
        self.assertEqual(mbf.get(second,local,49),32296.001953125)
        self.assertEqual(mbf.get(second,local,61),3229.60009765625)

    def test_actual_source_TIMER_zero_residue_is_copied_without_canonicalization(self):
        days,timers=self.clocks[('day-1','observed-a')];block,_=replay.replay_ports(self.before['day-1'],days,timers)
        self.assertEqual(timers[0][3],0);self.assertNotEqual(timers[0],bytes(4));self.assertEqual(block[101:105],timers[0])

    def test_source_fields_outside_writer_inventory_are_preserved(self):
        writes={41,42,43,44,45,46,47,48,*range(49,85),101,102,103,104}
        for stage in self.before:
            block,_=replay.replay_ports(self.before[stage],*self.clocks[(stage,'observed-a')]);before=self.before[stage][3051*137:4051*137]
            self.assertEqual(bytes(v for i,v in enumerate(block)if i%137 not in writes),bytes(v for i,v in enumerate(before)if i%137 not in writes))

    def test_strict_maximum_tie_retains_first_commodity_and_coefficient_magnitudes(self):
        world=self.before['day-1']
        for offset in(61,65,69):world=put(world,3052,offset,1000)
        for offset,value in((73,11),(77,-22),(81,33)):world=put(world,3052,offset,value)
        block,stats=replay.replay_ports(world,*self.clocks[('day-1','observed-a')])
        self.assertEqual(mbf.get(block,1,41),3)
        self.assertEqual([mbf.get(block,1,o)for o in(73,77,81)],[11,-22,-33])

    def test_unknown_world_container_and_extent_fail_closed(self):
        clocks=self.clocks[('day-2','observed-a')]
        for world in(None,bytearray(self.before['day-2']),self.before['day-2'][:-1]):
            with self.subTest(world=type(world)),self.assertRaises(ValueError):replay.replay_ports(world,*clocks)

    def test_unknown_geometry_fails_closed(self):
        for off in(53,57,61,93):
            with self.subTest(offset=off),self.assertRaises(ValueError):replay.replay_ports(put(self.before['day-2'],1,off,0),*self.clocks[('day-2','observed-a')])

    def test_calendar_shape_types_inventory_and_rollover_are_explicit(self):
        days,timers=self.clocks[('day-2','observed-a')]
        for invalid in(None,list(days),days[:-1],(True,)*1000,(305,)*1000,days[:500]+(308,)*500):
            with self.subTest(invalid=type(invalid)),self.assertRaises(ValueError):replay.replay_ports(self.before['day-2'],invalid,timers)

    def test_raw_timer_shapes_types_and_width_fail_closed(self):
        days,timers=self.clocks[('day-2','observed-a')]
        for invalid in(None,list(timers),timers[:-1],(bytes(3),)*1000,(bytearray(4),)*1000):
            with self.subTest(invalid=type(invalid)),self.assertRaises(ValueError):replay.replay_ports(self.before['day-2'],days,invalid)

    def test_out_of_scope_timer_values_and_nonmonotone_schedule_fail(self):
        days,timers=self.clocks[('day-2','observed-a')]
        for invalid in((mbf.enc(-1),)*1000,(mbf.enc(1),)*1000,(mbf.enc(.5),)+timers[1:]):
            with self.subTest(raw=invalid[0]),self.assertRaises(ValueError):replay.replay_ports(self.before['day-2'],days,invalid)

    def test_nonconsecutive_or_fractional_before_dates_reject(self):
        for last in(305,307,306.5):
            with self.subTest(last=last),self.assertRaises(ValueError):replay.replay_ports(put(self.before['day-2'],3052,45,last),*self.clocks[('day-2','observed-a')])

    def test_treasury_and_asking_price_branches_fail_closed(self):
        for offset in(89,97):
            with self.subTest(offset=offset),self.assertRaises(ValueError):replay.replay_ports(put(self.before['day-2'],3052,offset,1),*self.clocks[('day-2','observed-a')])

    def test_unknown_initial_stock_rate_or_time_rejects(self):
        for offset,value in((49,1),(61,1000.5),(61,32767),(101,.5)):
            with self.subTest(offset=offset,value=value),self.assertRaises(ValueError):replay.replay_ports(put(self.before['day-1'],3052,offset,value),*self.clocks[('day-1','observed-a')])

    def test_out_of_scope_rate_and_coefficient_ranges_reject(self):
        for offset,value in((61,999),(61,40001),(73,0),(73,101),(73,.5)):
            with self.subTest(offset=offset,value=value),self.assertRaises(ValueError):replay.replay_ports(put(self.before['day-2'],3052,offset,value),*self.clocks[('day-2','observed-a')])

    def test_evolved_empty_or_unrelated_stock_is_not_silently_admitted(self):
        for stock in(0,-1,1,1000000):
            with self.subTest(stock=stock),self.assertRaises(ValueError):replay.replay_ports(put(self.before['day-2'],3052,49,stock),*self.clocks[('day-2','observed-a')])


if __name__=='__main__':unittest.main()
