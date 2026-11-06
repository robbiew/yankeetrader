"""Before-only admission, cache and source-witness placement properties.

Synthetic unit witnesses exercise branch contracts; they are not claimed to be
new native captures. Frozen original clock frames supply parser context only.
"""
import copy
import gzip
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

import replay_maintenance_placement as model
from replay_qb_graph import mbf

ROOT=Path(__file__).resolve().parents[1]
TIMER=bytes.fromhex('cdcc4c7c')


def put(world,record,offset,value):
    at=(record-1)*137+offset
    world[at:at+4]=value if type(value)is bytes else mbf.enc(value)


def row(role,ordinal,old,timer=TIMER):
    return dict(role=role,ordinal=ordinal,old_state=old,timer=timer)


class BeforeFixture:
    @classmethod
    def setUpClass(cls):
        source=ROOT/'research/yt-maint/initial-controls/baseline-split/before-YTDATA.DAT.gz'
        cls.before=gzip.decompress(source.read_bytes())

    def changed(self,*patches):
        world=bytearray(self.before)
        for rec,offset,value in patches:put(world,rec,offset,value)
        return bytes(world)


class CacheProperties(BeforeFixture,unittest.TestCase):
    def test_original_default_cache_is_before_only(self):
        with patch.object(Path,'read_bytes',side_effect=AssertionError('cache opened a file')):
            result=model.cache(self.before)
        self.assertEqual(result['total'],10000)
        self.assertEqual(result['locations'][1],849)
        self.assertEqual(result['forces'][1],10000)
        self.assertEqual(result['cleared_sectors'],{849:bytes.fromhex('00008000')})
        self.assertTrue(all(result['locations'][g]==result['forces'][g]==0 for g in range(2,21)))

    def test_duplicate_hq_chain_consumes_one_physical_force(self):
        before=self.changed((53,105,849),(54,105,849),(71,105,849))
        result=model.cache(before)
        self.assertEqual(result['total'],10000)
        self.assertEqual(result['forces'][1],10000)
        self.assertEqual(result['cleared_sectors'],{849:bytes.fromhex('00008000')})
        for group in(2,3,20):self.assertEqual((result['locations'][group],result['forces'][group]),(0,0))
        self.assertEqual(before,self.changed((53,105,849),(54,105,849),(71,105,849)))

    def test_duplicate_mobile_sector_is_counted_once_in_slot_order(self):
        before=self.changed((53,105,1000),(54,105,1000),(1051,81,37),(1051,85,-1))
        result=model.cache(before)
        self.assertEqual(result['total'],10037)
        self.assertEqual((result['locations'][2],result['forces'][2]),(1000,37))
        self.assertEqual((result['locations'][3],result['forces'][3]),(0,0))
        self.assertEqual(set(result['cleared_sectors']),{849,1000})

    def test_later_duplicate_slots_cannot_reintroduce_force(self):
        result=model.cache(self.changed((57,105,1000),(60,105,1000),(71,105,1000),
                                        (1051,81,37),(1051,85,-1)))
        self.assertEqual(result['forces'][6],37)
        self.assertEqual(result['forces'][9],0)
        self.assertEqual(result['forces'][20],0)
        self.assertEqual(result['total'],10037)

    def test_neutral_and_mercenary_forces_are_not_consumed_as_xannor(self):
        for owner in (0,-2,2):
            with self.subTest(owner=owner):
                before=self.changed((53,105,3000),(3051,81,37),(3051,85,owner))
                result=model.cache(before)
                self.assertEqual(result['total'],10000)
                self.assertEqual((result['locations'][2],result['forces'][2]),(0,0))
                self.assertNotIn(3000,result['cleared_sectors'])
                self.assertEqual(mbf.get(before,3051,81),37)
                self.assertEqual(mbf.get(before,3051,85),owner)

    def test_unpointed_friendly_sector_is_not_silently_cached(self):
        result=model.cache(self.changed((1599,81,37),(1599,85,-1)))
        self.assertEqual(result['total'],10000)
        self.assertNotIn(1548,result['cleared_sectors'])

    def test_zero_force_pointer_normalizes_both_rows_to_zero(self):
        result=model.cache(self.changed((53,105,1000),(1051,81,0),(1051,85,-1)))
        self.assertEqual((result['locations'][2],result['forces'][2]),(0,0))
        self.assertIn(1000,result['cleared_sectors'])

    def test_invalid_world_type_extent_and_geometry_fail_closed(self):
        for value in(bytearray(self.before),self.before[:-1],self.changed((1,53,50)),self.changed((1,57,3050)),
                     self.changed((1,61,4050)),self.changed((1,93,4150))):
            with self.subTest(type=type(value),length=len(value)):
                with self.assertRaises(ValueError):model.cache(value)

    def test_fractional_negative_and_out_of_range_pointers_fail_closed(self):
        for where in(-1,.25,3001,1000000):
            with self.subTest(where=where):
                with self.assertRaises(ValueError):model.cache(self.changed((53,105,where)))

    def test_fractional_negative_and_large_pointed_xannor_forces_fail_closed(self):
        for force in(-1,.25,1000001):
            with self.subTest(force=force):
                with self.assertRaises(ValueError):model.cache(self.changed((53,105,1000),(1051,81,force),(1051,85,-1)))

    def test_pointed_xannor_force_bound_is_inclusive(self):
        result=model.cache(self.changed((53,105,1000),(1051,81,1000000),(1051,85,-1)))
        self.assertEqual(result['total'],1010000)


