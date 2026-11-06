"""Five-day before-only survivor replay: exact handoffs and hostile source inputs."""
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

import replay_maintenance_survivor_records as replay
import replay_maintenance_evolved_combat_records as combat
import replay_maintenance_evolved_clock_records as clock_chain
from replay_qb_graph import mbf

ROOT=Path(__file__).resolve().parents[1]
PROFILES=('mercenary-survivor','planet-survivor','neutral-survivor','mine-survivor')
COMBAT_CASE={'mercenary-survivor':'route-mercenary-100000','planet-survivor':'route-planet-neutral','neutral-survivor':'route-neutral-37'}
FINGERPRINTS={
 'mercenary-survivor':'0e5d8934af1be3debc72708ecdd3e2825a2c4000398253fc8b793340907669a6',
 'planet-survivor':'f545d697b28d93910407cfeb7baac96666062ebe3cb5ac3334d6a3e85f5e45b7',
 'neutral-survivor':'277c3cadeea74b02596c3d832566ff7de5b39a7a5a1b8edbd9a2ac563edd31b6',
 'mine-survivor':'7e470653aabe81d1d3402d8810aca8e2c745e800d0295abcf575d5d7e2a309d3',
}


def force(world,owner):
    return sum(int(mbf.get(world,51+s,81))for s in range(1,3001)if mbf.get(world,51+s,85)==owner)


def observation(path):return json.loads(gzip.decompress(path.read_bytes()))


