"""Independent corruption controls for retained maintenance phase chronology."""
import copy
import gzip
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import verify_maintenance_chronology as v


def mbf_integer(value):
    if not value:return b'\0'*4
    exponent=value.bit_length()
    mantissa=value*(1<<(24-exponent))-(1<<23)
    return mantissa.to_bytes(3,'little')+bytes([128+exponent])


class MaintenanceChronologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=(v.ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes()
        cls.pins=json.loads(v.PINS_FILE.read_text())
        cls.rows={}
        for name,pin in cls.pins['controls'].items():
            row=v.verify_control(v.DEFAULT/name,pin,cls.original)
            if name!='untouched':row.pop('world')
            cls.rows[name]=row
        cls.anchors=v.old_anchors()
        cls.graph=v.initial_graph()

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.name='candidate-01-first-state'
        self.folder=Path(self.temp.name)/self.name
        shutil.copytree(v.DEFAULT/self.name,self.folder)

    def meta(self,key,value):
        p=self.folder/'result.json';m=json.loads(p.read_text());m[key]=value;p.write_text(json.dumps(m))

    def write(self,name,raw):
        (self.folder/name).write_bytes(raw)
        p=self.folder/'result.json';m=json.loads(p.read_text());m['files'][name]=v.SHA(raw);p.write_text(json.dumps(m))

    def rejects(self):
        with self.assertRaises((AssertionError,KeyError,ValueError,FileNotFoundError)):
            v.verify_control(self.folder,self.pins['controls'][self.name],self.original)

    def test_complete_retained_matrix(self):
        self.assertEqual(v.verify(),{'controls':332,'untouched':1,'body_end':4,'nth_hits':327,'native_reads':3,'mobile_groups':19,'literal_rng_draws':25891})
    def test_raw_state_rehashed_manifest(self):
        b=bytearray((self.folder/'TRACE.BIN').read_bytes());b[-4]^=1;self.write('TRACE.BIN',b);self.rejects()
    def test_raw_world_rehashed_manifest(self):
        name='after-YTDATA.DAT.gz';b=bytearray(gzip.decompress((self.folder/name).read_bytes()));b[100]^=1
        self.write(name,gzip.compress(b,mtime=0));self.rejects()
    def test_wrong_site(self):self.meta('site',0x3c0e);self.rejects()
    def test_wrong_counter(self):self.meta('nth',2);self.rejects()
    def test_wrong_source(self):self.meta('source',0x7bc0);self.rejects()
    def test_unsafe_inline_operand_site(self):self.meta('site',0x3c13);self.rejects()
    def test_wrong_probe_identity(self):self.meta('copied_sha256','0'*64);self.rejects()
    def test_wrong_binary_identity(self):
        bins=dict(v.BINARIES);bins['YTMAINT.EXE']='0'*64;self.meta('binaries',bins);self.rejects()
    def test_wrong_inputs(self):
        m=json.loads((self.folder/'result.json').read_text());m['inputs']['YTDATA.DAT']='0'*64
        self.meta('inputs',m['inputs']);self.rejects()
    def test_undeclared_fixture_patch(self):self.meta('patches',[{'offset':1,'before':'00','after':'01'}]);self.rejects()
    def test_wrong_occupied_fixture(self):self.meta('occupied',[1095]);self.rejects()
    def test_false_main_body_end_claim(self):self.meta('complete',True);self.rejects()
    def test_missing_ok_witness(self):(self.folder/'OK.LOG').unlink();self.rejects()
    def test_nonzero_dos_error(self):self.write('ERROR.LOG',b'PROGRAM_ERROR\r\n');self.rejects()
    def test_empty_ok_witness(self):self.write('OK.LOG',b'');self.rejects()
    def test_forged_shell_return(self):self.write('RETURN.LOG',b'PROGRAM_RETURNED\r\nforged');self.rejects()
    def test_empty_launch(self):self.write('dosbox.log',b'');self.rejects()
    def test_contradictory_cpu(self):self.write('dosbox.log',(self.folder/'dosbox.log').read_bytes()+b'now | CPU: Setting fixed 1 cycles.\n');self.rejects()
    def test_contradictory_video(self):self.write('dosbox.log',(self.folder/'dosbox.log').read_bytes()+b'now | SDL: opengl video initialised\n');self.rejects()
    def test_contradictory_sound(self):self.write('dosbox.log',(self.folder/'dosbox.log').read_bytes()+b'now | MIXER: Sound output enabled\n');self.rejects()
    def test_wrong_mount(self):self.write('dosbox.log',(self.folder/'dosbox.log').read_bytes().replace(self.name.encode(),b'wrong-control'));self.rejects()
    def test_wrong_command_recipe(self):self.write('COMMANDS.TXT',(self.folder/'COMMANDS.TXT').read_bytes()+b'exit\n');self.rejects()
    def test_wrong_clock_observation(self):self.write('DOSTIME.LOG',b'Current time: 12:00:00.00pm\r\n');self.rejects()
    def test_wrong_date_observation(self):self.write('DOSDATE.LOG',b'Current date: Mon 11/03/2026\r\n');self.rejects()
    def test_extra_retained_artifact(self):(self.folder/'EXTRA.DAT').write_bytes(b'fake');self.rejects()
    def test_relabelled_metadata(self):self.meta('name','wrong-control');self.rejects()
    def test_changed_native_identity(self):
        raw=json.loads(v.NATIVE.read_text());raw['records'][0]['subject']['digest']['sha256']='0'*64
        p=Path(self.temp.name)/'native.json';p.write_text(json.dumps(raw))
        with self.assertRaisesRegex(AssertionError,'native identity'):v.verify_native(p,self.original)
    def test_truncated_native_observation(self):
        raw=json.loads(v.NATIVE.read_text());raw['records'][0]['normalized_result']['returned_bytes']-=1
        p=Path(self.temp.name)/'native.json';p.write_text(json.dumps(raw))
        with self.assertRaisesRegex(AssertionError,'native truncation'):v.verify_native(p,self.original)

    def semantic_reject(self,mutate,reason):
        rows=copy.deepcopy(self.rows);anchors=dict(self.anchors);mutate(rows,anchors)
        with self.assertRaisesRegex(AssertionError,reason):v.verify_semantics(rows,anchors,self.graph)
    def test_candidate_phase_start_without_pins(self):
        self.semantic_reject(lambda r,a:r['candidate-01-first-state'].__setitem__('state',r['candidate-01-first-state']['state']^1),'candidate scan starts')
    def test_candidate_player_count_without_pins(self):
        self.semantic_reject(lambda r,a:r['candidate-01-last-state'].__setitem__('state',r['candidate-01-last-state']['state']^1),'candidate fifty-player draw boundary')
    def test_scan_phase_start_without_pins(self):
        self.semantic_reject(lambda r,a:r['scan-01-first-state'].__setitem__('state',r['scan-01-first-state']['state']^1),'candidate scan joins')
    def test_scan_phase_end_without_pins(self):
        self.semantic_reject(lambda r,a:r['scan-01-last-state'].__setitem__('state',r['scan-01-last-state']['state']^1),'complete fifty-player blocks')
    def test_next_seed_anchor_without_pins(self):
        self.semantic_reject(lambda r,a:a.__setitem__('baseline--h2-old-002',a['baseline--h2-old-002']^1),'scan end reaches next reseed')
    def test_wanderer_bridge_without_pins(self):
        self.semantic_reject(lambda r,a:a.__setitem__('baseline--h1-old-002',a['baseline--h1-old-002']^1),'three Wanderer draws bridge')
    def test_allocator_bridge_without_pins(self):
        self.semantic_reject(lambda r,a:a.__setitem__('baseline--h1-old-003',a['baseline--h1-old-003']^1),'allocator final draw')
    def test_fallback_bridge_without_pins(self):
        self.semantic_reject(lambda r,a:a.__setitem__('baseline--h1-old-004',a['baseline--h1-old-004']^1),'fallback draw to candidate reseed')
    def test_decoded_group_without_pins(self):
        self.semantic_reject(lambda r,a:r['scan-01-first-group'].__setitem__('raw',mbf_integer(3)),'decoded active group identity')
    def test_decoded_first_player_without_pins(self):
        self.semantic_reject(lambda r,a:r['candidate-01-first-player'].__setitem__('raw',mbf_integer(3)),'first/last cached player slot')
    def test_decoded_last_player_without_pins(self):
        self.semantic_reject(lambda r,a:r['scan-01-last-player'].__setitem__('raw',mbf_integer(50)),'first/last cached player slot')
    def test_pre_step_sector_zero_without_pins(self):
        self.semantic_reject(lambda r,a:r['scan-01-first-prestep'].__setitem__('raw',b'\0'*4),'pre-step sector is a bounded')
    def test_fractional_destination_without_pins(self):
        self.semantic_reject(lambda r,a:r['scan-01-first-destination'].__setitem__('raw',bytes.fromhex('00004081')),'destination sector is a bounded')
    def test_nonedge_destination_without_pins(self):
        def change(rows,anchors):
            source=int(v.mbf(rows['scan-01-first-prestep']['raw']))
            invalid=next(n for n in range(1,3001)if n not in self.graph[source])
            rows['scan-01-first-destination']['raw']=mbf_integer(invalid)
        self.semantic_reject(change,'directed original warp edge')
    def test_last_destination_force_without_pins(self):
        def change(rows,anchors):
            destination=int(v.mbf(rows['scan-01-last-destination']['raw']))
            world=bytearray(rows['untouched']['world']);at=(50+destination)*137+81
            world[at:at+4]=b'\0'*4;rows['untouched']['world']=bytes(world)
        self.semantic_reject(change,'positive Xannor sector force')
    def test_desertion_draw_without_pins(self):
        self.semantic_reject(lambda r,a:r['desertion-11-before'].__setitem__('state',r['desertion-11-before']['state']^1),'twenty consecutive eager desertion')
    def test_desertion_post_boundary_without_pins(self):
        self.semantic_reject(lambda r,a:r['desertion-last-after'].__setitem__('state',r['desertion-last-after']['state']^1),'last desertion post-draw')
    def test_lottery_entry_without_pins(self):
        self.semantic_reject(lambda r,a:r['lottery-before'].__setitem__('state',r['lottery-before']['state']^1),'desertion to lottery gate')
    def test_lottery_post_boundary_without_pins(self):
        self.semantic_reject(lambda r,a:r['lottery-after'].__setitem__('state',r['lottery-after']['state']^1),'single lottery post-draw')
    def test_counter_total_without_pins(self):
        self.semantic_reject(lambda r,a:r['count-3c0e'].__setitem__('count',24799),'fresh complete phase counter')
    def test_counter_auxiliary_equality_without_pins(self):
        self.semantic_reject(lambda r,a:r['count-3348']['outputs'].__setitem__('after-YTNEWS.DAT.gz','0'*64),'outputs equal fresh untouched')
    def test_fresh_untouched_baseline_equality_without_pins(self):
        def change(rows,anchors):
            for name in ('untouched','count-3348','count-3c0e','count-7900','count-7946'):
                rows[name]['outputs']['after-YTNEWS.DAT.gz']='0'*64
        self.semantic_reject(change,'match prior pinned baseline')

if __name__=='__main__':unittest.main()
