"""Independent exact gateway economy comparison and bounded-input regressions."""
import builtins
import copy
import datetime
import gzip
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from replay_qb_graph import mbf,QB3
from verify_maintenance_clock_matrix import event_pair,CALENDAR_CALLERS
import replay_maintenance_gateway_planets as model

ROOT=Path(__file__).resolve().parents[1]/'research/yt-maint/gateway-hazard-controls'
MODES=('observed-a','observed-b','observed-c')


def source_planet_clocks(observation):
    """Test-side source-qualified clocks, without any captured old RNG bytes."""
    raw=copy.deepcopy(observation);dates=[];timers=[];seed=None
    for e in raw['events']:
        for side in('before','after'):e[side].pop('rng_raw')
        pair=event_pair(e,e['ordinal'])
        if pair.get('kind')=='timer'and pair.get('role')=='startup':
            initial=bytearray(pair['seconds']);initial[2]^=128
            seed=5|((initial[0]^initial[2])<<8)|((initial[1]^initial[3])<<16)
        if pair.get('kind')=='date'and pair.get('role')=='calendar'and CALENDAR_CALLERS[pair['nested_return_ip']]=='planet':dates.append(pair)
        if pair.get('kind')=='timer'and pair.get('role')=='planet':timers.append(pair)
    slots=tuple(int(mbf.dec(bytes.fromhex(t['before']['port_raw'])))for t in timers)
    assert slots==(1,3,99,100)
    assert slots==tuple(int(mbf.dec(bytes.fromhex(d['before']['port_raw'])))for d in dates)
    rows=tuple((4051+slot,(d['date']-datetime.date(2026,1,1)).days+1,t['minutes'])for slot,d,t in zip(slots,dates,timers))
    return seed,rows


def load(folder):
    before=gzip.decompress((folder/'before-YTDATA.DAT.gz').read_bytes())
    after=gzip.decompress((folder/'after-YTDATA.DAT.gz').read_bytes())
    ob=json.loads(gzip.decompress((folder/'host-time.json.gz').read_bytes()))
    seed,rows=source_planet_clocks(ob)
    return before,after,ob,seed,rows


def run(before,seed,rows):
    world=bytearray(before);stats=model.maintain(world,SimpleNamespace(rng=QB3(seed)),rows)
    return bytes(world),stats


class GatewayPlanets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.samples={str(p.parent.parent.name)+'/'+p.parent.name:load(p)for p in ROOT.glob('*/child-*/observed-a')}
    def test_all36_source_economies_match_exact_records_before_later_npc_actions(self):
        for key in self.samples:
            for mode in MODES:
                before,after,ob,seed,rows=load(ROOT/key/mode);world,stats=run(before,seed,rows)
                for record,day,timer in rows:
                    at=(record-1)*137;actual=world[at:at+137];expected=after[at:at+137]
                    # Actual NPC phase later spends home ground, augments HQ,
                    # and may clear gateway fighters. Economy is compared before it.
                    omitted={77}if record in(4052,4150,4151)else({129}if key.startswith(('empty/','pickup/','mine-pickup/'))and key.endswith('child-1')else set())
                    keep=[n for n in range(137)if not any(o<=n<o+4 for o in omitted)]
                    with self.subTest(case=key,mode=mode,record=record):self.assertEqual(bytes(actual[n]for n in keep),bytes(expected[n]for n in keep))
                self.assertEqual(stats['rng_draws'],12)
    def test_zero_rates_produce_nothing_before_the_minimum_rate_clamp(self):
        for case in('empty','pickup','mine-pickup','guarded-pickup','mine-guarded','fatal-before-pickup'):
            before,after,ob,seed,rows=self.samples[case+'/child-1'];world,stats=run(before,seed,rows)
            self.assertEqual([mbf.get(world,4054,o)for o in(45,49,53)],[1,1,1])
            self.assertEqual(mbf.get(world,4054,129),mbf.get(before,4054,129))
            self.assertEqual(mbf.get(world,4054,77),505000)
    def test_second_day_uses_inherited_one_rates_and_preserves_title_and_ground(self):
        for case in('empty','pickup','mine-pickup','guarded-pickup','mine-guarded','fatal-before-pickup'):
            before,after,ob,seed,rows=self.samples[case+'/child-2'];world,stats=run(before,seed,rows)
            self.assertEqual(mbf.get(world,4054,129),mbf.get(before,4054,129)+3)
            self.assertEqual(mbf.get(world,4054,77),510050)
            self.assertEqual([mbf.get(world,4054,o)for o in(45,49,53)],[1.0099999904632568]*3)
            self.assertEqual(mbf.get(world,4054,73),0)
    def test_no_target_or_capture_reads_and_poisoned_rng_bytes_are_irrelevant(self):
        before,after,ob,seed,rows=self.samples['mine-pickup/child-1'];poison=copy.deepcopy(ob)
        for e in poison['events']:
            for side in('before','after'):e[side]['rng_raw']='ffffffff'
        self.assertEqual(source_planet_clocks(poison),(seed,rows))
        with patch.object(builtins,'open',side_effect=AssertionError('core open')),patch.object(Path,'read_bytes',side_effect=AssertionError('core read')),patch.object(Path,'read_text',side_effect=AssertionError('core text')):
            self.assertEqual(run(before,seed,rows),run(before,*source_planet_clocks(poison)))
    def test_other_slots_gateway_ownership_bank_rates_and_metadata_fail_atomically(self):
        before,after,ob,seed,rows=self.samples['pickup/child-1']
        for record,offset,value in((4053,85,1),(4054,73,-1),(4054,117,1),(4054,45,1),(4054,81,305),(4054,129,38),(4054,77,500001),(3051,93,0)):
            world=bytearray(before);mbf.put(world,record,offset,value);saved=bytes(world)
            with self.subTest(record=record,offset=offset),self.assertRaises(ValueError):model.maintain(world,SimpleNamespace(rng=QB3(seed)),rows)
            self.assertEqual(bytes(world),saved)
    def test_reordered_mutable_or_wrong_date_clock_inputs_are_rejected(self):
        before,after,ob,seed,rows=self.samples['empty/child-1']
        for altered in(list(rows),rows[::-1],tuple((r,311,t)for r,d,t in rows),tuple((r,d,mbf.enc(720))for r,d,t in rows)):
            with self.assertRaises(ValueError):run(before,seed,altered)
    def test_full_world_changes_only_active_planet_numeric_writer_fields(self):
        before,after,ob,seed,rows=self.samples['guarded-pickup/child-1'];world,stats=run(before,seed,rows)
        allowed={i for r,d,t in rows for off in(41,45,49,53,57,61,65,69,77,89,113,117,125,129)for i in range((r-1)*137+off,(r-1)*137+off+4)}
        self.assertTrue(all(i in allowed for i,(a,b)in enumerate(zip(before,world))if a!=b))
    def test_unknown_home_names_and_missing_links_are_rejected(self):
        before,after,ob,seed,rows=self.samples['empty/child-2']
        world=bytearray(before);at=(4054-1)*137;world[at:at+13]=b'Other Gateway'
        with self.assertRaises(ValueError):run(bytes(world),seed,rows)
        world=bytearray(before);mbf.put(world,3050,93,3)
        with self.assertRaises(ValueError):run(bytes(world),seed,rows)

if __name__=='__main__':unittest.main()
