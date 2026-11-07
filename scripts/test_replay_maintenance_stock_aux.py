"""Exact original stock receipts from modeled worlds and hostile ledger checks."""
import copy
from dataclasses import replace
import datetime
from fractions import Fraction
import gzip
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import replay_maintenance_stock_aux as model
import replay_maintenance_stock_records as records
from replay_qb_graph import mbf


class StockAux(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.samples={};before=records.initial_before()
        for case in records.CASES:
            observations=tuple(json.loads(gzip.decompress(p.read_bytes()))for p in records.observation_paths(case,'observed-a'))
            inputs=tuple((records.combat.inputs_from_observation if i<3 else records.inputs_from_observation)(o)for i,o in enumerate(observations))
            outputs,stats=records.synthesize_chain(before,inputs,case);fixture,_=records.apply_fixture(outputs[2],case)
            cls.samples[case]=(fixture,outputs[3],inputs[3].clock,stats[3]['npcs'])

    def publish(self,sample):
        b,w,c,n=sample
        return model.synthesize(b,w['YTDATA.DAT'],c.news_date,c.news_clock,c.score_date,c.score_clock,created=n['created'],events=n['events'],mercenary=n['mercenary'])

    def test_all_five_auxiliary_files_equal_all72_native_runs(self):
        for case,sample in self.samples.items():
            files,_=self.publish(sample)
            for mode in records.MODES:
                for name,actual in files.items():
                    expected=gzip.decompress((records.DEFAULT/case/'child-1'/mode/('after-'+name+'.gz')).read_bytes())
                    with self.subTest(case=case,mode=mode,file=name):self.assertEqual(actual,expected)

    def test_positive_below_one_captures_but_suppresses_taking_zero(self):
        for case in('quarter','half','three-quarter','below-one'):
            files,stats=self.publish(self.samples[case]);raw=Fraction(*records.CASES[case])
            self.assertEqual(stats['stock_pickup'],0);self.assertEqual(stats['scores'][-2],9733700)
            self.assertEqual(Fraction.from_float(stats['fractional_discard']),raw)
            self.assertIn(b'97337 Mercenaries captured planet Gateway Cache!',files['YTNEWS.DAT'])
            self.assertNotIn(b'Mercenaries taking',files['YTNEWS.DAT'])

    def test_odd_half_and_above_one_floor_before_receipts(self):
        for case,amount in(('odd-half',1),('even-half',2),('above-one',1),('signed-boundary-half',32767)):
            files,stats=self.publish(self.samples[case])
            self.assertEqual(stats['stock_pickup'],amount);self.assertEqual(stats['scores'][-2],100*(97337+amount))
            self.assertIn(b'97337 Mercenaries taking '+str(amount).encode()+b' fighters from planet Gateway Cache!',files['YTNEWS.DAT'])
            self.assertNotIn(str(97337+amount).encode()+b' Mercenaries taking',files['YTNEWS.DAT'])

    def test_large_half_neighbors_and_odd_half_keep_actual_saved_denominator(self):
        for case,amount,fraction in(('large-below',189528,Fraction(31,64)),('large-half',189528,Fraction(1,2)),('large-above',189528,Fraction(33,64)),('large-odd-half',189529,Fraction(1,2))):
            files,stats=self.publish(self.samples[case]);self.assertEqual(stats['stock_pickup'],amount)
            self.assertEqual(Fraction.from_float(stats['fractional_discard']),fraction)
            self.assertEqual(stats['scores'][-2],100*(97337+amount));self.assertEqual(stats['percentages'][1],100)
            self.assertIn(f'{100*(97337+amount):,}'.encode(),files['YTSCORE.ASC'])
            self.assertIn(b'97337 Mercenaries taking '+str(amount).encode(),files['YTNEWS.DAT'])

    def test_every_fraction_is_discarded_and_complete_stock_clear_is_exact(self):
        for case,sample in self.samples.items():
            _,world,_,npc=sample;files,stats=self.publish(sample);event=npc['mercenary']['events'][0]
            raw=Fraction(*records.CASES[case]);whole=raw.numerator//raw.denominator
            self.assertEqual(Fraction(event['pickup'])+Fraction.from_float(event['fractional_discard']),raw)
            self.assertEqual(stats['stock_pickup'],whole)
            at=(4054-1)*137+129;self.assertEqual(world['YTDATA.DAT'][at:at+4],bytes.fromhex('00008000'))
            origin=(2419-1)*137;self.assertEqual(world['YTDATA.DAT'][origin+81:origin+89],bytes.fromhex('0000280000002800'))
            self.assertEqual(mbf.get(world['YTDATA.DAT'],4054,73),0);self.assertEqual(mbf.get(world['YTDATA.DAT'],4054,77),505000)

    def test_only_original_executable_is_opened_during_publication(self):
        read=Path.read_bytes;seen=[]
        def checked(path):
            self.assertEqual(path.name,'YTMAINT.EXE');self.assertIn('archive/dos-original',str(path));seen.append(path);return read(path)
        with patch.object(Path,'read_bytes',checked):self.publish(self.samples['large-odd-half'])
        self.assertTrue(seen)

    def test_coherent_wrong_rounding_still_rejected_by_source_stock(self):
        for case in('three-quarter','odd-half','large-above','large-odd-half'):
            b,w,c,n=copy.deepcopy(self.samples[case]);event=n['mercenary']['events'][0]
            wrong=event['pickup']+1;event['pickup']=wrong;event['force']+=1
            n['mercenary']['force']+=1;n['mercenary']['pickup']=wrong;n['mercenary']['activations'][0]['final_force']+=1
            data=bytearray(w['YTDATA.DAT']);mbf.put(data,3051,81,event['force']);w['YTDATA.DAT']=bytes(data)
            with self.subTest(case=case),self.assertRaisesRegex(ValueError,'source-grown positive stock'):self.publish((b,w,c,n))

    def test_false_fraction_raw_stock_or_preaddition_stamp_rejected(self):
        for key,value in(('raw_stock',189529.5),('fractional_discard',0),('initial_force',97338),('conversion','nearest-even'),('planet_name','The Wanderer'),('planet_slot',1)):
            b,w,c,n=copy.deepcopy(self.samples['large-half']);n['mercenary']['events'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.publish((b,w,c,n))

    def test_production_uses_before_rates_and_bank_not_cleared_target(self):
        for offset,value in((45,1),(117,500)):
            b,w,c,n=copy.deepcopy(self.samples['half']);data=bytearray(b['YTDATA.DAT']);mbf.put(data,4054,offset,value);b['YTDATA.DAT']=bytes(data)
            with self.subTest(offset=offset),self.assertRaises(ValueError):self.publish((b,w,c,n))

    def test_raw_numeric_zero_cannot_be_normalized_or_fraction_retained(self):
        for raw in(bytes(4),mbf.enc(.5)):
            b,w,c,n=copy.deepcopy(self.samples['half']);data=bytearray(w['YTDATA.DAT']);at=(4054-1)*137+129;data[at:at+4]=raw;w['YTDATA.DAT']=bytes(data)
            with self.subTest(raw=raw.hex()),self.assertRaisesRegex(ValueError,'exact source8472'):self.publish((b,w,c,n))
        b,w,c,n=copy.deepcopy(self.samples['half']);data=bytearray(w['YTDATA.DAT']);at=(2419-1)*137+81;data[at:at+4]=bytes(4);w['YTDATA.DAT']=bytes(data)
        with self.assertRaisesRegex(ValueError,'source859e'):self.publish((b,w,c,n))

    def test_ground_transfer_or_retitling_is_not_part_of_pickup(self):
        for record,offset,value in((4054,77,504999),(4054,73,-2),(3051,93,1)):
            b,w,c,n=copy.deepcopy(self.samples['large-half']);data=bytearray(w['YTDATA.DAT']);mbf.put(data,record,offset,value);w['YTDATA.DAT']=bytes(data)
            with self.subTest(record=record,offset=offset),self.assertRaises(ValueError):self.publish((b,w,c,n))

    def test_invented_actions_and_wrong_activation_or_summary_rejected(self):
        sample=self.samples['quarter']
        for change in('extra-event','held','wrong-origin','wrong-force','wrong-total','wrong-route'):
            b,w,c,n=copy.deepcopy(sample);m=n['mercenary'];a=m['activations'][0]
            if change=='extra-event':m['events'].append(copy.deepcopy(m['events'][0]))
            elif change=='held':a['held']=True
            elif change=='wrong-origin':a['origin']=2367
            elif change=='wrong-force':a['final_force']+=1
            elif change=='wrong-total':m['pickup']=1
            else:a['entered']=[2999]
            with self.subTest(change=change),self.assertRaises(ValueError):self.publish((b,w,c,n))

    def test_xannor_home_ground_and_actual_faction_losses_remain_bound(self):
        files,stats=self.publish(self.samples['half']);self.assertEqual(stats['modeled_losses'],{-1:2696,-2:0,0:0})
        self.assertEqual(stats['scores'][-1],227000)
        for key,value in(('force',1),('initial_force',1),('ground_spent',0),('planet_name','Gateway Cache')):
            b,w,c,n=copy.deepcopy(self.samples['half']);n['events'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.publish((b,w,c,n))

    def test_news_and_score_use_separate_explicit_clocks(self):
        b,w,c,n=self.samples['half'];normal,_=self.publish((b,w,c,n));clock=replace(c,score_clock='00:00:01')
        changed,_=self.publish((b,w,clock,n));self.assertEqual(changed['YTNEWS.DAT'],normal['YTNEWS.DAT'])
        self.assertNotEqual(changed['YTSCORE.ASC'],normal['YTSCORE.ASC']);self.assertIn(b'11-05-2026 00:00:01',changed['YTSCORE.ASC'])
        for date,newsclock,scoredate,scoreclock in((datetime.date(2026,11,6),c.news_clock,c.score_date,c.score_clock),(c.news_date,'25:00:00',c.score_date,c.score_clock),(c.news_date,c.news_clock,datetime.date(2026,11,4),c.score_clock)):
            with self.assertRaises(ValueError):model.synthesize(b,w['YTDATA.DAT'],date,newsclock,scoredate,scoreclock,events=n['events'],mercenary=n['mercenary'])

    def test_names_yesterday_news_empty_private_and_world_are_preserved(self):
        for sample in self.samples.values():
            b,w,c,n=sample;saved=bytes(w['YTDATA.DAT']);actual,_=self.publish(sample)
            self.assertEqual(actual['YTNAME.DAT'],b['YTNAME.DAT']);self.assertEqual(actual['YTYNEWS.DAT'],b['YTNEWS.DAT'])
            self.assertEqual(actual['YTRMSG.DAT'],b'');self.assertEqual(w['YTDATA.DAT'],saved)
        b,w,c,n=copy.deepcopy(self.samples['half']);b['YTRMSG.DAT']=b'private'
        with self.assertRaises(ValueError):self.publish((b,w,c,n))
        b,w,c,n=self.samples['half']
        with self.assertRaises(ValueError):model.synthesize(b,w['YTDATA.DAT'],c.news_date,c.news_clock,c.score_date,c.score_clock,created=('wanderer',),events=n['events'],mercenary=n['mercenary'])

if __name__=='__main__':unittest.main()