class PlacementProperties(BeforeFixture,unittest.TestCase):
    def ordinary(self):
        return [row('wanderer',1,0xc805),row('base',100,0)]

    def test_original_placement_consumes_explicit_witnesses_without_files(self):
        before=self.before
        witnesses=self.ordinary();saved=copy.deepcopy(witnesses)
        with patch.object(Path,'read_bytes',side_effect=AssertionError('placement opened a file')):
            result=model.placements(before,witnesses)
        self.assertEqual(result['accepted'],{'wanderer':1095,'base':904})
        self.assertEqual(result['attempts'][0]['seeded_state'],0xb08105)
        self.assertEqual(result['attempts'][0]['result_state'],0x5d6fb4)
        self.assertEqual(witnesses,saved)
        self.assertEqual(before,self.before)

    def test_two_rejections_reseed_each_time_and_preserve_old_low_byte(self):
        before=self.changed((51+1095,93,2),(51+1792,93,2))
        witnesses=[row('wanderer',1,0xc805),row('wanderer',2,0x5d6fb4),
                   row('wanderer',3,0x98e9a7),row('base',100,0)]
        result=model.placements(before,witnesses)
        attempts=result['attempts'][:3]
        self.assertEqual([r['candidate']for r in attempts],[1095,1792,1295])
        self.assertEqual([r['seeded_state']for r in attempts],[0xb08105,0xb081b4,0xb081a7])
        self.assertEqual([r['result_state']for r in attempts],[0x5d6fb4,0x98e9a7,0x6e75ce])
        self.assertEqual([r['rejected']for r in attempts],[True,True,False])
        continuous=(214013*0x5d6fb4+1744579)&0xffffff
        self.assertNotEqual(attempts[1]['result_state'],continuous)
        self.assertEqual(result['accepted'],{'wanderer':1295,'base':904})

    def test_three_rejections_are_not_a_fixed_two_attempt_sampler(self):
        before=self.changed((51+1095,93,2),(51+1792,93,2),(51+1295,93,2))
        witnesses=[row('wanderer',1,0xc805),row('wanderer',2,0x5d6fb4),
                   row('wanderer',3,0x98e9a7),row('wanderer',4,0x6e75ce),row('base',100,0)]
        result=model.placements(before,witnesses)
        self.assertEqual([r['candidate']for r in result['attempts'][:4]],[1095,1792,1295,2787])
        self.assertEqual(result['accepted']['wanderer'],2787)

    def test_positive_fraction_rejects_without_requiring_an_active_planet(self):
        before=self.changed((51+1095,93,.25))
        result=model.placements(before,[row('wanderer',1,0xc805),row('wanderer',2,0x5d6fb4),row('base',100,0)])
        self.assertEqual(mbf.get(before,4053,85),0)
        self.assertEqual(result['attempts'][0]['link'],.25)
        self.assertIs(result['attempts'][0]['rejected'],True)
        self.assertEqual(result['accepted']['wanderer'],1792)

    def test_negative_and_noncanonical_zero_links_accept(self):
        for value in(-1,bytes.fromhex('00004800')):
            with self.subTest(value=value):
                result=model.placements(self.changed((51+1095,93,value)),self.ordinary())
                self.assertEqual(result['accepted']['wanderer'],1095)
                self.assertIs(result['attempts'][0]['rejected'],False)

    def test_restored_wanderer_blocks_base_even_when_initial_link_was_zero(self):
        self.assertEqual(mbf.get(self.before,51+1095,93),0)
        result=model.placements(self.before,[row('wanderer',1,0xc805),row('base',100,0xc805),row('base',101,0x5d6fb4)])
        self.assertEqual(result['attempts'][1]['candidate'],1095)
        self.assertEqual(result['attempts'][1]['link'],1)
        self.assertIs(result['attempts'][1]['rejected'],True)
        self.assertEqual(result['accepted']['base'],1792)

    def test_restored_xannoron_hq_blocks_base_after_wanderer_phase(self):
        self.assertEqual(mbf.get(self.before,1,117),849)
        self.assertEqual(mbf.get(self.before,51+849,93),0)
        result=model.placements(self.before,[row('wanderer',1,0xc805),
            row('base',100,236,bytes.fromhex('8fc2757c')),row('base',101,0x485dff,bytes.fromhex('8fc2757c'))])
        self.assertEqual(result['attempts'][1]['candidate'],849)
        self.assertEqual(result['attempts'][1]['link'],100)
        self.assertTrue(result['attempts'][1]['rejected'])
        self.assertEqual(result['accepted']['base'],1576)

    def test_base_old_state_is_explicit_input_not_invented_cross_phase_replay(self):
        witnesses=self.ordinary()
        self.assertNotEqual(witnesses[1]['old_state'],0x5d6fb4)
        result=model.placements(self.before,witnesses)
        self.assertEqual(result['accepted']['base'],904)

    def test_ordinal_type_order_and_uniqueness_fail_closed(self):
        for ordinal in(0,-1,True,1,0.5,'2'):
            witnesses=self.ordinary();witnesses[1]['ordinal']=ordinal
            with self.subTest(ordinal=ordinal):
                with self.assertRaises(ValueError):model.placements(self.before,witnesses)

    def test_extra_or_malformed_witnesses_fail_closed(self):
        for witnesses in([],self.ordinary()[:1],self.ordinary()+[row('base',101,0)],
                          [row('base',1,0),row('wanderer',2,0xc805)],
                          [dict(self.ordinary()[0],extra=0),self.ordinary()[1]],
                          [dict(self.ordinary()[0],role='planet'),self.ordinary()[1]]):
            with self.subTest(witnesses=witnesses):
                with self.assertRaises(ValueError):model.placements(self.before,witnesses)

    def test_missing_acceptance_and_stale_retry_state_fail_closed(self):
        before=self.changed((51+1095,93,2))
        for witnesses in([row('wanderer',1,0xc805),row('base',100,0)],
                          [row('wanderer',1,0xc805),row('wanderer',2,0x5d6fb5),row('base',100,0)],
                          [row('wanderer',1,0xc805),row('wanderer',2,0x5d6eb4),row('base',100,0)]):
            with self.subTest(witnesses=witnesses):
                with self.assertRaises(ValueError):model.placements(before,witnesses)

    def test_inventory_bound_rejects_unconsumed_or_excessive_witnesses(self):
        with self.assertRaises(ValueError):model.placements(self.before,[row('wanderer',i+1,0xc805)for i in range(65)])

    def test_placement_geometry_rejects_before_any_rng(self):
        for offset,value in ((53,50),(57,3050),(61,4050),(93,4150)):
            with self.subTest(offset=offset):
                before=self.changed((1,offset,value))
                with patch.object(model,'QB3',side_effect=AssertionError('wrong geometry drew RNG')):
                    with self.assertRaisesRegex(ValueError,'geometry'):
                        model.placements(before,self.ordinary())

    def test_initial_special_planet_links_reject_before_any_rng(self):
        for slot in (1,99,100):
            with self.subTest(slot=slot):
                before=self.changed((51+1095,93,slot))
                with patch.object(model,'QB3',side_effect=AssertionError('unsupported fixture drew RNG')):
                    with self.assertRaisesRegex(ValueError,'preexisting special-planet'):
                        model.placements(before,self.ordinary())

    def test_raw_timer_and_state_types_fail_closed(self):
        for changes in({'timer':bytes(3)},{'timer':bytearray(TIMER)},{'timer':None},
                        {'old_state':-1},{'old_state':2**24},{'old_state':True},{'old_state':1.0}):
            witnesses=self.ordinary();witnesses[0].update(changes)
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):model.placements(self.before,witnesses)

    def test_initial_fixture_bounds_fail_closed(self):
        for before in(self.before[:-1],bytearray(self.before),self.changed((1,117,7)),
                       self.changed((1,117,3001)),self.changed((1,117,8.5)),
                       self.changed((51+1095,93,-2)),self.changed((51+1095,93,101)),
                       self.changed((4053,85,1))):
            with self.subTest(length=len(before)):
                with self.assertRaises(ValueError):model.placements(before,self.ordinary())


