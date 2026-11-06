"""Independent evolved-economy field, source-stream and rejection regressions."""
import builtins
import copy
import datetime
import gzip
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import replay_maintenance_evolved_planets as model
from replay_qb_graph import mbf,QB3,F32
from verify_maintenance_clock_matrix import event_pair,CALENDAR_CALLERS

ROOT=Path(__file__).resolve().parents[1]
CORPUS=ROOT/'research/yt-maint/convergence-chain-controls'


def inputs(before,observation):
    active=tuple(r for r in range(4052,4152)if mbf.get(before,r,85)>0)
    dates=[];minutes=[];startup=None;witnesses=[]
    for event in observation['events']:
        row=copy.deepcopy(event)
        witness=int.from_bytes(bytes.fromhex(row['before']['rng_raw']),'little')
        for side in('before','after'):row[side].pop('rng_raw')
        value=event_pair(row,row['ordinal'])
        if value.get('kind')=='timer'and value.get('role')=='startup':startup=value['seconds']
        if value.get('kind')=='date'and value.get('role')=='calendar'and CALENDAR_CALLERS[value['nested_return_ip']]=='planet':
            dates.append((value['date']-datetime.date(2026,1,1)).days+1)
        if value.get('kind')=='timer'and value.get('role')=='planet':
            minutes.append(value['minutes']);witnesses.append(witness)
    raw=bytearray(startup);raw[2]^=128
    seed=5|((raw[0]^raw[2])<<8)|((raw[1]^raw[3])<<16)
    return tuple(zip(active,dates,minutes)),seed,witnesses


