"""Independent source-order and conservation tests for gateway Mercenaries."""
import copy
import gzip
import json
import math
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import replay_maintenance_gateway_mercenary as merc
from replay_maintenance_collision_npcs import Stream
from replay_qb_graph import mbf,F32
from verify_maintenance_clock_matrix import event_pair


class FiniteRNG:
    def __init__(self,values):self.values=iter(values);self.draws=0;self.state=7;self.bounds=[]
    def rnd(self):
        self.draws+=1;self.state=(214013*self.state+1744579)&0xffffff
        return next(self.values)
    def integer(self,bound):
        self.bounds.append(bound);return math.floor(F32(self.rnd()*bound))+1


class FakeStream:
    def __init__(self,values,target=2500):self.rng=FiniteRNG(values);self.target=target;self.seeds=[]
    def reseed(self,family,caller):self.seeds.append((family,caller))
    def one(self,bound,*,caller):
        if (bound,caller)!=(3000,0x48cf):raise AssertionError('wrong target caller')
        return self.target


def gateway(stock=37,mines=0,defense=0):
    world=bytearray(4151*137)
    for off,value in((53,51),(57,3051),(61,4051),(93,4151)):mbf.put(world,1,off,value)
    for off,value in((81,defense),(85,-1 if defense else 0),(93,3),(129,mines)):mbf.put(world,3051,off,value)
    at=(4054-1)*137;world[at:at+41]=b'Gateway Cache'.ljust(41,b' ')
    for off,value in((85,13),(73,0),(77,505000),(129,stock)):mbf.put(world,4054,off,value)
    return world


def routed_world(stock=37,mines=0,defense=0,force=1000):
    world=gateway(stock,mines,defense)
    mbf.put(world,2419,81,force);mbf.put(world,2419,85,-2)
    mbf.put(world,2419,41,3000);mbf.put(world,3051,41,2500)
    return world


class GatewayMineSource(unittest.TestCase):
    def test_count_two_reseeds_each_initial_mine_even_after_death(self):
        world=gateway(mines=3);stream=FakeStream([.5,.5,.2,.4,.1,.1])
        event=merc.mine_hit(world,stream,3000,1)
        self.assertEqual(stream.seeds,[('h2',0x4aa4)]*3)
        self.assertEqual(stream.rng.bounds,[10000,5001,10000,2001,10000,1001])
        self.assertEqual((event['force'],event['losses'],event['mines'],event['mines_spent'],event['rng_draws']),(0,1,2,1,6))
        self.assertEqual(world[(3051-1)*137+129:(3051-1)*137+133],bytes.fromhex('00000082'))

    def test_surviving_damage_uses_shrinking_second_bound_not_two_fixed_draws(self):
        world=gateway(mines=1);stream=FakeStream([.5,.5]);event=merc.mine_hit(world,stream,3000,10000)
        self.assertEqual(event['rolls'],[2501]);self.assertEqual(event['force'],7499)
        self.assertEqual(world[(3051-1)*137+129:(3051-1)*137+133],bytes(4))

    def test_actual_three_observed_mine_rolls_derive_from_original_helper_state(self):
        # Primitive comparison only: the chain tests separately prove its input
        # state derives from startup. No witnessed old state enters the API.
        root=Path(__file__).resolve().parents[1]/'research/yt-maint/gateway-hazard-controls'
        for case,force,loss,remaining in(('mine-pickup',97337,712,0),('mine-guarded',97337,518,0),('fatal-before-pickup',1,1,2)):
            ob=json.loads(gzip.decompress((root/case/'child-1/observed-a/host-time.json.gz').read_bytes()))
            pairs=[];states=[]
            for raw in ob['events']:
                qualified=copy.deepcopy(raw)
                for side in('before','after'):qualified[side].pop('rng_raw')
                pair=event_pair(qualified,raw['ordinal'])
                if pair.get('role')=='helper2'and pair.get('nested_return_ip')==0x4aa4:
                    pairs.append(('h2',0x4aa4,pair['seconds']));states.append(int.from_bytes(bytes.fromhex(raw['before']['rng_raw']),'little'))
            stream=Stream(tuple(pairs),states[0]);world=gateway(mines=3 if case=='fatal-before-pickup'else 1)
            event=merc.mine_hit(world,stream,3000,force)
            self.assertEqual((event['losses'],event['mines']),(loss,remaining),case)
            self.assertEqual([s['old_state']for s in stream.seeds],states,case)

    def test_unmeasured_mines_or_location_reject_without_drawing(self):
        for mines in(0,4,1.5):
            stream=FakeStream([])
            with self.assertRaises(ValueError):merc.mine_hit(gateway(mines=mines),stream,3000,100)
            self.assertEqual(stream.rng.draws,0)
        with self.assertRaises(ValueError):merc.mine_hit(gateway(mines=1),FakeStream([]),2999,100)


