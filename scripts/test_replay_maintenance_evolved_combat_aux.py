"""Exact native publication from modeled worlds and computed combat events."""
import copy
import datetime
import gzip
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import replay_maintenance_evolved_combat_aux as model
import replay_maintenance_evolved_combat_records as records
from replay_qb_graph import mbf

class CombatAux(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.samples={}
        for case in records.CASES:
            before=records.initial_before(case)
            paths=(records.PARENT/case/'observed-a'/'host-time.json.gz',)+tuple(records.DEFAULT/case/f'child-{s}'/'observed-a'/'host-time.json.gz'for s in(1,2))
            inputs=tuple(records.inputs_from_observation(json.loads(gzip.decompress(p.read_bytes())))for p in paths)
            outputs,stats=records.synthesize_chain(before,inputs)
            for s in(1,2):cls.samples[case,s]=(outputs[s-1],outputs[s],inputs[s].clock,stats[s]['npcs'])
    def publish(self,sample):
        before,world,c,npc=sample
        return model.synthesize(before,world['YTDATA.DAT'],c.news_date,c.news_clock,c.score_date,c.score_clock,created=npc['created'],events=npc['events'],mercenary=npc['mercenary'])
    def test_five_auxiliary_files_equal_all48_native_outputs(self):
        for (case,s),sample in self.samples.items():
            actual,stats=self.publish(sample)
            for mode in records.MODES:
                for n,b in actual.items():
                    expected=gzip.decompress((records.DEFAULT/case/f'child-{s}'/mode/('after-'+n+'.gz')).read_bytes())
                    with self.subTest(case=case,child=s,mode=mode,file=n):self.assertEqual(b,expected)
    def test_actual188_unprinted_mercenary_loss_and_physical_denominator(self):
        actual,s=self.publish(self.samples['route-mercenary-100000',2])
        self.assertEqual(s['modeled_losses'],{-1:182,-2:188,0:0});self.assertEqual(s['scores'],{-1:496600,-2:9733700})
        self.assertIn(b'97525 Mercenaries attacking 182 fighters beloning to The Xannor!',actual['YTNEWS.DAT']);self.assertNotIn(b'188',actual['YTNEWS.DAT'])
        self.assertIn(b'The Mercenaries Won!',actual['YTNEWS.DAT']);self.assertEqual(s['percentages'][1],100)
    def test_news_rotation_empty_inbox_and_names_come_from_before(self):
        for sample in self.samples.values():
            b,w,c,n=sample;actual,_=self.publish(sample)
            self.assertEqual(actual['YTYNEWS.DAT'],b['YTNEWS.DAT']);self.assertEqual(actual['YTNAME.DAT'],b['YTNAME.DAT']);self.assertEqual(actual['YTRMSG.DAT'],b'')
    def test_only_original_executable_is_read_by_publisher(self):
        original_read=Path.read_bytes;seen=[]
        def read(p):
            seen.append(p);self.assertEqual(p.name,'YTMAINT.EXE');return original_read(p)
        with patch.object(Path,'read_bytes',read):self.publish(self.samples['route-mercenary-100000',2])
        self.assertTrue(seen)
    def test_false_casualty_or_final_physical_claim_rejected(self):
        sample=self.samples['route-mercenary-100000',2]
        for key,value in(('losses',187),('initial_defenders',183),('defender_name','Other')):
            b,w,c,n=copy.deepcopy(sample);n['mercenary']['events'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.publish((b,w,c,n))
        b,w,c,n=copy.deepcopy(sample);n['mercenary']['final_sectors']=[109]
        with self.assertRaises(ValueError):self.publish((b,w,c,n))
    def test_unknown_private_messages_calendar_or_home_creation_rejected(self):
        b,w,c,n=copy.deepcopy(self.samples['route-neutral-37',1]);b['YTRMSG.DAT']=b'private'
        with self.assertRaises(ValueError):self.publish((b,w,c,n))
        b,w,c,n=self.samples['route-neutral-37',1]
        with self.assertRaises(ValueError):model.synthesize(b,w['YTDATA.DAT'],c.news_date,c.news_clock,c.score_date,c.score_clock,created=('wanderer',))
        with self.assertRaises(ValueError):model.synthesize(b,w['YTDATA.DAT'],datetime.date(2026,11,4),c.news_clock,c.score_date,c.score_clock)
if __name__=='__main__':unittest.main()
