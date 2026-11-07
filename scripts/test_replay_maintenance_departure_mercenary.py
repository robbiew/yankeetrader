"""Source-derived occupied departures, friendly merges and stock-conversion tests."""
import copy
import gzip
import json
import math
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import replay_maintenance_departure_mercenary as merc
from replay_maintenance_collision_npcs import Stream
from replay_qb_graph import mbf,F32
from verify_maintenance_clock_matrix import event_pair

ROOT=Path(__file__).resolve().parents[1]
CORPUS=ROOT/'research/yt-maint/departure-merge-controls'


class FiniteRNG:
    def __init__(self,values):self.values=iter(values);self.draws=0;self.state=7;self.bounds=[]
    def rnd(self):
        self.draws+=1;self.state=(214013*self.state+1744579)&0xffffff
        return next(self.values)
    def integer(self,bound):
        self.bounds.append(bound);return math.floor(F32(self.rnd()*bound))+1


class FakeStream:
    def __init__(self,values,targets=()):self.rng=FiniteRNG(values);self.targets=iter(targets);self.seeds=[]
    def reseed(self,family,caller):self.seeds.append((family,caller))
    def one(self,bound,*,caller):
        if (bound,caller)!=(3000,0x48cf):raise AssertionError('wrong source target caller')
        return next(self.targets)


def world():
    result=bytearray(4151*137)
    for off,value in((53,51),(57,3051),(61,4051),(93,4151)):mbf.put(result,1,off,value)
    return result


def planet(data,slot=3,sector=3000,stock=37):
    rec=4051+slot;at=(rec-1)*137;title=b'The Wanderer'if slot==1 else b'Departure Cache'
    data[at:at+41]=title.ljust(41,b' ')
    for off,value in((85,len(title)),(73,0),(77,505000),(129,stock)):mbf.put(data,rec,off,value)
    mbf.put(data,51+sector,93,slot)
    return data


def force(data,sector,count,owner=-2):
    mbf.put(data,51+sector,81,count);mbf.put(data,51+sector,85,owner)


def qualified_helpers(case,stage,caller):
    raw=json.loads(gzip.decompress((CORPUS/case/stage/'observed-a/host-time.json.gz').read_bytes()));rows=[]
    for event in raw['events']:
        qualified=copy.deepcopy(event)
        for side in('before','after'):qualified[side].pop('rng_raw')
        pair=event_pair(qualified,qualified['ordinal'])
        if pair.get('kind')=='timer'and pair.get('nested_return_ip')==caller:
            rows.append((pair,int.from_bytes(bytes.fromhex(event['before']['rng_raw']),'little')))
    return rows


class OccupiedDeparture(unittest.TestCase):
    def fixture(self):
        data=planet(world());force(data,3000,97337)
        mbf.put(data,3051,41,2998);mbf.put(data,3049,41,2999)
        return data

    def test_occupied_origin_can_depart_without_taking_its_stock(self):
        data=self.fixture();row=merc.maintain(data,FakeStream([.1,.9,.9],[2998,2999]))
        self.assertEqual(row['final_sectors'],[2999]);self.assertEqual(row['force'],97337)
        self.assertEqual(row['events'],[]);self.assertEqual(mbf.get(data,4054,129),37)
        self.assertFalse(row['activations'][0]['held'])
        at=(3051-1)*137
        self.assertEqual(data[at+81:at+89],bytes.fromhex('0000280000002800'))

    def test_hold_and_exact_single_threshold_do_not_duplicate_pickup(self):
        for gate,held in((F32(.66)-2**-24,True),(F32(.66),False)):
            data=self.fixture();row=merc.maintain(data,FakeStream([.1,gate,.9],[2998,2999]))
            self.assertEqual(row['activations'][0]['held'],held);self.assertEqual(row['force'],97337)
            self.assertEqual(mbf.get(data,4054,129),37);self.assertEqual(row['pickup'],0)
            self.assertEqual(row['target_draws'],0 if held else 2)

    def test_fractional_and_unknown_owner_before_force_rejects_without_world_writes(self):
        for off,value in((81,97337.5),(85,2)):
            data=self.fixture();mbf.put(data,3051,off,value);before=bytes(data)
            with self.assertRaises(ValueError):merc.maintain(data,FakeStream([]))
            self.assertEqual(bytes(data),before)

    def test_tail_rejection_preserves_origin_already_cleared_in_internal_work(self):
        data=world();force(data,3000,399999);planet(data,slot=1,sector=2998,stock=37)
        mbf.put(data,3051,41,2998);before=bytes(data)
        with self.assertRaisesRegex(ValueError,'post-pickup'):merc.maintain(data,FakeStream([.1,.9],[2998]))
        self.assertEqual(bytes(data),before)


