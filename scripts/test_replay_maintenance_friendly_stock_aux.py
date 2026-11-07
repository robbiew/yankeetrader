"""Independent public-ledger consistency and hostile composition regressions."""
import copy
import gzip
import json
from pathlib import Path
import unittest

import replay_maintenance_friendly_stock_records as records
import replay_maintenance_friendly_stock_aux as model
from replay_qb_graph import mbf


class FriendlyStockAux(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.samples={};before=records.initial_before()
        for case in records.CASES:
            obs=tuple(json.loads(gzip.decompress(p.read_bytes()))for p in records.observation_paths(case,'observed-a'))
            values=tuple((records.combat.inputs_from_observation if i<3 else records.inputs_from_observation)(o)for i,o in enumerate(obs))
            out,stats=records.synthesize_chain(before,values,case);fixture,_=records.apply_fixture(out[2],case)
            cls.samples[case]=(fixture,out[3],values[3].clock,stats[3]['npcs'])

    def publish(self,sample):
        before,after,clock,npc=sample
        return model.synthesize(before,after['YTDATA.DAT'],clock.news_date,clock.news_clock,clock.score_date,clock.score_clock,
                                created=npc['created'],events=npc['events'],mercenary=npc['mercenary'])

    def rejects(self,sample):
        with self.assertRaises((ValueError,AssertionError)):self.publish(sample)

    def test_all_five_auxiliary_files_match_all_forty_eight_controls(self):
        for case,sample in self.samples.items():
            actual,_=self.publish(sample)
            for mode in records.MODES:
                for name,data in actual.items():
                    self.assertEqual(data,gzip.decompress((records.DEFAULT/case/'child-1'/mode/('after-'+name+'.gz')).read_bytes()))

    def test_combined_actor_no_capture_and_zero_receipt_suppression(self):
        for case,(friendly,governor,stock)in records.CASES.items():
            files,stats=self.publish(self.samples[case]);text=files['YTNEWS.DAT'];amount=stock.numerator//stock.denominator
            self.assertNotIn(b'captur',text.lower())
            self.assertNotIn(b'taking 0 fighters',text)
            if amount:
                self.assertIn(str(97337+friendly).encode()+b' Mercenaries taking ',text)
                self.assertIn(b'taking '+str(amount).encode()+b' fighters',text)
            self.assertEqual(stats['scores'][-2],100*(97337+friendly+amount))

    def test_wrong_premerge_receipt_actor_is_rejected(self):
        b,w,c,n=copy.deepcopy(self.samples['friendly-whole']);n['mercenary']['events'][0]['initial_force']=97337
        self.rejects((b,w,c,n))

    def test_coherent_double_count_total_is_rejected(self):
        b,w,c,n=copy.deepcopy(self.samples['friendly-whole']);m=n['mercenary'];e=m['events'][0]
        e['initial_force']+=37;e['force']+=37;m['force']+=37;m['activations'][1]['final_force']+=37
        world=bytearray(w['YTDATA.DAT']);mbf.put(world,3051,81,e['force']);w['YTDATA.DAT']=bytes(world)
        self.rejects((b,w,c,n))

    def test_coherent_overwrite_total_is_rejected(self):
        b,w,c,n=copy.deepcopy(self.samples['friendly-whole']);m=n['mercenary'];e=m['events'][0]
        e['initial_force']-=37;e['force']-=37;m['force']-=37;m['activations'][1]['final_force']-=37
        world=bytearray(w['YTDATA.DAT']);mbf.put(world,3051,81,e['force']);w['YTDATA.DAT']=bytes(world)
        self.rejects((b,w,c,n))

    def test_changed_governor_is_rejected_even_if_otherwise_admitted(self):
        for case,value in(('friendly-whole',-2),('friendly-owned-whole',0)):
            b,w,c,n=copy.deepcopy(self.samples[case]);world=bytearray(w['YTDATA.DAT']);mbf.put(world,4054,73,value);w['YTDATA.DAT']=bytes(world)
            self.rejects((b,w,c,n))

    def test_forged_event_governor_or_capture_is_rejected(self):
        for key,value in(('captured',True),('governor',-2)):
            b,w,c,n=copy.deepcopy(self.samples['friendly-whole']);n['mercenary']['events'][0][key]=value
            self.rejects((b,w,c,n))

    def test_departed_or_different_held_garrison_is_rejected(self):
        for key,value in(('held',False),('force',38),('gate',.9),('origin',2999)):
            b,w,c,n=copy.deepcopy(self.samples['friendly-whole']);n['mercenary']['activations'][0][key]=value
            self.rejects((b,w,c,n))

    def test_forged_incoming_or_merged_amounts_are_rejected(self):
        for key,value in(('incoming_force',97338),('entering_friendly_force',38),('merged',74)):
            b,w,c,n=copy.deepcopy(self.samples['friendly-whole']);n['mercenary']['events'][0][key]=value
            self.rejects((b,w,c,n))

    def test_numeric_zero_does_not_replace_source_clear_bytes(self):
        b,w,c,n=copy.deepcopy(self.samples['friendly-half']);world=bytearray(w['YTDATA.DAT']);world[4053*137+129:4053*137+133]=bytes(4);w['YTDATA.DAT']=bytes(world)
        self.rejects((b,w,c,n))

    def test_amount_fraction_and_summary_must_agree(self):
        for target,key,value in(('event','pickup',38),('event','fractional_discard',.75),('summary','merged',74)):
            b,w,c,n=copy.deepcopy(self.samples['friendly-whole']);m=n['mercenary'];(m['events'][0]if target=='event'else m)[key]=value
            self.rejects((b,w,c,n))


if __name__=='__main__':unittest.main()
