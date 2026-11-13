"""Defined sign/zero flags, actual Jcc, entry mapping and immutable observations."""
import json,os,shutil,tempfile,struct,unittest
from pathlib import Path
import verify_sign_zero as v
import recover_sign_zero as writer

class SignZero(unittest.TestCase):
 def trace(self,n):return(v.DEFAULT/n/'TRACE.BIN').read_bytes()
 def test_native_coverage(self):
  d=v.verify();self.assertEqual(len(d['cases']),248)
  self.assertEqual({op:sum(c['op']==op for c in d['cases'])for op in(167,168,169,170)},{167:62,168:62,169:62,170:62})
 def test_independent_payload_and_relocations(self):
  self.assertEqual(writer.cases(),v.CASES);original=(v.ROOT/'archive/dos-original/YT-INIT.EXE').read_bytes();table=struct.unpack_from('<H',original,24)[0]
  for c in v.CASES.values():
   stub=v.expected_payload(c);self.assertEqual(stub,writer.payload(c))
   for i in range(struct.unpack_from('<H',original,6)[0]):
    off,seg=struct.unpack_from('<HH',original,table+4*i);at=16*seg+off
    self.assertTrue(all(not(at<end and at+2>start)for start,end in((0x3a,0x3f),(0x6d,0x6d+len(stub)))))
 def test_actual_flags_and_branches(self):
  for n,c in v.CASES.items():
   raw=self.trace(n)
   for at in range(46,62):
    bad=bytearray(raw);bad[at]^=1
    with self.assertRaises(AssertionError):v.verify_trace(bad,c)
   for bit in(1,4,64,128,1024,2048):
    bad=bytearray(raw);bad[44:46]=(int.from_bytes(raw[44:46],'little')^bit).to_bytes(2,'little')
    with self.assertRaises(AssertionError):v.verify_trace(bad,c)
 def test_inputs_registers_rng_and_frame(self):
  for n in('opa7-e81-m000000','opa8-e01-mc00000','opa9-eff-m123456','opaa-e00-mffffff'):
   raw=self.trace(n);c=v.CASES[n]
   for at in list(range(36))+list(range(46,113)):
    bad=bytearray(raw);bad[at]^=1
    with self.assertRaises(AssertionError):v.verify_trace(bad,c)
 def test_initial_flags(self):
  n='seeded-opa7-e80-mc00000';raw=self.trace(n);c=v.CASES[n]
  for bit in(1,4,16,64,128,1024,2048):
   bad=bytearray(raw);bad[42:44]=(int.from_bytes(raw[42:44],'little')^bit).to_bytes(2,'little')
   with self.assertRaises(AssertionError):v.verify_trace(bad,c)
 def test_undefined_af_is_observed_not_predicted(self):
  n='opa7-e00-mffffff';raw=bytearray(self.trace(n));raw[44]^=16;v.verify_trace(raw,v.CASES[n])
  with tempfile.TemporaryDirectory()as tmp:
   p=Path(tmp)/'native';shutil.copytree(v.DEFAULT,p,copy_function=os.link);trace=p/n/'TRACE.BIN';trace.unlink();trace.write_bytes(raw)
   with self.assertRaisesRegex(AssertionError,'immutable observed artifact'):v.verify(p,fixture=None)
 def test_seed_flags_do_not_replace_result(self):
  for n,c in v.CASES.items():
   if n.startswith('seeded-'):self.assertEqual(v.verify_trace(self.trace(n),c),v.verify_trace(self.trace(n[7:]),v.CASES[n[7:]]))
 def test_same_fac_entry_for_a9_aa(self):
  for n,c in v.CASES.items():
   if n.startswith('opa9-'):
    other='opaa-'+n[5:];self.assertEqual(v.verify_trace(self.trace(n),c),v.verify_trace(self.trace(other),v.CASES[other]))
 def test_reused_comparison_zero_flags(self):
  import verify_single_compare as s;import verify_double_compare as d
  for c in v.CASES.values():
   raw=bytes.fromhex(c['left']if c['op']in(167,168)else c['fac'])
   expected=s.flags_for(raw[:4],bytes(4))if c['op']==167 else d.flags_for(raw,bytes(8))
   self.assertEqual(v.flags_for(c),expected)
 def test_zero_and_rotate_not_sgn(self):
  self.assertEqual(v.flags_for(v.CASES['opa7-e00-mffffff']),0x44)
  f=v.flags_for(v.CASES['opa7-e81-m000000']);self.assertTrue(f&128);self.assertFalse(f&1)
  f=v.flags_for(v.CASES['opa8-e01-mc00000']);self.assertTrue(f&1);self.assertFalse(f&2048)
 def test_unadmitted_entries(self):
  n='opa7-e00-m000000'
  for op in(159,160,165,166,171):
   with self.assertRaises(AssertionError):v.verify_trace(self.trace(n),dict(v.CASES[n],op=op))
 def test_dropped_fixture_rows_rejected(self):
  d=json.loads(v.FIXTURE.read_text());d['cases'].pop()
  with tempfile.TemporaryDirectory()as tmp:
   p=Path(tmp)/'fixture.json';p.write_text(json.dumps(d))
   with self.assertRaisesRegex(AssertionError,'portable fixture'):v.verify(fixture=p)

if __name__=='__main__':unittest.main()
