"""Portable semantic and provenance corruption controls for clock/date evidence."""
import copy
import datetime
import gzip
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import verify_maintenance_clock_matrix as v

class MatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ob={p:json.loads(gzip.decompress((v.DEFAULT/p/'observed-a/host-time.json.gz').read_bytes()))for p in v.PROFILES}
        cls.pins=json.loads(v.PINS_FILE.read_text())
    def observation(self):return copy.deepcopy(self.ob['noon'])
    def selected(self,ob,kind='timer',role='port'):
        return next(e for e in ob['events']if (lambda p:p['kind']==kind and p.get('role')==role)(v.event_pair(e,e['ordinal'])))
    def test_full_corpus(self):self.assertEqual(v.verify()['runs'],48)
    def test_all_profiles_source_parse_including_late(self):
        for profile,ob in self.ob.items():
            with self.subTest(profile=profile):self.assertEqual(len(v.model_inputs(ob)['port_dates']),1000)
    def test_dynamic_helper_inventory(self):
        self.assertEqual(len(v.model_inputs(self.ob['noon'])['helper1']),42)
        self.assertEqual(len(v.model_inputs(self.ob['late'])['helper1']),41)
    def test_carried_time_without_date_rewrite(self):
        value=v.model_inputs(self.ob['near-midnight-100k'])
        self.assertEqual((value['score_date'],value['score_clock']),(datetime.date(2026,11,2),'24:00:00'))
    def test_midnight_separate_sample_dates(self):
        value=v.model_inputs(self.ob['rollover'])
        self.assertEqual((value['news_date'],value['score_date']),(datetime.date(2026,11,2),datetime.date(2026,11,3)))
    def test_double_rounding(self):self.assertEqual(v.clock_to_raw(0,3)[1].hex(),'6e120376')
    def test_true_zero_only(self):
        self.assertEqual(v.clock_to_raw(0,0)[0].hex(),'00004800')
        self.assertNotEqual(v.clock_to_raw(0,5)[0].hex(),'00004800')
    def test_time_carry_boundary(self):
        self.assertEqual(v.native_time_text(0x173b,0x3b31),'23:59:59')
        self.assertEqual(v.native_time_text(0x173b,0x3b32),'24:00:00')
    def test_real_exhaustion_accounting(self):
        for p in('rollover','near-midnight-100k'):v.model_inputs(self.ob[p])
    def test_clock_shift_admitted_parser_but_not_saved_timestamp(self):
        ob=copy.deepcopy(self.ob['shift-two']);event=self.selected(ob)
        event['after']['dx']=(event['after']['dx']+5)%100
        inputs=v.model_inputs(ob)
        world=gzip.decompress((v.DEFAULT/'shift-two/observed-a/after-YTDATA.DAT.gz').read_bytes())
        with self.assertRaises(AssertionError):v.neutral.verify_port_timestamps(world,inputs)
    def test_zero_gap_mask_rejected(self):
        inputs=v.model_inputs(self.ob['shift-two']);world=bytearray(gzip.decompress((v.DEFAULT/'shift-two/observed-a/after-YTDATA.DAT.gz').read_bytes()))
        at=(3050+606)*137+101;world[at:at+4]=v.neutral.ZERO
        with self.assertRaises(AssertionError):v.neutral.verify_port_timestamps(world,inputs)
    def test_pins_cannot_be_rehashed(self):
        with tempfile.TemporaryDirectory()as d:
            pin=Path(d)/'pins.json';data=copy.deepcopy(self.pins);data['cases']['late/observed-a']['capture_sha256']='0'*64;pin.write_text(json.dumps(data))
            with self.assertRaisesRegex(AssertionError,'immutable clock-matrix'):v.verify(pins_path=pin)
    def test_exact48_inventory(self):
        with self.assertRaises(AssertionError):v.verify_equivalence({})
    def test_native_rehashed_mutation_rejected(self):
        data=copy.deepcopy(self.pins['native']);data['rea.json']='0'*64
        with self.assertRaises(AssertionError):v.verify_native(data)
    def test_mode_clock_recipe_mutation(self):
        f=v.DEFAULT/'noon/observed-a';meta=json.loads((f/'capture.json').read_text());meta['cycles']=10000
        with self.assertRaises(AssertionError):v.verify_launch(f,meta)
    def test_complete_source_inventory(self):v.verify_native(self.pins['native'])
    def test_sixth_cycle_requires_exhaustion(self):
        event=copy.deepcopy(self.selected(self.observation()))
        event['before'].update(cycles=100,cycle_left=0,pic=100)
        event['after'].update(cycles=94,cycle_left=0,pic=100)
        with self.assertRaisesRegex(AssertionError,'genuinely exhausted'):v.event_pair(event,event['ordinal'])
    def test_lost_exhaustion_cycle_requires_tick(self):
        event=copy.deepcopy(self.selected(self.observation()))
        event['before'].update(cycles=4,cycle_left=20,pic=100)
        event['after'].update(cycles=19,cycle_left=0,pic=100)
        with self.assertRaisesRegex(AssertionError,'PIC tick reset'):v.event_pair(event,event['ordinal'])
    def test_controller_forced_exit_rejected(self):
        folder=v.DEFAULT/'noon/unobserved-a';controller=json.loads((folder/'controller.json').read_text());controller['forced']=True
        with self.assertRaises(AssertionError):v.neutral.verify_controller(controller,'unobserved')
    def test_controller_actual_frida_version_rejected(self):
        folder=v.DEFAULT/'noon/observed-a';controller=json.loads((folder/'controller.json').read_text());controller['frida']['version']='17.0.0'
        raw=gzip.decompress((folder/'host-time.json.gz').read_bytes())
        with self.assertRaisesRegex(AssertionError,'Frida package version'):v.neutral.verify_controller(controller,'observed',json.loads(raw),raw)

