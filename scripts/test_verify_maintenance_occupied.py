"""Direct semantic/provenance corruption controls for active occupied-route evidence."""
import copy
import gzip
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import verify_maintenance_occupied as v


class OccupiedEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=v.DEFAULT
        cls.observer=(cls.root/'acquisition/observe_maintenance_placement.js').read_text()
        cls.case='wanderer-active-rejection';cls.folder=cls.root/cls.case/'observed-a'
        cls.raw=json.loads(gzip.decompress((cls.folder/'host-time.json.gz').read_bytes()))
        cls.before=v.before_inputs(cls.case)['YTDATA.DAT']
        cls.outputs={n:gzip.decompress((cls.folder/('after-'+n+'.gz')).read_bytes())for n in v.OUTPUTS}
        cls.trace=(cls.folder/'TRACE.BIN').read_bytes()
        cls.witnesses,_=v.verify_observation(cls.raw)

    def test_complete_independent_corpus(self):
        result=v.verify()
        self.assertEqual((result['cases'],result['full_runs'],result['paired_files']),(10,60,360))

    def test_initial_fixture_is_actual_active_planet(self):
        for case in v.CASES:v.verify_fixture(v.before_inputs(case)['YTDATA.DAT'],case)
        self.assertEqual(v.field(self.before,4053,85),14)
        self.assertEqual(v.field(self.before,4053,77),500000)
        self.assertEqual(v.field(self.before,4053,41),305)
        self.assertEqual(v.field(self.before,2838,93),2)

    def test_active_planet_rng_is_not_assumed_to_start_at_initial_seed(self):
        _,inputs=v.verify_observation(self.raw)
        startup=bytearray(inputs['startup']);startup[2]^=128
        seed=5|((startup[0]^startup[2])<<8)|((startup[1]^startup[3])<<16)
        self.assertNotEqual(self.witnesses[0]['old_state'],seed)

    def test_placement_witnesses_reject_actual_active_link(self):
        result=v.placement.verify_placements(self.before,self.outputs,self.trace,self.witnesses)
        self.assertGreater(result['attempts']['wanderer'],1)
        self.assertNotEqual(result['accepted']['wanderer'],2787)
        changed=bytearray(self.before);at=(2838-1)*137+93;changed[at:at+4]=bytes(4)
        with self.assertRaises(AssertionError):v.placement.verify_placements(bytes(changed),self.outputs,self.trace,self.witnesses)

    def test_corrupted_fixture_name_rejected(self):
        changed=bytearray(self.before);changed[(4053-1)*137]=ord('X')
        with self.assertRaisesRegex(AssertionError,'named active'):v.verify_fixture(bytes(changed),self.case)

    def test_corrupted_fixture_link_rejected(self):
        changed=bytearray(self.before);at=(2838-1)*137+93;changed[at:at+4]=bytes(4)
        with self.assertRaisesRegex(AssertionError,'actual sector link'):v.verify_fixture(bytes(changed),self.case)

    def test_hidden_active_planet_rejected(self):
        changed=bytearray(self.before);at=(4054-1)*137+85;changed[at:at+4]=v.encode(1)
        with self.assertRaisesRegex(AssertionError,'hidden active'):v.verify_fixture(bytes(changed),self.case)

    def test_missing_output_rejected_even_with_other_modes_equal(self):
        cases={m:{'outputs':dict(self.outputs)}for m in v.MODES};cases['observed-b']['outputs'].pop('YTNEWS.DAT')
        with self.assertRaises(AssertionError):v.verify_paired_outputs(cases)

    def test_observer_perturbation_rejected(self):
        cases={m:{'outputs':dict(self.outputs)}for m in v.MODES};cases['observed-b']['outputs']['YTNEWS.DAT']+=b'X'
        with self.assertRaisesRegex(AssertionError,'equal both'):v.verify_paired_outputs(cases)

    def test_second_unobserved_control_cannot_differ(self):
        cases={m:{'outputs':dict(self.outputs)}for m in v.MODES};cases['unobserved-b']['outputs']['YTDATA.DAT']=b''
        with self.assertRaisesRegex(AssertionError,'equal both'):v.verify_paired_outputs(cases)

    def test_six_mode_inventory_is_required(self):
        cases={m:{'outputs':dict(self.outputs)}for m in v.MODES};cases.pop('attach-only')
        with self.assertRaisesRegex(AssertionError,'all six'):v.verify_paired_outputs(cases)

    def test_manifest_cannot_be_replaced_with_rehashed_values(self):
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp);(root/'pins.json').write_text(json.dumps({'files':{}}))
            with self.assertRaisesRegex(AssertionError,'immutable occupied-route'):v.verify(root)

    def corpus_rejected(self,mutate):
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp)/'corpus';shutil.copytree(self.root,root);mutate(root)
            with self.assertRaises((AssertionError,FileNotFoundError,KeyError,ValueError)):v.verify(root)

    def test_extra_artifact_rejected(self):self.corpus_rejected(lambda p:(p/'unreviewed.json').write_text('{}'))
    def test_missing_capture_rejected(self):self.corpus_rejected(lambda p:(p/self.case/'observed-a/capture.json').unlink())
    def test_changed_snapshot_rejected(self):self.corpus_rejected(lambda p:(p/'acquisition/recover_maintenance_occupied.py').write_text('different'))
    def test_missing_snapshot_rejected(self):self.corpus_rejected(lambda p:(p/'acquisition/observe_maintenance_placement.js').unlink())

    def observation_rejected(self,mutate):
        value=copy.deepcopy(self.raw);mutate(value)
        with self.assertRaises((AssertionError,ValueError,KeyError)):v.verify_observation(value)

    def test_observation_rng_width_rejected(self):self.observation_rejected(lambda x:x['events'][0]['before'].update(rng_raw='000000'))
    def test_observation_rng_callback_mutation_rejected(self):self.observation_rejected(lambda x:x['events'][0]['before'].update(rng_raw='ffffff00'))
    def test_observation_errors_rejected(self):self.observation_rejected(lambda x:x.update(errors=['hook failed']))
    def test_observation_drops_rejected(self):self.observation_rejected(lambda x:x.update(dropped=1))
    def test_observation_partial_event_rejected(self):self.observation_rejected(lambda x:x['events'][0]['after'].pop('stack'))

    def semantic_rejected(self,case,mutate):
        folder=self.root/case/'unobserved-a'
        outputs={n:gzip.decompress((folder/('after-'+n+'.gz')).read_bytes())for n in v.OUTPUTS}
        mutate(outputs)
        with self.assertRaises((AssertionError,ValueError,KeyError)):
            v.verify_semantics(case,v.before_inputs(case)['YTDATA.DAT'],outputs)

    def test_public_casualty_amount_cannot_disagree_with_saved_force(self):
        self.semantic_rejected('route-mercenary-100000',lambda x:x.update({'YTNEWS.DAT':x['YTNEWS.DAT'].replace(b'lost 1412',b'lost 1413',1)}))

    def test_literal_plyr_result_cannot_be_relabelled_as_xannor(self):
        self.semantic_rejected('route-mercenary-37',lambda x:x.update({'YTNEWS.DAT':x['YTNEWS.DAT'].replace(b'Plyr ftrs dstrd',b'Xannor ftrs dstrd',1)}))

    def test_public_planet_death_pair_cannot_be_removed(self):
        self.semantic_rejected('route-planet-neutral',lambda x:x.update({'YTNEWS.DAT':x['YTNEWS.DAT'].replace(b' *** Xannor fighters destroyed!\r\n',b'',1)}))

    def test_saved_force_cannot_disagree_with_public_accounting(self):
        def mutate(outputs):
            world=bytearray(outputs['YTDATA.DAT']);at=(52-1)*137+81;world[at:at+4]=v.encode(1);outputs['YTDATA.DAT']=bytes(world)
        self.semantic_rejected('route-neutral-37',mutate)

    def test_unexplained_surviving_planet_ground_loss_rejected(self):
        outputs=dict(self.outputs);world=bytearray(outputs['YTDATA.DAT']);at=(4053-1)*137+77;world[at:at+4]=v.encode(504999);outputs['YTDATA.DAT']=bytes(world)
        with self.assertRaisesRegex(AssertionError,'exact surviving'):v.verify_active_outputs(self.case,self.before,outputs)

    def test_score_cannot_include_destroyed_foreign_force(self):
        self.semantic_rejected('route-mercenary-100000',lambda x:x.update({'YTSCORE.ASC':x['YTSCORE.ASC'].replace(b'514,800',b'514,900',1)}))

    def test_actual_prior_rng_advance_is_required(self):
        witnesses,inputs=v.verify_observation(self.raw)
        v.verify_initial_rng(witnesses,inputs,1)
        with self.assertRaisesRegex(AssertionError,'RNG advancement'):v.verify_initial_rng(witnesses,inputs,0)

    def native_rejected(self,mutate):
        packet=json.loads((self.root/'native/rea.json').read_text());mutate(packet)
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp);(root/'native').mkdir();(root/'native/rea.json').write_text(json.dumps(packet))
            with self.assertRaises((AssertionError,KeyError,ValueError)):v.verify_native(root)

    def test_native_packet_matches_all_original_bytes(self):v.verify_native(self.root)
    def test_native_subject_digest_cannot_change(self):self.native_rejected(lambda x:x['records'][0]['subject']['digest'].update(sha256='0'*64))
    def test_native_range_cannot_change(self):self.native_rejected(lambda x:x['records'][0]['parameters'].update(address='0x11661'))
    def test_native_extent_cannot_shrink(self):self.native_rejected(lambda x:x['records'][0]['normalized_result'].update(complete=False))
    def test_native_bytes_cannot_change(self):
        def mutate(x):
            r=x['records'][0]['normalized_result'];r['bytes_hex']=('00'if r['bytes_hex'][:2]!='00'else'ff')+r['bytes_hex'][2:]
        self.native_rejected(mutate)

    def case_rejected(self,mutate,case=None,mode='observed-a'):

        case=self.case if case is None else case
        with tempfile.TemporaryDirectory()as temp:
            folder=Path(temp)/case/mode;shutil.copytree(self.root/case/mode,folder)
            meta=json.loads((folder/'capture.json').read_text());mutate(folder,meta)
            meta['files']={name:v.SHA((folder/name).read_bytes())for name in meta['files']if(folder/name).exists()}
            (folder/'capture.json').write_text(json.dumps(meta))
            with self.assertRaises((AssertionError,ValueError,KeyError,FileNotFoundError)):
                v.verify_case(folder,case,mode,self.observer)


