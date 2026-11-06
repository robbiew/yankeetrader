"""Bounded before-only economy for evolved neutral/combat world contexts."""
import builtins
import copy
import gzip
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from replay_qb_graph import mbf,QB3
from replay_maintenance_evolved_combat_records import inputs_from_observation
import replay_maintenance_evolved_combat_planets as model

ROOT=Path(__file__).resolve().parents[1]/'research/yt-maint/evolved-combat-controls'
def load(p):
    b=gzip.decompress((p/'before-YTDATA.DAT.gz').read_bytes());a=gzip.decompress((p/'after-YTDATA.DAT.gz').read_bytes())
    ob=json.loads(gzip.decompress((p/'host-time.json.gz').read_bytes()))
    return b,a,ob,inputs_from_observation(ob)
def run(b,i):
    w=bytearray(b);s=model.maintain(w,SimpleNamespace(rng=QB3(i.clock.initial_state)),i.planet_clocks);return w,s

class CombatPlanets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.samples={(p.parent.name,p.name):load(p/'observed-a')for p in ROOT.glob('*/child-*')}
    def test_all24_observed_economies_match_before_later_ground_combat(self):
        for key in self.samples:
            for mode in('observed-a','observed-b','observed-c'):
                b,a,_,i=load(ROOT/key[0]/key[1]/mode);w,s=run(b,i)
                for r,d,t in i.planet_clocks:
                    at=(r-1)*137;actual=bytes(w[at:at+137]);expected=a[at:at+137]
                    if r in(4053,4151):actual=actual[:77]+actual[81:];expected=expected[:77]+expected[81:]
                    with self.subTest(case=key,mode=mode,record=r):self.assertEqual(actual,expected)
                self.assertEqual(s['rng_draws'],3*len(i.planet_clocks))
    def test_neutral_ground_is_economy_then_actual_capped_assault_losses(self):
        for stage,economy,saved,loss in(('child-1',510024,510002,22),('child-2',515102,515083,19)):
            b,a,_,i=self.samples['route-planet-neutral',stage];w,_=run(b,i)
            self.assertEqual(mbf.get(w,4053,77),economy);self.assertEqual(mbf.get(a,4053,77),saved);self.assertEqual(economy-saved,loss)
    def test_no_files_read_and_no_target_rng_state_used(self):
        b,_,ob,i=self.samples['route-mercenary-100000','child-1'];ob=copy.deepcopy(ob)
        for e in ob['events']:
            for side in('before','after'):e[side]['rng_raw']='00000000'
        j=inputs_from_observation(ob)
        with patch.object(builtins,'open',side_effect=AssertionError('corefile')),patch.object(Path,'read_bytes',side_effect=AssertionError('corefile')):self.assertEqual(run(b,i),run(b,j))
    def test_three_homes_or_exact_neutral_route_haven_only(self):
        b,_,_,i=self.samples['route-planet-neutral','child-1']
        for off,value in((73,-1),(89,720),(41,305),(81,305)):
            w=bytearray(b);mbf.put(w,4053,off,value);saved=bytes(w)
            with self.subTest(offset=off),self.assertRaises(ValueError):model.maintain(w,SimpleNamespace(rng=QB3(i.clock.initial_state)),i.planet_clocks)
            self.assertEqual(w,saved)
        w=bytearray(b);at=(4053-1)*137;w[at:at+41]=b'Convergence Haven'.ljust(41,b' ');mbf.put(w,4053,85,17)
        with self.assertRaises(ValueError):model.maintain(w,SimpleNamespace(rng=QB3(i.clock.initial_state)),i.planet_clocks)
    def test_unknown_calendar_rows_and_mutable_world_rejected(self):
        b,_,_,i=self.samples['route-neutral-37','child-1']
        for rows in(list(i.planet_clocks),i.planet_clocks[::-1],tuple((r,317,t)for r,d,t in i.planet_clocks)):
            with self.assertRaises(ValueError):model.maintain(bytearray(b),SimpleNamespace(rng=QB3(i.clock.initial_state)),rows)
        with self.assertRaises(ValueError):model.maintain(b,SimpleNamespace(rng=QB3(i.clock.initial_state)),i.planet_clocks)
if __name__=='__main__':unittest.main()
