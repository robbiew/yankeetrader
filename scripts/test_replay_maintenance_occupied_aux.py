"""Formatter/admission controls with independently constructed modeled worlds.

No observed after-record is used as a synthesis input here. Full-pipeline native
comparisons belong to the separate occupied-record replay caller tests.
"""
import copy
import datetime
from pathlib import Path
import unittest
from unittest.mock import patch

import replay_maintenance_occupied_aux as aux
from replay_qb_graph import mbf
import verify_maintenance_occupied as evidence

DATE=datetime.date(2026,11,2)
ROOT=Path(__file__).resolve().parents[1]


def put(world,record,offset,value):
    at=(record-1)*137+offset;world[at:at+4]=mbf.enc(value)


def fixture(case='route-mercenary-37',*,xannor=9963,mercenary=0,neutral=0):
    before=evidence.before_inputs(case);world=bytearray(before['YTDATA.DAT'])
    for record in range(2,52):put(world,record,109,-1)
    for sector in range(1,3001):
        put(world,51+sector,81,0);put(world,51+sector,85,0)
    for sector,force,owner in((849,xannor,-1),(3000,mercenary,-2),(854,neutral,0)):
        if force:put(world,51+sector,81,force);put(world,51+sector,85,owner)
    for record,text in((4052,'The Wanderer'),(4150,'Mercenary Base'),(4151,'Xannoron')):
        at=(record-1)*137;world[at:at+41]=text.encode().ljust(41,b' ');put(world,record,85,len(text))
    return before,bytes(world)


def defenses():
    return [dict(kind='defense',group=2,sector=854,initial_force=15,force=0,initial_defenders=37,defenders=27,owner=-2,x_damage=15,defender_damage=10),
            dict(kind='defense',group=3,sector=854,initial_force=100,force=78,initial_defenders=27,defenders=0,owner=-2,x_damage=22,defender_damage=27)]


