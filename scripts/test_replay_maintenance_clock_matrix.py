"""Properties of the explicit before-only clock/date matrix profile."""
import datetime
from dataclasses import replace
import gzip
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import replay_maintenance_clock_matrix as matrix
import replay_maintenance_clock_neutral as historical
import replay_maintenance_records as records
import replay_maintenance_aux as auxiliary
from replay_maintenance_ports import replay_ports,replay_capped_initial_ports

ROOT=Path(__file__).resolve().parents[1]
mbf=matrix.graph.mbf
DATE=datetime.date(2026,11,2)


class ClockMatrixModelProperties(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=ROOT/'research/yt-maint/initial-controls/baseline-split'
        cls.before={name:gzip.decompress((source/('before-'+name+'.gz')).read_bytes())for name in matrix.FILES[:3]}
        path=ROOT/'research/yt-maint/clock-neutral-controls/observed-a/host-time.json.gz'
        observation=json.loads(gzip.decompress(path.read_bytes()))
        old=historical.inputs_from_observation(observation,DATE)
        cls.old_inputs=old
        cls.inputs=matrix.Inputs(startup_date=DATE,final_date=DATE,port_dates=(DATE,)*1000,
            wanderer_date=DATE,xannoron_date=DATE,base_date=DATE,
            news_date=DATE,news_clock='00:00:00',score_date=DATE,score_clock='00:00:00',
            port_timer_minutes=old.port_timer_minutes,h1_timers=old.h1_timers,h2_timers=old.h2_timers,
            xannoron_timer=old.xannoron_timer,initial_state=old.initial_state)

    def test_historical_strict_before_only_result_is_unchanged(self):
        old,_=records.synthesize(self.before,self.old_inputs)
        new,_=matrix.synthesize(self.before,self.inputs)
        self.assertEqual(new,old)

    def test_source_base_year_calendar_count(self):
        before=self.before['YTDATA.DAT']
        self.assertEqual(matrix.legacy_day(before,DATE),306)
        self.assertEqual(matrix.legacy_day(before,datetime.date(2026,11,3)),307)
        self.assertEqual(matrix.legacy_day(before,datetime.date(2027,1,1)),366)
        self.assertNotEqual(matrix.legacy_day(before,datetime.date(2027,1,1)),1)

    def test_next_year_preserves_base_year_and_uses_relative_days(self):
        date=datetime.date(2027,1,1)
        inputs=replace(self.inputs,startup_date=date,final_date=date,port_dates=(date,)*1000,
            wanderer_date=date,xannoron_date=date,base_date=date,news_date=date,score_date=date)
        files,stats=matrix.synthesize(self.before,inputs);world=files['YTDATA.DAT']
        self.assertEqual(mbf.get(world,1,45),26)
        self.assertEqual(mbf.get(world,1,81),366)
        self.assertEqual(mbf.get(world,3052,45),366)
        self.assertEqual(mbf.get(world,4052,41),356)
        self.assertEqual(mbf.get(world,4151,41),366)
        self.assertEqual(mbf.get(world,4150,41),356)
        self.assertEqual(stats['final_day'],366)
        self.assertIn(b'01-01-2027',files['YTNEWS.DAT'])

    def test_noon_creation_timestamp_is_integer720(self):
        files,_=matrix.synthesize(self.before,replace(self.inputs,xannoron_timer=mbf.enc(43200)))
        self.assertEqual(mbf.get(files['YTDATA.DAT'],4151,89),720)
        at=4150*137+89
        self.assertEqual(files['YTDATA.DAT'][at:at+4],mbf.enc(720))

    def test_zero_creation_timestamp_preserves_raw_residue(self):
        raw=bytes.fromhex('00004800')
        files,_=matrix.synthesize(self.before,replace(self.inputs,xannoron_timer=raw))
        at=4150*137+89
        self.assertEqual(files['YTDATA.DAT'][at:at+4],raw)

    def test_port_date_and_timer_may_straddle_midnight(self):
        days=(306,)*600+(307,)*400
        times=(mbf.enc(1439.9),)*599+(bytes.fromhex('00004800'),)*401
        block,_=replay_capped_initial_ports(self.before['YTDATA.DAT'],days,times)
        self.assertEqual(mbf.dec(block[599*137+45:599*137+49]),306)
        self.assertEqual(block[599*137+101:599*137+105],bytes.fromhex('00004800'))
        self.assertEqual(mbf.dec(block[600*137+45:600*137+49]),307)
        with self.assertRaises(ValueError):replay_ports(self.before['YTDATA.DAT'],306,times)

    def test_native_time24_keeps_its_separately_sampled_date(self):
        files,_=matrix.synthesize(self.before,replace(self.inputs,score_clock='24:00:00'))
        self.assertIn(b'Last updated at: 11-02-2026 24:00:00',files['YTSCORE.ASC'])

    def test_news_and_score_dates_are_distinct_inputs(self):
        next_day=DATE+datetime.timedelta(days=1)
        files,_=matrix.synthesize(self.before,replace(self.inputs,news_clock='23:59:59',score_date=next_day,score_clock='00:00:08'))
        self.assertTrue(files['YTNEWS.DAT'].startswith(b'23:59:59 11-02-2026'))
        self.assertIn(b'Last updated at: 11-03-2026 00:00:08',files['YTSCORE.ASC'])

    def test_only_original_archive_is_read_by_core(self):
        read=Path.read_bytes;allowed=ROOT/'archive/dos-original/YTMAINT.EXE'
        def guard(path):
            if path!=allowed:raise AssertionError('target or unrelated file read: '+str(path))
            return read(path)
        with patch.object(Path,'read_bytes',guard):matrix.synthesize(self.before,self.inputs)

    def test_missing_source_dates_or_extra_helpers_fail_closed(self):
        for inputs in [replace(self.inputs,port_dates=self.inputs.port_dates[:-1]),
                       replace(self.inputs,h1_timers=self.inputs.h1_timers+(bytes(4),bytes(4))),
                       replace(self.inputs,final_date=DATE-datetime.timedelta(days=1))]:
            with self.subTest(inputs=inputs):
                with self.assertRaises(ValueError):matrix.synthesize(self.before,inputs)

    def test_outside_calendar_and_raw_state_bounds_fail(self):
        for date in (datetime.date(2025,12,31),datetime.date(2028,1,1),'2026-11-02'):
            with self.subTest(date=date):
                with self.assertRaises(ValueError):matrix.legacy_day(self.before['YTDATA.DAT'],date)
        for value in (-1,2**24,True):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):matrix.synthesize(self.before,replace(self.inputs,initial_state=value))

    def test_native_time24_is_the_only_admitted_overflow_string(self):
        for value in ('24:00:01','25:00:00','23:60:00','0:00:00'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):matrix.synthesize(self.before,replace(self.inputs,score_clock=value))


