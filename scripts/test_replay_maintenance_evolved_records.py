"""Complete modeled handoffs, independent clocks and narrow-chain admission."""
import builtins
import copy
from dataclasses import fields,replace
import datetime
import gzip
import io
import json
import math
from pathlib import Path
import unittest
from unittest.mock import patch

import replay_maintenance_evolved_records as replay
from replay_qb_graph import mbf,QB3,F32

ROOT=Path(__file__).resolve().parents[1]


def physical(world):
    return sum(int(mbf.get(world,51+s,81))for s in range(1,3001))


class EvolvedChainProperties(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.observations=tuple(json.loads(gzip.decompress((replay.DEFAULT/f'day-{i}'/'observed-a/host-time.json.gz').read_bytes()))for i in(1,2,3))
        cls.inputs=tuple(replay.inputs_from_observation(ob)for ob in cls.observations)
        cls.before=replay.initial_before()
        cls.outputs,cls.stats=replay.synthesize_chain(cls.before,cls.inputs)

    def reject(self,inputs):
        with self.assertRaises((ValueError,AssertionError)):replay.synthesize_chain(self.before,inputs)

    def test_complete_source_chains_match_all_54_native_targets_without_masks(self):
        report=replay.compare_cases()
        self.assertEqual(len(report['cases']),54);self.assertEqual(len(report['statistics']),9)
        self.assertEqual(sum(len(row['files'])for row in report['cases']),324)
        self.assertTrue(all(row['byte_mismatches']==0 for row in report['cases']))
        self.assertEqual(len(report['cache_checks']),36);self.assertEqual(sum(row['fields']for row in report['cache_checks']),1440)

    def test_single_initial_world_and_three_typed_clock_inputs_are_the_public_api(self):
        self.assertEqual(set(self.before),set(replay.FILES[:3]))
        self.assertEqual({f.name for f in fields(replay.Inputs)},{'clock','schedule','planet_clocks'})
        self.assertEqual(replay.SHA(self.before['YTDATA.DAT']),replay.INITIAL_SHA)
        self.assertEqual([x.clock.startup_date for x in self.inputs],[datetime.date(2026,11,d)for d in(2,3,4)])
        self.assertTrue(all(len(x)==3 and type(x[2])is bytes for day in self.inputs for x in day.schedule))

    def test_actual_chain_passes_the_prior_modeled_six_file_object_forward(self):
        real=replay._synthesize_day;seen=[];made=[]
        def spy(before,inputs):
            seen.append(before);result=real(before,inputs);made.append(result[0]);return result
        with patch.object(replay,'_synthesize_day',side_effect=spy):outputs,stats=replay.synthesize_chain(self.before,self.inputs)
        self.assertEqual(outputs,self.outputs);self.assertEqual(stats,self.stats)
        self.assertEqual(seen[0],self.before)
        self.assertIs(seen[1],made[0]);self.assertIs(seen[2],made[1])
        self.assertEqual(set(seen[1]),set(replay.FILES));self.assertEqual(set(seen[2]),set(replay.FILES))

    def test_handoff_cannot_substitute_native_child_files_for_modeled_markers(self):
        seen=[];made=[]
        def synthesize(before,inputs):
            seen.append(dict(before));n=len(made)
            result={name:before.get(name,b'')for name in replay.FILES}
            result['YTNEWS.DAT']=f'modeled-only-{n}'.encode();made.append(result)
            return result,{'derived_stage':n}
        with patch.object(replay,'_synthesize_day',side_effect=synthesize),patch.object(Path,'read_bytes',side_effect=AssertionError('native child file read')):
            output,stats=replay.synthesize_chain(self.before,self.inputs)
        self.assertEqual(seen[1]['YTNEWS.DAT'],b'modeled-only-0');self.assertEqual(seen[2]['YTNEWS.DAT'],b'modeled-only-1')
        self.assertEqual(output,tuple(made));self.assertEqual([x['derived_stage']for x in stats],[0,1,2])

    def test_entire_core_chain_reads_only_the_immutable_original(self):
        allowed=ROOT/'archive/dos-original/YTMAINT.EXE';original_bytes=Path.read_bytes;original_open=io.open
        def byte_guard(path):
            if path!=allowed:raise AssertionError('core read target/probe/recipe/child: '+str(path))
            return original_bytes(path)
        def open_guard(path,*args,**kwargs):
            if Path(path)!=allowed:raise AssertionError('core open target/probe/recipe/child: '+str(path))
            return original_open(path,*args,**kwargs)
        with patch.object(Path,'read_bytes',byte_guard),patch.object(Path,'read_text',side_effect=AssertionError('core target text read')),patch.object(io,'open',side_effect=open_guard),patch.object(builtins,'open',side_effect=open_guard):
            output,stats=replay.synthesize_chain(self.before,self.inputs)
        self.assertEqual(output,self.outputs);self.assertEqual(stats,self.stats)

    def test_poisoned_raw_rng_witnesses_cannot_change_inputs_or_outputs(self):
        poisoned=copy.deepcopy(self.observations)
        for ob in poisoned:
            for event in ob['events']:
                for side in('before','after'):event[side]['rng_raw']='00000000'
        inputs=tuple(replay.inputs_from_observation(ob)for ob in poisoned)
        self.assertEqual(inputs,self.inputs)
        output,stats=replay.synthesize_chain(self.before,inputs);self.assertEqual(output,self.outputs)
        for ob,row in zip(poisoned,stats):
            with self.assertRaises(ValueError):replay.validate_rng_witnesses(ob,row)

    def test_source_extraction_never_mutates_retained_observations(self):
        observations=copy.deepcopy(self.observations);saved=copy.deepcopy(observations)
        self.assertEqual(tuple(replay.inputs_from_observation(ob)for ob in observations),self.inputs)
        self.assertEqual(observations,saved)

    def test_all_helper_and_final_rng_states_are_independently_audited(self):
        for ob,row in zip(self.observations,self.stats):
            count=replay.validate_rng_witnesses(ob,row)
            self.assertEqual(count,len(row['npcs']['helper_seeds'])+2)
        row=copy.deepcopy(self.stats[1]);row['npcs']['helper_seeds'][0]['old_state']^=1
        with self.assertRaises(ValueError):replay.validate_rng_witnesses(self.observations[1],row)
        row=copy.deepcopy(self.stats[2]);row['npcs']['final_rng_state']^=1
        with self.assertRaises(ValueError):replay.validate_rng_witnesses(self.observations[2],row)

    def test_unknown_initial_world_rejects_before_any_file_read(self):
        before=dict(self.before);world=bytearray(before['YTDATA.DAT']);world[12345]^=1;before['YTDATA.DAT']=bytes(world)
        with patch.object(Path,'read_bytes',side_effect=AssertionError('no reads admitted')):
            with self.assertRaises(ValueError):replay.synthesize_chain(before,self.inputs)

    def test_changed_initial_names_or_old_news_reject_before_file_reads(self):
        for name in('YTNAME.DAT','YTNEWS.DAT'):
            before=dict(self.before);before[name]+=b'changed'
            with self.subTest(name=name),patch.object(Path,'read_bytes',side_effect=AssertionError('no reads admitted')):
                with self.assertRaises(ValueError):replay.synthesize_chain(before,self.inputs)

    def test_unknown_initial_container_and_child_six_file_inventory_reject(self):
        for before in(None,dict(self.before,extra=b''),{n:b for n,b in self.before.items()if n!='YTNEWS.DAT'},dict(self.before,YTDATA=bytearray()),self.outputs[0],dict(self.before,**{'YTDATA.DAT':bytearray(self.before['YTDATA.DAT'])})):
            with self.subTest(type=type(before)),self.assertRaises(ValueError):replay.synthesize_chain(before,self.inputs)

    def test_unknown_day_input_containers_lengths_and_classes_reject(self):
        for inputs in(None,list(self.inputs),self.inputs[:2],self.inputs+(self.inputs[2],),(None,)+self.inputs[1:],(dict(clock=self.inputs[0].clock,schedule=self.inputs[0].schedule,planet_clocks=self.inputs[0].planet_clocks),)+self.inputs[1:],(replace(self.inputs[0],clock=None),)+self.inputs[1:]):self.reject(inputs)

    def test_reordered_or_repeated_day_inputs_do_not_reset_the_chain(self):
        self.reject(self.inputs[::-1]);self.reject((self.inputs[0],)*3)
        changed=replace(self.inputs[1],clock=replace(self.inputs[1].clock,startup_date=datetime.date(2026,11,4)))
        self.reject((self.inputs[0],changed,self.inputs[2]))

    def test_mutable_source_input_arrays_and_rows_reject(self):
        first=self.inputs[0]
        for altered in(replace(first,schedule=list(first.schedule)),replace(first,planet_clocks=list(first.planet_clocks)),replace(first,clock=replace(first.clock,port_dates=list(first.clock.port_dates))),replace(first,clock=replace(first.clock,h1_timers=list(first.clock.h1_timers)))):
            self.reject((altered,)+self.inputs[1:])

    def test_seed_widths_and_malformed_port_inventories_reject(self):
        first=self.inputs[0]
        for clock in(replace(first.clock,initial_state=-1),replace(first.clock,initial_state=2**24),replace(first.clock,initial_state=True),replace(first.clock,port_dates=first.clock.port_dates[:-1]),replace(first.clock,port_timer_minutes=first.clock.port_timer_minutes[:-1]),replace(first.clock,port_timer_minutes=(bytes(3),)*1000)):
            self.reject((replace(first,clock=clock),)+self.inputs[1:])

    def test_helper_calls_are_computed_and_wrong_family_caller_order_reject(self):
        first=self.inputs[0];s=first.schedule
        schedules=[((s[0][0],0x437a,s[0][2]),)+s[1:], (('h2',s[0][1],s[0][2]),)+s[1:],(s[1],s[0])+s[2:]]
        for schedule in schedules:self.reject((replace(first,schedule=schedule),)+self.inputs[1:])

    def test_helper_clock_exhaustion_and_unconsumed_suffix_reject(self):
        first=self.inputs[0];last=first.schedule[-1];self.assertEqual(last[0],'h1')
        short=replace(first,schedule=first.schedule[:-1],clock=replace(first.clock,h1_timers=first.clock.h1_timers[:-1]))
        extra=replace(first,schedule=first.schedule+(last,),clock=replace(first.clock,h1_timers=first.clock.h1_timers+(last[2],)))
        self.reject((short,)+self.inputs[1:]);self.reject((extra,)+self.inputs[1:])

    def test_mutable_malformed_or_conflicting_helper_clock_rows_reject(self):
        first=self.inputs[0];s=first.schedule
        for schedule in(((s[0][0],s[0][1],bytes(3)),)+s[1:],((s[0][0],True,s[0][2]),)+s[1:],(list(s[0]),)+s[1:]):
            self.reject((replace(first,schedule=schedule),)+self.inputs[1:])
        self.reject((replace(first,clock=replace(first.clock,h2_timers=())),)+self.inputs[1:])

    def test_planet_clock_inventory_identity_order_and_types_reject(self):
        first=self.inputs[0];row=first.planet_clocks[0]
        for clocks in((),first.planet_clocks+(row,),((4052,row[1],row[2]),),((row[0],row[1],bytes(3)),),(list(row),)):
            self.reject((replace(first,planet_clocks=clocks),)+self.inputs[1:])
        second=replace(self.inputs[1],planet_clocks=self.inputs[1].planet_clocks[::-1])
        self.reject((first,second,self.inputs[2]))

    def test_optional_creation_clocks_follow_actual_home_presence(self):
        first=self.inputs[0]
        for clock in(replace(first.clock,wanderer_date=None),replace(first.clock,xannoron_date=None),replace(first.clock,xannoron_timer=None),replace(first.clock,base_date=None)):
            self.reject((replace(first,clock=clock),)+self.inputs[1:])
        for name,value in(('wanderer_date',datetime.date(2026,11,3)),('xannoron_date',datetime.date(2026,11,3)),('xannoron_timer',bytes(4)),('base_date',datetime.date(2026,11,3))):
            second=replace(self.inputs[1],clock=replace(self.inputs[1].clock,**{name:value}))
            self.reject((first,second,self.inputs[2]))

    def test_calendar_rollback_or_wrong_port_calendar_is_not_repaired(self):
        first=self.inputs[0]
        for clock in(replace(first.clock,final_date=datetime.date(2026,11,1)),replace(first.clock,port_dates=(datetime.date(2026,11,3),)*1000),replace(first.clock,base_date=datetime.date(2026,11,1))):
            self.reject((replace(first,clock=clock),)+self.inputs[1:])

    def test_invalid_observer_mode_or_incomplete_capture_is_rejected(self):
        for change in(dict(observe=False),dict(recipe='other'),dict(exit_code=1),dict(errors=['lost']),dict(dropped=1),dict(events=[])):
            ob=copy.deepcopy(self.observations[0]);ob.update(change)
            with self.subTest(change=list(change)),self.assertRaises(ValueError):replay.inputs_from_observation(ob)

    def test_actual_converged_force_loads_once_and_allocations_are_dynamic(self):
        self.assertEqual([s['npcs']['helper_calls']['h2']for s in self.stats],[19,17,0])
        first=self.outputs[0]['YTDATA.DAT'];self.assertEqual([mbf.get(first,51+g,105)for g in range(2,20)],[2802]*18)
        force=sum(self.stats[0]['npcs']['groups'][g]['strength']for g in range(2,20))
        self.assertEqual(force,6552);self.assertEqual(mbf.get(first,2853,81),force)
        self.assertEqual(self.stats[1]['npcs']['groups'][2]['strength'],force)
        self.assertEqual([s['npcs']['normalized_total']for s in self.stats],[10000]*3)
        self.assertTrue(all(physical(output['YTDATA.DAT'])==10000 for output in self.outputs))

    def test_source_cache_arrays_derive_from_the_prior_modeled_physical_world(self):
        second=self.stats[1]['npcs'];third=self.stats[2]['npcs']
        self.assertEqual(second['cache_locations'],{1:849,2:2802,**{g:0 for g in range(3,20)},20:1169})
        self.assertEqual(second['cache_forces'],{1:3095,2:6552,**{g:0 for g in range(3,20)},20:353})
        self.assertEqual(len(set(third['cache_locations'].values())),20)
        for index,npc in((0,second),(1,third)):
            previous=self.outputs[index]['YTDATA.DAT'];seen=set()
            for group,sector in npc['cache_locations'].items():
                if not sector:self.assertEqual(npc['cache_forces'][group],0);continue
                self.assertNotIn(sector,seen);seen.add(sector)
                self.assertEqual(npc['cache_forces'][group],mbf.get(previous,51+sector,81))
            self.assertEqual(sum(npc['cache_forces'].values()),10000)

    def test_creation_TIMER_malformed_type_and_width_are_never_silently_coerced(self):
        first=self.inputs[0]
        for raw in(bytes(3),bytearray(4),0,'00000000'):
            with self.subTest(raw_type=type(raw)):
                self.reject((replace(first,clock=replace(first.clock,xannoron_timer=raw)),)+self.inputs[1:])

    def test_persistent_mines_are_not_erased_between_modeled_days(self):
        for output,expected in zip(self.outputs,({1169},{1169,439},{1169,439,474})):
            world=output['YTDATA.DAT'];mines={s for s in range(1,3001)if mbf.get(world,51+s,129)>0}
            self.assertEqual(mines,expected)
            self.assertTrue(all(mbf.get(world,51+s,129)==1 for s in mines))

    def test_homes_exist_and_later_days_do_not_republish_creation(self):
        self.assertEqual([s['npcs']['created']for s in self.stats],[('wanderer','xannoron','base'),(),()])
        self.assertEqual([s['npcs']['wanderer_sector']for s in self.stats],[2787,2255,2290])
        self.assertEqual([s['npcs']['base_sector']for s in self.stats],[2177]*3)
        for index,output in enumerate(self.outputs):
            world=output['YTDATA.DAT'];self.assertEqual({r for r in range(4052,4152)if mbf.get(world,r,85)>0},{4052,4053,4150,4151})
            for notice in(b'P.H.O.E.N.I.X.',b'have made a Planet!',b'captured Genesis Device!'):
                self.assertEqual(output['YTNEWS.DAT'].count(notice),1 if index==0 else 0)

    def test_all_side_files_and_inactive_ranks_flow_through_each_modeled_day(self):
        previous=self.before
        for index,output in enumerate(self.outputs):
            self.assertEqual(output['YTNAME.DAT'],previous['YTNAME.DAT']);self.assertEqual(output['YTYNEWS.DAT'],previous['YTNEWS.DAT']);self.assertEqual(output['YTRMSG.DAT'],b'')
            world=output['YTDATA.DAT']
            self.assertTrue(all(mbf.get(world,r,109)==-1 for r in range(2,52)))
            self.assertIn(f'11-0{2+index}-2026'.encode(),output['YTNEWS.DAT']);self.assertIn(f'11-0{2+index}-2026'.encode(),output['YTSCORE.ASC'])
            previous=output

    def test_existing_xannoron_still_gets_source_common_random_ground_increment(self):
        for index in(1,2):
            stats=self.stats[index]['npcs'];planet=next(row for row in stats['active_planets']['rows']if row['record']==4151)
            self.assertEqual(len(stats['wanderer_attempts']),1)
            first=stats['helper_seeds'][0];self.assertEqual(first['caller'],0x1f88)
            rng=QB3(first['seeded_state']);rng.integer(3000);added=math.floor(F32(rng.rnd()*25))
            self.assertEqual(mbf.get(self.outputs[index]['YTDATA.DAT'],4151,77),planet['ground']+added)
            self.assertEqual(stats['helper_seeds'][1]['old_state'],rng.state)



class PlanetSourceBindingTests(unittest.TestCase):
    def test_raw_source_planet_indices_bind_actual_date_timer_pairs(self):
        import verify_maintenance_clock_matrix as source
        from replay_qb_graph import mbf
        original=json.loads(gzip.decompress((replay.DEFAULT/'day-2/observed-a/host-time.json.gz').read_bytes()))
        for changed_kind in ('timer','date','both'):
            ob=copy.deepcopy(original);changed=0
            for event in ob['events']:
                row=copy.deepcopy(event)
                for side in ('before','after'):row[side].pop('rng_raw')
                pair=source.event_pair(row,row['ordinal'])
                planet=(pair.get('kind')=='timer'and pair.get('role')=='planet')or(pair.get('kind')=='date'and pair.get('role')=='calendar'and source.CALENDAR_CALLERS[pair['nested_return_ip']]=='planet')
                if planet and mbf.dec(bytes.fromhex(event['before']['port_raw']))==1 and(changed_kind=='both'or pair['kind']==changed_kind):
                    for side in ('before','after'):event[side]['port_raw']=mbf.enc(3).hex()
                    changed+=1
            self.assertEqual(changed,2 if changed_kind=='both'else 1)
            with self.subTest(kind=changed_kind),self.assertRaises(ValueError):replay.inputs_from_observation(ob)

if __name__=='__main__':unittest.main()