class OccupiedAuxiliaryTests(unittest.TestCase):
    def invoke(self,case='route-mercenary-37',*,events=None,world=None,before=None,**kw):
        b,w=fixture(case)if before is None or world is None else(before,world)
        return aux.synthesize(b if before is None else before,w if world is None else world,
                              kw.pop('news_date',DATE),kw.pop('news_clock','00:00:00'),
                              kw.pop('score_date',DATE),kw.pop('score_clock','00:00:00'),
                              events=defenses()if events is None else events,**kw)

    def test_five_auxiliary_outputs_and_private_separation(self):
        before,_=fixture();actual,stats=self.invoke()
        self.assertEqual(set(actual),{'YTNAME.DAT','YTNEWS.DAT','YTYNEWS.DAT','YTRMSG.DAT','YTSCORE.ASC'})
        self.assertEqual(actual['YTNAME.DAT'],before['YTNAME.DAT'])
        self.assertEqual(actual['YTYNEWS.DAT'],before['YTNEWS.DAT'])
        self.assertEqual(actual['YTRMSG.DAT'],b'')
        self.assertEqual(stats['modeled_losses'],{-1:37,-2:37})

    def test_complete_before_only_callers_match_native_auxiliary_files(self):
        import gzip,json
        import replay_maintenance_occupied_records as records
        for case in records.ADMITTED_INPUTS.values():
            with self.subTest(case=case):
                folder=records.DEFAULT/case/'observed-a'
                observed=json.loads(gzip.decompress((folder/'host-time.json.gz').read_bytes()))
                actual,_=records.synthesize(records.before_inputs(case),records.inputs_from_observation(observed))
                # Expected output opens only after the full independent synthesis.
                for output in ('YTNAME.DAT','YTNEWS.DAT','YTYNEWS.DAT','YTRMSG.DAT','YTSCORE.ASC'):
                    expected=gzip.decompress((folder/('after-'+output+'.gz')).read_bytes())
                    self.assertEqual(actual[output],expected)

    def test_original_misleading_source_receipt_labels_preserved(self):
        actual,_=self.invoke();news=actual['YTNEWS.DAT']
        self.assertIn(b' *** Mercenaries: lost 15, dstrd 10 (Xannor ftrs dstrd)\r\n',news)
        self.assertIn(b' *** Mercenaries: lost 22, dstrd 27 (Plyr ftrs dstrd)\r\n',news)
        self.assertLess(news.index(b'lost 15'),news.index(b'lost 22'))
        self.assertLess(news.index(b'lost 22'),news.index(b'  -  Mercenary Report:'))

    def test_source_only_original_file_read_guard(self):
        before,world=fixture();read=Path.read_bytes;allowed=ROOT/'archive/dos-original/YTMAINT.EXE'
        def guard(path):
            if path!=allowed:raise AssertionError('target/unrelated file read: '+str(path))
            return read(path)
        with patch.object(Path,'read_bytes',guard):
            actual,_=self.invoke(before=before,world=world)
        self.assertTrue(actual['YTSCORE.ASC'].endswith(b'\x1a'))

    def test_separate_news_and_score_clock_sources(self):
        actual,_=self.invoke(news_clock='01:02:03',score_clock='04:05:06')
        self.assertTrue(actual['YTNEWS.DAT'].startswith(b'01:02:03 11-02-2026'))
        self.assertIn(b'Last updated at: 11-02-2026 04:05:06',actual['YTSCORE.ASC'])

    def test_positive_mercenary_score_percentage_from_saved_forces(self):
        before,world=fixture('route-mercenary-100000',xannor=5148,mercenary=97525)
        events=[dict(kind='defense',group=2,sector=854,initial_force=4852,force=0,initial_defenders=100000,defenders=97525,owner=-2,x_damage=4852,defender_damage=2475)]
        actual,stats=self.invoke(before=before,world=world,events=events)
        self.assertEqual(stats['scores'],{-1:514800,-2:9752500})
        self.assertIn(b'5.28%',actual['YTSCORE.ASC']);self.assertIn(b'100.00%',actual['YTSCORE.ASC'])

    def test_neutral_force_is_conserved_but_unscored(self):
        before,world=fixture('route-neutral-37',xannor=10000,neutral=37)
        _,stats=self.invoke(before=before,world=world,events=[])
        self.assertEqual(stats['scores'],{-1:1000000,-2:0});self.assertEqual(stats['physical'][1][0],37)

    def test_neutral_planet_name_and_dead_force_receipts(self):
        before,world=fixture('route-planet-neutral',xannor=4022)
        events=[dict(kind='planet',group=2,sector=854,planet_name='Route Haven',initial_force=5978,force=0)]
        actual,_=self.invoke(before=before,world=world,events=events)
        self.assertIn(b' *** 5978 Xannor attacked the planet "Route Haven"\r\n *** Xannor fighters destroyed!\r\n',actual['YTNEWS.DAT'])

    def test_unknown_event_kind_rejected(self):
        with self.assertRaisesRegex(ValueError,'unknown modeled'):self.invoke(events=[dict(kind='private')])

    def test_event_order_rejected(self):
        events=defenses();events.reverse()
        with self.assertRaisesRegex(ValueError,'source-ordered'):self.invoke(events=events)

    def test_dead_group_cannot_act_again(self):
        events=defenses();events[1]['group']=2
        with self.assertRaisesRegex(ValueError,'source-ordered'):self.invoke(events=events)

    def test_unknown_owner_rejected(self):
        events=defenses();events[0]['owner']=0
        with self.assertRaisesRegex(ValueError,'only Mercenary'):self.invoke(events=events)

    def test_both_survivors_rejected(self):
        events=defenses();events[0]['force']=1
        with self.assertRaisesRegex(ValueError,'one surviving side'):self.invoke(events=events)

    def test_raw_counter_cannot_understate_capped_loss(self):
        events=defenses();events[0]['x_damage']=1
        with self.assertRaisesRegex(ValueError,'cover actual'):self.invoke(events=events)

    def test_unexplained_physical_force_rejected(self):
        before,world=fixture(xannor=9964)
        with self.assertRaisesRegex(ValueError,'conserve each physical'):self.invoke(before=before,world=world)

    def test_fractional_saved_force_rejected(self):
        before,world=fixture();world=bytearray(world);put(world,900,81,.5)
        with self.assertRaisesRegex(ValueError,'bounded whole'):self.invoke(before=before,world=bytes(world))

    def test_human_assets_rejected(self):
        before,world=fixture();world=bytearray(world);put(world,2,85,1)
        with self.assertRaisesRegex(ValueError,'inactive human'):self.invoke(before=before,world=bytes(world))

    def test_tax_funded_hiring_rejected(self):
        before,world=fixture();data=bytearray(before['YTDATA.DAT']);put(data,3052,89,1);before={**before,'YTDATA.DAT':bytes(data)}
        with self.assertRaisesRegex(ValueError,'tax-funded'):self.invoke(before=before,world=world)

    def test_unlinked_planet_event_rejected(self):
        before,world=fixture('route-neutral-37',xannor=4022,neutral=37)
        event=dict(kind='planet',group=2,sector=854,planet_name='Route Haven',initial_force=5978,force=0)
        with self.assertRaisesRegex(ValueError,'neutral Route Haven'):self.invoke(before=before,world=world,events=[event])

    def test_missing_mercenary_before_context_rejected(self):
        before,world=fixture('route-neutral-37',xannor=9963,neutral=37)
        with self.assertRaises(ValueError):self.invoke(before=before,world=world)

    def test_event_names_cannot_select_arbitrary_public_text(self):
        event=dict(kind='planet',group=2,sector=854,planet_name='Injected',initial_force=5978,force=0)
        with self.assertRaisesRegex(ValueError,'only measured'):self.invoke(events=[event])

    def test_unmeasured_active_planet_before_assets_rejected(self):
        before,world=fixture('route-planet-friendly',xannor=10000)
        data=bytearray(before['YTDATA.DAT']);put(data,4053,45,2000)
        before={**before,'YTDATA.DAT':bytes(data)}
        with self.assertRaisesRegex(ValueError,'clean active-planet'):
            self.invoke(before=before,world=world,events=[])

    def test_halfway_percentages_remain_explicitly_unsupported(self):
        with self.assertRaisesRegex(ValueError,'halfway percentage'):
            aux._scoreboard(aux.original_literals(),DATE,'00:00:00',{-1:1,-2:20000})

    def test_three_raw_inputs_and_immutable_world_required(self):
        before,world=fixture()
        with self.assertRaisesRegex(ValueError,'three raw'):self.invoke(before={**before,'extra':b''})
        with self.assertRaisesRegex(ValueError,'three raw'):self.invoke(world=bytearray(world))

    def test_explicit_dates_and_valid_clocks_required(self):
        with self.assertRaisesRegex(ValueError,'calendar dates'):self.invoke(news_date='2026-11-02')
        with self.assertRaises(ValueError):self.invoke(score_clock='25:00:00')


if __name__=='__main__':unittest.main()
