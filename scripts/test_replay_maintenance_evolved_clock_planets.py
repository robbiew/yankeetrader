"""Native planet economy checks distinguish later NPC ground aftermath."""
import builtins
import copy
import gzip
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from replay_qb_graph import mbf,QB3
from replay_maintenance_evolved_records import inputs_from_observation
import replay_maintenance_evolved_clock_planets as model

CORPUS=Path(__file__).resolve().parents[1]/'research/yt-maint/evolved-clock-controls'

def load(folder):
    b=gzip.decompress((folder/'before-YTDATA.DAT.gz').read_bytes())
    a=gzip.decompress((folder/'after-YTDATA.DAT.gz').read_bytes())
    ob=json.loads(gzip.decompress((folder/'host-time.json.gz').read_bytes()))
    return b,a,ob,inputs_from_observation(ob)

def run(b,i):
    world=bytearray(b);stats=model.maintain(world,SimpleNamespace(rng=QB3(i.clock.initial_state)),i.planet_clocks)
    return world,stats

class ClockPlanets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.samples={(p.parent.name,p.name):load(p/'observed-a')for p in sorted(CORPUS.glob('*/child-*'))}

    def test_all_24_observed_record_economies_match_before_later_npc_ground(self):
        for key in self.samples:
            for mode in('observed-a','observed-b','observed-c'):
                b,a,_,i=load(CORPUS/key[0]/key[1]/mode);w,stats=run(b,i)
                for r in model.ACTIVE_SLOTS:
                    skip=(r==4151 or(key==('noon','child-1')and r==4052)or(key==('new-year','child-2')and r==4150))
                    at=(r-1)*137;actual=bytes(w[at:at+137]);expected=a[at:at+137]
                    if skip:actual=actual[:77]+actual[81:];expected=expected[:77]+expected[81:]
                    with self.subTest(profile=key,mode=mode,record=r):self.assertEqual(actual,expected)
                self.assertEqual(stats['rng_draws'],12)

    def test_later_ground_casualties_are_not_patched_into_economy(self):
        for key,r,loss in((('noon','child-1'),4052,19),(('new-year','child-2'),4150,5)):
            b,a,_,i=self.samples[key];w,_=run(b,i)
            self.assertEqual(mbf.get(w,r,77)-mbf.get(a,r,77),loss)

    def test_half_day_bank_growth_and_cap_use_before_economy(self):
        expected={('noon','child-1'):512575,('noon','child-2'):515137,('catchup-eleven','child-1'):555500,('new-year','child-1'):555500}
        for key,ground in expected.items():
            b,_,_,i=self.samples[key];w,s=run(b,i)
            self.assertEqual(mbf.get(w,4053,77),ground)
            if key[0]in('catchup-eleven','new-year'):self.assertTrue(all(row['elapsed']==10 for row in s['rows']))

    def test_rng_witnesses_are_not_model_inputs(self):
        b,_,ob,i=self.samples['noon','child-1'];ob=copy.deepcopy(ob)
        for event in ob['events']:
            for side in('before','after'):event[side]['rng_raw']='00000000'
        altered=inputs_from_observation(ob)
        self.assertEqual(run(b,i),run(b,altered))

    def test_core_opens_no_files_and_mutates_only_four_records(self):
        b,_,_,i=self.samples['new-year','child-1']
        with patch.object(builtins,'open',side_effect=AssertionError('core file access')),patch.object(Path,'read_bytes',side_effect=AssertionError('core file access')):w,_=run(b,i)
        for r in range(1,4152):
            if r not in model.ACTIVE_SLOTS:self.assertEqual(w[(r-1)*137:r*137],b[(r-1)*137:r*137])

    def test_bad_source_rows_and_prior_context_fail_without_mutation(self):
        b,_,_,i=self.samples['noon','child-1']
        for off,value in((41,305),(89,300),(73,1),(117,40000000),(81,304)):
            w=bytearray(b);mbf.put(w,4052,off,value);saved=bytes(w)
            with self.subTest(offset=off),self.assertRaises(ValueError):model.maintain(w,SimpleNamespace(rng=QB3(i.clock.initial_state)),i.planet_clocks)
            self.assertEqual(w,saved)
        for rows in(list(i.planet_clocks),i.planet_clocks[::-1],tuple((r,309,t)for r,d,t in i.planet_clocks)):
            w=bytearray(b)
            with self.assertRaises(ValueError):model.maintain(w,SimpleNamespace(rng=QB3(i.clock.initial_state)),rows)
            self.assertEqual(w,b)

    def test_selected_damage_predicate_rejects_without_world_mutation(self):
        b,_,_,i=self.samples['noon','child-1'];w=bytearray(b)
        for off in(45,49,53):mbf.put(w,4052,off,200000)
        saved=bytes(w)
        class Draws:
            state=1;draws=0
            def rnd(self):
                self.draws+=1
                return 1 if self.draws==1 else 0
        with self.assertRaisesRegex(ValueError,'selected plague'):model.maintain(w,SimpleNamespace(rng=Draws()),i.planet_clocks)
        self.assertEqual(w,saved)

if __name__=='__main__':unittest.main()
