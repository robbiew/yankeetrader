"""Independent semantic and provenance corruption controls for the full chain."""
import copy
import gzip
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import verify_maintenance_convergence as v


def put(world,record,offset,value):
    result=bytearray(world);at=(record-1)*137+offset;result[at:at+4]=v.encode(value);return bytes(result)


class ConvergenceEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=v.DEFAULT;cls.observer=(cls.root/'acquisition/observe_maintenance_placement.js').read_text();cls.cases={};cls.observations={}
        for day,(_,parent)in v.DAYS.items():
            before={n:gzip.decompress((cls.root/day/'observed-a'/('before-'+n+'.gz')).read_bytes())for n in(v.FILES[:3]if parent is None else v.FILES)}
            outputs={n:gzip.decompress((cls.root/day/'observed-a'/('after-'+n+'.gz')).read_bytes())for n in v.FILES}
            cls.cases[day]=dict(before=before,outputs=outputs)
            cls.observations[day]=json.loads(gzip.decompress((cls.root/day/'observed-a/host-time.json.gz').read_bytes()))
        cls.probe=cls.root/'day-2/cache-observed-a'
        cls.probe_before=gzip.decompress((cls.probe/'before-YTDATA.DAT.gz').read_bytes());cls.probe_world=gzip.decompress((cls.probe/'after-YTDATA.DAT.gz').read_bytes());cls.probe_trace=(cls.probe/'TRACE.BIN').read_bytes()

    def test_complete_independent_corpus(self):
        r=v.verify();self.assertEqual((r['days'],r['full_runs'],r['cache_probes'],r['full_output_files']),(3,18,12,108))
        self.assertEqual(r['stages']['day-1']['max_pointer_multiplicity'],18)
        self.assertEqual(r['stages']['day-2']['cache_consumed'],3)
        self.assertEqual(r['stages']['day-3']['cache_consumed'],20)

    def test_initial_input_reconstructed_independently(self):
        self.assertEqual(self.cases['day-1']['before'],v.initial_inputs())
        before=v.initial_inputs()['YTDATA.DAT'];self.assertEqual(v.field(before,2853,93),2);self.assertEqual(v.field(before,4053,85),17)

    def test_every_parent_file_is_inherited_exactly(self):
        for day,parent in [('day-2','day-1'),('day-3','day-2')]:
            self.assertEqual(self.cases[day]['before'],self.cases[parent]['outputs'])
            v.verify_inheritance(self.cases[day]['before'],self.cases[parent]['outputs'])

    def test_altering_any_inherited_file_rejects(self):
        for name in v.FILES:
            before=copy.deepcopy(self.cases['day-2']['before']);before[name]+=b'changed'
            with self.subTest(name=name),self.assertRaisesRegex(AssertionError,'exact parent'):v.verify_inheritance(before,self.cases['day-1']['outputs'])

    def test_missing_or_extra_inherited_file_rejects(self):
        for change in('missing','extra'):
            before=dict(self.cases['day-2']['before'])
            if change=='missing':before.pop('YTSCORE.ASC')
            else:before['other.dat']=b''
            with self.subTest(change=change),self.assertRaises(AssertionError):v.verify_inheritance(before,self.cases['day-1']['outputs'])

    def test_skipping_a_generation_rejects(self):
        with self.assertRaises(AssertionError):v.verify_inheritance(self.cases['day-3']['before'],self.cases['day-1']['outputs'])

    def test_paired_output_mutation_rejects(self):
        outputs=self.cases['day-1']['outputs'];rows={m:dict(outputs=dict(outputs))for m in v.MODES};v.verify_paired_outputs(rows)
        rows['observed-c']['outputs']['YTNEWS.DAT']+=b'x'
        with self.assertRaises(AssertionError):v.verify_paired_outputs(rows)

    def test_missing_pair_or_output_rejects(self):
        rows={m:dict(outputs=dict(self.cases['day-1']['outputs']))for m in v.MODES};rows.pop('attach-only')
        with self.assertRaises(AssertionError):v.verify_paired_outputs(rows)
        rows={m:dict(outputs=dict(self.cases['day-1']['outputs']))for m in v.MODES};rows['observed-a']['outputs'].pop('YTRMSG.DAT')
        with self.assertRaises(AssertionError):v.verify_paired_outputs(rows)

    def test_saved_force_is_not_multiplied_by_duplicate_pointers(self):
        world=self.cases['day-1']['outputs']['YTDATA.DAT'];self.assertEqual(v.physical(world),10000)
        self.assertEqual(v.field(world,2853,81),6552)
        payload,sectors=v.placement.expected_cache(world);self.assertEqual(sectors,{849,2802,1169})
        self.assertEqual(v.clocks.neutral.mbf_fraction(payload[4*23:4*24]),6552)
        for group in range(3,20):
            self.assertEqual(payload[4*group:4*group+4],bytes(4));self.assertEqual(payload[4*(group+21):4*(group+22)],bytes(4))

    def test_physical_force_owner_and_fraction_reject(self):
        world=self.cases['day-1']['outputs']['YTDATA.DAT']
        for altered in(put(world,2853,81,-1),put(world,2853,81,.5),put(world,2853,85,0)):
            with self.assertRaises(AssertionError):v.physical(altered)

    def test_force_loss_and_invention_reject(self):
        for amount in(6551,6553):
            outputs=dict(self.cases['day-1']['outputs']);outputs['YTDATA.DAT']=put(outputs['YTDATA.DAT'],2853,81,amount)
            with self.assertRaises(AssertionError):v.verify_semantics('day-1',self.cases['day-1']['before'],outputs)

    def test_wrong_converged_pointer_rejects(self):
        outputs=dict(self.cases['day-1']['outputs']);outputs['YTDATA.DAT']=put(outputs['YTDATA.DAT'],53,105,2801)
        with self.assertRaises(AssertionError):v.verify_semantics('day-1',self.cases['day-1']['before'],outputs)

    def test_evolved_duplicate_pointer_rejects(self):
        outputs=dict(self.cases['day-2']['outputs']);outputs['YTDATA.DAT']=put(outputs['YTDATA.DAT'],54,105,v.field(outputs['YTDATA.DAT'],53,105))
        with self.assertRaises(AssertionError):v.verify_semantics('day-2',self.cases['day-2']['before'],outputs)

    def test_wrong_combined_force_despite_conservation_rejects(self):
        outputs=dict(self.cases['day-1']['outputs']);world=outputs['YTDATA.DAT'];world=put(world,2853,81,6551);outputs['YTDATA.DAT']=put(world,900,81,3096)
        self.assertEqual(v.physical(outputs['YTDATA.DAT']),10000)
        with self.assertRaises(AssertionError):v.verify_semantics('day-1',self.cases['day-1']['before'],outputs)

    def test_watermark_link_and_name_reject(self):
        for record,offset,value in((1,81,306),(2853,93,0),(4053,85,0)):
            outputs=dict(self.cases['day-2']['outputs']);outputs['YTDATA.DAT']=put(outputs['YTDATA.DAT'],record,offset,value)
            with self.subTest(record=record,offset=offset),self.assertRaises(AssertionError):v.verify_semantics('day-2',self.cases['day-2']['before'],outputs)

    def test_private_mail_and_public_loss_invention_reject(self):
        for name,data in(('YTRMSG.DAT',b'invented'),('YTNEWS.DAT',b'Xannor fighters destroyed!')):
            outputs=dict(self.cases['day-2']['outputs']);outputs[name]=data
            with self.subTest(name=name),self.assertRaises(AssertionError):v.verify_semantics('day-2',self.cases['day-2']['before'],outputs)

    def test_name_and_news_rotation_reject(self):
        for name in('YTNAME.DAT','YTYNEWS.DAT'):
            outputs=dict(self.cases['day-2']['outputs']);outputs[name]+=b'changed'
            with self.subTest(name=name),self.assertRaises(AssertionError):v.verify_semantics('day-2',self.cases['day-2']['before'],outputs)

    def test_wrong_score_rejects(self):
        outputs=dict(self.cases['day-2']['outputs']);outputs['YTSCORE.ASC']=outputs['YTSCORE.ASC'].replace(b'1,000,000',b'1,000,001')
        with self.assertRaises(AssertionError):v.verify_semantics('day-2',self.cases['day-2']['before'],outputs)

    def test_probe_exact_payload_and_clear_residues(self):
        self.assertEqual(v.placement.verify_cache(self.probe_before,self.probe_world,self.probe_trace),dict(cache_force=10000,consumed=3))
        for sector in(849,1169,2802):
            for offset in(81,85):self.assertEqual(v.rawfield(self.probe_world,51+sector,offset),bytes.fromhex('00008000'))

    def test_probe_payload_cannot_invent_duplicate_force(self):
        trace=bytearray(self.probe_trace);at=len(trace)-168+4*(3+21);trace[at:at+4]=v.encode(6552)
        with self.assertRaises(AssertionError):v.placement.verify_cache(self.probe_before,self.probe_world,bytes(trace))

    def test_probe_incomplete_or_extra_payload_rejects(self):
        for trace in(self.probe_trace[:-1],self.probe_trace+b'x',self.probe_trace+b'Daily Maintenance Completed OK'):
            with self.assertRaises(AssertionError):v.placement.verify_cache(self.probe_before,self.probe_world,trace)

    def test_probe_canonicalizing_native_zero_rejects(self):
        for offset in(81,85):
            world=put(self.probe_world,2853,offset,0)
            with self.assertRaises(AssertionError):v.placement.verify_cache(self.probe_before,world,self.probe_trace)

    def test_probe_cannot_leave_stored_pointer(self):
        world=put(self.probe_world,53,105,2802)
        with self.assertRaises(AssertionError):v.placement.verify_cache(self.probe_before,world,self.probe_trace)

    def test_complete_observed_source_contexts(self):
        counts=[]
        for day in v.DAYS:
            rows=v.verify_observation(self.observations[day],day,self.cases[day]['before'],self.cases[day]['outputs']);counts.append((rows['helper1'],rows['helper2'],rows['active_planets']))
        self.assertEqual(counts,[(42,19,1),(41,17,4),(42,0,4)])

    def test_rng_corruption_and_callback_disagreement_reject(self):
        for change in('width','high','pair'):
            ob=copy.deepcopy(self.observations['day-2'])
            if change=='width':ob['events'][1]['before']['rng_raw']='00'
            elif change=='high':
                for side in('before','after'):ob['events'][1][side]['rng_raw']='000000ff'
            else:
                raw=int.from_bytes(bytes.fromhex(ob['events'][1]['after']['rng_raw']),'little')^1;ob['events'][1]['after']['rng_raw']=raw.to_bytes(4,'little').hex()
            with self.subTest(change=change),self.assertRaises(AssertionError):v.verify_observation(ob,'day-2',self.cases['day-2']['before'],self.cases['day-2']['outputs'])

    def test_event_ordinal_drops_errors_and_mode_reject(self):
        changes=[lambda o:o.update(dropped=1),lambda o:o.update(errors=['oops']),lambda o:o.update(observe=False),lambda o:o['events'][1].update(ordinal=99)]
        for mutate in changes:
            ob=copy.deepcopy(self.observations['day-2']);mutate(ob)
            with self.assertRaises(AssertionError):v.verify_observation(ob,'day-2',self.cases['day-2']['before'],self.cases['day-2']['outputs'])

    def test_changed_raw_saved_port_time_rejects(self):
        outputs=dict(self.cases['day-2']['outputs']);outputs['YTDATA.DAT']=put(outputs['YTDATA.DAT'],3657,101,1)
        with self.assertRaises(AssertionError):v.verify_observation(self.observations['day-2'],'day-2',self.cases['day-2']['before'],outputs)

    def test_wrong_actual_calendar_or_cpu_rejects(self):
        for change in('date','cpu'):
            ob=copy.deepcopy(self.observations['day-2'])
            if change=='cpu':
                for side in('before','after'):ob['events'][10][side]['cycle_max']=100000
            else:
                # Exact frame identity remains but actual DOS date disagrees.
                event=next(e for e in ob['events'] if e['function']==0x2a and e['before']['runtime_signature']is not None);event['after']['dx']=0x0b04
            with self.assertRaises(AssertionError):v.verify_observation(ob,'day-2',self.cases['day-2']['before'],self.cases['day-2']['outputs'])

    def test_text_headers_bind_independent_source_clocks(self):
        for name,old,new in(('YTNEWS.DAT',b'00:00:00 ',b'00:00:01 '),('YTSCORE.ASC',b'Last updated at: 11-03-2026 00:00:00',b'Last updated at: 11-03-2026 00:00:01')):
            outputs=dict(self.cases['day-2']['outputs']);outputs[name]=outputs[name].replace(old,new,1)
            self.assertNotEqual(outputs[name],self.cases['day-2']['outputs'][name])
            with self.subTest(name=name),self.assertRaises(AssertionError):v.verify_observation(self.observations['day-2'],'day-2',self.cases['day-2']['before'],outputs)

    def test_missing_helper_with_rebuilt_ordinals_rejects(self):
        for role in('helper1','helper2'):
            ob=copy.deepcopy(self.observations['day-2']);selected=None
            for index,event in enumerate(ob['events']):
                row=copy.deepcopy(event)
                for side in('before','after'):row[side].pop('rng_raw')
                pair=v.clocks.event_pair(row,row['ordinal'])
                if pair.get('kind')=='timer'and pair.get('role')==role:selected=index;break
            self.assertIsNotNone(selected);ob['events'].pop(selected)
            for ordinal,event in enumerate(ob['events'],1):event['ordinal']=ordinal
            with self.subTest(role=role),self.assertRaisesRegex(AssertionError,'source-helper inventory'):v.verify_observation(ob,'day-2',self.cases['day-2']['before'],self.cases['day-2']['outputs'])

    def test_missing_creation_timer_with_rebuilt_ordinals_rejects(self):
        ob=copy.deepcopy(self.observations['day-1']);selected=None
        for index,event in enumerate(ob['events']):
            row=copy.deepcopy(event)
            for side in('before','after'):row[side].pop('rng_raw')
            pair=v.clocks.event_pair(row,row['ordinal'])
            if pair.get('kind')=='timer'and pair.get('role')=='xannoron':selected=index;break
        self.assertIsNotNone(selected);ob['events'].pop(selected)
        for ordinal,event in enumerate(ob['events'],1):event['ordinal']=ordinal
        with self.assertRaisesRegex(AssertionError,'creation samples TIMER'):v.verify_observation(ob,'day-1',self.cases['day-1']['before'],self.cases['day-1']['outputs'])

    def modified_case(self,label,mutate):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);folder=Path(temp.name)/label;shutil.copytree(self.root/'day-2'/label,folder)
        meta=json.loads((folder/'capture.json').read_text());mutate(folder,meta)
        meta['files']={p.name:v.SHA(p.read_bytes())for p in folder.iterdir()if p.name!='capture.json'};(folder/'capture.json').write_text(json.dumps(meta)+'\n')
        return folder

    def test_rebound_metadata_cannot_disguise_wrong_parent_identity(self):
        folder=self.modified_case('observed-a',lambda f,m:m.update(parent='day-0'))
        with self.assertRaises(AssertionError):v.verify_case(folder,'day-2','observed-a',self.observer,self.cases['day-1']['outputs'])

    def test_rebound_hashes_cannot_disguise_guest_patch(self):
        folder=self.modified_case('observed-a',lambda f,m:m['guests'].update(**{'YTMAINT.EXE':'0'*64}))
        with self.assertRaises(AssertionError):v.verify_case(folder,'day-2','observed-a',self.observer,self.cases['day-1']['outputs'])

    def test_rebound_hashes_cannot_disguise_inherited_world_patch(self):
        def mutate(folder,meta):
            raw=gzip.decompress((folder/'before-YTDATA.DAT.gz').read_bytes());raw=put(raw,2853,81,6553);(folder/'before-YTDATA.DAT.gz').write_bytes(gzip.compress(raw,mtime=0));meta['inputs']['YTDATA.DAT']=v.SHA(raw)
        folder=self.modified_case('observed-a',mutate)
        with self.assertRaises(AssertionError):v.verify_case(folder,'day-2','observed-a',self.observer,self.cases['day-1']['outputs'])

    def test_rebound_hashes_cannot_disguise_changed_launch_cpu(self):
        def mutate(folder,meta):
            argv=json.loads((folder/'launch.json').read_text());argv[4]='cpu_cycles=100000';meta['argv']=argv;(folder/'launch.json').write_text(json.dumps(argv))
        folder=self.modified_case('observed-a',mutate)
        with self.assertRaises(AssertionError):v.verify_case(folder,'day-2','observed-a',self.observer,self.cases['day-1']['outputs'])

    def test_rebound_hashes_cannot_disguise_changed_observer_source(self):
        def mutate(folder,meta):
            p=folder/'loaded-observer.js';p.write_text(p.read_text()+'// altered observer\n')
        folder=self.modified_case('observed-a',mutate)
        with self.assertRaises(AssertionError):v.verify_case(folder,'day-2','observed-a',self.observer,self.cases['day-1']['outputs'])

    def test_probe_inherited_scoreboard_cannot_be_replaced_by_completed_score(self):
        def mutate(folder,meta):
            raw=self.cases['day-2']['outputs']['YTSCORE.ASC'];(folder/'after-YTSCORE.ASC.gz').write_bytes(gzip.compress(raw,mtime=0));meta['outputs']['YTSCORE.ASC']=v.SHA(raw)
        folder=self.modified_case('cache-observed-a',mutate)
        with self.assertRaises(AssertionError):v.verify_case(folder,'day-2','cache-observed-a',self.observer,self.cases['day-1']['outputs'])

    def test_forced_exit_or_missing_flush_cannot_pass(self):
        original=json.loads((self.root/'day-2/observed-a/controller.json').read_text());ob=self.observations['day-2'];raw=gzip.decompress((self.root/'day-2/observed-a/host-time.json.gz').read_bytes())
        for mutate in(lambda c:c.update(forced=True),lambda c:c.update(success=False),lambda c:c['messages'].pop()):
            c=copy.deepcopy(original);mutate(c)
            with self.assertRaises(AssertionError):v.clocks.neutral.verify_controller(c,'observed',ob,raw)

    def test_manifest_identity_and_artifact_inventory_are_not_mutable_metadata(self):
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp);(root/'pins.json').write_text('{}')
            with self.assertRaisesRegex(AssertionError,'immutable convergence-chain manifest'):v.verify(root)


if __name__=='__main__':unittest.main()
