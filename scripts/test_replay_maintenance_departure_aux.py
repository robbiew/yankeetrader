"""Before-only departure public-file synthesis and hostile action-ledger tests."""
import copy
import datetime
import gzip
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import replay_maintenance_departure_aux as model
import replay_maintenance_departure_records as records
from replay_qb_graph import mbf


class DepartureAux(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.samples={};before=records.initial_before()
        for case in records.CASES:
            obs=tuple(json.loads(gzip.decompress(p.read_bytes()))for p in records.observation_paths(case,'observed-a'))
            inputs=tuple((records.combat.inputs_from_observation if i<3 else records.inputs_from_observation)(o)for i,o in enumerate(obs))
            outputs,stats=records.synthesize_chain(before,inputs,case);fixture,_=records.apply_fixture(outputs[2],case)
            for stage,index in((1,3),(2,4)):
                cls.samples[case,stage]=(fixture if stage==1 else outputs[3],outputs[index],inputs[index].clock,stats[index]['npcs'])

    def publish(self,sample):
        b,w,c,n=sample
        return model.synthesize(b,w['YTDATA.DAT'],c.news_date,c.news_clock,c.score_date,c.score_clock,created=n['created'],events=n['events'],mercenary=n['mercenary'])

    def test_all_five_aux_files_equal_all96_native_outputs(self):
        for (case,stage),sample in self.samples.items():
            actual,_=self.publish(sample)
            for mode in records.MODES:
                for n,b in actual.items():
                    expected=gzip.decompress((records.DEFAULT/case/f'child-{stage}'/mode/('after-'+n+'.gz')).read_bytes())
                    with self.subTest(case=case,child=stage,mode=mode,file=n):self.assertEqual(b,expected)

    def test_larger_wanderer_pickup_derives_floor_fraction_and_saved_denominator(self):
        sample=self.samples['occupied-second-four',1];actual,s=self.publish(sample);b,w,c,n=sample
        event=next(e for e in n['mercenary']['events']if e['kind']=='mercenary-pickup')
        self.assertEqual(model._stock(b['YTDATA.DAT'],w['YTDATA.DAT'],4052),189528.296875)
        self.assertEqual((event['raw_stock'],event['pickup'],event['fractional_discard']),(189528.296875,189528,.296875))
        self.assertEqual((s['stock_pickup'],s['fractional_discard'],s['scores'][-2]),(189528,.296875,28686500))
        self.assertIn(b'97337 Mercenaries captured planet The Wanderer!',actual['YTNEWS.DAT'])
        self.assertIn(b'97337 Mercenaries taking 189528 fighters from planet The Wanderer!',actual['YTNEWS.DAT'])
        self.assertIn(b'28,686,500',actual['YTSCORE.ASC']);self.assertEqual(s['percentages'][1],100)
        self.assertNotIn(b'286865 Mercenaries taking',actual['YTNEWS.DAT'])
        at=(4052-1)*137+129;self.assertEqual(w['YTDATA.DAT'][at:at+4],bytes.fromhex('00008000'))

    def test_merge_is_physical_bookkeeping_without_invented_news_text(self):
        sample=self.samples['occupied-friendly-second-four',1];actual,s=self.publish(sample);n=sample[3]
        event=next(e for e in n['mercenary']['events']if e['kind']=='mercenary-merge')
        self.assertEqual((event['initial_force'],event['merged'],event['force']),(97337,37,97374))
        self.assertEqual((s['stock_pickup'],s['silent_merges'],s['modeled_losses'][-2]),(0,1,0))
        self.assertEqual(s['scores'][-2],9737400);self.assertEqual(s['public_events'],len(n['events']))
        self.assertNotIn(b'merg',actual['YTNEWS.DAT'].lower());self.assertNotIn(b'Mercenaries taking',actual['YTNEWS.DAT'])
        self.assertNotIn(b'Mercenaries captured',actual['YTNEWS.DAT']);self.assertNotIn(b'Mercenaries attacking',actual['YTNEWS.DAT'])

    def test_earlier_friendly_defeat_uses_plyr_label_then_same_group_continues(self):
        sample=self.samples['friendly-merge',1];actual,s=self.publish(sample);events=sample[3]['events']
        index=next(i for i,e in enumerate(events)if e['kind']=='defense');event=events[index]
        self.assertGreater(event['force'],0);self.assertEqual(event['defenders'],0)
        self.assertEqual((events[index+1]['group'],events[index+1]['initial_force']),(event['group'],event['force']))
        self.assertEqual(events[index+1]['force'],0)
        self.assertIn(b'(Plyr ftrs dstrd)',actual['YTNEWS.DAT']);self.assertEqual(s['modeled_losses'][-2],37)
        self.assertEqual(s['silent_merges'],0)

    def test_later_defense_mine_and_offense_ledgers_bind_exact_public_stamps(self):
        actual,s=self.publish(self.samples['occupied-second-two',2]);news=actual['YTNEWS.DAT']
        self.assertEqual(s['modeled_losses'][-2],2837+5973+9);self.assertEqual(s['scores'][-2],8851800)
        self.assertEqual(s['modeled_losses'][-1],2794+16)
        self.assertIn(b'(Xannor ftrs dstrd)',news)
        mine=news.index(b'94500 mercenaries hit sector mines in sector 2356!')
        lost=news.index(b'Lost a total of 5973 fighters!');attack=news.index(b'88527 Mercenaries attacking 16 fighters beloning to The Xannor!')
        self.assertLess(mine,lost);self.assertLess(lost,attack);self.assertIn(b'The Mercenaries Won!',news)

    def test_occupied_origin_never_grants_its_unencountered_cache_stock(self):
        for (case,stage),sample in self.samples.items():
            b,w,c,n=sample;actual,_=self.publish(sample)
            self.assertEqual(mbf.get(w['YTDATA.DAT'],4054,129),37 if stage==1 else 40)
            self.assertEqual(mbf.get(w['YTDATA.DAT'],4054,73),0)
            self.assertNotIn(b'Mercenaries captured planet Departure Cache',actual['YTNEWS.DAT'])
            self.assertNotIn(b'fighters from planet Departure Cache',actual['YTNEWS.DAT'])

    def test_separate_vacant_score_clock_and_second_two_four_headers(self):
        actual,_=self.publish(self.samples['vacant-origin',1])
        self.assertTrue(actual['YTNEWS.DAT'].startswith(b'00:00:00 11-05-2026'))
        self.assertIn(b'Last updated at: 11-05-2026 00:00:01',actual['YTSCORE.ASC'])
        for case,clock in(('occupied-second-two',b'00:00:02'),('occupied-second-four',b'00:00:04')):
            actual,_=self.publish(self.samples[case,2]);self.assertTrue(actual['YTNEWS.DAT'].startswith(clock+b' 11-06-2026'))
            self.assertIn(b'11-06-2026 '+clock,actual['YTSCORE.ASC'])

    def test_empty_union_transit_is_admitted_without_inventing_encounters(self):
        sample=self.samples['occupied-friendly-second-four',1];actual,_=self.publish(sample)
        entered=sample[3]['mercenary']['activations'][0]['entered'];self.assertIn(1,entered);self.assertIn(4,entered)
        self.assertNotIn(b'sector 1!',actual['YTNEWS.DAT']);self.assertNotIn(b'sector 4!',actual['YTNEWS.DAT'])

    def test_only_immutable_original_executable_is_read_during_publication(self):
        read=Path.read_bytes;seen=[]
        def checked(path):
            self.assertEqual(path.name,'YTMAINT.EXE');self.assertIn('archive/dos-original',str(path));seen.append(path);return read(path)
        with patch.object(Path,'read_bytes',checked):self.publish(self.samples['occupied-second-four',1])
        self.assertTrue(seen)

    def test_positive_surviving_defender_counter_inflation_rejected(self):
        sample=self.samples['occupied-second-two',2]
        for index,event in enumerate(sample[3]['events']):
            if event['kind']!='defense':continue
            self.assertGreater(event['defenders'],0)
            for extra in(1,5000):
                b,w,c,n=copy.deepcopy(sample);n['events'][index]['defender_damage']+=extra
                with self.subTest(group=event['group'],extra=extra),self.assertRaisesRegex(ValueError,'surviving defender'):self.publish((b,w,c,n))

    def test_surviving_attacker_counter_or_two_dead_winners_rejected(self):
        sample=self.samples['friendly-merge',1];index=next(i for i,e in enumerate(sample[3]['events'])if e['kind']=='defense')
        b,w,c,n=copy.deepcopy(sample);n['events'][index]['x_damage']+=1
        with self.assertRaisesRegex(ValueError,'surviving attacker'):self.publish((b,w,c,n))
        b,w,c,n=copy.deepcopy(sample);n['events'][index]['force']=0
        with self.assertRaisesRegex(ValueError,'positive winner'):self.publish((b,w,c,n))

    def test_forged_merge_count_or_missing_merge_cannot_create_force(self):
        sample=self.samples['occupied-friendly-second-four',1]
        for key,value in(('merged',36),('initial_defenders',36),('force',97375),('owner',-1),('losses',1)):
            b,w,c,n=copy.deepcopy(sample);n['mercenary']['events'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.publish((b,w,c,n))
        b,w,c,n=copy.deepcopy(sample);n['mercenary']['events']=[]
        with self.assertRaises(ValueError):self.publish((b,w,c,n))

    def test_stock_fraction_rounding_or_force_inflation_rejected(self):
        sample=self.samples['occupied-second-four',1]
        for key,value in(('raw_stock',189529.296875),('pickup',189529),('fractional_discard',0),('force',286866),('planet_name','Departure Cache'),('planet_slot',3)):
            b,w,c,n=copy.deepcopy(sample);n['mercenary']['events'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.publish((b,w,c,n))

    def test_source_economy_change_cannot_hide_behind_unchanged_stock(self):
        b,w,c,n=copy.deepcopy(self.samples['occupied-second-four',1]);data=bytearray(b['YTDATA.DAT']);mbf.put(data,4052,45,mbf.get(data,4052,45)+100);b['YTDATA.DAT']=bytes(data)
        with self.assertRaises(ValueError):self.publish((b,w,c,n))
        b,w,c,n=copy.deepcopy(self.samples['occupied-midnight',2]);data=bytearray(b['YTDATA.DAT']);mbf.put(data,4054,45,2);b['YTDATA.DAT']=bytes(data)
        with self.assertRaisesRegex(ValueError,'stock'):self.publish((b,w,c,n))

    def test_positive_offensive_winner_and_real_mine_residue_required(self):
        sample=self.samples['occupied-second-two',2]
        for index,key,value in((0,'losses',5972),(0,'mines',1),(1,'force',0),(1,'defender_losses',15)):
            b,w,c,n=copy.deepcopy(sample);n['mercenary']['events'][index][key]=value
            with self.subTest(index=index,key=key),self.assertRaises(ValueError):self.publish((b,w,c,n))
        b,w,c,n=copy.deepcopy(sample);n['mercenary']['events'].reverse()
        with self.assertRaises(ValueError):self.publish((b,w,c,n))

    def test_route_activation_and_final_total_are_bound_to_physical_world(self):
        sample=self.samples['occupied-friendly-second-four',1]
        for key,value in(('force',97338),('origin',2999),('gate',-1),('entered',[2367]),('final_force',97375)):
            b,w,c,n=copy.deepcopy(sample);n['mercenary']['activations'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.publish((b,w,c,n))
        b,w,c,n=copy.deepcopy(sample);n['mercenary']['final_sectors']=[3000]
        with self.assertRaises(ValueError):self.publish((b,w,c,n))

    def test_unknown_date_clock_private_stream_creation_or_large_force_rejected(self):
        b,w,c,n=self.samples['occupied-midnight',1]
        for date,clock,created in((datetime.date(2026,11,6),c.news_clock,()),(c.news_date,'25:00:00',()),(c.news_date,c.news_clock,('base',))):
            with self.subTest(date=date,clock=clock),self.assertRaises(ValueError):model.synthesize(b,w['YTDATA.DAT'],date,clock,c.score_date,c.score_clock,created=created,events=n['events'],mercenary=n['mercenary'])
        b,w,c,n=copy.deepcopy(self.samples['occupied-midnight',1]);b['YTRMSG.DAT']=b'private'
        with self.assertRaises(ValueError):self.publish((b,w,c,n))
        b,w,c,n=copy.deepcopy(self.samples['occupied-second-four',2]);data=bytearray(w['YTDATA.DAT']);mbf.put(data,51+93,81,400001);w['YTDATA.DAT']=bytes(data)
        with self.assertRaises(ValueError):self.publish((b,w,c,n))

    def test_names_news_rotation_and_world_bytes_are_not_rewritten(self):
        for sample in self.samples.values():
            b,w,c,n=sample;saved=bytes(w['YTDATA.DAT']);actual,_=self.publish(sample)
            self.assertEqual(actual['YTNAME.DAT'],b['YTNAME.DAT']);self.assertEqual(actual['YTYNEWS.DAT'],b['YTNEWS.DAT'])
            self.assertEqual(actual['YTRMSG.DAT'],b'');self.assertEqual(w['YTDATA.DAT'],saved)

if __name__=='__main__':unittest.main()
