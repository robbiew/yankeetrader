"""Source-literal gateway publication from complete before-only modeled worlds."""
import copy
import datetime
import gzip
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import replay_maintenance_gateway_aux as model
import replay_maintenance_gateway_records as records
from replay_qb_graph import mbf


class GatewayAux(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.samples={}
        before=records.initial_before()
        for case in records.CASES:
            paths=records.observation_paths(case,'observed-a')
            obs=tuple(json.loads(gzip.decompress(p.read_bytes()))for p in paths)
            inputs=tuple((records.combat.inputs_from_observation if i<3 else records.inputs_from_observation)(ob)for i,ob in enumerate(obs))
            outputs,stats=records.synthesize_chain(before,inputs,case)
            fixture,_=records.apply_fixture(outputs[2],case)
            for stage,index in((1,3),(2,4)):
                cls.samples[case,stage]=(fixture if stage==1 else outputs[3],outputs[index],inputs[index].clock,stats[index]['npcs'])

    def publish(self,sample):
        before,world,c,npc=sample
        return model.synthesize(before,world['YTDATA.DAT'],c.news_date,c.news_clock,c.score_date,c.score_clock,created=npc['created'],events=npc['events'],mercenary=npc['mercenary'])

    def test_all_five_files_equal_all72_native_outputs(self):
        for (case,stage),sample in self.samples.items():
            actual,_=self.publish(sample)
            for mode in records.MODES:
                for n,b in actual.items():
                    expected=gzip.decompress((records.DEFAULT/case/f'child-{stage}'/mode/('after-'+n+'.gz')).read_bytes())
                    with self.subTest(case=case,child=stage,mode=mode,file=n):self.assertEqual(b,expected)

    def test_mine_then_pickup_uses_preaddition_stamp_and_saved_denominator(self):
        actual,s=self.publish(self.samples['mine-pickup',1]);news=actual['YTNEWS.DAT']
        self.assertEqual(s['modeled_losses'],{-1:2696,-2:712,0:0});self.assertEqual(s['stock_pickup'],37)
        self.assertEqual(s['scores'],{-1:227000,-2:9666200});self.assertEqual(s['percentages'][1],100)
        mine=news.index(b'97337 mercenaries hit sector mines in sector 3000!')
        lost=news.index(b'Lost a total of 712 fighters!')
        capture=news.index(b'96625 Mercenaries captured planet Gateway Cache!')
        taking=news.index(b'96625 Mercenaries taking 37 fighters from planet Gateway Cache!')
        self.assertLess(mine,lost);self.assertLess(lost,capture);self.assertLess(capture,taking)
        self.assertNotIn(b'96662 Mercenaries taking',news)

    def test_empty_stock_capture_has_no_zero_taking_line(self):
        actual,s=self.publish(self.samples['empty',1])
        self.assertIn(b'97337 Mercenaries captured planet Gateway Cache!',actual['YTNEWS.DAT'])
        self.assertNotIn(b'Mercenaries taking',actual['YTNEWS.DAT']);self.assertEqual(s['stock_pickup'],0)

    def test_guarded_mine_offense_retains_stock_and_suppresses_capture(self):
        actual,s=self.publish(self.samples['mine-guarded',1]);news=actual['YTNEWS.DAT']
        self.assertEqual(s['modeled_losses'],{-1:2733,-2:558,0:0});self.assertEqual(s['stock_pickup'],0)
        self.assertIn(b'Lost a total of 518 fighters!',news)
        self.assertIn(b'96819 Mercenaries attacking 37 fighters beloning to The Xannor!',news)
        self.assertIn(b'The Mercenaries Won!',news)
        self.assertNotIn(b'Mercenaries taking',news);self.assertNotIn(b'Mercenaries captured',news)

    def test_fatal_first_mine_prints_original_typo_and_no_loss_or_pickup(self):
        actual,s=self.publish(self.samples['fatal-before-pickup',1]);news=actual['YTNEWS.DAT']
        self.assertEqual(s['modeled_losses'][-2],1);self.assertEqual(s['scores'][-2],0)
        self.assertIn(b'The mercenariers were killed!',news)
        self.assertNotIn(b'Lost a total of',news);self.assertNotIn(b'Mercenaries taking',news)
        self.assertNotIn(b'Mercenaries captured',news)

    def test_second_day_no_repeated_pickup_and_exact_rotation(self):
        for case in records.CASES:
            before,world,c,n=self.samples[case,2];actual,s=self.publish(self.samples[case,2])
            self.assertEqual(actual['YTYNEWS.DAT'],before['YTNEWS.DAT']);self.assertEqual(actual['YTNAME.DAT'],before['YTNAME.DAT'])
            self.assertEqual(actual['YTRMSG.DAT'],b'');self.assertEqual(s['stock_pickup'],0);self.assertEqual(s['public_events'],0)
            self.assertNotIn(b'Mercenaries taking',actual['YTNEWS.DAT'])
            self.assertEqual(mbf.get(world['YTDATA.DAT'],4054,129),mbf.get(before['YTDATA.DAT'],4054,129)+3)

    def test_synthesis_reads_only_immutable_original_executable(self):
        read=Path.read_bytes;seen=[]
        def guarded(path):
            self.assertEqual(path.name,'YTMAINT.EXE');seen.append(path);return read(path)
        with patch.object(Path,'read_bytes',guarded):self.publish(self.samples['mine-pickup',1])
        self.assertTrue(seen)

    def test_forged_mine_casualty_residue_or_event_order_rejected(self):
        for key,value in(('losses',711),('mines',1),('initial_force',97336),('force',96624)):
            sample=copy.deepcopy(self.samples['mine-pickup',1]);sample[3]['mercenary']['events'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.publish(sample)
        sample=copy.deepcopy(self.samples['mine-pickup',1]);sample[3]['mercenary']['events'].reverse()
        with self.assertRaises(ValueError):self.publish(sample)

    def test_forged_pickup_stamp_amount_or_identity_rejected(self):
        for key,value in(('initial_force',96662),('pickup',36),('force',96661),('planet_name','Other'),('planet_slot',2),('captured',False)):
            sample=copy.deepcopy(self.samples['mine-pickup',1]);sample[3]['mercenary']['events'][-1][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.publish(sample)

    def test_unprinted_battle_loss_and_forged_final_physical_claim_rejected(self):
        for key,value in(('losses',39),('force',0),('defender_losses',36),('defender_name','Other')):
            sample=copy.deepcopy(self.samples['mine-guarded',1]);sample[3]['mercenary']['events'][-1][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.publish(sample)
        sample=copy.deepcopy(self.samples['mine-guarded',1]);sample[3]['mercenary']['final_sectors']=[3000]
        with self.assertRaises(ValueError):self.publish(sample)

    def test_title_stock_or_private_change_rejected(self):
        for record,offset,value in((4054,73,-2),(4054,129,1),(3051,93,2)):
            b,w,c,n=copy.deepcopy(self.samples['pickup',1]);data=bytearray(w['YTDATA.DAT']);mbf.put(data,record,offset,value);w['YTDATA.DAT']=bytes(data)
            with self.subTest(offset=offset),self.assertRaises(ValueError):self.publish((b,w,c,n))
        sample=copy.deepcopy(self.samples['empty',1]);sample[0]['YTRMSG.DAT']=b'private'
        with self.assertRaises(ValueError):self.publish(sample)

    def test_stock_validation_derives_before_rates_instead_of_observed_three(self):
        b,w,c,n=copy.deepcopy(self.samples['guarded-pickup',2]);data=bytearray(b['YTDATA.DAT']);mbf.put(data,4054,45,2);b['YTDATA.DAT']=bytes(data)
        with self.assertRaisesRegex(ValueError,'stock production'):self.publish((b,w,c,n))
        for rate in(-1,11):
            b,w,c,n=copy.deepcopy(self.samples['guarded-pickup',2]);data=bytearray(b['YTDATA.DAT']);mbf.put(data,4054,45,rate);b['YTDATA.DAT']=bytes(data)
            with self.subTest(rate=rate),self.assertRaisesRegex(ValueError,'bounded gateway rates'):self.publish((b,w,c,n))

    def test_unknown_calendar_creation_or_event_rejected(self):
        b,w,c,n=self.samples['empty',1]
        with self.assertRaises(ValueError):model.synthesize(b,w['YTDATA.DAT'],c.news_date,c.news_clock,c.score_date,c.score_clock,created=('wanderer',),events=n['events'],mercenary=n['mercenary'])
        with self.assertRaises(ValueError):model.synthesize(b,w['YTDATA.DAT'],datetime.date(2026,11,6),c.news_clock,c.score_date,c.score_clock,events=n['events'],mercenary=n['mercenary'])
        sample=copy.deepcopy(self.samples['empty',1]);sample[3]['events'][0]['kind']='unknown'
        with self.assertRaises(ValueError):self.publish(sample)

if __name__=='__main__':unittest.main()
