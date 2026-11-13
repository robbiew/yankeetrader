"""Reject protocol relabeling, lost flags, wrong resolver context and forged evidence."""
import json,os,shutil,tempfile,unittest
from pathlib import Path
import recover_inline_single_compare as writer
import verify_inline_single_compare as v

class InlineSingleCompare(unittest.TestCase):
 def trace(self,n):return (v.DEFAULT/n/'TRACE.BIN').read_bytes()
 def test_complete_native(self):
  d=v.verify();self.assertEqual(len(d['cases']),296);self.assertEqual(sum(c['kind']=='full'for c in d['cases']),275)
 def test_independent_diagnostics_and_relocations(self):
  import struct
  self.assertEqual(writer.cases(),v.CASES)
  original=(v.ROOT/'archive/dos-original/YT-INIT.EXE').read_bytes();table=struct.unpack_from('<H',original,24)[0]
  for c in v.CASES.values():
   stub=v.expected_payload(c);self.assertEqual(writer.payload(c),stub)
   for i in range(struct.unpack_from('<H',original,6)[0]):
    off,seg=struct.unpack_from('<HH',original,table+4*i);at=16*seg+off
    self.assertTrue(all(not(at<end and at+2>start)for start,end in ((0x3a,0x3f),(0x6d,0x6d+len(stub)))))
 def test_actual_jcc_and_five_flags(self):
  for n,c in v.CASES.items():
   if c['kind']!='full':continue
   raw=self.trace(n)
   for at in range(42,58):
    bad=bytearray(raw);bad[at]^=1
    with self.assertRaises(AssertionError):v.verify_trace(bad,c)
   for bit in (1,4,64,128,1024,2048):
    bad=bytearray(raw);bad[40:42]=(int.from_bytes(raw[40:42],'little')^bit).to_bytes(2,'little')
    with self.assertRaises(AssertionError):v.verify_trace(bad,c)
 def test_every_protocol_input_and_readonly_byte(self):
  for n in ('bm-one-equal-80','bz-positive-negative-82','address-bm-wrap-01'):
   c=v.CASES[n];raw=self.trace(n)
   for at in list(range(30))+list(range(58,len(raw))):
    bad=bytearray(raw);bad[at]^=1
    with self.assertRaises(AssertionError):v.verify_trace(bad,c)
 def test_direction_and_requested_flags(self):
  n='seeded-bm-zeros';c=v.CASES[n];raw=self.trace(n)
  for bit in (1,4,16,64,128,1024,2048):
   bad=bytearray(raw);bad[38:40]=(int.from_bytes(raw[38:40],'little')^bit).to_bytes(2,'little')
   with self.assertRaises(AssertionError):v.verify_trace(bad,c)
 def test_protocols_cannot_be_relabelled(self):
  for n in ('bm-one-equal-80','address-bm-00'):
   c=dict(v.CASES[n]);c['kind']='full'if c['kind']=='address'else'address'
   with self.assertRaises(AssertionError):v.verify_trace(self.trace(n),c)
   for op in (159,161,163,166):
    with self.assertRaises(AssertionError):v.verify_trace(self.trace(n),dict(v.CASES[n],op=op))
 def test_resolver_only_has_no_comparison_claim(self):
  for n,c in v.CASES.items():
   if c['kind']=='address':self.assertEqual(set(v.verify_trace(self.trace(n),c)),{'resolved'})
 def test_wrong_base_poison_is_distinguishable(self):
  for n,c in v.CASES.items():
   if c['kind']=='full':
    wanted=v.direct.flags_for(bytes.fromhex(c['left']),bytes.fromhex(c['fac'])[4:]);wrong=v.direct.flags_for(bytes.fromhex('0123c5fe'),bytes.fromhex(c['fac'])[4:])
    # Some pairs can share flags; operands and selected address remain independently checked.
    if wanted!=wrong:
     bad=bytearray(self.trace(n));bad[40:42]=wrong.to_bytes(2,'little');bad[42:58]=v.direct.branches_for(wrong)
     with self.assertRaises(AssertionError):v.verify_trace(bad,c)
 def test_undefined_af_is_observed_but_not_predicted(self):
  n='bm-zeros-80';raw=bytearray(self.trace(n));raw[40]^=16;v.verify_trace(raw,v.CASES[n])
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'native';shutil.copytree(v.DEFAULT,p,copy_function=os.link);trace=p/n/'TRACE.BIN';trace.unlink();trace.write_bytes(raw)
   with self.assertRaisesRegex(AssertionError,'immutable observed artifact'):v.verify(p,fixture=None)
 def test_fixture_cannot_omit_controls(self):
  d=json.loads(v.FIXTURE.read_text());d['cases'].pop()
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'fixture.json';p.write_text(json.dumps(d))
   with self.assertRaisesRegex(AssertionError,'portable fixture'):v.verify(fixture=p)
 def test_alias_wrap_original_headers_and_safe_span(self):
  for tag in ('bm','bz'):
   for sel in (128,129,130):
    n=f'address-caller-{tag}-{sel:02x}';c=v.CASES[n];self.assertEqual((c['base10'],c['base12']),(0x7e00,0x08c3));v.verify_trace(self.trace(n),c)
   n=f'address-{tag}-wrap-01';self.assertEqual(v.offset(v.CASES[n]),0)
   n=f'{tag}-safe-last-span';self.assertEqual(v.offset(v.CASES[n]),65532);v.verify_trace(self.trace(n),v.CASES[n])
 def test_initial_seed_does_not_replace_result_flags(self):
  for n,c in v.CASES.items():
   if n.startswith('seeded-'):
    base=n[7:]+'-80';a=v.verify_trace(self.trace(n),c);b=v.verify_trace(self.trace(base),v.CASES[base]);self.assertEqual(a,b)

if __name__=='__main__':unittest.main()