class GatewayPickupSource(unittest.TestCase):
    def test_empty_stock_still_captures_without_grant(self):
        world=gateway(stock=0);event=merc.pickup(world,3000,97337)
        self.assertEqual((event['initial_force'],event['force'],event['pickup'],event['captured']),(97337,97337,0,True))

    def test_fighter_transfer_preserves_title_ground_and_pre_pickup_stamp(self):
        world=gateway();before=bytes(world);event=merc.pickup(world,3000,96625)
        self.assertEqual((event['initial_force'],event['force'],event['pickup']),(96625,96662,37))
        self.assertEqual((mbf.get(world,3051,81),mbf.get(world,3051,85)),(96662,-2))
        at=(4054-1)*137
        self.assertEqual(world[at:at+129],before[at:at+129]);self.assertEqual(world[at+133:at+137],before[at+133:at+137])
        self.assertEqual(world[at+129:at+133],bytes.fromhex('00008000'))

    def test_pickup_rejects_guard_mine_wrong_link_or_title(self):
        for record,off,value in((3051,81,37),(3051,85,-1),(3051,93,2),(3051,129,1),(4054,73,2),(4054,85,12),(4054,129,41)):
            world=gateway();mbf.put(world,record,off,value)
            with self.subTest(record=record,off=off),self.assertRaises(ValueError):merc.pickup(world,3000,1000)

    def test_pickup_opens_only_original_executable(self):
        read=Path.read_bytes
        def guarded(path):
            if path.name!='YTMAINT.EXE'or 'archive/dos-original'not in str(path):raise AssertionError('captured file opened')
            return read(path)
        with patch.object(Path,'read_bytes',guarded):merc.pickup(gateway(),3000,1000)


class GatewayRouteComposition(unittest.TestCase):
    def test_mine_precedes_pickup_and_stops_before_endpoint(self):
        world=routed_world(mines=1,force=10000);stream=FakeStream([.1,.9,.5,.5])
        row=merc.maintain(world,stream)
        self.assertEqual([e['kind']for e in row['events']],['mercenary-mine','mercenary-pickup'])
        self.assertEqual((row['force'],row['losses'],row['pickup']),(7536,2501,37))
        self.assertEqual(row['final_sectors'],[3000]);self.assertEqual(row['activations'][0]['entered'],[3000])
        self.assertEqual(mbf.get(world,2551,81),0)

    def test_offense_victory_does_not_fall_through_to_planet_pickup(self):
        world=routed_world(defense=1);stream=FakeStream([.1,.1,.9,.9,.1])
        row=merc.maintain(world,stream)
        self.assertEqual([e['kind']for e in row['events']],['mercenary-attack'])
        self.assertEqual(row['force'],1000);self.assertEqual(row['final_sectors'],[2500])
        self.assertEqual(mbf.get(world,4054,129),37)

    def test_fatal_mine_prevents_battle_pickup_and_destination_save(self):
        world=routed_world(mines=3,force=1);stream=FakeStream([.1,.9,.5,.5,.2,.4,.1,.1])
        row=merc.maintain(world,stream)
        self.assertEqual([e['kind']for e in row['events']],['mercenary-mine'])
        self.assertEqual((row['force'],row['losses'],row['pickup']),(0,1,0));self.assertEqual(row['final_sectors'],[])
        self.assertEqual(mbf.get(world,4054,129),37);self.assertEqual(mbf.get(world,3051,129),2)
        self.assertEqual(stream.rng.draws,8)

    def test_planet_hold_consumes_gate_without_another_pickup(self):
        world=gateway(stock=3);mbf.put(world,3051,81,97374);mbf.put(world,3051,85,-2)
        stream=FakeStream([.1,.1]);row=merc.maintain(world,stream)
        self.assertEqual(row['force'],97374);self.assertEqual(row['events'],[])
        self.assertTrue(row['activations'][0]['held']);self.assertEqual(mbf.get(world,4054,129),3)

    def test_departure_zero_is_not_pickup_zero(self):
        world=routed_world();merc.maintain(world,FakeStream([.1,.9]))
        at=(2419-1)*137
        self.assertEqual(world[at+81:at+89],bytes.fromhex('0000280000002800'))
        self.assertNotEqual(world[at+81:at+85],world[(4054-1)*137+129:(4054-1)*137+133])


if __name__=='__main__':unittest.main()
