"""Independent formatter/admission tests for the measured evolved chain."""
import copy
import datetime
import gzip
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import replay_maintenance_evolved_aux as aux
from replay_qb_graph import mbf
from verify_maintenance_convergence import initial_inputs

ROOT=Path(__file__).resolve().parents[1]
DATE=datetime.date(2026,11,2)


def put(world,record,offset,value):
    at=(record-1)*137+offset;world[at:at+4]=mbf.enc(value)


def set_name(world,record,text,owner):
    at=(record-1)*137;world[at:at+41]=text.ljust(41,b' ');put(world,record,85,len(text));put(world,record,73,owner)


def initial_worlds():
    before=initial_inputs();world=bytearray(before['YTDATA.DAT'])
    for record in range(2,52):put(world,record,109,-1)
    for slot,sector,text,owner in((1,2787,b'The Wanderer',0),(99,2177,b'Mercenary Base',-2),(100,849,b'Xannoron',-1)):
        set_name(world,4051+slot,text,owner);put(world,51+sector,93,slot)
    return before,bytes(world)


def evolved_worlds():
    before,world=initial_worlds()
    side,_=aux.synthesize(before,world,DATE,'00:00:00',DATE,'00:00:01',created=aux.CREATED)
    return {'YTDATA.DAT':world,**side},world


def clocks(path):
    """Test-only generic source decoder, with no fixed missing-home inventory."""
    from verify_maintenance_clock_matrix import event_pair,native_time_text
    observed=json.loads(gzip.decompress(path.read_bytes()));values={}
    for event in observed['events']:
        row=copy.deepcopy(event)
        for side in('before','after'):row[side].pop('rng_raw')
        pair=event_pair(row,row['ordinal'])
        if pair.get('role')in('news','score'):
            if pair['kind']=='date':values[pair['role']+'_date']=pair['date']
            elif pair['kind']=='time':values[pair['role']+'_clock']=native_time_text(pair['after']['cx'],pair['after']['dx'])
    return values


