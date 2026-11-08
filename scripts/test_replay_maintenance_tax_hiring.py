"""Before-only boundaries, exact native comparisons, and hostile ledger controls."""
import builtins
import copy
from dataclasses import replace
import gzip
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import replay_maintenance_tax_hiring_records as replay
from replay_maintenance_tax_hiring_rng import verify,verify_hiring
from replay_maintenance_tax_hiring_rules import tax_ports,hire
from replay_maintenance_tax_hiring_aux import synthesize as publish
from replay_maintenance_collision_records import validate_rng_witnesses
from replay_qb_graph import mbf


class TaxReplay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before=replay.initial_before();cls.inputs={};cls.observations={};cls.outputs={};cls.stats={}
        for case in replay.CASES:
            observations=tuple(json.loads(gzip.decompress(p.read_bytes()))for p in replay.observation_paths(case,'observed-a'))
            cls.observations[case]=observations;cls.inputs[case]=tuple(replay.inputs_from_observation(o)for o in observations)
            cls.outputs[case],cls.stats[case]=replay.synthesize_chain(cls.before,case,cls.inputs[case])

    def test_complete_matrix_before_target_loading(self):
        real=replay.synthesize_chain;read=Path.read_bytes;sequence=[]
        def model(*args):
            result=real(*args);sequence.append('modeled');return result
        def guarded(path):
            if path.name.startswith('after-'):
                self.assertTrue(sequence);sequence.append('target')
            return read(path)
        with patch.object(replay,'synthesize_chain',side_effect=model),patch.object(Path,'read_bytes',guarded):report=replay.compare_cases()
        self.assertEqual(sequence,(['modeled']+['target']*72)*6)
        self.assertEqual((len(report['cases']),len(report['statistics'])),(72,12))
        self.assertTrue(all(row['byte_mismatches']==0 for row in report['cases']))
        self.assertEqual({(c['profile'],c['child'],c['observation'],c['target'])for c in report['cases']},{(c,d,o,t)for c in replay.CASES for d in(1,2)for o in('observed-a','observed-b','observed-c')for t in replay.MODES})

    def test_core_cannot_read_captures_or_native_handoffs(self):
        read=Path.read_bytes
        def only_original(path):
            if path!=replay.ROOT/'archive/dos-original/YTMAINT.EXE':raise AssertionError(str(path))
            return read(path)
        with patch.object(Path,'read_bytes',only_original),patch.object(builtins,'open',side_effect=AssertionError('unqualified input read')):
            output,_=replay.synthesize_chain(self.before,'ten-groups',self.inputs['ten-groups'])
        self.assertEqual(output,self.outputs['ten-groups'])

    def test_fixture_and_children_pass_actual_modeled_objects(self):
        prefix=replay.combat.synthesize_chain;fixture=replay.apply_fixture;child=replay._synthesize_day;parents=[];made=[];edited=[];seen=[]
        def pre(*args):
            out=prefix(*args);parents.extend(out[0]);return out
        def intervene(files,case):
            self.assertIs(files,parents[-1]);out=fixture(files,case);edited.append(out);return out
        def nextday(files,inputs):
            seen.append(files);out=child(files,inputs);made.append(out[0]);return out
        with patch.object(replay.combat,'synthesize_chain',side_effect=pre),patch.object(replay,'apply_fixture',side_effect=intervene),patch.object(replay,'_synthesize_day',side_effect=nextday):
            result,_=replay.synthesize_chain(self.before,'one-group',self.inputs['one-group'])
        self.assertIs(seen[0],edited[0]);self.assertIs(seen[1],made[0]);self.assertIs(result[4],made[1])

    def test_fixture_changes_only_four_bytes_and_preserves_parent(self):
        parent=self.outputs['one-group'][2];saved=copy.deepcopy(parent)
        for case,amount in replay.CASES.items():
            out=replay.apply_fixture(parent,case);at=(3053-1)*137+89
            self.assertEqual(out['YTDATA.DAT'],parent['YTDATA.DAT'][:at]+mbf.enc(amount)+parent['YTDATA.DAT'][at+4:])
            for name in replay.FILES:
                if name!='YTDATA.DAT':self.assertIs(out[name],parent[name])
        self.assertEqual(parent,saved)

    def test_captured_rng_bytes_are_not_model_inputs(self):
        observations=copy.deepcopy(self.observations['one-group'])
        for ob in observations:
            for event in ob['events']:
                for side in('before','after'):event[side]['rng_raw']='ffffffff'
        inputs=tuple(replay.inputs_from_observation(o)for o in observations)
        self.assertEqual(inputs,self.inputs['one-group'])

    def test_all_helper_and_final_witnesses_agree(self):
        for case in replay.CASES:
            for index in(3,4):
                self.assertGreater(validate_rng_witnesses(self.observations[case][index],self.stats[case][index]),2)
        row=copy.deepcopy(self.stats['ten-groups'][3]);row['npcs']['helper_seeds'][0]['old_state']^=1
        with self.assertRaises(ValueError):validate_rng_witnesses(self.observations['ten-groups'][3],row)

    def test_clock_and_case_boundaries(self):
        values=self.inputs['one-group'];row=values[3]
        invalid=[values[:-1],list(values),values[:3]+(values[4],values[3])]
        for schedule in(list(row.schedule),row.schedule[:-1],(('h1',0x9999,row.schedule[0][2]),)+row.schedule[1:]):invalid.append(values[:3]+(replace(row,schedule=schedule),values[4]))
        for key in('port_dates','port_timer_minutes','h1_timers','h2_timers'):
            invalid.append(values[:3]+(replace(row,clock=replace(row.clock,**{key:list(getattr(row.clock,key))})),values[4]))
        invalid.append(values[:3]+(replace(row,clock=replace(row.clock,news_clock='00:00:01')),values[4]))
        invalid.append(values[:3]+(replace(row,planet_clocks=list(row.planet_clocks)),values[4]))
        for inputs in invalid:
            with self.subTest(inputs_type=type(inputs)),self.assertRaises((ValueError,AssertionError)):replay.synthesize_chain(self.before,'one-group',inputs)
        with self.assertRaises(ValueError):replay.synthesize_chain(self.before,'unknown',values)
        world=bytearray(self.before['YTDATA.DAT']);world[0]^=1
        with self.assertRaises(ValueError):replay.synthesize_chain({**self.before,'YTDATA.DAT':bytes(world)},'one-group',values)

    def test_tax_hiring_and_loss_ledgers(self):
        expected={'one-group':[(10,1,90),(9,0,81)],'ten-groups':[(100,10,900),(90,9,810)]}
        for case,rows in expected.items():
            for index,(tax,hired,balance)in enumerate(rows,3):
                stats=self.stats[case][index]['npcs'];world=self.outputs[case][index]['YTDATA.DAT']
                self.assertEqual((stats['taxation']['tax'],stats['hiring']['hired'],mbf.get(world,3053,89)),(tax,hired,balance))
        events=self.stats['ten-groups'][3]['npcs']['mercenary']['events'];self.assertEqual(sum(e['kind']=='mercenary-mine'for e in events),1)
        self.assertEqual(sum(e['kind']=='mercenary-attack'and e['force']==0 for e in events),3)
        self.assertTrue(any(e['kind']=='mercenary-merge'for e in self.stats['ten-groups'][4]['npcs']['mercenary']['events']))

    def action_inputs(self):
        row=self.stats['ten-groups'][3]['npcs'];events=tuple(row['events'])+tuple(e for e in row['mercenary']['events']if e['kind']!='mercenary-merge')
        return row,copy.deepcopy(events)

    def test_coherent_event_seed_forgery_rejected(self):
        from types import SimpleNamespace
        from replay_qb_graph import QB3
        from replay_maintenance_tax_hiring_mercenary import attack
        row,events=self.action_inputs();index=next(i for i,e in enumerate(events)if e['kind']=='mercenary-attack');event=events[index]
        world=bytearray(self.outputs['ten-groups'][2]['YTDATA.DAT']);record=51+event['sector']
        for offset,value in((81,event['initial_defenders']),(85,-1),(93,0),(129,0)):mbf.put(world,record,offset,value)
        forged=attack(world,SimpleNamespace(rng=QB3(event['initial_rng_state']^1)),event['sector'],event['initial_force'])
        changed=list(events);changed[index]=forged
        with self.assertRaises(ValueError):verify(row['rng_audit'],row['rng_source'],row['rng_contexts'],tuple(changed))

    def test_coherent_casualties_forgery_rejected(self):
        row,events=self.action_inputs();event=next(e for e in events if e['kind']=='mercenary-attack');event['force']=1;event['losses']=event['initial_force']-1
        with self.assertRaises(ValueError):verify(row['rng_audit'],row['rng_source'],row['rng_contexts'],events)

    def test_action_inventory_and_source_walk_forgery_rejected(self):
        row,events=self.action_inputs()
        with self.assertRaises(ValueError):verify(row['rng_audit'],row['rng_source'],row['rng_contexts'],events[:-1])
        corrupt=copy.deepcopy(events);corrupt[0]['sector']^=1
        with self.assertRaises(ValueError):verify(row['rng_audit'],row['rng_source'],row['rng_contexts'],corrupt)
        audit=replace(row['rng_audit'],initial_state=row['rng_audit'].initial_state^1)
        with self.assertRaises(ValueError):verify(audit,row['rng_source'],row['rng_contexts'],events)
        operations=list(row['rng_audit'].operations);i=next(i for i,op in enumerate(operations)if op[0]=='draw');operations[i]=('draw',operations[i][1]+1)
        with self.assertRaises(ValueError):verify(replace(row['rng_audit'],operations=tuple(operations)),row['rng_source'],row['rng_contexts'],events)

    def test_hiring_placements_bind_source_rng(self):
        row=self.stats['ten-groups'][3]['npcs'];hiring=copy.deepcopy(row['hiring']);hiring['placements'][0]['sector']=3;hiring['placements'][0]['attempts'][-1]=3
        with self.assertRaises(ValueError):verify_hiring(row['rng_audit'],hiring)

    def test_raw_zero_treasury_residues_survive(self):
        before=replay.apply_fixture(self.outputs['one-group'][2],'one-group');world=bytearray(before['YTDATA.DAT']);at=(3054-1)*137+89;raw=bytes(world[at:at+4]);self.assertNotEqual(raw,bytes(4))
        tax_ports(world);self.assertEqual(bytes(world[at:at+4]),raw)

    def test_unmeasured_treasury_and_asking_prices_rejected(self):
        parent=replay.apply_fixture(self.outputs['one-group'][2],'one-group')
        for r,o,n in((3053,89,-1),(3053,89,1001),(3053,89,1.5),(3054,89,10),(3053,97,1)):
            world=bytearray(parent['YTDATA.DAT']);mbf.put(world,r,o,n)
            with self.subTest(record=r,value=n),self.assertRaises(ValueError):tax_ports(world)

    def test_hiring_retries_occupied_sector_and_accepts_union(self):
        world=bytearray(self.outputs['one-group'][2]['YTDATA.DAT']);mbf.put(world,53,81,1);mbf.put(world,54,81,0)
        class Stream:
            def placement_attempt(self,*args):pass
            def __init__(self):self.calls=[];self.values=iter((1,2))
            def one(self,bound,caller):self.calls.append((bound,caller));return next(self.values)
        stream=Stream();result=hire(world,stream,10)
        self.assertEqual(result['placements'],[dict(sector=3,force=1,attempts=[2,3])]);self.assertEqual(stream.calls,[(2999,0x4546)]*2);self.assertEqual(mbf.get(world,54,85),-2)

    def publication(self,mutate):
        case='ten-groups';inputs=self.inputs[case][3];clock=inputs.clock
        before=replay.apply_fixture(self.outputs[case][2],case);world=self.outputs[case][3]['YTDATA.DAT'];row=copy.deepcopy(self.stats[case][3]['npcs'])
        before,world,row=mutate(before,world,row)
        return publish(before,world,clock.news_date,clock.news_clock,clock.score_date,clock.score_clock,created=row['created'],events=row['events'],mercenary=row['mercenary'],taxation=row['taxation'],hiring=row['hiring'],rng_audit=row['rng_audit'],rng_source=row['rng_source'],rng_contexts=row['rng_contexts'])

    def test_publication_checks_force_conservation(self):
        def change(before,world,row):
            data=bytearray(world);sector=row['mercenary']['final_sectors'][0];mbf.put(data,51+sector,81,mbf.get(data,51+sector,81)+1)
            return before,bytes(data),row
        with self.assertRaises(ValueError):self.publication(change)

    def test_publication_checks_exact_zero_treasury_bytes(self):
        def change(before,world,row):
            data=bytearray(world);at=(3054-1)*137+89;data[at:at+4]=bytes(4);return before,bytes(data),row
        with self.assertRaises(ValueError):self.publication(change)

    def test_publication_rejects_forged_hiring_count(self):
        def change(before,world,row):
            row['hiring']['hired']+=1;return before,world,row
        with self.assertRaises(ValueError):self.publication(change)

    def test_publication_rejects_forged_event_seed(self):
        def change(before,world,row):
            row['mercenary']['events'][0]['initial_rng_state']^=1;return before,world,row
        with self.assertRaises(ValueError):self.publication(change)

    def test_earth_raw_zero_treasury_corruption_rejected(self):
        def change(before,world,row):
            data=bytearray(world);at=(3052-1)*137+89
            raw=bytes(data[at:at+4]);replacement=bytes.fromhex('01000000')
            self.assertNotEqual(raw,replacement);self.assertEqual(mbf.dec(replacement),0)
            data[at:at+4]=replacement;return before,bytes(data),row
        with self.assertRaises(ValueError):self.publication(change)

    def test_regrouped_attempts_cannot_claim_occupied_sector(self):
        from replay_maintenance_tax_hiring_rng import SourceStream
        schedule=tuple(('h1',0x4546,mbf.enc(2))for _ in range(64))
        probe=SourceStream(schedule,5);occupied=probe.one(2999,caller=0x4546)+1
        world=bytearray(4151*137);mbf.put(world,51+occupied,81,1)
        stream=SourceStream(schedule,5);hiring=hire(world,stream,100)
        self.assertGreater(len(hiring['placements'][0]['attempts']),1)
        verify_hiring(stream.audit(),hiring)
        forged=copy.deepcopy(hiring);first=forged['placements'][0];second=forged['placements'][1]
        moved=first['attempts'].pop();first['sector']=first['attempts'][-1];second['attempts'].insert(0,moved)
        self.assertEqual([n for p in forged['placements']for n in p['attempts']],[n for p in hiring['placements']for n in p['attempts']])
        self.assertEqual(first['sector'],occupied)
        with self.assertRaises(ValueError):verify_hiring(stream.audit(),forged)

    def test_no_hiring_has_no_draws_and_capacity_is_bounded_failure(self):
        world=bytearray(self.outputs['one-group'][2]['YTDATA.DAT'])
        class NoDraw:
            def one(self,*args,**kwargs):raise AssertionError('unexpected helper')
        self.assertEqual(hire(world,NoDraw(),9)['placements'],[])
        class Blocked:
            def placement_attempt(self,*args):pass
            def one(self,*args,**kwargs):return 1
        mbf.put(world,53,81,1)
        with self.assertRaises(ValueError):hire(world,Blocked(),10)


if __name__=='__main__':unittest.main()
