"""Atomic composition admission; historical public pickup stays strict."""
from fractions import Fraction
import unittest
from unittest.mock import patch
from replay_qb_graph import mbf
import replay_maintenance_departed_stock_mercenary as model
from replay_maintenance_departed_stock_rules import CASES
import replay_maintenance_stock_mercenary as old


def world(friendly,governor,stock):
    data=bytearray(4151*137);at=4053*137;data[at:at+41]=b'Gateway Cache'.ljust(41,b' ')
    for rec,off,value in((3051,81,friendly),(3051,85,-2),(3051,93,3),(4054,85,13),(4054,73,governor),(4054,129,float(stock)),(4054,77,505000)):
        mbf.put(data,rec,off,value)
    return data


class FriendlyPickup(unittest.TestCase):
    def test_each_exact_joint_profile_adds_once_and_preserves_governor(self):
        for case,(friendly,governor,stock)in CASES.items():
            with self.subTest(case=case):
                data=world(friendly,governor,stock);before=bytes(data);event=model.pickup(data,3000,97337)
                amount=stock.numerator//stock.denominator
                self.assertEqual((event['initial_force'],event['force'],event['pickup'],event['merged'],event['captured']),
                                 (97337+friendly,97337+friendly+amount,amount,friendly,False))
                self.assertEqual(data[4053*137:4053*137+129],before[4053*137:4053*137+129])
                self.assertEqual(data[4053*137+129:4053*137+133],bytes.fromhex('00008000'))
                self.assertEqual(mbf.get(data,4054,73),governor)

    def test_departed_force_is_excluded_from_actor_and_capture_is_emitted(self):
        for governor in (0,-2):
            for stock in (Fraction(0),Fraction(1,2),Fraction(37)):
                if governor==-2 and stock!=37:continue
                data=world(0,governor,stock);mbf.put(data,3051,85,0)
                event=model.pickup(data,3000,97337)
                self.assertTrue(event['captured']);self.assertEqual(event['initial_force'],97337)
                self.assertEqual(event['force'],97337+int(stock));self.assertEqual(event['merged'],0)

    def test_unknown_joint_stock_garrison_governor_or_hazard_rejects_before_writes(self):
        for rec,offset,value in((3051,81,38),(3051,85,-1),(3051,93,2),(3051,129,1),
                                (4054,73,-1),(4054,129,-1),(4054,129,1),(4054,117,1),(4054,85,12)):
            data=world(37,0,Fraction(1,2));mbf.put(data,rec,offset,value);before=bytes(data)
            with self.subTest(rec=rec,offset=offset),self.assertRaises(ValueError):model.pickup(data,3000,97337)
            self.assertEqual(bytes(data),before)

    def test_wrong_incoming_force_or_sector_is_rejected_before_writes(self):
        for sector,force in((2999,97337),(True,97337),(3000,True),(3000,97338),(3000,0)):
            data=world(37,0,Fraction(37));before=bytes(data)
            with self.assertRaises(ValueError):model.pickup(data,sector,force)
            self.assertEqual(bytes(data),before)

    def test_unmeasured_noncanonical_zero_input_is_rejected(self):
        data=world(37,0,Fraction(0));data[4053*137+129:4053*137+133]=bytes.fromhex('00004800');before=bytes(data)
        with self.assertRaises(ValueError):model.pickup(data,3000,97337)
        self.assertEqual(bytes(data),before)

    def test_capacity_guard_precedes_stock_clear(self):
        data=world(37,0,Fraction(37));before=bytes(data)
        with patch.object(old,'MAX_FORCE',97000),self.assertRaises(ValueError):model.pickup(data,3000,97337)
        self.assertEqual(bytes(data),before)

    def test_historical_stock_public_pickup_rejects_new_composition(self):
        for friendly,governor,stock in CASES.values():
            data=world(friendly,governor,stock);before=bytes(data)
            with self.assertRaises(ValueError):old.pickup(data,3000,97337)
            self.assertEqual(bytes(data),before)

    def test_scan_failure_does_not_commit_partial_world(self):
        data=world(37,0,Fraction(37));mbf.put(data,2419,81,97337);mbf.put(data,2419,85,-2);before=bytes(data)
        def fail(work,stream,**kwargs):
            mbf.put(work,3051,81,0)
            raise ValueError('unmeasured route')
        with patch.object(old,'_maintain',side_effect=fail),self.assertRaises(ValueError):model.maintain(data,object())
        self.assertEqual(bytes(data),before)


if __name__=='__main__':unittest.main()
