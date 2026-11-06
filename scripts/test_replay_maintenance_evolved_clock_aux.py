"""Casualty-backed news, scores and inherited side-file publication."""
import copy
import datetime
import unittest
from unittest.mock import patch
from pathlib import Path
import replay_maintenance_evolved_clock_aux as aux
import replay_maintenance_evolved_aux as old
from test_replay_maintenance_evolved_aux import evolved_worlds,put

DATE=datetime.date(2027,1,2)

class ClockAuxiliaryTests(unittest.TestCase):
    def setUp(self):
        self.before,self.world=evolved_worlds()

    def invoke(self,before=None,world=None,events=(),**kw):
        return aux.synthesize(self.before if before is None else before,self.world if world is None else world,
                              DATE,'00:00:00',DATE,'00:00:01',events=events,**kw)

    def loss(self,count):
        data=bytearray(self.world)
        # Fixture force is initially consolidated at the configured HQ.
        from replay_maintenance_aux import field
        for sector in range(1,3001):
            rec=51+sector
            if field(data,rec,81)>=count:
                put(data,rec,81,field(data,rec,81)-count);break
        else:raise AssertionError('no fixture force')
        return bytes(data)

    def mine(self):
        return dict(kind='mine',group=2,sector=980,initial_force=6,force=0,initial_mines=1,mines=0)

    def planet(self,group=2,slot=99,force=23):
        return dict(kind='planet',group=group,sector=2177 if slot==99 else 2787,
                    planet_slot=slot,planet_name='Mercenary Base'if slot==99 else'The Wanderer',
                    initial_force=force,force=0,initial_ground=194650 if slot==99 else 250,ground=194649 if slot==99 else 249)

    def test_mine_receipt_prints_original_force_and_actual_sector_not_uncapped_roll(self):
        out,stats=self.invoke(world=self.loss(6),events=(self.mine(),))
        self.assertIn(b' *** 6 Xannor hit sector mines in sector 980!',out['YTNEWS.DAT'])
        self.assertIn(b' *** The Xannor were killed!',out['YTNEWS.DAT'])
        self.assertIn(b'999,400',out['YTSCORE.ASC']);self.assertEqual(stats['physical_force'],9994)

    def test_actual_base_title_and_ground_casualties_publish_in_source_order(self):
        events=tuple(self.planet(group=g,force=f)for g,f in zip((2,3,4,5),(23,216,53,70)))
        out,stats=self.invoke(world=self.loss(362),events=events)
        news=out['YTNEWS.DAT']
        self.assertEqual(news.count(b'Xannor attacked the planet "Mercenary Base"'),4)
        self.assertEqual(news.count(b' *** Xannor fighters destroyed!'),4)
        self.assertEqual(stats['scores'],{-1:963800,-2:0})
        self.assertLess(news.index(b'Xannor report:'),news.index(b'Xannor attacked'))
        self.assertLess(news.rindex(b'Xannor fighters destroyed!'),news.index(b'Mercenary Report:'))

    def test_wanderer_title_has_no_extra_capture_or_creation_receipt(self):
        out,_=self.invoke(world=self.loss(100),events=(self.planet(slot=1,force=100),))
        self.assertIn(b'100 Xannor attacked the planet "The Wanderer"',out['YTNEWS.DAT'])
        self.assertNotIn(b'P.H.O.E.N.I.X.',out['YTNEWS.DAT'])

    def test_previous_losses_are_not_replenished_or_counted_twice(self):
        world=self.loss(1700);before=dict(self.before,**{'YTDATA.DAT':world})
        out,stats=self.invoke(before=before,world=world)
        self.assertEqual(stats['scores'],{-1:830000,-2:0})
        self.assertNotIn(b'Xannor fighters destroyed!',out['YTNEWS.DAT'])

    def test_unbacked_public_losses_or_hidden_physical_losses_reject(self):
        with self.assertRaises(ValueError):self.invoke(events=(self.mine(),))
        with self.assertRaises(ValueError):self.invoke(world=self.loss(6))

    def test_bad_order_duplicate_groups_unknown_types_survivors_and_titles_reject(self):
        examples=[({'kind':'unknown'},),(dict(self.mine(),force=1),),(self.mine(),self.mine()),
                  (self.planet(group=3),self.planet(group=2)),(dict(self.planet(),planet_name='Invented'),),
                  (dict(self.planet(),ground=0),),(dict(self.mine(),mines=1),)]
        for events in examples:
            with self.subTest(events=events),self.assertRaises(ValueError):self.invoke(events=events)

    def test_names_previous_news_private_bytes_and_independent_clocks(self):
        out,stats=self.invoke()
        self.assertEqual(out['YTYNEWS.DAT'],self.before['YTNEWS.DAT'])
        self.assertEqual(out['YTNAME.DAT'],self.before['YTNAME.DAT']);self.assertEqual(out['YTRMSG.DAT'],b'')
        self.assertIn(b'01-02-2027 00:00:01',out['YTSCORE.ASC'])
        self.assertTrue(out['YTNEWS.DAT'].startswith(b'00:00:00 01-02-2027'))
        with self.assertRaises(ValueError):self.invoke(before=dict(self.before,**{'YTRMSG.DAT':b'private'}))

    def test_existing_home_and_private_side_inventory_cannot_be_suppressed(self):
        data=bytearray(self.world);put(data,4150,73,0)
        with self.assertRaises(ValueError):self.invoke(world=bytes(data))
        with self.assertRaises(ValueError):self.invoke(created=old.CREATED)

    def test_only_original_executable_can_be_read_during_publication(self):
        read=Path.read_bytes;allowed=Path(__file__).resolve().parents[1]/'archive/dos-original/YTMAINT.EXE'
        def guard(path):
            if path!=allowed:raise AssertionError('non-original publication input')
            return read(path)
        with patch.object(Path,'read_bytes',guard):self.invoke()

if __name__=='__main__':unittest.main()
