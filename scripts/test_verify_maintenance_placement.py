"""Direct semantic/provenance corruption controls for placement/cache evidence."""
import copy
import gzip
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import verify_maintenance_placement as v


class PlacementEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=v.DEFAULT
        cls.observer=(cls.root/'acquisition/observe_maintenance_placement.js').read_text()
        cls.case='wanderer-reject-two';cls.folder=cls.root/cls.case/'observed-a'
        cls.raw=json.loads(gzip.decompress((cls.folder/'host-time.json.gz').read_bytes()))
        cls.before=v.before_inputs(cls.case)['YTDATA.DAT']
        cls.outputs={n:gzip.decompress((cls.folder/('after-'+n+'.gz')).read_bytes())for n in v.OUTPUTS}
        cls.trace=(cls.folder/'TRACE.BIN').read_bytes()
        cls.witnesses,_=v.verify_observation(cls.raw)
        cls.native=json.loads((cls.root/'native/rea.json').read_text())
        probe=cls.root/cls.case/'cache-probe'
        cls.cache_after=gzip.decompress((probe/'after-YTDATA.DAT.gz').read_bytes())
        cls.cache_trace=(probe/'TRACE.BIN').read_bytes()

    def test_complete_independent_corpus(self):
        result=v.verify()
        self.assertEqual((result['cases'],result['full_runs'],result['cache_probes'],result['paired_files'],result['native_reads']),(12,72,12,432,4))

    def test_direct_cache_snapshot_reconciles_unique_physical_force(self):
        for case in v.CASES:
            before=v.before_inputs(case)['YTDATA.DAT'];folder=self.root/case/'cache-probe'
            result=v.verify_cache(before,gzip.decompress((folder/'after-YTDATA.DAT.gz').read_bytes()),(folder/'TRACE.BIN').read_bytes())
            self.assertEqual(result['cache_force'],10037 if case=='duplicate-mobile'else 10000)

    def test_strict_positive_gate_and_rejected_state_progression(self):
        result=v.verify_placements(self.before,self.outputs,self.trace,self.witnesses)
        self.assertEqual(result['attempts']['wanderer'],3)
        self.assertEqual(result['accepted']['wanderer'],1295)
        self.assertEqual(v.verify_force_accounting(self.before,self.outputs,self.case),dict(initial=10000,survivors=6319,reported_losses=3681))

    def test_fractional_positive_link_rejects_and_raw_zero_residue_accepts(self):
        for case,count,destination in [('wanderer-positive-fraction',2,1792),('wanderer-zero-residue',1,1095)]:
            folder=self.root/case/'observed-a'
            observation=json.loads(gzip.decompress((folder/'host-time.json.gz').read_bytes()))
            witnesses,_=v.verify_observation(observation)
            outputs={n:gzip.decompress((folder/('after-'+n+'.gz')).read_bytes())for n in v.OUTPUTS}
            before=v.before_inputs(case)['YTDATA.DAT'];trace=(folder/'TRACE.BIN').read_bytes()
            result=v.verify_placements(before,outputs,trace,witnesses)
            self.assertEqual((result['attempts']['wanderer'],result['accepted']['wanderer']),(count,destination))
            if count==2:
                changed=bytearray(before);start=(1146-1)*137+93;changed[start:start+4]=bytes(4)
                with self.assertRaisesRegex(AssertionError,'after acceptance'):
                    v.verify_placements(bytes(changed),outputs,trace,witnesses)

    def test_native_bytes_and_declared_probe_are_independently_reconstructed(self):
        v.verify_native(self.root)
        original=(v.ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes()
        patched=v.patched_original(original)
        self.assertEqual(len(patched),len(original))
        self.assertEqual(patched[:512],original[:512])
        self.assertIn(bytes.fromhex('b9a800'),patched[0x244:0x272])

    def case_rejected(self,mutate,case=None,mode='observed-a'):
        case=self.case if case is None else case
        with tempfile.TemporaryDirectory()as temp:
            folder=Path(temp)/case/mode;shutil.copytree(self.root/case/mode,folder)
            meta=json.loads((folder/'capture.json').read_text());mutate(folder,meta)
            # Rehash declared capture artifacts so the targeted semantic/source
            # invariant must reject; immutable corpus tests are separate below.
            meta['files']={name:v.SHA((folder/name).read_bytes())for name in meta['files']if(folder/name).exists()}
            (folder/'capture.json').write_text(json.dumps(meta))
            with self.assertRaises((AssertionError,ValueError,KeyError,FileNotFoundError)):
                v.verify_case(folder,case,mode,self.observer)

    def native_rejected(self,mutate):
        value=copy.deepcopy(self.native);mutate(value)
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp);(root/'native').mkdir();(root/'native/rea.json').write_text(json.dumps(value))
            with self.assertRaises((AssertionError,ValueError,KeyError)):
                v.verify_native(root)

    def observation_rejected(self,mutate):
        value=copy.deepcopy(self.raw);mutate(value)
        with self.assertRaises((AssertionError,ValueError,KeyError)):
            v.verify_observation(value)

    def placement_rejected(self,mutate):
        outputs=dict(self.outputs);witnesses=copy.deepcopy(self.witnesses)
        trace=mutate(outputs,witnesses,self.trace)
        with self.assertRaises((AssertionError,ValueError,KeyError)):
            v.verify_placements(self.before,outputs,trace if isinstance(trace,bytes)else self.trace,witnesses)

    def test_manifest_cannot_be_replaced_with_rehashed_values(self):
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp);(root/'pins.json').write_text(json.dumps({'files':{}}))
            with self.assertRaisesRegex(AssertionError,'immutable placement/cache'):
                v.verify(root)

    def test_extra_unlisted_artifact_rejected(self):
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp)/'corpus';shutil.copytree(self.root,root)
            (root/'unreviewed.json').write_text('{}')
            with self.assertRaisesRegex(AssertionError,'artifact inventory'):v.verify(root)

    def test_missing_pinned_artifact_rejected(self):
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp)/'corpus';shutil.copytree(self.root,root)
            (root/'native/rea.json').unlink()
            with self.assertRaisesRegex(AssertionError,'artifact inventory'):v.verify(root)

    def test_changed_artifact_cannot_pass_old_pins(self):
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp)/'corpus';shutil.copytree(self.root,root)
            (root/'native/rea.json').write_text('{}')
            with self.assertRaisesRegex(AssertionError,'immutable artifact'):v.verify(root)


