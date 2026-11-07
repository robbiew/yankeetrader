"""Positive SINGLE INT-floor, complete fraction clearing and atomic pickup tests."""
from fractions import Fraction
from pathlib import Path
import math
import unittest
from unittest.mock import patch

import replay_maintenance_stock_mercenary as merc
import replay_maintenance_gateway_mercenary as historical_gateway
import replay_maintenance_departure_mercenary as historical_departure
from replay_qb_graph import mbf
from test_replay_maintenance_gateway_mercenary import FakeStream

VALUES=((1,4),(1,2),(3,4),(3,2),(5,2),(12129823,64),(379057,2),(12129825,64),(379059,2),(16777215,16777216),(8388609,8388608),(65535,2))


def gateway(stock):
    data=bytearray(4151*137)
    for o,v in((53,51),(57,3051),(61,4051),(93,4151)):mbf.put(data,1,o,v)
    for o,v in((81,0),(85,0),(93,3),(129,0)):mbf.put(data,3051,o,v)
    at=(4054-1)*137;data[at:at+41]=b'Gateway Cache'.ljust(41,b' ')
    for o,v in((85,13),(73,0),(77,505000),(129,stock)):mbf.put(data,4054,o,v)
    return data


def routed(stock):
    data=gateway(stock);mbf.put(data,2419,81,97337);mbf.put(data,2419,85,-2)
    mbf.put(data,2419,41,3000);mbf.put(data,3051,41,2500)
    return data


