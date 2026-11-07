"""Measured owner-transfer and linked-mine guards; atomic scan failure."""
import unittest
from unittest.mock import patch
from fractions import Fraction
from replay_qb_graph import mbf
import replay_maintenance_neutral_owner_stock_mercenary as model
import replay_maintenance_stock_mercenary as old


def world(local=37,owner=0,stock=37,mines=0):
    w=bytearray(4151*137);w[4053*137:4053*137+41]=b'Gateway Cache'.ljust(41,b' ')
    for r,o,n in ((3051,81,local),(3051,85,owner),(3051,93,3),(3051,129,mines),(4054,85,13),(4054,129,stock),(4054,77,500000),(2419,81,97337),(2419,85,-2)):
        mbf.put(w,r,o,n)
    return w

class MineStream:
    def __init__(self):self.rng=self;self.state=12;self.draws=0;self.calls=[];self.bounds=[]
    def reseed(self,tag,caller):self.calls.append((tag,caller))
    def integer(self,bound):
        self.bounds.append(bound);self.draws+=1;return 20 if self.draws==1 else 5

class OwnerMineTests(unittest.TestCase):
    def test_neutral_transfer_is_distinct_from_friendly_merge(self):
        for owner in (0,-2):
            w=world(owner=owner);e=model.pickup(w,3000,97337)
            self.assertEqual(e['initial_force'],97374);self.assertEqual(e['force'],97411)
            self.assertEqual(e['neutral_transferred'],37 if owner==0 else 0)
            self.assertEqual(e['merged'],37 if owner==-2 else 0)
            self.assertFalse(e['captured'])

    def test_positive_neutral_one_empty_and_half_stock(self):
        for local,stock in ((1,0),(37,.5)):
            w=world(local=local,stock=stock);e=model.pickup(w,3000,97337)
            self.assertEqual(e['pickup'],0);self.assertEqual(e['force'],97337+local)
            self.assertEqual(w[4053*137+129:4053*137+133],bytes.fromhex('00008000'))

    def test_post_mine_incoming_count_precedes_local_and_stock(self):
        w=world();e=model.pickup(w,3000,96956)
        self.assertEqual((e['incoming_force'],e['initial_force'],e['force']),(96956,96993,97030))

    def test_departed_local_is_excluded_and_capture_uses_survivors(self):
        e=model.pickup(world(local=0),3000,92963)
        self.assertTrue(e['captured']);self.assertEqual((e['initial_force'],e['force'],e['neutral_transferred']),(92963,93000,0))

    def test_linked_mine_has_one_count_two_helper_and_debits_incoming_only(self):
        for owner in (0,-2):
            w=world(owner=owner,mines=1);stream=MineStream();e=model.mine_hit(w,stream,3000,97337)
            self.assertEqual(stream.calls,[('h2',0x4aa4)]);self.assertEqual(stream.bounds,[10000,20])
            self.assertEqual((e['losses'],e['force'],e['rng_draws']),(5,97332,2))
            self.assertEqual((mbf.get(w,3051,81),mbf.get(w,4054,129),mbf.get(w,3051,129)),(37,37,0))

    def test_unknown_link_mines_force_owner_or_stock_rejects_before_writes(self):
        for r,o,n in ((3051,93,0),(3051,129,2),(3051,85,-1),(4054,129,.5),(3051,81,38)):
            w=world(mines=1);mbf.put(w,r,o,n);before=bytes(w)
            with self.assertRaises(ValueError):model.mine_hit(w,MineStream(),3000,97337)
            self.assertEqual(w,before)
        for sector,force in ((2999,97337),(3000,1),(3000,True)):
            w=world(mines=1);before=bytes(w)
            with self.assertRaises(ValueError):model.mine_hit(w,MineStream(),sector,force)
            self.assertEqual(w,before)

    def test_unknown_pickup_joint_context_rejects_before_writes(self):
        for local,owner,stock in ((1,-2,0),(37,0,1),(38,0,37),(0,0,.5)):
            w=world(local,owner,stock);before=bytes(w)
            with self.assertRaises(ValueError):model.pickup(w,3000,97337)
            self.assertEqual(w,before)

    def test_historical_public_helpers_keep_strict_guards(self):
        w=world(mines=1);before=bytes(w)
        with self.assertRaises(ValueError):old.mine_hit(w,MineStream(),3000,97337)
        self.assertEqual(w,before)
        for owner in (0,-2):
            w=world(owner=owner);before=bytes(w)
            with self.assertRaises(ValueError):old.pickup(w,3000,97337)
            self.assertEqual(w,before)

    def test_scan_failure_does_not_commit_partial_world(self):
        w=world();before=bytes(w)
        def fail(work,stream,**kwargs):mbf.put(work,3051,81,0);raise ValueError('unknown branch')
        with patch.object(old,'_maintain',side_effect=fail),self.assertRaises(ValueError):model.maintain(w,object())
        self.assertEqual(w,before)

if __name__=='__main__':unittest.main()
