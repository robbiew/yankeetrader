"""Independent clock conversion and malicious-observation regressions."""
import copy
from fractions import Fraction
import gzip
import json
from pathlib import Path
import struct
import unittest

import verify_maintenance_clock_neutral as v


class DOSClockArithmeticTests(unittest.TestCase):
    def test_original_zero_residue(self):
        self.assertEqual(v.clock_to_raw(0,0),(bytes.fromhex('00004800'),)*2)
        self.assertNotEqual(v.clock_to_raw(0,0)[0],bytes(4))
    def test_five_hundredths(self):
        self.assertEqual(tuple(x.hex()for x in v.clock_to_raw(0,5)),('cdcc4c7c','0e745a76'))
    def test_ten_hundredths(self):
        self.assertEqual(tuple(x.hex()for x in v.clock_to_raw(0,10)),('cdcc4c7d','0e745a77'))
    def test_both_single_rounding_stages_matter(self):
        self.assertEqual(tuple(x.hex()for x in v.clock_to_raw(0,3)),('8fc2757b','6e120376'))
        direct,_=v._single_positive(Fraction(3,6000))
        self.assertEqual(direct.hex(),'6f120376')
        self.assertNotEqual(direct,v.clock_to_raw(0,3)[1])
    def test_lower_even_tie(self):
        raw,_=v._single_positive(Fraction((1<<24)+1,1<<24))
        self.assertEqual(raw.hex(),'00000081')
    def test_upper_even_tie(self):
        raw,_=v._single_positive(Fraction((1<<24)+3,1<<24))
        self.assertEqual(raw.hex(),'02000081')
    def test_valid_day_edge(self):
        self.assertEqual(tuple(x.hex()for x in v.clock_to_raw(0x173b,0x3b63)),('ffbf2891','ffff338b'))
    def test_hour_24_rejected(self):
        with self.assertRaises(AssertionError):v.clock_to_raw(24<<8,0)
    def test_minute_60_rejected(self):
        with self.assertRaises(AssertionError):v.clock_to_raw(60,0)
    def test_second_60_rejected(self):
        with self.assertRaises(AssertionError):v.clock_to_raw(0,60<<8)
    def test_hundredth_100_rejected(self):
        with self.assertRaises(AssertionError):v.clock_to_raw(0,100)
    def test_width_and_boolean_rejected(self):
        for cx,dx in [(-1,0),(65536,0),(0,65536),(True,0),(0,False)]:
            with self.subTest(cx=cx,dx=dx),self.assertRaises(AssertionError):v.clock_to_raw(cx,dx)
    def test_independent_float32_crosscheck(self):
        def f32(value):return struct.unpack('<f',struct.pack('<f',value))[0]
        for hour in (0,12,23):
            for minute in (0,59):
                for second in (0,59):
                    for hundredth in range(100):
                        seconds,minutes=v.clock_to_raw((hour<<8)|minute,(second<<8)|hundredth)
                        raw=((hour*60+minute)*60+second)*100+hundredth
                        self.assertEqual(float(v.mbf_fraction(seconds)),f32(raw/100))
                        self.assertEqual(float(v.mbf_fraction(minutes)),f32(f32(raw/100)/60))


class HostClockPairingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        paths=sorted(v.DEFAULT.glob('*/host-time.json.gz'))
        candidates=[json.loads(gzip.decompress(p.read_bytes()))for p in paths]
        cls.original=next((x for x in candidates if len(x.get('events',[]))==1066),None)
        assert cls.original is not None, 'retained complete host-observed control is required'
        cls.inputs=v.model_inputs(cls.original)
        cls.port606=cls.inputs['entries']['port'][605]['ordinal']-1

    def setUp(self):self.observation=copy.deepcopy(self.original)
    def rejects(self,reason=None):
        with self.assertRaisesRegex(AssertionError,reason or'.'):v.model_inputs(self.observation)
    def event(self):return self.observation['events'][self.port606]
    def set_word(self,index,value):
        for stage in ('before','after'):
            row=self.event()[stage];raw=bytearray.fromhex(row['stack']);struct.pack_into('<H',raw,2*index,value);row['stack']=raw.hex()

    def test_complete_input_inventory(self):
        self.assertEqual((len(self.inputs['port_minutes']),len(self.inputs['helper1']),len(self.inputs['helper2']),self.inputs['qualified'],len(self.inputs['unclassified'])),(1000,41,19,1062,4))
    def test_missing_paired_event(self):self.observation['events'].pop(self.port606);self.rejects('time-call inventory')
    def test_duplicate_ordinal(self):self.event()['ordinal']-=1;self.rejects('paired event ordinal')
    def test_missing_return(self):
        self.event().pop('after')
        with self.assertRaises((AssertionError,KeyError)):v.model_inputs(self.observation)
    def test_explicit_observer_error(self):self.observation['errors']=['read failure'];self.rejects('error-free')
    def test_dropped_events(self):self.observation['dropped']=1;self.rejects('error-free')
    def test_wrong_dos_function(self):self.event()['before']['ax']=0x2b00;self.rejects('GetSystemTime')
    def test_wrong_dos_return(self):self.event()['after']['ax']=0x2c01;self.rejects('GetSystemTime')
    def test_return_stack_substitution(self):self.event()['after']['stack']='00'*40;self.rejects('unchanged guest context')
    def test_return_ds_substitution(self):
        self.event()['after']['ds']+=1;self.event()['after']['ds_phys']+=16;self.rejects('unchanged guest context')
    def test_return_port_substitution(self):self.event()['after']['port_raw']='00000081';self.rejects('unchanged guest context')
    def test_return_pic_substitution(self):self.event()['after']['pic']+=1;self.rejects('unchanged guest context')
    def test_return_ip_not_advanced(self):self.event()['after']['ip']-=2;self.rejects('return boundary')
    def test_emulated_cycle_overhead_changed(self):self.event()['after']['cycles']-=1;self.rejects('overhead is preserved')
    def test_invalid_returned_clock(self):self.event()['after']['dx']=100;self.rejects('valid returned DOS time')
    def test_wrong_runtime_frame_signature(self):self.set_word(0,0xc138);self.rejects('unqualified DOS calls|original order|stable port attribution')
    def test_wrong_application_return_site(self):self.set_word(7,0x0928);self.rejects('original order|stable port attribution')
    def test_same_runtime_and_main_cs(self):
        words=struct.unpack('<20H',bytes.fromhex(self.event()['before']['stack']));self.set_word(1,words[8]);self.rejects('far-call fixup|distinct observed')
    def test_port_identity_cannot_be_relabelled(self):
        for stage in ('before','after'):self.event()[stage]['port_raw']='00000081'
        self.rejects('original order')
    def test_noninteger_port_identity(self):
        for stage in ('before','after'):self.event()[stage]['port_raw']='00004081'
        self.rejects('integer port identity')
    def test_qualified_data_segment_must_stay_stable(self):
        for stage in ('before','after'):
            self.event()[stage]['ds']+=1;self.event()[stage]['ds_phys']+=16
        self.rejects('stable port attribution')
    def test_valid_clockshift_is_not_silently_zeroed(self):
        self.event()['after']['dx']=5
        inputs=v.model_inputs(self.observation)
        self.assertEqual(inputs['port_minutes'][605].hex(),'0e745a76')
        self.assertNotEqual(inputs['port_minutes'][605],v.ZERO)
    def test_port606_clockshift_yields_four_real_byte_differences(self):
        from replay_maintenance_ports import replay_ports
        before=gzip.decompress((v.ROOT/'research/yt-maint/initial-controls/baseline-split/before-YTDATA.DAT.gz').read_bytes())
        exact,_=replay_ports(before,306,self.inputs['port_minutes'])
        self.event()['after']['dx']=5
        wrong,_=replay_ports(before,306,v.model_inputs(self.observation)['port_minutes'])
        differences=[i for i,(a,b)in enumerate(zip(exact,wrong))if a!=b]
        self.assertEqual(differences,list(range(605*137+101,605*137+105)))
        self.assertEqual(len(differences),4)
    def complete_replay(self,observation):
        import datetime
        from replay_maintenance_records import Inputs,synthesize
        data=v.model_inputs(observation)
        raw=bytearray(data['startup']);raw[2]^=0x80
        state=5|((raw[0]^raw[2])<<8)|((raw[1]^raw[3])<<16)
        root=v.ROOT/'research/yt-maint/initial-controls/baseline-split'
        before={n:gzip.decompress((root/('before-'+n+'.gz')).read_bytes())for n in ('YTDATA.DAT','YTNAME.DAT','YTNEWS.DAT')}
        inputs=Inputs(datetime.date(2026,11,2),'00:00:00',tuple(data['port_minutes']),tuple(data['helper1']),tuple(data['helper2']),data['xannoron'],state)
        outputs,stats=synthesize(before,inputs)
        # Completed targets are read only after pure synthesis and never supplied
        # to a model or the observed-register converter.
        target={n:gzip.decompress((root/('after-'+n+'.gz')).read_bytes())for n in outputs}
        return outputs,target,stats
    def test_complete_six_file_replay_from_one_observation(self):
        from replay_maintenance_records import compare
        outputs,target,stats=self.complete_replay(self.observation)
        result=compare(target,outputs)
        self.assertEqual((result['compared_bytes'],result['byte_mismatches']),(570059,0))
        self.assertEqual((stats['npcs']['total_draws'],stats['npcs']['final_rng_state']),(25891,0x4307ee))
    def test_clockshift_cannot_be_masked_in_complete_replay(self):
        from replay_maintenance_records import compare
        self.event()['after']['dx']=5
        outputs,target,_=self.complete_replay(self.observation)
        result=compare(target,outputs)
        self.assertEqual(result['byte_mismatches'],4)
        self.assertEqual({(d['file'],d['record'],d['field_offset'])for d in result['first_differences']},{('YTDATA.DAT',3657,o)for o in range(101,105)})
    def test_positive_clock_must_not_use_canonical_zero(self):
        self.event()['after']['dx']=5;data=v.model_inputs(self.observation)
        self.assertNotEqual(data['port_seconds'][605],bytes(4))
        self.assertNotEqual(data['port_minutes'][605],bytes(4))

class CaptureProvenanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pins=json.loads(v.PINS_FILE.read_text())
        cls.observer=v.OBSERVER.read_text()
    def setUp(self):
        import tempfile,shutil
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name)/'observed-a'
        shutil.copytree(v.DEFAULT/'observed-a',self.folder)
    def metadata(self,change):
        p=self.folder/'capture.json';m=json.loads(p.read_text());change(m);p.write_text(json.dumps(m,indent=2)+'\n')
    def write(self,name,raw):
        (self.folder/name).write_bytes(raw)
        self.metadata(lambda m:m['files'].__setitem__(name,v.SHA(raw)))
    def controller(self,change):
        c=json.loads((self.folder/'controller.json').read_text());change(c)
        raw=(json.dumps(c,indent=2)+'\n').encode();self.write('controller.json',raw)
        self.metadata(lambda m:m.__setitem__('controller',c))
    def observation(self,change):
        a=json.loads(gzip.decompress((self.folder/'host-time.json.gz').read_bytes()));change(a)
        self.write('host-time.json.gz',gzip.compress((json.dumps(a,separators=(',',':'))+'\n').encode(),mtime=0))
    def rejects(self,reason='.'):
        with self.assertRaisesRegex((AssertionError,ValueError,KeyError,FileNotFoundError),reason):
            v.verify_case(self.folder,self.pins['cases']['observed-a'],self.observer)
    def test_complete_corpus_verifies(self):self.assertEqual(v.verify()['byte_mismatches'],0)
    def test_guest_before_patched(self):self.metadata(lambda m:m['guest_before'].__setitem__('YTMAINT.EXE','0'*64));self.rejects('byte-identical')
    def test_guest_after_patched(self):self.metadata(lambda m:m['guest_after'].__setitem__('BRUN30.EXE','0'*64));self.rejects('byte-identical')
    def test_untrusted_input_world(self):self.metadata(lambda m:m['inputs'].__setitem__('YTDATA.DAT','0'*64));self.rejects('before inputs')
    def test_wrong_host_digest(self):self.metadata(lambda m:m['host'].__setitem__('sha256','0'*64));self.rejects('host binary')
    def test_wrong_host_uuid(self):self.metadata(lambda m:m['host'].__setitem__('uuid','0'*36));self.rejects('host binary')
    def test_changed_dos_clock_recipe(self):self.metadata(lambda m:m.__setitem__('clock','00:00:01'));self.rejects('DOS clock recipe')
    def test_changed_emulator_environment(self):self.metadata(lambda m:m['environment'].__setitem__('SDL_VIDEODRIVER','cocoa'));self.rejects('environment')
    def test_changed_actual_cpu(self):self.write('dosbox.stderr',(self.folder/'dosbox.stderr').read_bytes()+b'now | CPU: Setting fixed 1 cycles.\n');self.rejects('fixed CPU')
    def test_changed_command_recipe(self):self.write('COMMANDS.TXT',(self.folder/'COMMANDS.TXT').read_bytes()+b'time 12:00:00\n');self.rejects('command recipe')
    def test_changed_observer_source(self):self.write('loaded-observer.js',(self.folder/'loaded-observer.js').read_bytes()+b'/* undeclared observer */\n');self.rejects('observer template')
    def test_forced_termination(self):self.controller(lambda c:c.__setitem__('forced',True));self.rejects('owned-process cleanup')
    def test_still_live_process(self):self.controller(lambda c:c.__setitem__('process_exited',False));self.rejects('owned-process cleanup')
    def test_nonzero_process_exit(self):self.controller(lambda c:c.__setitem__('exit_code',1));self.rejects('natural zero exit')
    def test_detached_before_process_termination(self):self.controller(lambda c:c.__setitem__('detached_reason','application-requested'));self.rejects('natural termination')
    def test_observer_not_ready(self):self.controller(lambda c:c.__setitem__('ready',False));self.rejects('ready before')
    def test_incomplete_flush(self):self.controller(lambda c:c['messages'][1]['payload'].__setitem__('bytes',1));self.rejects('exact-byte trace flush')
    def test_wrong_frida_version(self):self.controller(lambda c:c['frida'].__setitem__('version','17.0.0'));self.rejects('Frida package version')
    def test_wrong_frida_module_digest(self):self.controller(lambda c:c['frida'].__setitem__('module_sha256','0'*64));self.rejects('Frida package/module digest')
    def test_forged_observed_module(self):self.observation(lambda a:a['module'].__setitem__('uuid','0'*36));self.rejects('native host identity')
    def test_forged_zero_gap_clock(self):
        def change(a):
            event=next(e for e in a['events']if e['before']['port_raw']==v_mbf606 and struct.unpack('<20H',bytes.fromhex(e['before']['stack']))[7]==0x0927)
            event['after']['dx']=5
        original=json.loads(gzip.decompress((self.folder/'host-time.json.gz').read_bytes()))
        ports=v.port_events(original);v_mbf606=original['events'][ports[605]['ordinal']-1]['before']['port_raw']
        self.observation(change);self.rejects('without any gap mask')
    def test_false_successful_dos_status(self):self.write('ERROR.LOG',b'PROGRAM_ERROR\r\n');self.rejects('DOS program status')
    def test_missing_complete_after_file(self):(self.folder/'after-YTNEWS.DAT.gz').unlink();self.rejects()
    def test_uncaptured_extra_output(self):(self.folder/'after-EXTRA.DAT.gz').write_bytes(gzip.compress(b'fake'));self.rejects('capture inventory')


if __name__=='__main__':unittest.main()