class RetainedClockMatrixComparisons(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=matrix.compare_cases()

    def test_all_observations_remain_in_the_report(self):
        rows=self.report['cases']
        compared=[row for row in rows if row['model_status']=='compared']
        gaps=[row for row in rows if row['model_status']=='unsupported']
        self.assertEqual(len(compared),126)
        self.assertEqual(len(gaps),3)
        self.assertEqual({row['recipe']for row in gaps},{'late'})
        self.assertEqual({row['observation']for row in gaps},{'observed-a','observed-b','observed-c'})
        self.assertEqual(len({row['recipe']for row in rows}),8)

    def test_every_supported_comparison_is_complete_and_exact(self):
        for row in self.report['cases']:
            if row['model_status']!='compared':continue
            with self.subTest(recipe=row['recipe'],observation=row['observation'],target=row['target']):
                self.assertEqual(row['byte_mismatches'],0)
                self.assertEqual(set(row['files']),set(matrix.FILES))
                self.assertEqual(row['files']['YTDATA.DAT']['replayed_bytes'],4151*137)

    def test_late_gap_is_neutral_wanderer_from_model_prefix(self):
        for row in self.report['cases']:
            if row['model_status']!='unsupported':continue
            self.assertEqual(row['reason'],'NPC branch: no entered planet/mine action in selected fixture')
            context=row['context']
            self.assertEqual(context['evidence_type'],'before-only-model-prefix')
            self.assertEqual((context['group'],context['sector'],context['planet_slot']),(2,658,1))
            self.assertEqual((context['planet_name'],context['planet_owner']),('The Wanderer',0))
            self.assertEqual(context['group_strength'],382)
            self.assertEqual(context['rng_state'],0xea7184)
            self.assertEqual(context['helper_calls'],{'h1':4,'h2':1})

    def test_source_qualified_extended_profiles_are_not_midnight_substitutes(self):
        stats=self.report['statistics']
        for row in stats:
            with self.subTest(recipe=row['recipe'],observation=row['observation']):
                if row['recipe']in('shift-two','noon','rollover'):
                    self.assertEqual(row['npcs']['helper_calls'],{'h1':42,'h2':19})
                    player=row['npcs']['lottery_player']
                    self.assertIsInstance(player,int)
                    self.assertTrue(2<=player<=51)
                if row['recipe']=='near-midnight-100k':
                    self.assertEqual(row['score_clock'],'24:00:00')
                    self.assertEqual(row['score_date'],'2026-11-02')
                if row['recipe']=='rollover':
                    self.assertEqual(set(row['ports']['calendar_days']),{306,307})
                    self.assertEqual(row['final_day'],307)
                    self.assertEqual((row['news_date'],row['score_date']),('2026-11-02','2026-11-03'))
                if row['recipe']=='next-year':self.assertEqual(row['final_day'],366)


if __name__=='__main__':unittest.main()
