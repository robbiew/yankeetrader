"""Fatal scan atomicity, qualified contexts and historical API boundaries."""
import unittest
from unittest.mock import patch
from replay_qb_graph import mbf
import replay_maintenance_defender_stock_mercenary as model
from replay_maintenance_defender_stock_rules import admit_world
import replay_maintenance_stock_mercenary as historical

def world(force=1,defense=37,stock=37,day=308):
 w=bytearray(4151*137);w[4053*137:4053*137+41]=b'Gateway Cache'.ljust(41,b' ')
 for r,o,n in((1,81,day),(2419,81,force),(2419,85,-2 if force else 0),(3051,81,defense),(3051,85,-1),(3051,93,3),(4054,85,13),(4054,129,stock)):
  mbf.put(w,r,o,n)
 if day==309:w[2418*137+81:2418*137+89]=bytes.fromhex('0000280000002800')
 return w
class DefenderScan(unittest.TestCase):
 def test_four_declared_first_day_contexts(self):
  for force,defense,stock in((1,37,37),(1,37,0),(37,1000,37),(37,37,37)):admit_world(world(force,defense,stock))
 def test_unmeasured_joint_context_is_rejected(self):
  for force,defense,stock,day in((1,1000,0,308),(0,1,0,309),(2,37,37,308),(0,0,37,309)):
   with self.assertRaises(ValueError):admit_world(world(force,defense,stock,day))
 def test_raw_before_aliases_are_rejected(self):
  for r,o,raw in((4054,73,'aabbcc00'),(4054,129,'00008000')):
   w=world(stock=0);w[(r-1)*137+o:(r-1)*137+o+4]=bytes.fromhex(raw)
   with self.assertRaises(ValueError):admit_world(w)
  w=world(0,37,37,309);w[2418*137+81:2418*137+89]=bytes(8)
  with self.assertRaises(ValueError):admit_world(w)
 def test_scan_failure_preserves_original_world(self):
  w=world();saved=bytes(w)
  def fail(copy,stream):mbf.put(copy,3051,81,0);raise ValueError('unmeasured route')
  with patch.object(model,'scan',side_effect=fail),self.assertRaises(ValueError):model.maintain(w,object())
  self.assertEqual(w,saved)
 def test_nonfatal_scan_result_is_not_admitted_or_committed(self):
  w=world();saved=bytes(w)
  with patch.object(model,'scan',return_value=dict(events=[dict(kind='mercenary-attack',force=1,defenders=0)],activations=[])),self.assertRaises(ValueError):model.maintain(w,object())
  self.assertEqual(w,saved)
 def test_historical_stock_entry_rejects_new_defensive_context(self):
  w=world();saved=bytes(w)
  with self.assertRaises(ValueError):historical.maintain(w,object())
  self.assertEqual(w,saved)
if __name__=='__main__':unittest.main()
