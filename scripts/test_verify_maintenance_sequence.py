"""Corruption controls for portable maintenance sequencing witnesses."""
import copy
import gzip
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import verify_maintenance_sequence as v


class MaintenanceSequenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=(v.ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes()
        cls.pins=json.loads(v.PINS_FILE.read_text())
        cls.observed={}
        for name,pin in cls.pins['controls'].items():
            row=v.verify_control(v.DEFAULT/name,pin,cls.original)
            if not name.endswith('--untouched'):row.pop('world')
            cls.observed[name]=row

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.name='baseline--h1-draw-001'
        self.folder=Path(self.temp.name)/self.name
        shutil.copytree(v.DEFAULT/self.name,self.folder)

    def change_meta(self,field,value):
        p=self.folder/'result.json';m=json.loads(p.read_text());m[field]=value;p.write_text(json.dumps(m))

    def write(self,name,data):
        (self.folder/name).write_bytes(data)
        p=self.folder/'result.json';m=json.loads(p.read_text());m['files'][name]=v.SHA(data);p.write_text(json.dumps(m))

    def rejects(self):
        with self.assertRaises((AssertionError,KeyError,ValueError,FileNotFoundError)):
            v.verify_control(self.folder,self.pins['controls'][self.name],self.original)

    def test_complete_retained_matrix(self):
        self.assertEqual(v.verify()['controls'],463)

    def test_state_rehashed_manifest(self):
        data=bytearray((self.folder/'TRACE.BIN').read_bytes());data[-4]^=1;self.write('TRACE.BIN',data);self.rejects()

    def test_world_rehashed_manifest(self):
        name='after-YTDATA.DAT.gz';b=bytearray(gzip.decompress((self.folder/name).read_bytes()));b[300]^=1
        self.write(name,gzip.compress(b,mtime=0));self.rejects()

    def test_wrong_counter_threshold(self):self.change_meta('nth',2);self.rejects()
    def test_wrong_site(self):self.change_meta('site',0x7989);self.rejects()
    def test_wrong_source(self):self.change_meta('source',0x7ea4);self.rejects()
    def test_wrong_copy_digest(self):self.change_meta('copied_sha256','0'*64);self.rejects()
    def test_wrong_input_digest(self):
        m=json.loads((self.folder/'result.json').read_text());m['inputs']['YTDATA.DAT']='0'*64
        self.change_meta('inputs',m['inputs']);self.rejects()
    def test_wrong_binary_digest(self):
        x=dict(v.BINARIES);x['BRUN30.EXE']='0'*64;self.change_meta('binaries',x);self.rejects()
    def test_undeclared_occupancy(self):self.change_meta('occupied',[1095]);self.rejects()
    def test_patch_relabeling(self):self.change_meta('patches',[{'offset':1,'before':'00','after':'01'}]);self.rejects()
    def test_fake_complete_flag(self):self.change_meta('complete',True);self.rejects()
    def test_missing_output(self):(self.folder/'OK.LOG').unlink();self.rejects()
    def test_error_witness(self):self.write('ERROR.LOG',b'PROGRAM_ERROR\r\n');self.rejects()
    def test_empty_ok_witness(self):self.write('OK.LOG',b'');self.rejects()
    def test_extra_return_witness(self):self.write('RETURN.LOG',b'PROGRAM_RETURNED\r\nFORGED');self.rejects()
    def test_empty_launch(self):self.write('dosbox.log',b'');self.rejects()
    def test_contradictory_cpu(self):self.write('dosbox.log',(self.folder/'dosbox.log').read_bytes()+b'now | CPU: Setting fixed 4000 cycles.\n');self.rejects()
    def test_contradictory_video(self):self.write('dosbox.log',(self.folder/'dosbox.log').read_bytes()+b'now | SDL: opengl video initialised\n');self.rejects()
    def test_contradictory_sound(self):self.write('dosbox.log',(self.folder/'dosbox.log').read_bytes()+b'now | MIXER: Sound output enabled\n');self.rejects()
    def test_wrong_mount(self):self.write('dosbox.log',(self.folder/'dosbox.log').read_bytes().replace(self.name.encode(),b'wrong-control'));self.rejects()
    def test_wrong_commands(self):self.write('COMMANDS.TXT',(self.folder/'COMMANDS.TXT').read_bytes().replace(b'cpu_cycles=200000',b'cpu_cycles=1')+b'exit\n');self.rejects()
    def test_clock_substitution(self):
        self.write('DOSTIME.LOG',(v.DEFAULT/'shift--untouched'/'DOSTIME.LOG').read_bytes());self.rejects()
    def test_wrong_date(self):self.write('DOSDATE.LOG',b'Current date: Mon 11/03/2026\r\n');self.rejects()
    def test_unknown_file(self):(self.folder/'EXTRA.DAT').write_bytes(b'fake');self.rejects()
    def test_metadata_pin(self):self.change_meta('name','relabelled');self.rejects()
    def test_wrong_native_identity(self):
        raw=json.loads(v.NATIVE.read_text());raw['records'][0]['subject']['digest']['sha256']='0'*64
        path=Path(self.temp.name)/'native.json';path.write_text(json.dumps(raw))
        with self.assertRaisesRegex(AssertionError,'native identity'):v.verify_native(path,self.original)
    def test_truncated_native(self):
        raw=json.loads(v.NATIVE.read_text());raw['records'][0]['normalized_result']['returned_bytes']-=1
        path=Path(self.temp.name)/'native.json';path.write_text(json.dumps(raw))
        with self.assertRaisesRegex(AssertionError,'native truncation'):v.verify_native(path,self.original)

    def semantic_reject(self,mutate,reason):
        observations=copy.deepcopy(self.observed);mutate(observations)
        with self.assertRaisesRegex(AssertionError,reason):v.verify_semantics(observations)
    def test_reseed_semantics_without_pins(self):
        self.semantic_reject(lambda o:o['baseline--h1-seed-002'].__setitem__('state',o['baseline--h1-seed-002']['state']^1),'RANDOMIZE')
    def test_h1_draw_semantics_without_pins(self):
        self.semantic_reject(lambda o:o['baseline--h1-draw-002'].__setitem__('state',o['baseline--h1-draw-002']['state']^1),'helper1 LCG')
    def test_h2_draw_semantics_without_pins(self):
        self.semantic_reject(lambda o:o['baseline--h2-draw-008'].__setitem__('state',o['baseline--h2-draw-008']['state']^1),'helper2 recurrence')
    def test_h2_fac_semantics_without_pins(self):
        self.semantic_reject(lambda o:o['baseline--h2-fac-008'].__setitem__('raw',bytes.fromhex('00000081')),'RND FAC')
    def test_auxiliary_mismatch_without_pins(self):
        self.semantic_reject(lambda o:o['baseline--count-2237']['outputs'].__setitem__('after-YTNEWS.DAT.gz','0'*64),'all DAT/ASC')
    def test_repeated_helper_count_without_pins(self):
        self.semantic_reject(lambda o:o['baseline--count-7908'].__setitem__('count',40),'one seed/draw')
    def test_literal_site_count_without_pins(self):
        self.semantic_reject(lambda o:o['baseline--count-3348'].__setitem__('count',951),'literal-site count inventory')
    def test_occupied_old_state_chain_without_pins(self):
        self.semantic_reject(lambda o:o['occupied--h1-old-002'].__setitem__('state',o['occupied--h1-old-002']['state']^1),'rejected candidate state flows')
    def test_occupied_helper_count_without_pins(self):
        def change(o):
            for site in ('7900','7908'):o['occupied--count-'+site]['count']=41
        self.semantic_reject(change,'additional occupied-candidate helper call')
    def test_occupied_world_links_rejected_candidate_without_pins(self):
        def change(o):
            row=o['occupied--untouched'];world=bytearray(row['world'])
            at=(50+1792)*137+93;world[at:at+4]=b'\0'*4
            at=(50+1095)*137+93;world[at:at+4]=bytes.fromhex('00000081')
            row['world']=bytes(world)
        self.semantic_reject(change,'only accepted candidate links')
    def test_occupied_candidate_draw_without_pins(self):
        self.semantic_reject(lambda o:o['occupied--h1-draw-002'].__setitem__('state',o['occupied--h1-draw-001']['state']),'second occupied-fixture candidate')
    def test_optimistic_receipt_semantics_without_pins(self):
        self.semantic_reject(lambda o:o['occupied--untouched'].__setitem__('trace',o['occupied--untouched']['trace'].replace(b'Wanderer has successfully warped!\r\n',b'',1)),'optimistic success receipt')
    def test_caller_unknown_return_without_pins(self):
        self.semantic_reject(lambda o:o['baseline--h1-caller-001'].__setitem__('caller_ip',0x7777),'far-call return identity')
    def test_caller_zero_segment_without_pins(self):
        self.semantic_reject(lambda o:o['baseline--h1-caller-001'].__setitem__('caller_cs',0),'far-call return identity')
    def test_caller_mixed_segments_without_pins(self):
        self.semantic_reject(lambda o:o['baseline--h1-caller-001'].__setitem__('caller_cs',0x1234),'shared observed caller code segment')
    def test_caller_wrong_phase_without_pins(self):
        self.semantic_reject(lambda o:o['baseline--h1-caller-041'].__setitem__('caller_ip',0x7312),'helper1 phase caller sequence')
    def test_forged_normal_completion(self):
        meta=dict(site=None,complete=True)
        with self.assertRaisesRegex(AssertionError,'untouched normal completion'):v.classify_trace(v.MAINT_BANNER+b'fake',meta)
    def test_forged_count_as_untouched(self):
        meta=dict(site=None,complete=True)
        with self.assertRaisesRegex(AssertionError,'untouched normal completion'):v.classify_trace(v.MAINT_BANNER+b'\xfe\xffC!',meta)
    def test_instrumented_false_cleanup(self):
        meta=dict(site=0x7908,complete=True,nth=65535,source=0x234)
        with self.assertRaisesRegex(AssertionError,'cleanup is bypassed'):v.classify_trace(v.MAINT_BANNER+b'Daily Maintenance Completed OK\r\n\xfe\xffC!',meta)
    def test_counter_underflow_claim(self):
        meta=dict(site=0x7908,complete=True,nth=1,source=0x234)
        with self.assertRaisesRegex(AssertionError,'remaining finite counter'):v.classify_trace(v.MAINT_BANNER+b'\x02\x00C!',meta)
    def test_impossible_32bit_state(self):
        meta=dict(site=0x7908,complete=False,nth=1,source=0x234)
        with self.assertRaisesRegex(AssertionError,'24-bit runtime'):v.classify_trace(v.MAINT_BANNER+b'\0\0\0\1',meta)

if __name__=='__main__':unittest.main()
