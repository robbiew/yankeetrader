"""Survivor publication tests use modeled bytes, never after-file templates."""
import copy
import gzip
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from replay_qb_graph import mbf
from replay_maintenance_evolved_combat_records import inputs_from_observation,FILES,MODES
from replay_maintenance_evolved_records import _watermark_and_inactive_ranks
from replay_maintenance_survivor_ports import replay_ports
from replay_maintenance_survivor_npcs import synthesize as npcs
import replay_maintenance_survivor_aux as model
ROOT=Path(__file__).resolve().parents[1]/'research/yt-maint/survivor-chain-controls'
class SurvivorAux(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.samples={}
  for p in ROOT.glob('*/child-*/observed-a'):
   b={n:gzip.decompress((p/('before-'+n+'.gz')).read_bytes())for n in FILES};i=inputs_from_observation(json.loads(gzip.decompress((p/'host-time.json.gz').read_bytes())));c=i.clock;day=int(mbf.get(b['YTDATA.DAT'],1,81))+1
   block,ps=replay_ports(b['YTDATA.DAT'],(day,)*1000,c.port_timer_minutes);world=b['YTDATA.DAT'][:3051*137]+block+b['YTDATA.DAT'][4051*137:]
   world,n=npcs(world,SimpleNamespace(clock=c,schedule=i.schedule,phase_days={k:None if getattr(c,k+'_date')is None else day for k in('wanderer','xannoron','base')},final_day=day,planet_clocks=i.planet_clocks));world=_watermark_and_inactive_ranks(world,day)
   cls.samples[p.parent.parent.name,p.parent.name]=(b,world,c,n)
 def publish(self,sample):
  b,w,c,n=sample;return model.synthesize(b,w,c.news_date,c.news_clock,c.score_date,c.score_clock,created=n['created'],events=n['events'],mercenary=n['mercenary'])
 def test_five_aux_files_match_all48_native_controls(self):
  for (case,child),sample in self.samples.items():
   files,stats=self.publish(sample)
   for mode in MODES:
    for name,actual in files.items():
     expected=gzip.decompress((ROOT/case/child/mode/('after-'+name+'.gz')).read_bytes())
     with self.subTest(case=case,child=child,mode=mode,file=name):self.assertEqual(actual,expected)
 def test_printed_counters_and_actual_2533_3491_losses_are_separate(self):
  files,s=self.publish(self.samples['mercenary-survivor','child-2']);self.assertEqual(s['modeled_losses'],{-1:2533,-2:3491,0:0});self.assertEqual(s['scores'],{-1:243300,-2:9384600})
  self.assertAlmostEqual(s['percentages'][0],100*243300/9384600);self.assertEqual(s['percentages'][1],100.0);self.assertIn(b'Mercenaries: lost 1, dstrd 0 (Xannor ftrs dstrd)',files['YTNEWS.DAT']);self.assertNotIn(b'3491',files['YTNEWS.DAT'])
 def test_zero_xannor_score_is_allowed_with_positive_mercenary_denominator(self):
  b,w,c,n=copy.deepcopy(self.samples['mercenary-survivor','child-1']);old=bytearray(b['YTDATA.DAT']);new=bytearray(w)
  for data in(old,new):
   for sector in range(1,3001):
    if mbf.get(data,51+sector,85)==-1:mbf.put(data,51+sector,81,0)
  b['YTDATA.DAT']=bytes(old);files,s=self.publish((b,bytes(new),c,n));self.assertEqual(s['percentages'],[0.0,100.0]);self.assertEqual(s['scores'][-1],0)
 def test_news_score_clock_calls_remain_independent(self):
  sample=self.samples['neutral-survivor','child-1'];b,w,c,n=sample;files,s=self.publish(sample)
  self.assertTrue(files['YTNEWS.DAT'].startswith(b'00:00:00 11-05-2026'));self.assertIn(b'11-05-2026 00:00:01',files['YTSCORE.ASC'])
 def test_before_names_rotated_news_empty_inbox_and_raw_world_aliases_preserved(self):
  for sample in self.samples.values():
   b,w,c,n=sample;saved=bytes(w);files,s=self.publish(sample)
   self.assertEqual(files['YTNAME.DAT'],b['YTNAME.DAT']);self.assertEqual(files['YTYNEWS.DAT'],b['YTNEWS.DAT']);self.assertEqual(files['YTRMSG.DAT'],b'');self.assertEqual(w,saved)
 def test_only_original_executable_is_opened(self):
  read=Path.read_bytes;seen=[]
  def checked(p):seen.append(p);self.assertEqual(p.name,'YTMAINT.EXE');return read(p)
  with patch.object(Path,'read_bytes',checked):self.publish(self.samples['mercenary-survivor','child-2'])
  self.assertTrue(seen)
 def test_false_damage_counts_physical_results_or_public_context_rejected(self):
  sample=self.samples['mercenary-survivor','child-2']
  for key,value in(('owner',0),('defender_damage',-1),('x_damage',0),('force',1)):
   b,w,c,n=copy.deepcopy(sample);n['events'][0][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):self.publish((b,w,c,n))
  b,w,c,n=copy.deepcopy(sample);n['mercenary']['force']+=1
  with self.assertRaises(ValueError):self.publish((b,w,c,n))
  b,w,c,n=copy.deepcopy(sample);b['YTRMSG.DAT']=b'private'
  with self.assertRaises(ValueError):self.publish((b,w,c,n))
if __name__=='__main__':unittest.main()