def replace_file(path,old,new):
    raw=path.read_bytes();assert old in raw,'mutation must affect actual retained witness';path.write_bytes(raw.replace(old,new,1))


def case_mutation(name,mutate,case=None,mode='observed-a'):
    def test(self):self.case_rejected(mutate,case,mode)
    setattr(OccupiedEvidenceTests,'test_reject_case_'+name,test)


case_mutation('wrong_recipe',lambda p,m:m.update(recipe='another-capture'))
case_mutation('wrong_mode',lambda p,m:m.update(mode='unobserved-a'))
case_mutation('changed_planet_fixture',lambda p,m:m['patches']['planets'][0].__setitem__(0,2788))
case_mutation('wrong_before_hash',lambda p,m:m['inputs'].update({'YTDATA.DAT':'0'*64}))
case_mutation('wrong_host_binary',lambda p,m:m.update(host_sha256='0'*64))
case_mutation('patched_guest',lambda p,m:m['guests'].update({'YTMAINT.EXE':'0'*64}))
case_mutation('long_capture',lambda p,m:m.update(elapsed_seconds=41))
case_mutation('wrong_actual_cpu',lambda p,m:replace_file(p/'dosbox.stderr',b'CPU: Setting fixed 200000 cycles.',b'CPU: Setting fixed 100000 cycles.'))
case_mutation('wrong_actual_version',lambda p,m:replace_file(p/'dosbox.stderr',b'version 0.83.0',b'version 0.82.0'))
case_mutation('wrong_actual_audio',lambda p,m:replace_file(p/'dosbox.stderr',b"disabled ('nosound' mode)",b"enabled ('sound' mode)"))
case_mutation('wrong_actual_video',lambda p,m:replace_file(p/'dosbox.stderr',b'SDL: dummy video initialised',b'SDL: other video initialised'))
case_mutation('wrong_actual_argv',lambda p,m:replace_file(p/'dosbox.stderr',b'cpu_cycles=200000',b'cpu_cycles=100000'))
case_mutation('wrong_command',lambda p,m:replace_file(p/'COMMANDS.TXT',b'ytmaint > TRACE.BIN',b'ytconfig > TRACE.BIN'))
case_mutation('false_errorlevel',lambda p,m:(p/'ERROR.LOG').write_bytes(b'PROGRAM_ERROR\r\n'))
case_mutation('missing_return',lambda p,m:(p/'RETURN.LOG').write_bytes(b''))
case_mutation('missing_full_footer',lambda p,m:replace_file(p/'TRACE.BIN',b'Daily Maintenance Completed OK',b'Daily Maintenance NOT done'))
case_mutation('forged_observer_source',lambda p,m:(p/'loaded-observer.js').write_text('/*another observer*/'))
case_mutation('missing_output',lambda p,m:(p/'after-YTSCORE.ASC.gz').unlink())
case_mutation('wrong_output_hash',lambda p,m:m['outputs'].update({'YTNEWS.DAT':'0'*64}))


def mutate_controller(p,m,key,value):
    x=json.loads((p/'controller.json').read_text());x[key]=value;m['controller']=x;(p/'controller.json').write_text(json.dumps(x))


case_mutation('forced_exit',lambda p,m:mutate_controller(p,m,'forced',True))
case_mutation('unsuccessful_exit',lambda p,m:mutate_controller(p,m,'success',False))
case_mutation('live_child',lambda p,m:mutate_controller(p,m,'process_exited',False))
case_mutation('wrong_exit',lambda p,m:mutate_controller(p,m,'exit_code',1))

if __name__=='__main__':unittest.main()
