"""Whole-file and meaningful fail-closed tests for the bounded research model."""
import dataclasses
import datetime
from pathlib import Path
import unittest
from unittest import mock

import replay_maintenance_records as model


class ReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from verify_maintenance_record_inputs import verify
        from verify_maintenance_sequence import verify as verify_helper_inputs
        verify_helper_inputs();verify()
        cls.before,cls.inputs=model.measured_case_inputs()
        cls.actual,cls.stats=model.synthesize(cls.before,cls.inputs)
        cls.report=model.controlled_cases()

    def test_all_six_files_match_both_instrumented_comparison_runs(self):
        cases=[c for c in self.report['cases']if c['kind']=='instrumented-body-end']
        self.assertEqual(len(cases),2)
        for c in cases:
            self.assertEqual(c['byte_mismatches'],0)
            self.assertEqual(c['compared_bytes'],570059)
            self.assertTrue(all(f['observed_sha256']==f['replayed_sha256']for f in c['files'].values()))

    def test_untouched_gap_is_not_hidden_or_count_only_masked(self):
        for c in self.report['cases']:
            if c['kind']!='untouched':continue
            self.assertEqual(c['byte_mismatches'],4)
            self.assertEqual([(d['file'],d['record'],d['field_offset'])for d in c['first_differences']],
                             [('YTDATA.DAT',3657,n)for n in range(101,105)])
            self.assertEqual(bytes(d['observed']for d in c['first_differences']),bytes.fromhex('00004800'))
            self.assertEqual(bytes(d['replayed']for d in c['first_differences']),bytes.fromhex('0e745a76'))

    def test_all_other_world_blocks_and_auxiliary_files_are_exact(self):
        case=self.report['cases'][0]
        for key in ('configuration','players','sectors','planets'):
            self.assertEqual(case['world_blocks'][key]['byte_mismatches'],0)
        self.assertEqual(case['world_blocks']['ports']['byte_mismatches'],4)
        self.assertEqual(sum(f['observed_bytes']for n,f in case['files'].items()if n!='YTDATA.DAT'),1372)
        for name,comparison in case['files'].items():
            if name!='YTDATA.DAT':self.assertEqual(comparison['byte_mismatches'],0)

    def test_core_reads_only_the_immutable_original_binary(self):
        original_read=Path.read_bytes
        allowed=(Path(__file__).resolve().parents[1]/'archive/dos-original/YTMAINT.EXE').resolve()
        def guard(path):
            if path.resolve()!=allowed:raise AssertionError('synthesis attempted non-original file read: '+str(path))
            return original_read(path)
        with mock.patch.object(Path,'read_bytes',guard):
            actual,stats=model.synthesize(self.before,self.inputs)
        self.assertEqual(actual,self.actual)

    def test_reconstructed_rng_and_route_counts(self):
        npc=self.stats['npcs']
        self.assertEqual(npc['total_draws'],25891)
        self.assertEqual(npc['final_rng_state'],0x4307ee)
        self.assertEqual(npc['helper_calls'],{'h1':41,'h2':19})
        self.assertEqual(npc['interception_draws'],24800)
        self.assertEqual(npc['candidate_draws'],950)
        self.assertEqual(len(npc['groups']),20)  # tracked HQ plus nineteen mobile groups
        self.assertEqual(len(npc['routes']),19)

    def test_inherited_wanderer_field81_is_not_cleared(self):
        start=4051*137+81
        self.assertEqual(self.actual['YTDATA.DAT'][start:start+4],self.before['YTDATA.DAT'][start:start+4])
        self.assertEqual(model.graph.mbf.dec(self.actual['YTDATA.DAT'][start:start+4]),305)

    def test_unassigned_input_byte_propagates_without_after_template(self):
        before=dict(self.before);raw=bytearray(before['YTDATA.DAT']);at=4051*137+133
        raw[at]=37;before['YTDATA.DAT']=bytes(raw)
        actual,_=model.synthesize(before,self.inputs)
        self.assertEqual([i for i,(a,b)in enumerate(zip(actual['YTDATA.DAT'],self.actual['YTDATA.DAT']))if a!=b],[at])
        for n in actual:
            if n!='YTDATA.DAT':self.assertEqual(actual[n],self.actual[n])

    def test_raw_zero_timer_mantissa_is_preserved(self):
        at=3051*137+101
        self.assertEqual(self.actual['YTDATA.DAT'][at:at+4],bytes.fromhex('00004800'))
        self.assertEqual(model.graph.mbf.dec(self.actual['YTDATA.DAT'][at:at+4]),0)

    def test_xannoron_truncation_preserves_fraction_mantissa(self):
        at=4150*137+89
        self.assertEqual(self.actual['YTDATA.DAT'][at:at+4],bytes.fromhex('0e745a00'))
        self.assertEqual(model.graph.mbf.dec(self.actual['YTDATA.DAT'][at:at+4]),0)

    def rejected_world(self,record,offset,value):
        before=dict(self.before);raw=bytearray(before['YTDATA.DAT']);at=(record-1)*137+offset
        raw[at:at+4]=model.graph.mbf.enc(value);before['YTDATA.DAT']=bytes(raw)
        with self.assertRaises((ValueError,AssertionError)):model.synthesize(before,self.inputs)

    def test_active_player_is_rejected(self):self.rejected_world(2,85,1)
    def test_initial_mine_is_rejected(self):self.rejected_world(351,129,1)
    def test_initial_existing_planet_is_rejected(self):self.rejected_world(4052,85,1)
    def test_owned_port_is_rejected(self):self.rejected_world(3052,89,2)
    def test_nondefault_geometry_is_rejected(self):self.rejected_world(1,53,52)

    def test_wrong_elapsed_fixture_is_rejected(self):
        inputs=dataclasses.replace(self.inputs,date=datetime.date(2026,11,3))
        with self.assertRaises(ValueError):model.synthesize(self.before,inputs)

    def test_missing_measured_helper_inputs_are_rejected(self):
        inputs=dataclasses.replace(self.inputs,h1_timers=())
        with self.assertRaises(AssertionError):model.synthesize(self.before,inputs)

    def test_invalid_seed_is_rejected(self):
        for seed in (-1,2**24,True):
            with self.subTest(seed=seed),self.assertRaises(ValueError):
                model.synthesize(self.before,dataclasses.replace(self.inputs,initial_state=seed))

    def test_missing_before_file_is_rejected(self):
        with self.assertRaises(ValueError):model.synthesize({'YTDATA.DAT':self.before['YTDATA.DAT']},self.inputs)

    def test_nonmonotone_timer_schedule_is_rejected(self):
        raw=bytes.fromhex('0e745a76');zero=bytes.fromhex('00004800')
        with self.assertRaises(ValueError):model.synthesize(self.before,dataclasses.replace(self.inputs,port_timer_minutes=(raw,zero)*500))

    def test_explicit_aux_clock_changes_only_text_files(self):
        actual,_=model.synthesize(self.before,dataclasses.replace(self.inputs,clock='00:00:01'))
        self.assertEqual(actual['YTDATA.DAT'],self.actual['YTDATA.DAT'])
        self.assertTrue(actual['YTNEWS.DAT'].startswith(b'00:00:01'))
        self.assertNotEqual(actual['YTSCORE.ASC'],self.actual['YTSCORE.ASC'])

    def test_comparison_checks_entire_file_extent(self):
        changed=dict(self.actual);changed['YTNEWS.DAT']=changed['YTNEWS.DAT'][:-1]
        result=model.compare(self.actual,changed)
        self.assertEqual(result['byte_mismatches'],1)


if __name__=='__main__':unittest.main()
