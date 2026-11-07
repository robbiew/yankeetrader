"""Independent fatal-combat ledger, exact-byte and extinction regressions."""
import copy,gzip,json,unittest
from replay_qb_graph import mbf
import replay_maintenance_defender_stock_records as r
import replay_maintenance_defender_stock_aux as a

class DefenderAux(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.samples={};before=r.initial_before()
  for case in r.CASES:
   obs=tuple(json.loads(gzip.decompress(p.read_bytes()))for p in r.observation_paths(case,'observed-a'))
   inputs=tuple((r.combat.inputs_from_observation if i<3 else r.inputs_from_observation)(o)for i,o in enumerate(obs))
   outs,stats=r.synthesize_chain(before,inputs,case);fixture,_=r.apply_fixture(outs[2],case)
   cls.samples[case,1]=(fixture,outs[3],inputs[3].clock,stats[3]['npcs'])
   cls.samples[case,2]=(outs[3],outs[4],inputs[4].clock,stats[4]['npcs'])
 def pub(self,s):
  b,w,c,n=s
  return a.synthesize(b,w['YTDATA.DAT'],c.news_date,c.news_clock,c.score_date,c.score_clock,created=n['created'],events=n['events'],mercenary=n['mercenary'])
 def reject(self,s):
  with self.assertRaises((ValueError,AssertionError)):self.pub(s)
 def sample(self,case='balanced-37-whole',day=1):return copy.deepcopy(self.samples[case,day])
 def test_all_aux_files_match_all_native_modes(self):
  for (case,day),s in self.samples.items():
   out,_=self.pub(s)
   for mode in r.MODES:
    for name,b in out.items():self.assertEqual(b,gzip.decompress((r.DEFAULT/case/f'child-{day}'/mode/('after-'+name+'.gz')).read_bytes()))
 def test_losing_receipt_and_zero_mercenary_score_are_derived(self):
  for (case,day),s in self.samples.items():
   out,stats=self.pub(s);self.assertEqual(stats['scores'][-2],0)
   self.assertEqual(b'The Mercenaries Lost!' in out['YTNEWS.DAT'],day==1)
 def test_wrong_battle_rng_state_is_rejected(self):
  b,w,c,n=self.sample();n['mercenary']['events'][0]['initial_rng_state']^=1;self.reject((b,w,c,n))
 def test_wrong_battle_rng_witness_is_rejected(self):
  for key in ('final_rng_state','rounds','rng_draws'):
   b,w,c,n=self.sample();n['mercenary']['events'][0][key]+=1;self.reject((b,w,c,n))
 def test_coherent_defender_casualty_forgery_is_rejected(self):
  b,w,c,n=self.sample('37-versus-1000-whole');e=n['mercenary']['events'][0];e['defenders']-=1;e['defender_losses']+=1
  data=bytearray(w['YTDATA.DAT']);mbf.put(data,3051,81,e['defenders']);w['YTDATA.DAT']=bytes(data)
  self.reject((b,w,c,n))
 def test_wrong_winner_is_rejected(self):
  b,w,c,n=self.sample();n['mercenary']['events'][0]['force']=1;self.reject((b,w,c,n))
 def test_missing_or_duplicated_fatal_event_is_rejected(self):
  for duplicate in (False,True):
   b,w,c,n=self.sample();es=n['mercenary']['events'];es.append(copy.deepcopy(es[0]))if duplicate else es.pop();self.reject((b,w,c,n))
 def test_stock_debit_cannot_hide_behind_a_losing_battle(self):
  b,w,c,n=self.sample();data=bytearray(w['YTDATA.DAT']);mbf.put(data,4054,129,0);w['YTDATA.DAT']=bytes(data);self.reject((b,w,c,n))
 def test_raw_stock_and_governor_zero_aliases_are_rejected(self):
  for offset in(73,129):
   b,w,c,n=self.sample('one-versus-37-empty');data=bytearray(w['YTDATA.DAT']);data[4053*137+offset:4053*137+offset+4]=bytes.fromhex('aabbcc00');w['YTDATA.DAT']=bytes(data);self.reject((b,w,c,n))
 def test_departure_raw_zero_alias_is_rejected(self):
  b,w,c,n=self.sample();data=bytearray(w['YTDATA.DAT']);data[2418*137+81:2418*137+89]=bytes(8);w['YTDATA.DAT']=bytes(data);self.reject((b,w,c,n))
 def test_coherent_resurrection_on_next_day_is_rejected(self):
  b,w,c,n=self.sample(day=2);data=bytearray(w['YTDATA.DAT']);mbf.put(data,2419,81,1);mbf.put(data,2419,85,-2);w['YTDATA.DAT']=bytes(data);n['mercenary']['force']=1;n['mercenary']['final_sectors']=[2368];self.reject((b,w,c,n))
 def test_missing_or_wrong_route_activation_is_rejected(self):
  for key,value in(('route',[2368,3000]),('entered',[]),('target',2368),('held',True),('final_sector',3000)):
   b,w,c,n=self.sample();n['mercenary']['activations'][0][key]=value;self.reject((b,w,c,n))
 def test_forged_casualty_summary_is_rejected(self):
  b,w,c,n=self.sample();n['mercenary']['losses']-=1;self.reject((b,w,c,n))
 def test_next_day_action_is_rejected_even_without_inventory_change(self):
  b,w,c,n=self.sample(day=2);n['mercenary']['activations'].append(dict(origin=2368,force=0));self.reject((b,w,c,n))
 def test_private_inbox_or_home_recreation_is_rejected(self):
  b,w,c,n=self.sample();b['YTRMSG.DAT']=b'invented';self.reject((b,w,c,n))
  b,w,c,n=self.sample();n['created']=('wanderer',);self.reject((b,w,c,n))
if __name__=='__main__':unittest.main()
