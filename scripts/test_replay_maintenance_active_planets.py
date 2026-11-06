"""Independent-record and fail-closed controls for bounded active economy."""
import copy
import gzip
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import replay_maintenance_active_planets as model
from replay_qb_graph import QB3, mbf
import verify_maintenance_occupied as evidence
from verify_maintenance_clock_matrix import model_inputs


def clocks(case, mode='observed-a'):
    path=evidence.DEFAULT/case/mode/'host-time.json.gz'
    raw=json.loads(gzip.decompress(path.read_bytes()))
    for event in raw['events']:
        for side in('before','after'):event[side].pop('rng_raw')
    raw['recipe']='host-dos-clock-matrix-observer-v1'
    source=model_inputs(raw)
    startup=bytearray(source['startup']);startup[2]^=128
    seed=5|((startup[0]^startup[2])<<8)|((startup[1]^startup[3])<<16)
    world=evidence.before_inputs(case)['YTDATA.DAT']
    active=tuple(r for r in range(4052,4152)if mbf.get(world,r,85)!=0)
    rows=tuple((record,306,row['minutes'])for record,row in zip(active,source['planet_timers']))
    assert len(active)==len(source['planet_timers'])
    return world,rows,seed


class ActivePlanetReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before,cls.clocks,cls.seed=clocks('wanderer-occupied')
        cls.double,cls.double_clocks,cls.double_seed=clocks('wanderer-two-occupied')

    def replay(self, world=None, rows=None, seed=None):
        world=bytearray(self.before if world is None else world)
        stream=SimpleNamespace(rng=QB3(self.seed if seed is None else seed))
        stats=model.maintain(world,stream,self.clocks if rows is None else rows)
        return bytes(world),stats,stream

    def invalid(self,world=None,rows=None,pattern=None):
        world=bytearray(self.before if world is None else world)
        prior=bytes(world);stream=SimpleNamespace(rng=QB3(self.seed))
        with self.assertRaisesRegex(ValueError,pattern or'.*'):
            model.maintain(world,stream,self.clocks if rows is None else rows)
        self.assertEqual(bytes(world),prior)
        self.assertEqual(stream.rng.state,self.seed)
        self.assertEqual(stream.rng.draws,0)

    def changed(self,record,offset,value):
        world=bytearray(self.before);mbf.put(world,record,offset,value);return world

    def test_complete_unattacked_active_records_match_all_source_observations(self):
        for case,declared in evidence.CASES.items():
            if not declared['planets']or case=='route-planet-neutral':continue
            expected=gzip.decompress((evidence.DEFAULT/case/'unobserved-a/after-YTDATA.DAT.gz').read_bytes())
            for mode in('observed-a','observed-b','observed-c'):
                with self.subTest(case=case,mode=mode):
                    before,rows,seed=clocks(case,mode)
                    actual,stats,_=self.replay(before,rows,seed)
                    for record,_,_ in rows:
                        at=(record-1)*137
                        self.assertEqual(actual[at:at+137],expected[at:at+137])
                    self.assertEqual(stats['rng_draws'],3*len(rows))

    def test_neutral_record_matches_before_later_ground_combat(self):
        before,rows,seed=clocks('route-planet-neutral')
        actual,_,_=self.replay(before,rows,seed)
        target=gzip.decompress((evidence.DEFAULT/'route-planet-neutral/unobserved-a/after-YTDATA.DAT.gz').read_bytes())
        at=(4053-1)*137
        differing=[o for o in range(137)if actual[at+o]!=target[at+o]]
        self.assertTrue(differing)
        self.assertTrue(all(77<=o<81 for o in differing))
        self.assertEqual(mbf.get(actual,4053,77)-mbf.get(target,4053,77),25)

    def test_economy_only_writes_active_record_extent(self):
        actual,_,_=self.replay();at=(4053-1)*137
        self.assertEqual(actual[:at],self.before[:at]);self.assertEqual(actual[at+137:],self.before[at+137:])

    def test_no_target_or_program_file_is_read_during_synthesis(self):
        world=bytearray(self.before);stream=SimpleNamespace(rng=QB3(self.seed))
        with (patch('builtins.open',side_effect=AssertionError('synthesis opened a file')),
              patch.object(Path,'read_bytes',side_effect=AssertionError('synthesis read bytes'))):
            model.maintain(world,stream,self.clocks)
        self.assertEqual(stream.rng.draws,3)

    def test_derived_initial_rng_continues_across_two_active_records(self):
        _,stats,_=self.replay(self.double,self.double_clocks,self.double_seed)
        self.assertEqual((stats['rng_draws'],stats['initial_rng_state'],stats['final_rng_state']),(6,0xc805,0x48839b))

    def test_single_active_record_consumes_eager_event_draws(self):
        _,stats,stream=self.replay()
        self.assertEqual((stats['rng_draws'],stream.rng.state),(3,0xd61ece))
        self.assertFalse(stats['rows'][0]['event_selected'])

    def test_no_active_records_leave_world_and_rng_unchanged(self):
        before=evidence.before_inputs('route-neutral-37')['YTDATA.DAT']
        actual,stats,stream=self.replay(before,(),self.seed)
        self.assertEqual(actual,before);self.assertEqual(stats['rng_draws'],0);self.assertEqual(stream.rng.state,self.seed)

    def test_raw_zero_timer_residue_is_copied_without_normalization(self):
        rows=((4053,306,bytes.fromhex('00004800')),)
        actual,_,_=self.replay(rows=rows);at=(4053-1)*137+89
        self.assertEqual(actual[at:at+4],rows[0][2]);self.assertEqual(mbf.get(actual,4053,57),1000)

    def test_subminute_fraction_is_not_discarded(self):
        actual,stats,_=self.replay()
        self.assertGreater(stats['rows'][0]['elapsed'],1)
        self.assertEqual(mbf.get(actual,4053,57),1000.0006103515625)
        self.assertEqual(mbf.get(actual,4053,129),3000.001708984375)
        self.assertEqual(mbf.get(actual,4053,69),1.0000005960464478)

    def test_zero_bank_plasma_and_mines_stay_zero(self):
        actual,_,_=self.replay()
        for offset in(113,117,125):self.assertEqual(mbf.get(actual,4053,offset),0)

    def test_name_owner_and_unmapped_tail_remain_source_bytes(self):
        actual,_,_=self.replay();at=(4053-1)*137
        for start,end in((0,41),(73,77),(81,89),(93,113),(121,125),(133,137)):
            self.assertEqual(actual[at+start:at+end],self.before[at+start:at+end])

    def test_changed_last_day_is_not_admitted(self):self.invalid(self.changed(4053,41,304),pattern='prior-day')
    def test_changed_ground_is_not_admitted(self):self.invalid(self.changed(4053,77,500001),pattern='500000')
    def test_changed_rate_is_not_admitted(self):self.invalid(self.changed(4053,45,1001),pattern='1000-rate')
    def test_human_owner_is_not_admitted(self):self.invalid(self.changed(4053,73,2),pattern='prior-day')
    def test_bank_bonus_is_not_silently_ignored(self):self.invalid(self.changed(4053,117,1),pattern='zero-bank')
    def test_nonzero_warehouse_is_not_silently_ignored(self):self.invalid(self.changed(4053,57,1),pattern='zero-stock')
    def test_stored_timer_is_not_silently_ignored(self):self.invalid(self.changed(4053,89,.5),pattern='zero-stock')
    def test_existing_weapon_stock_is_not_silently_ignored(self):self.invalid(self.changed(4053,129,1),pattern='zero-stock')
    def test_nonzero_unmapped_field_is_not_silently_ignored(self):self.invalid(self.changed(4053,133,1),pattern='zero-stock')
    def test_missing_clocks_are_rejected(self):self.invalid(rows=(),pattern='per active')
    def test_extra_clocks_are_rejected(self):self.invalid(rows=self.clocks+self.clocks,pattern='per active')
    def test_mutable_clock_sequence_is_rejected(self):self.invalid(rows=list(self.clocks),pattern='immutable')
    def test_mutable_clock_row_is_rejected(self):self.invalid(rows=(list(self.clocks[0]),),pattern='typed immutable')
    def test_mutable_timer_is_rejected(self):self.invalid(rows=((4053,306,bytearray(self.clocks[0][2])),),pattern='typed immutable')
    def test_short_timer_is_rejected(self):self.invalid(rows=((4053,306,b'\x00'),),pattern='typed immutable')
    def test_wrong_calendar_is_rejected(self):self.invalid(rows=((4053,307,self.clocks[0][2]),),pattern='day306')
    def test_backward_calendar_is_rejected(self):self.invalid(rows=((4053,304,self.clocks[0][2]),),pattern='day306')
    def test_boolean_record_is_rejected(self):self.invalid(rows=((True,306,self.clocks[0][2]),),pattern='typed immutable')
    def test_boolean_day_is_rejected(self):self.invalid(rows=((4053,True,self.clocks[0][2]),),pattern='typed immutable')
    def test_wrong_physical_record_is_rejected(self):self.invalid(rows=((4054,306,self.clocks[0][2]),),pattern='ordered')
    def test_wrong_clock_order_is_rejected(self):self.invalid(self.double,tuple(reversed(self.double_clocks)),pattern='ordered')
    def test_outside_measured_midnight_clock_is_rejected(self):self.invalid(rows=((4053,306,mbf.enc(1)),),pattern='midnight')
    def test_negative_clock_is_rejected(self):self.invalid(rows=((4053,306,mbf.enc(-1)),),pattern='midnight')
    def test_lost_planet_link_is_rejected(self):self.invalid(self.changed(1146,93,0),pattern='one physical')
    def test_duplicate_planet_link_is_rejected(self):self.invalid(self.changed(1147,93,2),pattern='one physical')
    def test_reserved_active_planet_is_not_admitted(self):self.invalid(self.changed(4052,85,1),pattern='ordinary active slots')
    def test_reserved_hq_planet_is_not_admitted(self):self.invalid(self.changed(4151,85,1),pattern='ordinary active slots')
    def test_wrong_world_extent_is_rejected(self):self.invalid(self.before[:-1],pattern='complete mutable')
    def test_wrong_geometry_is_rejected(self):self.invalid(self.changed(1,61,4050),pattern='geometry')

    def test_invalid_ascii_name_is_rejected(self):
        world=bytearray(self.before);world[(4053-1)*137]=0
        self.invalid(world,pattern='ASCII')

    def test_bad_name_padding_is_rejected(self):
        world=bytearray(self.before);world[(4053-1)*137+40]=ord('X')
        self.invalid(world,pattern='ASCII')


if __name__=='__main__':unittest.main()