class EvolvedAuxiliaryTests(unittest.TestCase):
    def invoke(self,*,before=None,world=None,created=aux.CREATED,**kw):
        if before is None or world is None:
            first,after=initial_worlds()
        return aux.synthesize(first if before is None else before,after if world is None else world,
                              kw.pop('news_date',DATE),kw.pop('news_clock','00:00:00'),
                              kw.pop('score_date',DATE),kw.pop('score_clock','00:00:01'),created=created,**kw)

    def test_initial_publication_and_exact_copy_rules(self):
        before,_=initial_worlds();out,stats=self.invoke()
        self.assertEqual(set(out),aux.FILES-{'YTDATA.DAT'})
        self.assertEqual(out['YTNAME.DAT'],before['YTNAME.DAT']);self.assertEqual(out['YTYNEWS.DAT'],before['YTNEWS.DAT'])
        self.assertEqual(out['YTRMSG.DAT'],b'');self.assertEqual(stats['created'],list(aux.CREATED))
        for text in(b'missing or has been destroyed',b'regenerated with P.H.O.E.N.I.X.',b'home base now has a planet',b'captured Genesis Device'):
            self.assertIn(text,out['YTNEWS.DAT'])

    def test_existing_homes_do_not_repeat_restoration_news(self):
        before,world=evolved_worlds();out,stats=self.invoke(before=before,world=world,created=())
        self.assertEqual(stats['created'],[])
        for text in(b'missing or has been destroyed',b'regenerated',b'have made a Planet',b'captured Genesis Device'):
            self.assertNotIn(text,out['YTNEWS.DAT'])
        self.assertIn(b'Xannor report:',out['YTNEWS.DAT']);self.assertIn(b'Mercenary Report:',out['YTNEWS.DAT'])
        self.assertEqual(out['YTYNEWS.DAT'],before['YTNEWS.DAT'])

    def test_source_order_places_home_news_around_faction_reports(self):
        out,_=self.invoke();news=out['YTNEWS.DAT']
        parts=[b'Wanderer is missing',b'Wanderer regenerated',b'Xannor have made',b'Xannor report:',b'Mercenary Report:',b'captured Genesis Device']
        self.assertEqual([news.index(p)for p in parts],sorted(news.index(p)for p in parts))

    def test_separate_source_news_and_score_clocks(self):
        out,_=self.invoke(news_clock='01:02:03',score_clock='04:05:06',score_date=DATE+datetime.timedelta(days=1))
        self.assertTrue(out['YTNEWS.DAT'].startswith(b'01:02:03 11-02-2026'))
        self.assertIn(b'Last updated at: 11-03-2026 04:05:06',out['YTSCORE.ASC'])

    def test_physical_score_does_not_multiply_duplicate_pointers(self):
        before,world=initial_worlds();data=bytearray(world)
        for group in range(2,20):put(data,51+group,105,849)
        out,stats=self.invoke(before=before,world=bytes(data))
        self.assertEqual(stats['physical_force'],10000);self.assertEqual(stats['scores'],{-1:1000000,-2:0})
        self.assertIn(b'1,000,000',out['YTSCORE.ASC'])

    def test_inherited_rank_minus_one_remains_admitted(self):
        before,world=evolved_worlds();out,_=self.invoke(before=before,world=world,created=())
        self.assertEqual(out['YTNAME.DAT'],before['YTNAME.DAT'])

    def test_core_reads_only_immutable_original(self):
        before,world=initial_worlds();read=Path.read_bytes;allowed=ROOT/'archive/dos-original/YTMAINT.EXE'
        def guard(path):
            if path!=allowed:raise AssertionError('target/trace/recipe read: '+str(path))
            return read(path)
        with patch.object(Path,'read_bytes',guard),patch.object(Path,'read_text',side_effect=AssertionError('no text sources')):
            self.invoke(before=before,world=world)

    def test_all_three_synthetic_auxiliary_stages_match_native_after_source_extraction(self):
        root=ROOT/'research/yt-maint/convergence-chain-controls'
        for mode in('observed-a','observed-b','observed-c'):
            before,world=initial_worlds()
            for day in range(1,4):
                folder=root/('day-'+str(day))/mode;source=clocks(folder/'host-time.json.gz')
                actual,_=aux.synthesize(before,world,**source,created=aux.CREATED if day==1 else())
                # All expected files open after independent modeled-state synthesis.
                for filename,value in actual.items():
                    with self.subTest(mode=mode,day=day,file=filename):
                        self.assertEqual(value,gzip.decompress((folder/('after-'+filename+'.gz')).read_bytes()))
                before={'YTDATA.DAT':world,**actual}

    def test_created_flag_cannot_suppress_missing_home_notice(self):
        with self.assertRaisesRegex(ValueError,'actual missing'):self.invoke(created=())

    def test_created_flag_cannot_claim_existing_home_restoration(self):
        before,world=evolved_worlds()
        with self.assertRaisesRegex(ValueError,'actual missing'):self.invoke(before=before,world=world,created=aux.CREATED)

    def test_mutable_unordered_partial_or_unknown_creation_mask_rejected(self):
        for created in(list(aux.CREATED),tuple(reversed(aux.CREATED)),('wanderer',),('other',)):
            with self.subTest(created=created),self.assertRaises(ValueError):self.invoke(created=created)

    def test_nonempty_inherited_private_mail_rejected(self):
        before,world=evolved_worlds();before['YTRMSG.DAT']=b'private'
        with self.assertRaisesRegex(ValueError,'private-message'):self.invoke(before=before,world=world,created=())

    def test_wrong_raw_input_inventory_or_mutable_world_rejected(self):
        before,world=initial_worlds()
        for invalid in(None,{**before,'extra':b''},{k:v for k,v in before.items()if k!='YTNAME.DAT'},{**before,'YTDATA.DAT':bytearray(before['YTDATA.DAT'])}):
            with self.subTest(value=type(invalid).__name__),self.assertRaises(ValueError):
                aux.synthesize(invalid,world,DATE,'00:00:00',DATE,'00:00:01',created=aux.CREATED)
        with self.assertRaises(ValueError):self.invoke(world=bytearray(world))

    def test_six_evolved_files_cannot_bypass_missing_bootstrap_context(self):
        before,world=initial_worlds();before.update({'YTYNEWS.DAT':b'', 'YTRMSG.DAT':b'', 'YTSCORE.ASC':b''})
        with self.assertRaisesRegex(ValueError,'inventory and home'):self.invoke(before=before,world=world)

    def test_active_human_assets_or_wrong_rank_publication_rejected(self):
        before,world=initial_worlds()
        for record,offset,value in((2,85,1),(2,57,42),(2,109,0)):
            data=bytearray(world);put(data,record,offset,value)
            with self.subTest(offset=offset),self.assertRaisesRegex(ValueError,'inactive humans'):self.invoke(world=bytes(data))
        data=bytearray(before['YTDATA.DAT']);put(data,2,109,-2)
        with self.assertRaises(ValueError):self.invoke(before={**before,'YTDATA.DAT':bytes(data)})

    def test_foreign_or_fractional_physical_force_rejected(self):
        before,world=initial_worlds()
        for offset,value in((81,9999),(81,10000.5),(85,-2),(85,0)):
            data=bytearray(world);put(data,900,offset,value)
            with self.subTest(offset=offset,value=value),self.assertRaises(ValueError):self.invoke(world=bytes(data))

    def test_treasury_hiring_context_rejected(self):
        before,world=initial_worlds();data=bytearray(world);put(data,3052,89,1)
        with self.assertRaisesRegex(ValueError,'tax-funded'):self.invoke(world=bytes(data))

    def test_changed_home_name_owner_or_link_rejected(self):
        before,world=initial_worlds()
        for mutate in(lambda w:put(w,4052,73,-1),lambda w:put(w,4052,85,1),lambda w:put(w,51+2787,93,0),lambda w:put(w,51+2200,93,1)):
            data=bytearray(world);mutate(data)
            with self.subTest(mutation=mutate),self.assertRaises(ValueError):self.invoke(world=bytes(data))

    def test_missing_home_stale_link_rejected(self):
        before,world=initial_worlds();data=bytearray(before['YTDATA.DAT']);put(data,51+2787,93,1)
        with self.assertRaisesRegex(ValueError,'stale sector'):self.invoke(before={**before,'YTDATA.DAT':bytes(data)})

    def test_existing_home_source_title_must_match(self):
        before,world=evolved_worlds();data=bytearray(before['YTDATA.DAT']);put(data,4052,73,-1)
        with self.assertRaisesRegex(ValueError,'existing named home'):self.invoke(before={**before,'YTDATA.DAT':bytes(data)},world=world,created=())

    def test_convergence_planet_and_unknown_active_planets_rejected(self):
        before,world=initial_worlds()
        for record in(4053,4054):
            data=bytearray(world);put(data,record,85,1)
            with self.subTest(record=record),self.assertRaises(ValueError):self.invoke(world=bytes(data))

    def test_unknown_sector_planet_reference_rejected(self):
        before,world=initial_worlds();data=bytearray(world);put(data,2100,93,3)
        with self.assertRaisesRegex(ValueError,'sector references'):self.invoke(world=bytes(data))

    def test_fixed_geometry_and_unaliased_scoreboard_path_required(self):
        before,world=initial_worlds()
        for offset,value in((53,52),(41,10)):
            data=bytearray(world);put(data,1,offset,value)
            with self.subTest(offset=offset),self.assertRaises(ValueError):self.invoke(world=bytes(data))

    def test_separate_typed_dates_and_native_clock_bounds_required(self):
        for kw in(dict(news_date='2026-11-02'),dict(score_date=datetime.datetime(2026,11,2)),dict(news_clock='25:00:00'),dict(score_clock='24:00:01')):
            with self.subTest(kw=kw),self.assertRaises(ValueError):self.invoke(**kw)
        out,_=self.invoke(score_clock='24:00:00');self.assertIn(b'24:00:00',out['YTSCORE.ASC'])


if __name__=='__main__':unittest.main()