def replace_file(path,old,new):
    raw=path.read_bytes();assert old in raw,'mutation must affect a retained witness';path.write_bytes(raw.replace(old,new,1))


def case_mutation(name,mutate,case=None,mode='observed-a'):
    def test(self):self.case_rejected(mutate,case,mode)
    setattr(PlacementEvidenceTests,'test_reject_case_'+name,test)


case_mutation('wrong_recipe',lambda p,m:m.update(recipe='another-capture'))
case_mutation('wrong_mode',lambda p,m:m.update(mode='unobserved-a'))
case_mutation('changed_fixture_patch',lambda p,m:m['patches'][0].__setitem__(2,3))
case_mutation('wrong_before_hash',lambda p,m:m['inputs'].update({'YTDATA.DAT':'0'*64}))
case_mutation('wrong_host_binary',lambda p,m:m.update(host_sha256='0'*64))
case_mutation('patched_full_guest',lambda p,m:m['guests'].update({'YTMAINT.EXE':'0'*64}))
case_mutation('unpatched_cache_guest',lambda p,m:m['guests'].update({'YTMAINT.EXE':v.clocks.GUESTS['YTMAINT.EXE']}),mode='cache-probe')
case_mutation('long_capture',lambda p,m:m.update(elapsed_seconds=41))
case_mutation('wrong_actual_cpu',lambda p,m:replace_file(p/'dosbox.stderr',b'CPU: Setting fixed 200000 cycles.',b'CPU: Setting fixed 100000 cycles.'))
case_mutation('wrong_actual_version',lambda p,m:replace_file(p/'dosbox.stderr',b'version 0.83.0',b'version 0.82.0'))
case_mutation('wrong_actual_audio',lambda p,m:replace_file(p/'dosbox.stderr',b"disabled ('nosound' mode)",b"enabled ('sound' mode)"))
case_mutation('wrong_actual_video',lambda p,m:replace_file(p/'dosbox.stderr',b'SDL: dummy video initialised',b'SDL: other video initialised'))
case_mutation('wrong_actual_argv',lambda p,m:replace_file(p/'dosbox.stderr',b'cpu_cycles=200000',b'cpu_cycles=100000'))
case_mutation('wrong_command',lambda p,m:replace_file(p/'COMMANDS.TXT',b'ytmaint > TRACE.BIN',b'ytconfig > TRACE.BIN'))
case_mutation('wrong_actual_date',lambda p,m:replace_file(p/'DOSDATE.LOG',b'11/02/2026',b'11/03/2026'))
case_mutation('wrong_actual_time',lambda p,m:replace_file(p/'DOSTIME.LOG',b' 0:00:00.00',b' 0:00:01.00'))
case_mutation('false_errorlevel',lambda p,m:(p/'ERROR.LOG').write_bytes(b'PROGRAM_ERROR\r\n'))
case_mutation('missing_return',lambda p,m:(p/'RETURN.LOG').write_bytes(b''))
case_mutation('missing_full_footer',lambda p,m:replace_file(p/'TRACE.BIN',b'Daily Maintenance Completed OK',b'Daily Maintenance NOT done'))
case_mutation('forged_observer_source',lambda p,m:(p/'loaded-observer.js').write_text('/*another observer*/'))
case_mutation('cache_truncated_output',lambda p,m:(p/'TRACE.BIN').write_bytes((p/'TRACE.BIN').read_bytes()[:-1]),mode='cache-probe')
case_mutation('cache_masquerades_as_full',lambda p,m:(p/'TRACE.BIN').write_bytes(b'Daily Maintenance Completed OK\r\n'+(p/'TRACE.BIN').read_bytes()),mode='cache-probe')


