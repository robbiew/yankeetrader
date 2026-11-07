"""Independent public-ledger consistency and hostile composition regressions."""
import copy
import gzip
import json
from pathlib import Path
import unittest

import replay_maintenance_neutral_owner_stock_records as records
import replay_maintenance_neutral_owner_stock_aux as model
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
            departed=case=='friendly-mine-second-four'
            self.assertEqual(b'captur' in text.lower(),departed)
            self.assertNotIn(b'taking 0 fighters',text)
            if amount:
                self.assertIn(str(self.samples[case][3]['mercenary']['events'][-1]['initial_force']).encode()+b' Mercenaries taking ',text)
                self.assertIn(b'taking '+str(amount).encode()+b' fighters',text)
            self.assertEqual(stats['scores'][-2],100*self.samples[case][3]['mercenary']['force'])

    def test_wrong_premerge_receipt_actor_is_rejected(self):
        b,w,c,n=copy.deepcopy(self.samples['friendly-mine-second-four']);n['mercenary']['events'][-1]['initial_force']=97374
        self.rejects((b,w,c,n))

    def test_coherent_double_count_total_is_rejected(self):
        b,w,c,n=copy.deepcopy(self.samples['friendly-mine-second-four']);m=n['mercenary'];e=m['events'][-1]
        e['initial_force']+=37;e['force']+=37;m['force']+=37;m['activations'][1]['final_force']+=37
        world=bytearray(w['YTDATA.DAT']);mbf.put(world,3051,81,e['force']);w['YTDATA.DAT']=bytes(world)
        self.rejects((b,w,c,n))

    def test_coherent_overwrite_total_is_rejected(self):
        b,w,c,n=copy.deepcopy(self.samples['friendly-mine-second-four']);m=n['mercenary'];e=m['events'][-1]
        e['initial_force']-=37;e['force']-=37;m['force']-=37;m['activations'][1]['final_force']-=37
        world=bytearray(w['YTDATA.DAT']);mbf.put(world,3051,81,e['force']);w['YTDATA.DAT']=bytes(world)
        self.rejects((b,w,c,n))

    def test_changed_governor_is_rejected_even_if_otherwise_admitted(self):
        for case,value in(('friendly-mine-second-four',-2),('friendly-mine-second-two',-2)):
            b,w,c,n=copy.deepcopy(self.samples[case]);world=bytearray(w['YTDATA.DAT']);mbf.put(world,4054,73,value);w['YTDATA.DAT']=bytes(world)
            self.rejects((b,w,c,n))

    def test_forged_event_governor_or_capture_is_rejected(self):
        for key,value in(('captured',False),('governor',-2)):
            b,w,c,n=copy.deepcopy(self.samples['friendly-mine-second-four']);n['mercenary']['events'][-1][key]=value
            self.rejects((b,w,c,n))

    def test_forged_hold_or_local_force_is_rejected(self):
        for key,value in(('held',True),('force',38),('gate',0),('origin',2999)):
            b,w,c,n=copy.deepcopy(self.samples['friendly-mine-second-four']);n['mercenary']['activations'][0][key]=value
            self.rejects((b,w,c,n))

    def test_forged_incoming_or_merged_amounts_are_rejected(self):
        for key,value in(('incoming_force',97338),('entering_friendly_force',38),('merged',74)):
            b,w,c,n=copy.deepcopy(self.samples['friendly-mine-second-four']);n['mercenary']['events'][-1][key]=value
            self.rejects((b,w,c,n))

    def test_numeric_zero_does_not_replace_source_clear_bytes(self):
        b,w,c,n=copy.deepcopy(self.samples['neutral-half']);world=bytearray(w['YTDATA.DAT']);world[4053*137+129:4053*137+133]=bytes(4);w['YTDATA.DAT']=bytes(world)
        self.rejects((b,w,c,n))

    def test_amount_fraction_and_summary_must_agree(self):
        for target,key,value in(('event','pickup',38),('event','fractional_discard',.75),('summary','merged',74)):
            b,w,c,n=copy.deepcopy(self.samples['friendly-mine-second-four']);m=n['mercenary'];(m['events'][-1]if target=='event'else m)[key]=value
            self.rejects((b,w,c,n))

    def test_missing_later_activation_and_coherent_overwrite_are_rejected(self):
        for case in ('friendly-mine-second-four','friendly-mine-second-four'):
            b,w,c,n=copy.deepcopy(self.samples[case]);n['mercenary']['activations'].pop()
            self.rejects((b,w,c,n))

    def test_changed_derived_route_target_and_rejection_list_are_rejected(self):
        for key,value in (('route',[3000,1810]),('target',1810),('candidates',[3000])):
            b,w,c,n=copy.deepcopy(self.samples['friendly-mine-second-four']);n['mercenary']['activations'][0][key]=value
            self.rejects((b,w,c,n))

    def test_departed_force_cannot_be_reabsorbed_with_coherent_score_total(self):
        b,w,c,n=copy.deepcopy(self.samples['friendly-mine-second-four']);world=bytearray(w['YTDATA.DAT']);m=n['mercenary']
        mbf.put(world,407,81,0);mbf.put(world,407,85,0);mbf.put(world,3051,81,93037)
        w['YTDATA.DAT']=bytes(world);e=m['events'][-1]
        e.update(initial_force=93000,force=93037,entering_friendly_force=37,merged=37,captured=False)
        m.update(final_sectors=[3000],merged=37);m['activations'][1]['final_force']=93037;m['activations'].pop()
        self.assertEqual(m['force'],sum(model._mercenary_map(w['YTDATA.DAT']).values()))
        self.rejects((b,w,c,n))

    def test_coherent_omitted_final_activation_cannot_end_scan_early(self):
        b,w,c,n=copy.deepcopy(self.samples['friendly-mine-second-four']);m=n['mercenary']
        omitted=m['activations'].pop();self.assertEqual((omitted['origin'],omitted['final_sector']),(13,356))
        world=bytearray(w['YTDATA.DAT'])
        mbf.put(world,51+356,81,0);mbf.put(world,51+356,85,0)
        mbf.put(world,51+13,81,37);mbf.put(world,51+13,85,-2)
        w['YTDATA.DAT']=bytes(world);m['final_sectors']=[13,3000]
        self.assertEqual(m['force'],sum(model._mercenary_map(w['YTDATA.DAT']).values()))
        self.rejects((b,w,c,n))

    def test_coherent_neutral_transfer_cannot_be_dropped_or_doubled(self):
        for value in (0,74):
            b,w,c,n=copy.deepcopy(self.samples['neutral-whole']);n['mercenary']['neutral_transferred']=value;n['mercenary']['events'][-1]['neutral_transferred']=value
            self.rejects((b,w,c,n))

    def test_mine_cannot_charge_local_fighters_or_follow_pickup(self):
        b,w,c,n=copy.deepcopy(self.samples['neutral-mine-whole']);n['mercenary']['events'][0]['initial_force']+=37
        self.rejects((b,w,c,n))
        b,w,c,n=copy.deepcopy(self.samples['neutral-mine-whole']);n['mercenary']['events'].reverse()
        self.rejects((b,w,c,n))

    def test_missing_mine_or_inconsistent_damage_is_rejected(self):
        b,w,c,n=copy.deepcopy(self.samples['neutral-mine-whole']);n['mercenary']['events'].pop(0)
        self.rejects((b,w,c,n))
        b,w,c,n=copy.deepcopy(self.samples['neutral-mine-whole']);n['mercenary']['events'][0]['rolls'][0]+=1
        self.rejects((b,w,c,n))


if __name__=='__main__':unittest.main()