class FriendlyMerge(unittest.TestCase):
    def test_merge_adds_actual_friendly_force_and_clears_original_literal(self):
        data=world();force(data,2368,37);before=bytes(data);event=merc.merge(data,2368,97337)
        self.assertEqual((event['kind'],event['initial_force'],event['initial_defenders'],event['force'],event['merged'],event['losses']),('mercenary-merge',97337,37,97374,37,0))
        at=(2419-1)*137
        self.assertEqual(data[at+81:at+89],bytes.fromhex('0000800000008000'))
        self.assertEqual(data[:at+81],before[:at+81]);self.assertEqual(data[at+89:],before[at+89:])

    def test_merge_continues_route_then_reactivates_combined_force(self):
        data=planet(world());force(data,3000,97337);force(data,2368,37)
        for rec,to in((3051,2368),(2419,2500),(2551,2998)):mbf.put(data,rec,41,to)
        stream=FakeStream([.1,.1,.9,.9],[2500,2998]);row=merc.maintain(data,stream)
        self.assertEqual(row['final_sectors'],[2998]);self.assertEqual(row['force'],97374)
        self.assertEqual([(a['origin'],a['force'])for a in row['activations']],[(3000,97337),(2500,97374)])
        self.assertEqual([e['kind']for e in row['events']],['mercenary-merge'])
        self.assertEqual((row['initial_force'],row['merged'],row['pickup'],row['losses']),(97374,37,0,0))
        self.assertEqual(stream.rng.draws,4);self.assertEqual(mbf.get(data,4054,129),37)

    def test_friendly_force_is_not_a_second_global_gift(self):
        for count in(1,37,199,1000):
            data=world();force(data,2368,count);event=merc.merge(data,2368,10000)
            self.assertEqual(event['force'],10000+count);self.assertEqual(mbf.get(data,2419,81),0)
            self.assertEqual(event['losses'],0)

    def test_unmeasured_merge_contexts_reject_before_clear(self):
        for off,value in((85,0),(85,-1),(81,1.5),(93,3),(129,1)):
            data=world();force(data,2368,37);mbf.put(data,2419,off,value);before=bytes(data)
            with self.subTest(off=off,value=value),self.assertRaises(ValueError):merc.merge(data,2368,1000)
            self.assertEqual(bytes(data),before)

    def test_merged_capacity_rejects_before_clear(self):
        data=world();force(data,2368,37);before=bytes(data)
        with self.assertRaisesRegex(ValueError,'bounded merged'):merc.merge(data,2368,399999)
        self.assertEqual(bytes(data),before)