class SurvivorRecordProperties(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before={};cls.observations={};cls.inputs={};cls.outputs={};cls.stats={}
        for profile in PROFILES:
            cls.before[profile]=replay.initial_before(profile)
            if profile=='mine-survivor':
                paths=(clock_chain.old.DEFAULT/'day-1/observed-a/host-time.json.gz',)+tuple(clock_chain.DEFAULT/'second-two'/f'child-{i}/observed-a/host-time.json.gz'for i in(1,2))
            else:
                case=COMBAT_CASE[profile]
                paths=(combat.PARENT/case/'observed-a/host-time.json.gz',)+tuple(combat.DEFAULT/case/f'child-{i}/observed-a/host-time.json.gz'for i in(1,2))
            paths+=tuple(replay.DEFAULT/profile/f'child-{i}/observed-a/host-time.json.gz'for i in(1,2))
            obs=tuple(observation(p)for p in paths);cls.observations[profile]=obs
            inputs=tuple(replay.inputs_from_observation(ob)for ob in obs);cls.inputs[profile]=inputs
            cls.outputs[profile],cls.stats[profile]=replay.synthesize_chain(cls.before[profile],inputs)

    def reject(self,inputs,profile='mercenary-survivor'):
        with self.assertRaises((ValueError,AssertionError)):replay.synthesize_chain(self.before[profile],inputs)

    def test_144_new_child_comparisons_cover_864_complete_native_files(self):
        synthesize=replay.synthesize_chain;read=Path.read_bytes;events=[]
        def modeled(before,inputs):
            result=synthesize(before,inputs);events.append('five-days-complete');return result
        def guarded(path):
            if path.name.startswith('after-'):
                if not events:raise AssertionError('captured target read before all five modeled days')
                events.append('native-target')
            return read(path)
        with patch.object(replay,'synthesize_chain',side_effect=modeled),patch.object(Path,'read_bytes',guarded):report=replay.compare_cases()
        self.assertEqual(events,sum((['five-days-complete']+['native-target']*72 for _ in range(12)),[]))
        self.assertEqual((len(report['cases']),len(report['statistics'])),(144,24))
        self.assertEqual(sum(len(r['files'])for r in report['cases']),864)
        self.assertTrue(all(r['byte_mismatches']==0 for r in report['cases']))
        self.assertEqual({(r['profile'],r['child'],r['observation'],r['target'])for r in report['cases']},
                         {(p,c,o,t)for p in PROFILES for c in(1,2)for o in('observed-a','observed-b','observed-c')for t in replay.MODES})

    def test_only_original_three_file_fingerprints_and_five_typed_days_enter(self):
        self.assertEqual(set(replay.PROFILES),set(PROFILES))
        self.assertEqual({f.name for f in fields(replay.Inputs)},{'clock','schedule','planet_clocks'})
        for profile in PROFILES:
            self.assertEqual(set(self.before[profile]),set(replay.FILES[:3]));self.assertEqual(replay.SHA(self.before[profile]['YTDATA.DAT']),FINGERPRINTS[profile])
            self.assertEqual(len(self.inputs[profile]),5)
            self.assertEqual([i.clock.startup_date for i in self.inputs[profile]],[datetime.date(2026,11,d)for d in range(2,7)])

    def test_all_prefix_outputs_and_new_handoffs_are_actual_modeled_objects(self):
        for profile,prefix in(('mercenary-survivor',combat),('mine-survivor',clock_chain)):
            real_prefix=prefix.synthesize_chain;real_new=replay._synthesize_day;prefix_outputs=[];seen=[];made=[]
            def first(before,inputs):
                out=real_prefix(before,inputs);prefix_outputs.extend(out[0]);return out
            def child(before,inputs):
                seen.append(before);out=real_new(before,inputs);made.append(out[0]);return out
            with patch.object(prefix,'synthesize_chain',side_effect=first),patch.object(replay,'_synthesize_day',side_effect=child):
                outputs,stats=replay.synthesize_chain(self.before[profile],self.inputs[profile])
            self.assertIs(seen[0],prefix_outputs[2]);self.assertIs(seen[1],made[0]);self.assertIs(outputs[3],made[0]);self.assertIs(outputs[4],made[1])
            self.assertEqual(outputs,self.outputs[profile]);self.assertEqual(stats,self.stats[profile])

    def test_marker_prefix_and_children_cannot_be_replaced_by_native_handoffs(self):
        for profile,prefix in(('mercenary-survivor',combat),('mine-survivor',clock_chain)):
            seen=[];made=[]
            def first(before,inputs):
                outputs=[]
                for stage in range(3):
                    out={n:before.get(n,b'')for n in replay.FILES};out['YTNEWS.DAT']=f'prefix-only-{stage}'.encode();outputs.append(out)
                made.extend(outputs);return tuple(outputs),tuple({'stage':i}for i in range(3))
            def child(before,inputs):
                seen.append(before);out=dict(before);out['YTNEWS.DAT']=f'new-only-{len(made)}'.encode();made.append(out);return out,{'stage':len(made)-1}
            with patch.object(prefix,'synthesize_chain',side_effect=first),patch.object(replay,'_synthesize_day',side_effect=child),patch.object(Path,'read_bytes',side_effect=AssertionError('captured child read')):
                outputs,stats=replay.synthesize_chain(self.before[profile],self.inputs[profile])
            self.assertIs(seen[0],made[2]);self.assertIs(seen[1],made[3]);self.assertEqual(seen[0]['YTNEWS.DAT'],b'prefix-only-2');self.assertEqual(seen[1]['YTNEWS.DAT'],b'new-only-3')
            self.assertEqual(outputs,tuple(made));self.assertEqual([s['stage']for s in stats],list(range(5)))

    def test_five_day_core_reads_only_original_executable(self):
        allowed=ROOT/'archive/dos-original/YTMAINT.EXE';read=Path.read_bytes;original_open=io.open
        def byte_guard(path):
            if path!=allowed:raise AssertionError('core target/probe/recipe read: '+str(path))
            return read(path)
        def open_guard(path,*args,**kwargs):
            if Path(path)!=allowed:raise AssertionError('core target/probe/recipe open: '+str(path))
            return original_open(path,*args,**kwargs)
        for profile in('mercenary-survivor','mine-survivor'):
            with patch.object(Path,'read_bytes',byte_guard),patch.object(Path,'read_text',side_effect=AssertionError('captured text read')),patch.object(io,'open',side_effect=open_guard),patch.object(builtins,'open',side_effect=open_guard):
                outputs,stats=replay.synthesize_chain(self.before[profile],self.inputs[profile])
            self.assertEqual(outputs,self.outputs[profile]);self.assertEqual(stats,self.stats[profile])

    def test_poisoned_rng_witnesses_never_become_synthesis_inputs(self):
        for profile in PROFILES:
            obs=copy.deepcopy(self.observations[profile])
            for row in obs:
                for event in row['events']:
                    for side in('before','after'):event[side]['rng_raw']='00000000'
            inputs=tuple(replay.inputs_from_observation(o)for o in obs);self.assertEqual(inputs,self.inputs[profile])
            if profile=='mercenary-survivor':
                outputs,stats=replay.synthesize_chain(self.before[profile],inputs);self.assertEqual(outputs,self.outputs[profile]);self.assertEqual(stats,self.stats[profile])
            for ob,stats in zip(obs,self.stats[profile]):
                with self.assertRaises(ValueError):replay.validate_rng_witnesses(ob,stats)

    def test_source_extraction_preserves_all_five_observations(self):
        for profile in PROFILES:
            obs=copy.deepcopy(self.observations[profile]);saved=copy.deepcopy(obs)
            self.assertEqual(tuple(replay.inputs_from_observation(o)for o in obs),self.inputs[profile]);self.assertEqual(obs,saved)

    def test_all_prefix_and_new_helper_and_final_rng_witnesses_are_audited(self):
        for profile in PROFILES:
            for stage,(ob,row)in enumerate(zip(self.observations[profile],self.stats[profile])):
                expected=len(self.inputs[profile][stage].schedule)
                self.assertEqual(len(row['npcs']['helper_seeds']),expected);self.assertEqual(replay.validate_rng_witnesses(ob,row),expected+2)
                bad=copy.deepcopy(row);bad['npcs']['final_rng_state']^=1
                with self.assertRaises(ValueError):replay.validate_rng_witnesses(ob,bad)
                for index in{0,expected//2,expected-1}:
                    bad=copy.deepcopy(row);bad['npcs']['helper_seeds'][index]['old_state']^=1
                    with self.assertRaises(ValueError):replay.validate_rng_witnesses(ob,bad)

    def test_unknown_initial_world_names_or_news_reject_before_any_read(self):
        for profile in('mercenary-survivor','mine-survivor'):
            for n in replay.FILES[:3]:
                before=dict(self.before[profile]);before[n]+=b'changed'
                with patch.object(Path,'read_bytes',side_effect=AssertionError('unadmitted file read')):
                    with self.assertRaises(ValueError):replay.synthesize_chain(before,self.inputs[profile])

    def test_unrelated_known_initial_world_is_outside_survivor_scope(self):
        before=combat.old.before_inputs('route-mercenary-37')
        with patch.object(Path,'read_bytes',side_effect=AssertionError('unadmitted read')):
            with self.assertRaises(ValueError):replay.synthesize_chain(before,self.inputs['mercenary-survivor'])

    def test_original_only_initial_inventory_and_raw_immutability_are_required(self):
        profile='mercenary-survivor';before=self.before[profile]
        for bad in(None,self.outputs[profile][2],dict(before,extra=b''),{n:b for n,b in before.items()if n!='YTNEWS.DAT'},dict(before,**{'YTDATA.DAT':bytearray(before['YTDATA.DAT'])})):
            with self.assertRaises(ValueError):replay.synthesize_chain(bad,self.inputs[profile])

    def test_five_day_tuple_and_typed_clock_objects_are_required(self):
        values=self.inputs['mercenary-survivor']
        for bad in(None,list(values),values[:4],values+(values[-1],),(None,)+values[1:],values[:3]+(replace(values[3],clock=None),values[4])):self.reject(bad)

    def test_dates_cannot_skip_repeat_reverse_or_extend_the_five_day_chain(self):
        inputs=self.inputs['mercenary-survivor'];self.reject(inputs[::-1]);self.reject((inputs[0],)*5)
        for index,date in((0,datetime.date(2026,11,1)),(3,datetime.date(2026,11,6)),(4,datetime.date(2026,11,7))):
            changed=list(inputs);changed[index]=replace(inputs[index],clock=replace(inputs[index].clock,startup_date=date));self.reject(tuple(changed))

    def test_mine_survivor_cannot_substitute_a_different_same_date_prefix(self):
        values=self.inputs['mine-survivor'];prefix=values[1]
        self.assertEqual((prefix.clock.news_clock,prefix.clock.score_clock),('00:00:02','00:00:02'))
        changed=replace(prefix,clock=replace(prefix.clock,news_clock='00:00:00',score_clock='00:00:00'))
        self.reject((values[0],changed)+values[2:],'mine-survivor')

    def test_news_and_score_clocks_remain_independent_measured_inputs(self):
        neutral=self.inputs['neutral-survivor'];self.assertEqual((neutral[3].clock.news_clock,neutral[3].clock.score_clock),('00:00:00','00:00:01'))
        self.reject(neutral[:3]+(replace(neutral[3],clock=replace(neutral[3].clock,score_clock='00:00:00')),neutral[4]),'neutral-survivor')
        for name in('news_clock','score_clock'):
            values=self.inputs['mercenary-survivor'];changed=replace(values[3],clock=replace(values[3].clock,**{name:'00:00:09'}));self.reject(values[:3]+(changed,values[4]))

    def test_new_port_planet_and_final_dates_cannot_be_repaired(self):
        values=self.inputs['mercenary-survivor'];day=values[3]
        for clock in(replace(day.clock,port_dates=(datetime.date(2026,11,4),)*1000),replace(day.clock,score_date=datetime.date(2026,11,4)),replace(day.clock,final_date=datetime.date(2026,11,4))):
            self.reject(values[:3]+(replace(day,clock=clock),values[4]))

    def test_mutable_source_arrays_rows_and_schedule_reject(self):
        values=self.inputs['mercenary-survivor'];day=values[3];s=day.schedule
        for changed in(replace(day,schedule=list(s)),replace(day,planet_clocks=list(day.planet_clocks)),replace(day,clock=replace(day.clock,port_dates=list(day.clock.port_dates))),replace(day,schedule=(list(s[0]),)+s[1:]),replace(day,schedule=((s[0][0],True,s[0][2]),)+s[1:])):
            self.reject(values[:3]+(changed,values[4]))

    def test_bad_startup_state_and_incomplete_raw_timer_arrays_reject(self):
        values=self.inputs['mercenary-survivor'];day=values[3]
        for clock in(replace(day.clock,initial_state=-1),replace(day.clock,initial_state=True),replace(day.clock,initial_state=2**24),replace(day.clock,port_timer_minutes=(bytes(3),)*1000),replace(day.clock,port_dates=day.clock.port_dates[:-1])):
            self.reject(values[:3]+(replace(day,clock=clock),values[4]))

    def test_new_helper_caller_order_and_consumption_are_computed(self):
        values=self.inputs['mercenary-survivor'];day=values[3];s=day.schedule
        for changed in(replace(day,schedule=((s[0][0],0x437a,s[0][2]),)+s[1:]),replace(day,schedule=(s[1],s[0])+s[2:]),replace(day,schedule=s[:-1],clock=replace(day.clock,h1_timers=day.clock.h1_timers[:-1]))):
            self.reject(values[:3]+(changed,values[4]))

    def test_source_context_and_observer_completion_are_authenticated(self):
        ob=copy.deepcopy(self.observations['mercenary-survivor'][3]);e=next(e for e in ob['events']if e['before']['runtime_signature']is not None)
        for side in('before','after'):e[side]['caller_code']='00'
        with self.assertRaises((ValueError,AssertionError)):replay.inputs_from_observation(ob)
        for change in(dict(observe=False),dict(exit_code=1),dict(dropped=1),dict(errors=['lost']),dict(events=[])):
            ob=copy.deepcopy(self.observations['mercenary-survivor'][3]);ob.update(change)
            with self.assertRaises((ValueError,AssertionError)):replay.inputs_from_observation(ob)

    def test_actual_three_four_planet_inventories_and_creation_clock_absence(self):
        for profile in PROFILES:
            values=self.inputs[profile];day=values[3];expected=(4052,4053,4150,4151)if profile in('planet-survivor','mine-survivor')else(4052,4150,4151)
            self.assertEqual(tuple(row[0]for row in day.planet_clocks),expected)
            for rows in((),day.planet_clocks[::-1],day.planet_clocks+(day.planet_clocks[0],)):
                self.reject(values[:3]+(replace(day,planet_clocks=rows),values[4]),profile)
        values=self.inputs['mercenary-survivor'];day=values[3]
        for name,value in(('wanderer_date',day.clock.startup_date),('xannoron_date',day.clock.startup_date),('base_date',day.clock.startup_date),('xannoron_timer',bytes(4))):
            self.reject(values[:3]+(replace(day,clock=replace(day.clock,**{name:value})),values[4]))

    def test_each_day_rotates_its_own_modeled_news_and_keeps_private_files(self):
        for profile in PROFILES:
            previous=self.before[profile]
            for output in self.outputs[profile]:
                self.assertEqual(set(output),set(replay.FILES));self.assertTrue(all(type(b)is bytes for b in output.values()))
                self.assertEqual(output['YTNAME.DAT'],previous['YTNAME.DAT']);self.assertEqual(output['YTYNEWS.DAT'],previous['YTNEWS.DAT']);self.assertEqual(output['YTRMSG.DAT'],b'');previous=output

    def test_actual_five_day_survivor_totals_are_derived_without_reset(self):
        expected={
            'mercenary-survivor':[(5148,97525,0),(5148,97525,0),(4966,97337,0),(4966,97337,0),(2433,93846,0)],
            'planet-survivor':[(4022,0,0),(1408,0,0),(616,0,0),(470,0,0),(400,0,0)],
            'neutral-survivor':[(10000,0,37),(10000,0,37),(10000,0,37),(10000,0,37),(8575,0,37)],
            'mine-survivor':[(10000,0,0),(10000,0,0),(9994,0,0),(9176,0,0),(9176,0,0)],
        }
        for profile,totals in expected.items():
            self.assertEqual([tuple(force(o['YTDATA.DAT'],owner)for owner in(-1,-2,0))for o in self.outputs[profile]],totals)
        for output in self.outputs['neutral-survivor']:
            self.assertEqual(mbf.get(output['YTDATA.DAT'],51+854,81),37);self.assertEqual(mbf.get(output['YTDATA.DAT'],51+854,85),0)

    def test_stale_parent_pointer_changes_are_not_canonicalized_or_reused(self):
        prefix,new=self.outputs['mercenary-survivor'][2:4]
        self.assertEqual(mbf.get(prefix['YTDATA.DAT'],51+8,105),109);self.assertEqual(mbf.get(prefix['YTDATA.DAT'],51+109,81),0)
        self.assertEqual(mbf.get(new['YTDATA.DAT'],51+8,105),328);self.assertEqual(mbf.get(new['YTDATA.DAT'],51+328,81),2)

    def test_new_raw_pointer_aliases_remain_shared_physical_locations(self):
        world=self.outputs['mine-survivor'][4]['YTDATA.DAT']
        self.assertEqual((mbf.get(world,51+2,105),mbf.get(world,51+19,105)),(1436,1436))
        self.assertEqual((mbf.get(world,51+13,105),mbf.get(world,51+15,105)),(2369,2369))
        for sector in(1436,2369):self.assertGreater(mbf.get(world,51+sector,81),0);self.assertEqual(mbf.get(world,51+sector,85),-1)

    def test_zero_column_receipt_preserves_independent_physical_losses(self):
        previous,final=self.outputs['mercenary-survivor'][3:]
        self.assertIn(b' *** Mercenaries: lost 1, dstrd 0 (Xannor ftrs dstrd)',final['YTNEWS.DAT'])
        self.assertEqual((force(previous['YTDATA.DAT'],-1)-force(final['YTDATA.DAT'],-1),force(previous['YTDATA.DAT'],-2)-force(final['YTDATA.DAT'],-2)),(2533,3491))
        self.assertEqual(final['YTNEWS.DAT'].count(b'*** Mercenaries: lost'),18)

    def test_four_mercenary_activations_use_force_after_earlier_defense_losses(self):
        rows=self.stats['mercenary-survivor']
        for index,origins,targets in((3,[2368,1680,1389,1082],[1680,1389,1082,2812]),(4,[2812,2499,1351,815],[2499,1351,815,2790])):
            tail=rows[index]['npcs']['mercenary'];moves=tail['activations']
            self.assertEqual([m['origin']for m in moves],origins);self.assertEqual([m['target']for m in moves],targets)
            self.assertTrue(all(a['origin']>b['origin']and a['target']==b['origin']for a,b in zip(moves,moves[1:])))
        tail=rows[4]['npcs']['mercenary']
        self.assertEqual((tail['initial_force'],tail['force'],tail['losses']),(93846,93846,0))
        self.assertEqual(force(self.outputs['mercenary-survivor'][3]['YTDATA.DAT'],-2)-tail['initial_force'],3491)
        self.assertEqual(tail['events'],[])

    def test_added_days_keep_persistent_mines_without_invented_second_deposit(self):
        for output in self.outputs['mine-survivor'][3:]:
            world=output['YTDATA.DAT'];mines={s:int(mbf.get(world,51+s,129))for s in range(1,3001)if mbf.get(world,51+s,129)>0}
            self.assertEqual(mines,{439:1,474:1,1169:1})

    def test_five_day_inputs_and_original_files_remain_immutable(self):
        profile='mercenary-survivor';before=dict(self.before[profile]);inputs=copy.deepcopy(self.inputs[profile])
        replay.synthesize_chain(self.before[profile],self.inputs[profile]);self.assertEqual(self.before[profile],before);self.assertEqual(self.inputs[profile],inputs)


if __name__=='__main__':unittest.main()