class ComparisonInventoryProperties(unittest.TestCase):
    def test_empty_declared_recipe_cannot_report_zero_comparison_success(self):
        with tempfile.TemporaryDirectory()as temporary:
            root=Path(temporary)
            (root/'recipe.json').write_text(json.dumps({'recipe':'maintenance-placement-cache-v1','cases':{}}))
            with self.assertRaisesRegex(ValueError,'nonempty declared recipe'):
                model.compare(root)

    def test_partial_mode_inventory_rejects_before_reading_targets(self):
        with tempfile.TemporaryDirectory()as temporary:
            root=Path(temporary)
            (root/'recipe.json').write_text(json.dumps({'recipe':'maintenance-placement-cache-v1','cases':{'fixture':[]}}))
            (root/'fixture/unobserved-a').mkdir(parents=True)
            with patch.object(Path,'read_bytes',side_effect=AssertionError('partial corpus read a target')):
                with self.assertRaisesRegex(ValueError,'complete six-mode plus cache-probe'):
                    model.compare(root)


class ObservationProperties(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=ROOT/'research/yt-maint/clock-matrix-controls/noon/observed-a/host-time.json.gz'
        cls.raw=json.loads(gzip.decompress(source.read_bytes()))
        cls.raw['recipe']='host-dos-placement-cache-observer-v1'
        # The extra values are synthetic unit inputs; original raw guest clock
        # frames remain unchanged and continue through the existing parser.
        for event in cls.raw['events']:
            for side in('before','after'):event[side]['rng_raw']='05c80000'

    def observation(self):return copy.deepcopy(self.raw)
    def helper(self,raw):
        return next(e for e in raw['events']if e['before']['nested_application_call']and e['before']['nested_application_call'].startswith('9af378'))

    def test_source_frames_are_reused_without_mutating_input(self):
        raw=self.observation();saved=copy.deepcopy(raw)
        result=model.observations(raw)
        self.assertEqual([r['role']for r in result],['wanderer','base'])
        self.assertTrue(all(r['old_state']==0xc805 for r in result))
        self.assertTrue(all(type(r['timer'])is bytes and len(r['timer'])==4 for r in result))
        self.assertLess(result[0]['ordinal'],result[1]['ordinal'])
        self.assertEqual(raw,saved)

    def test_wrong_recipe_fails_closed(self):
        raw=self.observation();raw['recipe']='host-dos-clock-matrix-observer-v1'
        with self.assertRaises(ValueError):model.observations(raw)

    def test_changed_rng_across_dos_callback_fails_closed(self):
        raw=self.observation();self.helper(raw)['after']['rng_raw']='06c80000'
        with self.assertRaises(ValueError):model.observations(raw)

    def test_malformed_rng_types_width_and_24bit_bound_fail_closed(self):
        for value in('05c8','00000001','zzzzzzzz',True,None):
            raw=self.observation();event=self.helper(raw)
            for side in('before','after'):event[side]['rng_raw']=value
            with self.subTest(value=value):
                with self.assertRaises((ValueError,TypeError)):model.observations(raw)

    def test_missing_rng_or_fabricated_source_address_fails_closed(self):
        raw=self.observation();self.helper(raw)['before'].pop('rng_raw')
        with self.assertRaises(KeyError):model.observations(raw)
        raw=self.observation();event=self.helper(raw)
        for side in('before','after'):event[side]['rng_address']=0x235
        with self.assertRaises(AssertionError):model.observations(raw)

    def test_wrong_real_mode_rng_segment_context_fails_closed(self):
        raw=self.observation();event=self.helper(raw)
        for side in('before','after'):event[side]['ds_phys']+=16
        with self.assertRaises(AssertionError):model.observations(raw)

    def test_wrong_original_helper_call_source_fails_closed(self):
        raw=self.observation();event=self.helper(raw)
        for side in('before','after'):event[side]['nested_application_call']='0'*len(event[side]['nested_application_call'])
        with self.assertRaises(AssertionError):model.observations(raw)

    def test_dropped_events_and_ordinals_fail_closed(self):
        for mutate in(lambda r:r.update(dropped=1),lambda r:self.helper(r).update(ordinal=0)):
            raw=self.observation();mutate(raw)
            with self.assertRaises(AssertionError):model.observations(raw)


if __name__=='__main__':unittest.main()
