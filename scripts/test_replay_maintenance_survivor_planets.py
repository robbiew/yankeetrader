"""Native survivor economy before separately modeled NPC ground aftermath."""
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
import replay_maintenance_survivor_planets as model
ROOT=Path(__file__).resolve().parents[1]/'research/yt-maint/survivor-chain-controls'
def load(p):
 b=gzip.decompress((p/'before-YTDATA.DAT.gz').read_bytes());a=gzip.decompress((p/'after-YTDATA.DAT.gz').read_bytes());ob=json.loads(gzip.decompress((p/'host-time.json.gz').read_bytes()));return b,a,ob,inputs_from_observation(ob)
def run(b,i):
 w=bytearray(b);s=model.maintain(w,SimpleNamespace(rng=QB3(i.clock.initial_state)),i.planet_clocks);return w,s
class SurvivorPlanets(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.samples={str(p.parent.parent.name)+'/'+p.parent.name:load(p)for p in ROOT.glob('*/child-*/observed-a')}
 def test_all24_observed_economies_except_later_ground_match_exactly(self):
  for key in self.samples:
   for mode in('observed-a','observed-b','observed-c'):
    b,a,ob,i=load(ROOT/key/mode);w,s=run(b,i)
    for r,d,t in i.planet_clocks:
     at=(r-1)*137;actual=bytes(w[at:at+137]);expected=a[at:at+137]
     if r in(4052,4053,4151):actual=actual[:77]+actual[81:];expected=expected[:77]+expected[81:]
     with self.subTest(profile=key,mode=mode,record=r):self.assertEqual(actual,expected)
    self.assertEqual(s['rng_draws'],len(i.planet_clocks)*3)
 def test_friendly_and_neutral_ground_economy_are_distinct_from_assaults(self):
  for k in('mine-survivor/child-1','mine-survivor/child-2'):
   b,a,ob,i=self.samples[k];w,s=run(b,i);self.assertEqual(mbf.get(w,4053,77),mbf.get(a,4053,77))
  for k in('planet-survivor/child-1','planet-survivor/child-2'):
   b,a,ob,i=self.samples[k];w,s=run(b,i);self.assertGreater(mbf.get(w,4053,77),mbf.get(a,4053,77))
 def test_no_file_reads_or_rng_witness_input(self):
  b,a,ob,i=self.samples['neutral-survivor/child-1'];ob=copy.deepcopy(ob)
  for e in ob['events']:
   for side in('before','after'):e[side]['rng_raw']='00000000'
  j=inputs_from_observation(ob)
  with patch.object(builtins,'open',side_effect=AssertionError('corefile')),patch.object(Path,'read_bytes',side_effect=AssertionError('corefile')):self.assertEqual(run(b,i),run(b,j))
 def test_stale_calendars_unknown_titles_ownership_and_metadata_rejected_atomically(self):
  b,a,ob,i=self.samples['mine-survivor/child-1']
  for r,o,v in((4052,41,296),(4053,73,0),(4053,89,720),(4053,81,305)):
   w=bytearray(b);mbf.put(w,r,o,v);saved=bytes(w)
   with self.subTest(record=r,offset=o),self.assertRaises(ValueError):model.maintain(w,SimpleNamespace(rng=QB3(i.clock.initial_state)),i.planet_clocks)
   self.assertEqual(w,saved)
  for rows in(list(i.planet_clocks),i.planet_clocks[::-1],tuple((r,311,t)for r,d,t in i.planet_clocks)):
   with self.assertRaises(ValueError):model.maintain(bytearray(b),SimpleNamespace(rng=QB3(i.clock.initial_state)),rows)
if __name__=='__main__':unittest.main()