def native_mutation(name,mutate):
    def test(self):self.native_rejected(mutate)
    setattr(PlacementEvidenceTests,'test_reject_native_'+name,test)


native_mutation('missing_read',lambda n:n['records'].pop())
native_mutation('duplicate_range',lambda n:n['records'].__setitem__(1,copy.deepcopy(n['records'][0])))
native_mutation('wrong_address',lambda n:n['records'][0]['parameters'].update(address='0x126ca'))
native_mutation('zero_extent',lambda n:n['records'][0]['parameters'].update(length=0))
native_mutation('incomplete_read',lambda n:n['records'][0]['normalized_result'].update(complete=False))
native_mutation('truncated_bytes',lambda n:n['records'][0]['normalized_result'].update(bytes_hex=n['records'][0]['normalized_result']['bytes_hex'][:-2]))
native_mutation('mutated_opcode',lambda n:n['records'][0]['normalized_result'].update(bytes_hex='00'+n['records'][0]['normalized_result']['bytes_hex'][2:]))
native_mutation('wrong_target_name',lambda n:n['records'][0]['subject'].update(name='BRUN30.EXE'))
native_mutation('wrong_guest',lambda n:n['records'][0]['subject']['digest'].update(sha256='0'*64))
native_mutation('wrong_operation',lambda n:n['records'][0].update(operation='trace_native_values'))


def observation_mutation(name,mutate):
    def test(self):self.observation_rejected(mutate)
    setattr(PlacementEvidenceTests,'test_reject_observation_'+name,test)


def rng_pair(ob,value,side=None):
    event=next(e for e in ob['events']if e['before'].get('runtime_signature')=='50535152b42ccd21')
    for key in(('before','after')if side is None else(side,)):event[key]['rng_raw']=value


observation_mutation('wrong_recipe',lambda o:o.update(recipe='host-dos-clock-matrix-observer-v1'))
observation_mutation('dropped_event',lambda o:o.update(dropped=1))
observation_mutation('runtime_error',lambda o:o.update(errors=['lost event']))
observation_mutation('missing_rng',lambda o:o['events'][0]['before'].pop('rng_raw'))
observation_mutation('truncated_rng',lambda o:rng_pair(o,'000000'))
observation_mutation('nonhex_rng',lambda o:rng_pair(o,'zzzzzzzz'))
observation_mutation('out_of_range_rng',lambda o:rng_pair(o,'00000001'))
observation_mutation('changed_rng_during_dos',lambda o:rng_pair(o,'00000000','after'))
observation_mutation('false_startup_state',lambda o:[e[side].update(rng_raw='00000000')for e in o['events']for side in('before','after')])


def mutate_world(outputs,record,offset,value):
    raw=bytearray(outputs['YTDATA.DAT']);start=(record-1)*137+offset
    raw[start:start+4]=value if type(value)is bytes else v.encode(value);outputs['YTDATA.DAT']=bytes(raw)


def placement_mutation(name,mutate):
    def test(self):self.placement_rejected(mutate)
    setattr(PlacementEvidenceTests,'test_reject_placement_'+name,test)


