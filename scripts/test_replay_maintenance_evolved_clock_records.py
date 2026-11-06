"""Full before-only clock chains: native comparisons and hostile provenance inputs."""
import builtins
import copy
from dataclasses import fields,replace
import datetime
import gzip
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import replay_maintenance_evolved_clock_records as replay
from replay_qb_graph import mbf

ROOT=Path(__file__).resolve().parents[1]
PROFILES={
 'second-two':(('2026-11-03','00:00:02'),('2026-11-04','00:00:00')),
 'noon':(('2026-11-03','12:00:00'),('2026-11-04','00:00:00')),
 'catchup-eleven':(('2026-11-13','00:00:00'),('2026-11-14','00:00:00')),
 'new-year':(('2027-01-01','00:00:00'),('2027-01-02','00:00:00')),
}


class EvolvedClockChainProperties(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before=replay.old.initial_before();cls.observations={};cls.inputs={};cls.outputs={};cls.stats={}
        first=json.loads(gzip.decompress((replay.old.DEFAULT/'day-1/observed-a/host-time.json.gz').read_bytes()))
        for profile in PROFILES:
            obs=(first,)+tuple(json.loads(gzip.decompress((replay.DEFAULT/profile/f'child-{i}/observed-a/host-time.json.gz').read_bytes()))for i in(1,2))
            cls.observations[profile]=obs;cls.inputs[profile]=tuple(replay.inputs_from_observation(ob)for ob in obs)
            cls.outputs[profile],cls.stats[profile]=replay.synthesize_chain(cls.before,cls.inputs[profile])

    def reject(self,inputs,profile='second-two'):
        with self.assertRaises((AssertionError,ValueError)):replay.synthesize_chain(self.before,inputs)

    def test_all_144_complete_native_comparisons_without_masks(self):
        synthesize=replay.synthesize_chain;read=Path.read_bytes;events=[]
        def modeled(before,inputs):
            result=synthesize(before,inputs);events.append('chain-complete');return result
        def guarded_read(path):
            if path.name.startswith('after-'):
                if not events:raise AssertionError('comparison target read before full modeled chain')
                events.append('native-target')
            return read(path)
        with patch.object(replay,'synthesize_chain',side_effect=modeled),patch.object(Path,'read_bytes',guarded_read):
            report=replay.compare_cases()
        self.assertEqual(events,sum((['chain-complete']+['native-target']*72 for _ in range(12)),[]))
        self.assertEqual((len(report['cases']),len(report['statistics'])),(144,24))
        self.assertEqual(sum(len(r['files'])for r in report['cases']),864)
        self.assertTrue(all(r['byte_mismatches']==0 for r in report['cases']))
        self.assertEqual({(r['profile'],r['child'],r['observation'],r['target'])for r in report['cases']},
                         {(p,c,o,t)for p in PROFILES for c in(1,2)for o in('observed-a','observed-b','observed-c')for t in replay.MODES})

    def test_clock_inputs_are_explicit_and_have_no_target_payload(self):
        self.assertEqual({f.name for f in fields(replay.Inputs)},{'clock','schedule','planet_clocks'})
        self.assertEqual(set(self.before),set(replay.FILES[:3]))
        for profile,pairs in PROFILES.items():
            inputs=self.inputs[profile]
            self.assertEqual(inputs[0].clock.startup_date,datetime.date(2026,11,2))
            self.assertEqual([(r.clock.startup_date.isoformat(),r.clock.news_clock)for r in inputs[1:]],list(pairs))
            self.assertTrue(all(type(raw)is bytes and len(raw)==4 for row in inputs for _,_,raw in row.schedule))

    def test_actual_modeled_six_file_objects_are_handed_forward(self):
        old_real=replay.old._synthesize_day;new_real=replay._synthesize_day;seen=[];made=[]
        def run(real,before,inputs):
            seen.append(before);out=real(before,inputs);made.append(out[0]);return out
        with patch.object(replay.old,'_synthesize_day',side_effect=lambda b,i:run(old_real,b,i)),patch.object(replay,'_synthesize_day',side_effect=lambda b,i:run(new_real,b,i)):
            outputs,stats=replay.synthesize_chain(self.before,self.inputs['noon'])
        self.assertIs(seen[0],self.before);self.assertIs(seen[1],made[0]);self.assertIs(seen[2],made[1])
        self.assertEqual(outputs,self.outputs['noon']);self.assertEqual(stats,self.stats['noon'])
        self.assertEqual(set(seen[1]),set(replay.FILES));self.assertEqual(set(seen[2]),set(replay.FILES))

    def test_marker_handoffs_cannot_be_replaced_by_native_child_saves(self):
        seen=[];made=[]
        def synthetic(before,inputs):
            seen.append(before);result={n:before.get(n,b'')for n in replay.FILES}
            result['YTNEWS.DAT']=f'modeled-only-{len(made)}'.encode();made.append(result)
            return result,{'stage':len(made)}
        with patch.object(replay.old,'_synthesize_day',side_effect=synthetic),patch.object(replay,'_synthesize_day',side_effect=synthetic),patch.object(Path,'read_bytes',side_effect=AssertionError('native child read')):
            output,stats=replay.synthesize_chain(self.before,self.inputs['new-year'])
        self.assertIs(seen[1],made[0]);self.assertIs(seen[2],made[1])
        self.assertEqual(seen[1]['YTNEWS.DAT'],b'modeled-only-0');self.assertEqual(seen[2]['YTNEWS.DAT'],b'modeled-only-1')
        self.assertEqual(output,tuple(made));self.assertEqual([s['stage']for s in stats],[1,2,3])

    def test_core_reads_only_original_executable_not_capture_or_recipe(self):
        allowed=ROOT/'archive/dos-original/YTMAINT.EXE';read=Path.read_bytes;original_open=io.open
        def byte_guard(path):
            if path!=allowed:raise AssertionError('core target/probe read: '+str(path))
            return read(path)
        def open_guard(path,*args,**kwargs):
            if Path(path)!=allowed:raise AssertionError('core target/probe open: '+str(path))
            return original_open(path,*args,**kwargs)
        with patch.object(Path,'read_bytes',byte_guard),patch.object(Path,'read_text',side_effect=AssertionError('target text read')),patch.object(io,'open',side_effect=open_guard),patch.object(builtins,'open',side_effect=open_guard):
            out,stats=replay.synthesize_chain(self.before,self.inputs['catchup-eleven'])
        self.assertEqual(out,self.outputs['catchup-eleven']);self.assertEqual(stats,self.stats['catchup-eleven'])

    def test_poisoned_captured_rng_cannot_seed_or_change_synthesis(self):
        for profile in PROFILES:
            obs=copy.deepcopy(self.observations[profile])
            for ob in obs:
                for event in ob['events']:
                    for side in('before','after'):event[side]['rng_raw']='00000000'
            inputs=tuple(replay.inputs_from_observation(ob)for ob in obs)
            self.assertEqual(inputs,self.inputs[profile])
            if profile=='noon':
                output,stats=replay.synthesize_chain(self.before,inputs)
                self.assertEqual(output,self.outputs[profile]);self.assertEqual(stats,self.stats[profile])
            for ob,row in zip(obs,self.stats[profile]):
                with self.assertRaises(ValueError):replay.validate_rng_witnesses(ob,row)

    def test_extraction_does_not_modify_captured_clock_evidence(self):
        for profile in PROFILES:
            obs=copy.deepcopy(self.observations[profile]);saved=copy.deepcopy(obs)
            self.assertEqual(tuple(replay.inputs_from_observation(o)for o in obs),self.inputs[profile]);self.assertEqual(obs,saved)

    def test_every_helper_and_final_rng_witness_is_audited(self):
        for profile in PROFILES:
            for ob,row in zip(self.observations[profile],self.stats[profile]):
                self.assertEqual(replay.validate_rng_witnesses(ob,row),len(row['npcs']['helper_seeds'])+2)
        for profile in PROFILES:
            for stage in(1,2):
                row=copy.deepcopy(self.stats[profile][stage]);row['npcs']['final_rng_state']^=1
                with self.assertRaises(ValueError):replay.validate_rng_witnesses(self.observations[profile][stage],row)
                row=copy.deepcopy(self.stats[profile][stage]);row['npcs']['helper_seeds'][0]['old_state']^=1
                with self.assertRaises(ValueError):replay.validate_rng_witnesses(self.observations[profile][stage],row)

    def test_unknown_initial_bytes_reject_before_any_file_read(self):
        for name in replay.FILES[:3]:
            before=dict(self.before);before[name]+=b'changed'
            with self.subTest(name=name),patch.object(Path,'read_bytes',side_effect=AssertionError('unadmitted read')):
                with self.assertRaises(ValueError):replay.synthesize_chain(before,self.inputs['noon'])

    def test_initial_inventory_and_raw_immutability_are_required(self):
        candidates=(None,self.outputs['noon'][0],dict(self.before,extra=b''),{n:b for n,b in self.before.items()if n!='YTNEWS.DAT'},dict(self.before,**{'YTDATA.DAT':bytearray(self.before['YTDATA.DAT'])}))
        for before in candidates:
            with self.subTest(kind=type(before)),self.assertRaises(ValueError):replay.synthesize_chain(before,self.inputs['noon'])

    def test_frozen_three_stage_input_container_is_required(self):
        inputs=self.inputs['second-two']
        for value in(None,list(inputs),inputs[:2],inputs+(inputs[-1],),(None,)+inputs[1:],(replace(inputs[0],clock=None),)+inputs[1:]):self.reject(value)

    def test_unmeasured_date_pair_and_wrong_parent_reject(self):
        inputs=self.inputs['second-two']
        for index,date in((0,datetime.date(2026,11,1)),(1,datetime.date(2026,11,5)),(2,datetime.date(2026,11,5))):
            altered=list(inputs);altered[index]=replace(inputs[index],clock=replace(inputs[index].clock,startup_date=date));self.reject(tuple(altered))
        self.reject(inputs[::-1]);self.reject((inputs[0],)*3)

    def test_unmeasured_profile_text_clocks_reject(self):
        for profile in PROFILES:
            inputs=self.inputs[profile]
            for index in(1,2):
                changed=list(inputs);changed[index]=replace(inputs[index],clock=replace(inputs[index].clock,news_clock='00:00:09'));self.reject(tuple(changed))

    def test_mutable_helper_port_or_planet_clock_arrays_reject(self):
        inputs=self.inputs['noon'];first=inputs[0]
        for row in(replace(first,schedule=list(first.schedule)),replace(first,planet_clocks=list(first.planet_clocks)),replace(first,clock=replace(first.clock,port_dates=list(first.clock.port_dates))),replace(first,clock=replace(first.clock,h1_timers=list(first.clock.h1_timers)))):
            self.reject((row,)+inputs[1:])

    def test_raw_clock_widths_and_startup_state_types_reject(self):
        inputs=self.inputs['noon'];first=inputs[0]
        for clock in(replace(first.clock,initial_state=-1),replace(first.clock,initial_state=True),replace(first.clock,initial_state=2**24),replace(first.clock,port_dates=first.clock.port_dates[:-1]),replace(first.clock,port_timer_minutes=(bytes(3),)*1000)):
            self.reject((replace(first,clock=clock),)+inputs[1:])

    def test_helper_order_caller_and_family_are_not_inferred_from_targets(self):
        inputs=self.inputs['noon'];first=inputs[0];s=first.schedule
        for schedule in(((s[0][0],0x437a,s[0][2]),)+s[1:],(('h2',s[0][1],s[0][2]),)+s[1:],(s[1],s[0])+s[2:]):
            self.reject((replace(first,schedule=schedule),)+inputs[1:])

    def test_source_caller_context_is_authenticated_before_input_extraction(self):
        for profile in PROFILES:
            ob=copy.deepcopy(self.observations[profile][1]);row=ob['events'][10]
            row['before']['caller_code']='00'+row['before']['caller_code'][2:]
            with self.assertRaises((ValueError,AssertionError)):replay.inputs_from_observation(ob)

    def test_missing_or_extra_helper_clock_cannot_silently_truncate(self):
        inputs=self.inputs['noon'];first=inputs[0];last=first.schedule[-1]
        for row in(replace(first,schedule=first.schedule[:-1],clock=replace(first.clock,h1_timers=first.clock.h1_timers[:-1])),replace(first,schedule=first.schedule+(last,),clock=replace(first.clock,h1_timers=first.clock.h1_timers+(last[2],)))):
            self.reject((row,)+inputs[1:])

    def test_wrong_planet_order_or_source_calendar_rejects(self):
        inputs=self.inputs['second-two'];second=inputs[1]
        for row in(replace(second,planet_clocks=second.planet_clocks[::-1]),replace(second,clock=replace(second.clock,port_dates=(datetime.date(2026,11,2),)*1000)),replace(second,clock=replace(second.clock,final_date=datetime.date(2026,11,2)))):
            self.reject((inputs[0],row,inputs[2]))

    def test_children_reject_mutable_or_malformed_source_rows(self):
        inputs=self.inputs['noon'];child=inputs[1];schedule=child.schedule
        altered=(replace(child,schedule=list(schedule)),
                 replace(child,planet_clocks=list(child.planet_clocks)),
                 replace(child,clock=replace(child.clock,port_timer_minutes=(bytes(3),)*1000)),
                 replace(child,schedule=((schedule[0][0],True,schedule[0][2]),)+schedule[1:]),
                 replace(child,schedule=((schedule[0][0],schedule[0][1],bytes(3)),)+schedule[1:]))
        for row in altered:self.reject((inputs[0],row,inputs[2]))

    def test_child_helper_caller_order_and_completion_are_computed(self):
        inputs=self.inputs['second-two'];child=inputs[1];s=child.schedule
        for row in(replace(child,schedule=((s[0][0],0x437a,s[0][2]),)+s[1:]),
                   replace(child,schedule=(s[1],s[0])+s[2:]),
                   replace(child,schedule=s[:-1],clock=replace(child.clock,h1_timers=child.clock.h1_timers[:-1]))):
            self.reject((inputs[0],row,inputs[2]))

    def test_existing_child_homes_cannot_accept_invented_creation_clocks(self):
        inputs=self.inputs['second-two'];child=inputs[1]
        for name,value in(('wanderer_date',child.clock.startup_date),('xannoron_date',child.clock.startup_date),('base_date',child.clock.startup_date),('xannoron_timer',bytes(4))):
            row=replace(child,clock=replace(child.clock,**{name:value}))
            self.reject((inputs[0],row,inputs[2]))

    def test_child_score_clock_is_typed_and_its_calendar_is_independent(self):
        inputs=self.inputs['second-two'];child=inputs[1]
        for name,value in(('score_clock','25:00:00'),('score_clock',None),('score_date',datetime.date(2026,11,2))):
            row=replace(child,clock=replace(child.clock,**{name:value}))
            self.reject((inputs[0],row,inputs[2]))

    def test_modeled_output_handoffs_keep_exact_side_file_rotation(self):
        for profile in PROFILES:
            prior=self.before
            for output in self.outputs[profile]:
                self.assertEqual(set(output),set(replay.FILES));self.assertTrue(all(type(b)is bytes for b in output.values()))
                self.assertEqual(output['YTNAME.DAT'],prior['YTNAME.DAT']);self.assertEqual(output['YTYNEWS.DAT'],prior['YTNEWS.DAT']);self.assertEqual(output['YTRMSG.DAT'],b'');prior=output

    def test_measured_losses_are_modeled_and_publicly_accounted(self):
        expected={'second-two':(10000,9994),'noon':(8300,8300),'catchup-eleven':(10000,10000),'new-year':(10000,9638)}
        for profile,forces in expected.items():
            self.assertEqual(tuple(sum(int(mbf.get(o['YTDATA.DAT'],51+s,81))for s in range(1,3001))for o in self.outputs[profile][1:]),forces)
        self.assertIn(b'6 Xannor hit sector mines in sector 980!',self.outputs['second-two'][2]['YTNEWS.DAT'])
        self.assertEqual(self.outputs['noon'][1]['YTNEWS.DAT'].count(b'Xannor fighters destroyed!'),14)
        self.assertEqual(self.outputs['new-year'][2]['YTNEWS.DAT'].count(b'Xannor fighters destroyed!'),4)

    def test_repeated_group_endpoint_keeps_single_mine_not_accumulated_count(self):
        # Group 20 revisits 439 in the New Year chain. Both retained native
        # stages contain one mine; guard this independently of bulk comparison.
        first,second=self.outputs['new-year'][1:]
        self.assertEqual(mbf.get(first['YTDATA.DAT'],51+439,129),1)
        self.assertEqual(mbf.get(second['YTDATA.DAT'],51+439,129),1)
        self.assertEqual(mbf.get(second['YTDATA.DAT'],51+1169,129),1)

    def test_new_year_keeps_base_year_and_uses_serial_day_not_doy(self):
        for output,day in zip(self.outputs['new-year'][1:],(366,367)):
            world=output['YTDATA.DAT'];self.assertEqual(mbf.get(world,1,45),26);self.assertEqual(mbf.get(world,1,81),day)
            self.assertTrue(all(mbf.get(world,3051+p,45)==day for p in range(1,1001)))

    def test_input_and_initial_objects_are_not_mutated_by_synthesis(self):
        saved=dict(self.before);inputs=self.inputs['second-two'];snapshot=copy.deepcopy(inputs)
        replay.synthesize_chain(self.before,inputs)
        self.assertEqual(self.before,saved);self.assertEqual(inputs,snapshot)


if __name__=='__main__':unittest.main()