class BoundedHomePickup(unittest.TestCase):
    def test_actual_wanderer_fraction_is_fully_cleared_but_not_granted(self):
        data=planet(world(),slot=1,sector=93,stock=189528.296875);before=bytes(data)
        event=merc.pickup(data,93,97337)
        self.assertEqual((event['raw_stock'],event['pickup'],event['fractional_discard'],event['initial_force'],event['force']),(189528.296875,189528,.296875,97337,286865))
        self.assertEqual(event['conversion'],'bounded-positive-subhalf-whole')
        self.assertEqual((mbf.get(data,144,81),mbf.get(data,144,85)),(286865,-2))
        at=(4052-1)*137
        self.assertEqual(data[at:at+129],before[at:at+129]);self.assertEqual(data[at+129:at+133],bytes.fromhex('00008000'))
        self.assertEqual(data[at+133:at+137],before[at+133:at+137])

    def test_half_or_larger_fraction_is_not_inferred_from_one_native_witness(self):
        for stock in(.5,.75,189528.5,189528.75):
            data=planet(world(),slot=1,sector=93,stock=stock);before=bytes(data)
            with self.subTest(stock=stock),self.assertRaisesRegex(ValueError,'stock conversion'):merc.pickup(data,93,1000)
            self.assertEqual(bytes(data),before)

    def test_departure_cache_stock_remains_explicit_whole_bound(self):
        for stock in(0,37,40):
            data=planet(world(),stock=stock);event=merc.pickup(data,3000,1000)
            self.assertEqual((event['pickup'],event['force']),(stock,1000+stock))
        for stock in(37.25,41):
            data=planet(world(),stock=stock);before=bytes(data)
            with self.assertRaises(ValueError):merc.pickup(data,3000,1000)
            self.assertEqual(bytes(data),before)

    def test_post_pickup_capacity_validates_before_any_record_write(self):
        for stock in(37,189528.296875):
            data=planet(world(),slot=1,sector=93,stock=stock);before=bytes(data)
            with self.assertRaisesRegex(ValueError,'post-pickup'):merc.pickup(data,93,399999)
            self.assertEqual(bytes(data),before)

    def test_original_identity_validates_before_any_record_write(self):
        data=planet(world(),slot=1,sector=93,stock=37);before=bytes(data)
        with patch.object(Path,'read_bytes',return_value=b'changed'),self.assertRaisesRegex(ValueError,'identity'):merc.pickup(data,93,1000)
        self.assertEqual(bytes(data),before)

    def test_direct_pickup_opens_only_original_executable(self):
        read=Path.read_bytes
        def guarded(path):
            if path.name!='YTMAINT.EXE'or 'archive/dos-original'not in str(path):raise AssertionError('captured output opened')
            return read(path)
        with patch.object(Path,'read_bytes',guarded):merc.pickup(planet(world(),slot=1,sector=93,stock=189528.296875),93,97337)


class ActualMixedMineDefense(unittest.TestCase):
    def test_measured_second_two_tail_mine_then_battle_derive_5973_and_9(self):
        # Primitive comparison witness only; full chain must separately derive
        # this old state from original startup, not use it as an input seed.
        rows=qualified_helpers('occupied-second-two','child-2',0x4aa4)
        self.assertEqual(len(rows),1);pair,old=rows[0];stream=Stream((('h2',0x4aa4,pair['seconds']),),old)
        data=world();force(data,2356,16,-1);mbf.put(data,2407,129,1)
        event=merc.mine_hit(data,stream,2356,94500);self.assertEqual((event['losses'],event['force'],event['mines']),(5973,88527,0))
        battle=merc.attack(data,stream,2356,event['force'])
        self.assertEqual((battle['initial_defenders'],battle['losses'],battle['force'],battle['defenders']),(16,9,88518,0))
        self.assertEqual(data[(2407-1)*137+129:(2407-1)*137+133],bytes(4))

    def test_measured_last_case_second_day_one_fighter_battle_costs_one(self):
        rows=qualified_helpers('occupied-friendly-second-four','child-2',0x48cf)
        self.assertEqual(len(rows),2);pair,old=rows[0];stream=Stream((('h1',0x48cf,pair['seconds']),),old)
        self.assertEqual(stream.one(3000,caller=0x48cf),11)
        data=world();force(data,100,1,-1);event=merc.attack(data,stream,100,97374)
        self.assertEqual((event['defender_losses'],event['losses'],event['force']),(1,1,97373))

    def test_mine_helper_failure_leaves_original_record_unwritten(self):
        data=world();mbf.put(data,2407,129,2);before=bytes(data)
        with self.assertRaises(StopIteration):merc.mine_hit(data,FakeStream([.5,.5]),2356,94500)
        self.assertEqual(bytes(data),before)

    def test_invalid_mine_context_rejects_before_draws_and_writes(self):
        for off,value in((129,0),(129,4),(129,1.5),(93,3),(85,2)):
            data=world();mbf.put(data,2407,129,1);mbf.put(data,2407,off,value);before=bytes(data);stream=FakeStream([])
            with self.subTest(off=off,value=value),self.assertRaises(ValueError):merc.mine_hit(data,stream,2356,94500)
            self.assertEqual(stream.rng.draws,0);self.assertEqual(bytes(data),before)


if __name__=='__main__':unittest.main()