# Each mutation targets a distinct authenticated semantic contract, rather than
# merely changing an immutable digest. Pair mutations preserve raw entry/leave
# equality where necessary to reach the source-attribution check.
def add_mutation(name,mutate):
    def test(self):
        ob=self.observation();mutate(self,ob)
        with self.assertRaises((AssertionError,ValueError)):v.model_inputs(ob)
    setattr(MatrixTests,'test_reject_'+name,test)

def paired(self,ob,key,value,kind='timer',role='port'):
    event=self.selected(ob,kind,role)
    for side in('before','after'):event[side][key]=value

add_mutation('dropped',lambda s,o:o.update(dropped=1))
add_mutation('error',lambda s,o:o.update(errors=['lost event']))
add_mutation('nonzero_exit',lambda s,o:o.update(exit_code=1))
add_mutation('wrong_recipe',lambda s,o:o.update(recipe='host-dos-time-observer-v1'))
add_mutation('hook_disabled',lambda s,o:o.update(observe=False))
add_mutation('missing_pair',lambda s,o:o['events'].pop(30))
add_mutation('duplicate_pair',lambda s,o:o['events'].insert(30,copy.deepcopy(o['events'][30])))
add_mutation('wrong_function',lambda s,o:s.selected(o).update(function=42))
add_mutation('interrupt_ip',lambda s,o:s.selected(o)['after'].update(ip=0x13e5))
add_mutation('raw_source_signature',lambda s,o:paired(s,o,'runtime_signature','00'*8))
add_mutation('application_fixup',lambda s,o:paired(s,o,'application_call','9a2fc10000'))
add_mutation('caller_window',lambda s,o:paired(s,o,'caller_code','00'*32))
add_mutation('port_fraction',lambda s,o:paired(s,o,'port_raw','00000000'))
add_mutation('port_order_duplicate',lambda s,o:paired(s,o,'port_raw','00000082'))
add_mutation('segment_cache',lambda s,o:paired(s,o,'ds_phys',1))
add_mutation('unknown_nested',lambda s,o:paired(s,o,'nested_application_call','00'*5,'date','calendar'))
add_mutation('bp_stack_disagreement',lambda s,o:paired(s,o,'bp_frame','00'*64,'date','calendar'))
add_mutation('auto_adjust',lambda s,o:paired(s,o,'auto_adjust',1))
add_mutation('cpu_max',lambda s,o:paired(s,o,'cycle_max',12345))
add_mutation('budget_delta',lambda s,o:s.selected(o)['after'].update(cycles=s.selected(o)['after']['cycles']-10))
add_mutation('time_hundredth',lambda s,o:s.selected(o)['after'].update(dx=100))
add_mutation('date_weekday',lambda s,o:s.selected(o,'date','news')['after'].update(ax=0x2a07))
add_mutation('date_calendar_invalid',lambda s,o:s.selected(o,'date','news')['after'].update(dx=0x0d01))
add_mutation('module_identity',lambda s,o:o['module'].update(uuid='00000000-0000-0000-0000-000000000000'))

if __name__=='__main__':unittest.main()