class EvolvedPlanetEconomy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before={};cls.after={};cls.observations={};cls.clocks={};cls.seed={};cls.modeled={}
        for day in('day-1','day-2','day-3'):
            folder=CORPUS/day/'observed-a'
            cls.before[day]=gzip.decompress((folder/'before-YTDATA.DAT.gz').read_bytes())
            cls.after[day]=gzip.decompress((folder/'after-YTDATA.DAT.gz').read_bytes())
            cls.observations[day]=json.loads(gzip.decompress((folder/'host-time.json.gz').read_bytes()))
            cls.clocks[day],cls.seed[day],_=inputs(cls.before[day],cls.observations[day])
            world=bytearray(cls.before[day]);stream=SimpleNamespace(rng=QB3(cls.seed[day]));stats=model.maintain(world,stream,cls.clocks[day]);cls.modeled[day]=(bytes(world),stats)

    def test_complete_records_match_all_nine_observations_before_later_npc_ground(self):
        for day in self.before:
            for observed in('observed-a','observed-b','observed-c'):
                folder=CORPUS/day/observed
                before=gzip.decompress((folder/'before-YTDATA.DAT.gz').read_bytes())
                ob=json.loads(gzip.decompress((folder/'host-time.json.gz').read_bytes()))
                rows,seed,_=inputs(before,ob);world=bytearray(before)
                model.maintain(world,SimpleNamespace(rng=QB3(seed)),rows)
                expected=gzip.decompress((folder/'after-YTDATA.DAT.gz').read_bytes())
                for rec,_,_ in rows:
                    at=(rec-1)*137
                    for offset in range(137):
                        if rec==4151 and offset in range(77,81):continue
                        with self.subTest(day=day,mode=observed,record=rec,offset=offset):self.assertEqual(world[at+offset],expected[at+offset])

    def test_xannoron_ground_is_economy_only_before_later_npc_increment(self):
        self.assertEqual(mbf.get(self.modeled['day-2'][0],4151,77),520)
        self.assertEqual(mbf.get(self.modeled['day-3'][0],4151,77),807)
        self.assertEqual(mbf.get(self.after['day-2'],4151,77)-520,4)
        self.assertEqual(mbf.get(self.after['day-3'],4151,77)-807,3)

    def test_three_derived_event_draws_per_active_record_agree_with_witnesses(self):
        for day in self.before:
            rows,seed,witnesses=inputs(self.before[day],self.observations[day]);rng=QB3(seed)
            for witness in witnesses:
                self.assertEqual(rng.state,witness)
                for _ in range(3):rng.rnd()
            stats=self.modeled[day][1]
            self.assertEqual(stats['rng_draws'],3*len(rows));self.assertEqual(stats['final_rng_state'],rng.state)
            self.assertTrue(all(not r['event_selected']for r in stats['rows']))

    def test_captured_rng_is_not_an_input_to_core_economy(self):
        day='day-2';ob=copy.deepcopy(self.observations[day])
        for event in ob['events']:
            for side in('before','after'):event[side]['rng_raw']='00000000'
        rows,seed,witnesses=inputs(self.before[day],ob)
        self.assertEqual((rows,seed),(self.clocks[day],self.seed[day]));self.assertEqual(set(witnesses),{0})
        world=bytearray(self.before[day]);model.maintain(world,SimpleNamespace(rng=QB3(seed)),rows)
        self.assertEqual(bytes(world),self.modeled[day][0])

    def test_core_opens_no_original_target_or_capture_file(self):
        world=bytearray(self.before['day-2']);stream=SimpleNamespace(rng=QB3(self.seed['day-2']))
        with patch.object(Path,'read_bytes',side_effect=AssertionError('no reads')),patch.object(Path,'read_text',side_effect=AssertionError('no reads')),patch.object(builtins,'open',side_effect=AssertionError('no reads')):
            model.maintain(world,stream,self.clocks['day-2'])
        self.assertEqual(bytes(world),self.modeled['day-2'][0])

    def test_fractional_elapsed_and_source_timer_are_preserved(self):
        world,stats=self.modeled['day-1'];self.assertGreater(stats['rows'][0]['elapsed'],1)
        self.assertEqual(mbf.get(world,4053,57),1000.0006103515625)
        self.assertEqual(mbf.get(world,4053,129),3000.001708984375)
        self.assertEqual(world[(4053-1)*137+89:(4053-1)*137+93],self.clocks['day-1'][0][2])

    def test_ten_day_catchup_is_applied_to_old_reserved_home_timestamps(self):
        rows=self.modeled['day-2'][1]['rows'];by_record={r['record']:r for r in rows}
        self.assertEqual(by_record[4052]['elapsed'],10);self.assertEqual(by_record[4150]['elapsed'],10)
        self.assertEqual(by_record[4053]['elapsed'],1)

    def test_single_floor_avoids_false_one_credit_and_ground_loss(self):
        w=self.modeled['day-2'][0]
        self.assertEqual(mbf.get(w,4052,117),275000)
        self.assertEqual(mbf.get(w,4053,77),510050)
        self.assertEqual(mbf.get(w,4150,77),190000)
        self.assertEqual(mbf.get(self.modeled['day-3'][0],4052,77),280)

    def test_old_bank_bonus_precedes_interest(self):
        w=self.modeled['day-2'][0]
        self.assertEqual(mbf.get(w,4052,57),50250)
        self.assertEqual(mbf.get(w,4052,117),275000)
        self.assertEqual(mbf.get(w,4052,77),250)

    def test_fighter_base_is_truncated_before_elapsed(self):
        w=self.modeled['day-3'][0]
        self.assertEqual(mbf.get(w,4053,129),9090.001953125)
        self.assertEqual(mbf.get(w,4150,129),3890041)
        self.assertEqual(mbf.get(w,4052,129),172100)

    def test_surplus_replaces_rate_before_natural_growth(self):
        w=self.modeled['day-2'][0]
        self.assertEqual(mbf.get(w,4150,57),1025000)
        self.assertEqual(mbf.get(w,4150,45),112750)
        self.assertEqual(mbf.get(self.modeled['day-3'][0],4150,45),115190.5)

    def test_subunit_weapon_bank_production_is_not_truncated(self):
        w=self.modeled['day-3'][0]
        self.assertEqual(mbf.get(w,4052,113),0.11099999397993088)
        self.assertEqual(mbf.get(w,4052,125),11.100000381469727)

    def test_nonplanet_records_are_not_mutated(self):
        for day,(world,_)in self.modeled.items():
            active={r for r,_,_ in self.clocks[day]}
            for rec in range(1,4152):
                if rec in active:continue
                at=(rec-1)*137
                self.assertEqual(world[at:at+137],self.before[day][at:at+137])

    def test_reserved_inherited_fields_are_preserved(self):
        for day in('day-2','day-3'):
            world=self.modeled[day][0]
            for rec in(4052,4150,4151):
                for offset in(81,93,97,101,105,109,121,133):
                    at=(rec-1)*137+offset;self.assertEqual(world[at:at+4],self.before[day][at:at+4])

    def rejected(self,world=None,rows=None):
        world=bytearray(self.before['day-2'])if world is None else world
        rows=self.clocks['day-2']if rows is None else rows
        old=bytes(world);stream=SimpleNamespace(rng=QB3(self.seed['day-2']))
        with self.assertRaises(ValueError):model.maintain(world,stream,rows)
        self.assertEqual(bytes(world),old);self.assertEqual(stream.rng.draws,0)

    def test_wrong_geometry_and_extent_reject_before_mutation(self):
        self.rejected(bytearray(self.before['day-2'][:-1]))
        world=bytearray(self.before['day-2']);mbf.put(world,1,61,4050);self.rejected(world)

    def test_clock_inventory_order_types_and_width_reject(self):
        rows=self.clocks['day-2']
        for value in(list(rows),rows[:-1],rows+(rows[-1],),tuple(reversed(rows)),((4052,307,b'bad'),)+rows[1:],((4052,True,rows[0][2]),)+rows[1:],((4052,307,bytearray(rows[0][2])),)+rows[1:]):
            with self.subTest(value=value):self.rejected(rows=value)

    def test_wrong_or_backward_date_and_nonmidnight_timer_reject(self):
        rows=self.clocks['day-2']
        for day,timer in((306,rows[0][2]),(308,rows[0][2]),(307,mbf.enc(-1)),(307,mbf.enc(1))):
            self.rejected(rows=((4052,day,timer),)+rows[1:])
        world=bytearray(self.before['day-2']);mbf.put(world,1,81,400);self.rejected(world)

    def test_wrong_active_shape_name_or_owner_reject(self):
        for rec,off,value in((4052,85,0),(4053,73,0),(4150,73,-1),(4151,85,7)):
            world=bytearray(self.before['day-2']);mbf.put(world,rec,off,value);self.rejected(world)
        world=bytearray(self.before['day-2']);world[(4053-1)*137]=ord('X');self.rejected(world)

    def test_missing_or_duplicate_sector_link_reject(self):
        before=self.before['day-2'];slot=2
        links=[s for s in range(1,3001)if mbf.get(before,51+s,93)==slot]
        world=bytearray(before);mbf.put(world,51+links[0],93,0);self.rejected(world)
        world=bytearray(before);mbf.put(world,51+99,93,slot);self.rejected(world)

    def test_unbounded_or_negative_bank_rate_and_stock_reject(self):
        for off,val in((117,-1),(117,30000010),(45,0),(45,200001),(57,-1),(129,10000001)):
            world=bytearray(self.before['day-2']);mbf.put(world,4053,off,val);self.rejected(world)

    def test_unknown_inherited_fields_reject(self):
        for rec in(4053,4150):
            world=bytearray(self.before['day-2']);mbf.put(world,rec,133,1);self.rejected(world)

    def test_selected_event_is_rejected_without_world_commit(self):
        class Fake:
            def __init__(self):self.state=1;self.draws=0;self.values=iter([0,0,0,0,0,0,.99,0,0])
            def rnd(self):self.draws+=1;self.state+=1;return next(self.values)
        world=bytearray(self.before['day-2']);old=bytes(world)
        with self.assertRaisesRegex(ValueError,'plague/civil-war'):model.maintain(world,SimpleNamespace(rng=Fake()),self.clocks['day-2'])
        self.assertEqual(bytes(world),old)


if __name__=='__main__':unittest.main()