class PositiveSingleFloor(unittest.TestCase):
    def test_all_twelve_exact_measured_positive_values_floor(self):
        for numerator,denominator in VALUES:
            value=float(Fraction(numerator,denominator))
            with self.subTest(value=value):self.assertEqual(merc.positive_single_floor(value),numerator//denominator)

    def test_odd_even_half_ties_do_not_use_nearest_rounding(self):
        for value,wanted in((.5,0),(1.5,1),(2.5,2),(32767.5,32767),(189528.5,189528),(189529.5,189529)):
            self.assertEqual(merc.positive_single_floor(value),wanted)
        self.assertNotEqual(merc.positive_single_floor(1.5),round(1.5))
        self.assertNotEqual(merc.positive_single_floor(32767.5),round(32767.5))

    def test_adjacent_large_fractions_do_not_use_rounding_side(self):
        low,half,high=(189528+float(Fraction(n,64))for n in(31,32,33))
        self.assertEqual([merc.positive_single_floor(n)for n in(low,half,high)],[189528]*3)
        self.assertEqual(round(high),189529)

    def test_single_values_immediately_below_and_above_one(self):
        below=16777215/16777216;above=8388609/8388608
        self.assertEqual((merc.positive_single_floor(below),merc.positive_single_floor(above)),(0,1))
        self.assertNotEqual(mbf.enc(below),mbf.enc(1));self.assertNotEqual(mbf.enc(above),mbf.enc(1))

    def test_zero_negative_nonfinite_bools_and_nonsingle_values_reject(self):
        for value in(0,-.25,-1,True,False,float('inf'),float('-inf'),float('nan'),.1,1e-100,2**-129,189529.515625,400000,10**1000,'0.5',None):
            with self.subTest(value=value),self.assertRaises(ValueError):merc.positive_single_floor(value)


class AtomicStockPickup(unittest.TestCase):
    def test_subunit_stock_still_captures_and_clears_every_fraction(self):
        for value in(.25,.5,.75,16777215/16777216):
            data=gateway(value);before=bytes(data);event=merc.pickup(data,3000,97337)
            self.assertEqual((event['initial_force'],event['force'],event['pickup'],event['captured']),(97337,97337,0,True))
            self.assertEqual(event['fractional_discard'],value)
            at=(4054-1)*137
            self.assertEqual(data[at+129:at+133],bytes.fromhex('00008000'))
            self.assertEqual(data[at:at+129],before[at:at+129]);self.assertEqual(data[at+133:at+137],before[at+133:at+137])

    def test_all_positive_receipts_stamp_original_force_and_derive_saved_sum(self):
        for numerator,denominator in VALUES:
            value=float(Fraction(numerator,denominator));whole=numerator//denominator;data=gateway(value)
            event=merc.pickup(data,3000,97337)
            self.assertEqual(event['conversion'],'bounded-positive-single-INT-floor')
            self.assertEqual((event['raw_stock'],event['pickup'],event['force'],event['fractional_discard']),(value,whole,97337+whole,value-whole))
            self.assertEqual((mbf.get(data,3051,81),mbf.get(data,3051,85)),(97337+whole,-2))
            self.assertEqual((event['sector'],event['planet_slot'],event['planet_name']),(3000,3,'Gateway Cache'))

    def test_title_owner_ground_and_all_other_planet_bytes_are_retained(self):
        data=gateway(189529.5);before=bytes(data);merc.pickup(data,3000,97337);at=(4054-1)*137
        self.assertEqual(data[at:at+129],before[at:at+129]);self.assertEqual(data[at+133:at+137],before[at+133:at+137])
        self.assertEqual(mbf.get(data,4054,73),0);self.assertEqual(mbf.get(data,4054,77),505000)

    def test_capacity_is_checked_before_clear_or_physical_force_writes(self):
        for force,stock in((400000,1.5),(399999,2.5),(400000,189529.5)):
            data=gateway(stock);before=bytes(data)
            with self.subTest(force=force,stock=stock),self.assertRaisesRegex(ValueError,'post-pickup'):merc.pickup(data,3000,force)
            self.assertEqual(bytes(data),before)
        data=gateway(.75);event=merc.pickup(data,3000,400000)
        self.assertEqual(event['force'],400000);self.assertEqual(mbf.get(data,4054,129),0)

    def test_invalid_force_sector_title_or_stock_rejects_without_writes(self):
        for force in(0,-1,True,97337.5,400001):
            data=gateway(.5);before=bytes(data)
            with self.subTest(force=force),self.assertRaises(ValueError):merc.pickup(data,3000,force)
            self.assertEqual(bytes(data),before)
        for sector in(1,2999,True,3000.0):
            data=gateway(.5);before=bytes(data)
            with self.subTest(sector=sector),self.assertRaises(ValueError):merc.pickup(data,sector,97337)
            self.assertEqual(bytes(data),before)
        for rec,off,value in((3051,81,1),(3051,85,-2),(3051,93,1),(3051,129,1),(4054,73,-1),(4054,85,12),(4054,129,0),(4054,129,-.5),(4054,129,189529.515625)):
            data=gateway(.5);mbf.put(data,rec,off,value);before=bytes(data)
            with self.subTest(record=rec,off=off,value=value),self.assertRaises(ValueError):merc.pickup(data,3000,97337)
            self.assertEqual(bytes(data),before)
        data=gateway(.5);data[(4054-1)*137]=ord('X');before=bytes(data)
        with self.assertRaisesRegex(ValueError,'identity'):merc.pickup(data,3000,97337)
        self.assertEqual(bytes(data),before)

    def test_bad_original_literal_identity_rejects_before_stock_clear(self):
        data=gateway(.5);before=bytes(data)
        with patch.object(Path,'read_bytes',return_value=b'changed'),self.assertRaisesRegex(ValueError,'identity'):merc.pickup(data,3000,97337)
        self.assertEqual(bytes(data),before)

    def test_pickup_reads_only_original_binary_and_consumes_no_rng(self):
        read=Path.read_bytes;opened=[]
        def guarded(path):
            if path.name!='YTMAINT.EXE'or 'archive/dos-original'not in str(path):raise AssertionError('captured target opened')
            opened.append(path);return read(path)
        with patch.object(Path,'read_bytes',guarded):merc.pickup(gateway(189528.5),3000,97337)
        self.assertEqual(len(opened),1)


class BoundedTailAndHistoricalGuards(unittest.TestCase):
    def test_before_fix_original_gateway_half_guard_fails_then_new_model_passes(self):
        data=gateway(.5);before=bytes(data)
        with self.assertRaisesRegex(ValueError,'whole gateway stock'):historical_gateway.pickup(data,3000,97337)
        self.assertEqual(bytes(data),before)
        event=merc.pickup(data,3000,97337)
        self.assertEqual((event['pickup'],event['force']),(0,97337))
        self.assertEqual(data[(4054-1)*137+129:(4054-1)*137+133],bytes.fromhex('00008000'))

    def test_historical_departure_fraction_guard_remains_closed(self):
        data=bytearray(4151*137);at=(4052-1)*137;data[at:at+41]=b'The Wanderer'.ljust(41,b' ')
        for o,v in((85,12),(73,0),(129,.5)):mbf.put(data,4052,o,v)
        mbf.put(data,144,93,1);before=bytes(data)
        with self.assertRaisesRegex(ValueError,'stock conversion'):historical_departure.pickup(data,93,97337)
        self.assertEqual(bytes(data),before)

    def test_measured_tail_has_one_pickup_and_no_extra_draws_or_reactivation(self):
        for numerator,denominator in VALUES:
            value=float(Fraction(numerator,denominator));data=routed(value);stream=FakeStream([.1,.9],target=2500)
            row=merc.maintain(data,stream)
            self.assertEqual((row['initial_force'],row['force'],row['pickup']),(97337,97337+numerator//denominator,numerator//denominator))
            self.assertEqual((row['desertion_draws'],row['movement_gate_draws'],row['target_draws']),(1,1,1));self.assertEqual(stream.rng.draws,2)
            self.assertEqual(row['final_sectors'],[3000]);self.assertEqual(len(row['activations']),1)
            self.assertEqual([e['kind']for e in row['events']],['mercenary-pickup'])
            self.assertEqual((row['losses'],row['merged']),(0,0));self.assertEqual(row['activations'][0]['entered'],[3000])

    def test_unmeasured_origin_or_second_group_rejects_without_writes(self):
        for rec,off,value in((2419,81,97336),(2419,85,0),(2419,93,1),(2419,129,1),(151,81,37)):
            data=routed(.5);mbf.put(data,rec,off,value)
            if rec==151:mbf.put(data,151,85,-2)
            before=bytes(data)
            with self.subTest(record=rec,off=off),self.assertRaises(ValueError):merc.maintain(data,FakeStream([]))
            self.assertEqual(bytes(data),before)

    def test_tail_stream_failure_keeps_original_departure_fields_intact(self):
        data=routed(.5);before=bytes(data)
        with self.assertRaises(StopIteration):merc.maintain(data,FakeStream([.1]))
        self.assertEqual(bytes(data),before)


if __name__=='__main__':unittest.main()
