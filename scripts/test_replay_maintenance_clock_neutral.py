"""Regressions for the explicit before-only host-clock replay profile."""
import copy
import datetime
import gzip
import json
from pathlib import Path
import unittest
from unittest import mock

import replay_maintenance_clock_neutral as model


class ClockProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trace=json.loads(gzip.decompress((model.DEFAULT/'observed-a/host-time.json.gz').read_bytes()))
        before_root=model.ROOT/'research/yt-maint/initial-controls/baseline-split'
        cls.before={n:gzip.decompress((before_root/('before-'+n+'.gz')).read_bytes())for n in model.FILES[:3]}
        cls.parameters=model.inputs_from_observation(cls.trace,datetime.date(2026,11,2))
        cls.actual,cls.stats=model.synthesize(cls.before,cls.parameters)

    def test_one_trace_has_all_clock_inputs_and_actual_seed(self):
        p=self.parameters
        self.assertEqual((len(p.port_timer_minutes),len(p.h1_timers),len(p.h2_timers)),(1000,41,19))
        self.assertEqual(p.initial_state,0xc805)
        self.assertEqual(self.stats['npcs']['total_draws'],25891)
        self.assertEqual(self.stats['npcs']['final_rng_state'],0x4307ee)

    def test_transition_is_derived_at607_and_zero_residue_is_preserved(self):
        self.assertEqual(self.parameters.port_timer_minutes[605],bytes.fromhex('00004800'))
        self.assertEqual(self.parameters.port_timer_minutes[606],bytes.fromhex('0e745a76'))
        offset=(3051+605)*137+101
        self.assertEqual(self.actual['YTDATA.DAT'][offset:offset+4],bytes.fromhex('00004800'))

    def test_profile_conversion_reads_no_file(self):
        with mock.patch.object(Path,'read_bytes',side_effect=AssertionError('profile must use only supplied observation')):
            self.assertEqual(model.inputs_from_observation(self.trace,datetime.date(2026,11,2)),self.parameters)

    def test_synthesis_reads_no_targets_or_prior_probe(self):
        original=Path.read_bytes
        allowed=(model.ROOT/'archive/dos-original/YTMAINT.EXE').resolve()
        def guard(path):
            if path.resolve()!=allowed:raise AssertionError('non-original synthesis read: '+str(path))
            return original(path)
        with mock.patch.object(Path,'read_bytes',guard):
            actual,_=model.synthesize(self.before,self.parameters)
        self.assertEqual(actual,self.actual)

    def test_all_repeats_match_all_six_complete_fresh_and_historical_targets(self):
        report=model.replay_cases()
        self.assertEqual(len(report['cases']),30)
        for row in report['cases']:
            with self.subTest(trace=row['observation'],control=row['control']):
                self.assertEqual(row['byte_mismatches'],0)
                self.assertEqual(row['compared_bytes'],570059)
                self.assertEqual(set(row['files']),set(model.FILES))

    def test_different_date_is_not_admitted_as_general_clock_prediction(self):
        with self.assertRaises(ValueError):model.inputs_from_observation(self.trace,datetime.date(2026,11,3))

    def test_changed_text_second_is_rejected(self):
        trace=copy.deepcopy(self.trace)
        trace['events'][-1]['after']['dx']=256
        with self.assertRaises(ValueError):model.inputs_from_observation(trace,datetime.date(2026,11,2))

    def test_unassigned_before_byte_is_not_replaced_by_after_template(self):
        before=dict(self.before);world=bytearray(before['YTDATA.DAT']);offset=4051*137+133
        world[offset]=37;before['YTDATA.DAT']=bytes(world)
        actual,_=model.synthesize(before,self.parameters)
        self.assertEqual([i for i,(a,b)in enumerate(zip(actual['YTDATA.DAT'],self.actual['YTDATA.DAT']))if a!=b],[offset])

if __name__=='__main__':unittest.main()