placement_mutation('missing_phase',lambda o,w,t:w.pop())
placement_mutation('reordered_witnesses',lambda o,w,t:w.reverse())
placement_mutation('duplicate_ordinal',lambda o,w,t:w[1].update(ordinal=w[0]['ordinal']))
placement_mutation('false_rejection_state',lambda o,w,t:w[1].update(old_state=(w[1]['old_state']+1)&0xffffff))
placement_mutation('premature_acceptance',lambda o,w,t:w.pop(0))
placement_mutation('missing_receipt',lambda o,w,t:t.replace(b'Wanderer has successfully warped!',b'',1))
placement_mutation('extra_receipt',lambda o,w,t:t+b'Wanderer has successfully warped!')
placement_mutation('missing_base_public_news',lambda o,w,t:o.update({'YTNEWS.DAT':o['YTNEWS.DAT'].replace(b'  -  The Mercenaries have built a home base using a captured Genesis Device!',b'',1)}))
placement_mutation('invented_private_message',lambda o,w,t:o.update({'YTRMSG.DAT':b'private placement'}))
placement_mutation('wrong_saved_wanderer',lambda o,w,t:mutate_world(o,51+1295,93,0))
placement_mutation('duplicate_saved_wanderer',lambda o,w,t:mutate_world(o,51+10,93,1))


class DirectCacheMutations(unittest.TestCase):
    def setUp(self):
        self.before=v.before_inputs('duplicate-hq-chain')['YTDATA.DAT']
        folder=v.DEFAULT/'duplicate-hq-chain/cache-probe'
        self.after=gzip.decompress((folder/'after-YTDATA.DAT.gz').read_bytes());self.trace=(folder/'TRACE.BIN').read_bytes()

    def reject(self,after=None,trace=None):
        with self.assertRaises(AssertionError):v.verify_cache(self.before,self.after if after is None else after,trace if isinstance(trace,bytes)else self.trace)

    def test_duplicate_force_cannot_be_counted_twice(self):
        raw=bytearray(self.trace);raw[-168+4*(21+2):-168+4*(21+3)]=v.encode(10000);self.reject(trace=bytes(raw))

    def test_higher_duplicate_location_must_clear(self):
        raw=bytearray(self.trace);raw[-168+8:-168+12]=v.encode(849);self.reject(trace=bytes(raw))

    def test_stored_pointer_cannot_survive_early_normalization(self):
        raw=bytearray(self.after);start=(53-1)*137+105;raw[start:start+4]=v.encode(849);self.reject(after=bytes(raw))

    def test_consumed_raw_zero_cannot_be_canonicalized(self):
        raw=bytearray(self.after);start=(900-1)*137+81;raw[start:start+4]=bytes(4);self.reject(after=bytes(raw))

    def test_foreign_force_cannot_be_consumed_by_xannor_cache(self):
        before=v.before_inputs('pointer-mercenary-sector')['YTDATA.DAT'];folder=v.DEFAULT/'pointer-mercenary-sector/cache-probe'
        after=bytearray(gzip.decompress((folder/'after-YTDATA.DAT.gz').read_bytes()));start=(3051-1)*137+81;after[start:start+4]=bytes(4)
        with self.assertRaises(AssertionError):v.verify_cache(before,bytes(after),(folder/'TRACE.BIN').read_bytes())

    def test_phantom_added_force_fails_news_conservation(self):
        case='unpointed-friendly-merge';before=v.before_inputs(case)['YTDATA.DAT'];folder=v.DEFAULT/case/'unobserved-a'
        outputs={n:gzip.decompress((folder/('after-'+n+'.gz')).read_bytes())for n in v.OUTPUTS}
        mutate_world(outputs,1599,81,53)
        with self.assertRaises(AssertionError):v.verify_force_accounting(before,outputs,case)

    def test_unused_cache_cells_are_retained_but_not_modeled(self):
        raw=bytearray(self.trace)
        for index in(0,21):
            start=len(raw)-168+4*index;raw[start:start+4]=bytes.fromhex('deadbeef')
        # Outer immutable pins authenticate these raw cells; the pure cache
        # model only claims the40source-owned fields.
        v.verify_cache(self.before,self.after,bytes(raw))

    def test_wrong_zero_score_column_cannot_match_elsewhere_on_board(self):
        case='duplicate-hq';before=v.before_inputs(case)['YTDATA.DAT'];folder=v.DEFAULT/case/'unobserved-a'
        outputs={n:gzip.decompress((folder/('after-'+n+'.gz')).read_bytes())for n in v.OUTPUTS}
        old=b'                  0    0.00%'
        self.assertIn(old,outputs['YTSCORE.ASC'])
        outputs['YTSCORE.ASC']=outputs['YTSCORE.ASC'].replace(old,b'                  1    0.00%',1)
        with self.assertRaisesRegex(AssertionError,'both NPC scoreboard'):
            v.verify_force_accounting(before,outputs,case)


if __name__=='__main__':unittest.main()
