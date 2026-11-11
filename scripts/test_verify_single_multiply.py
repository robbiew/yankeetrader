"""Reject lost FAC residue, premature rounding, missing sticky bits and fake errors."""
import json,shutil,tempfile,unittest
from pathlib import Path
import verify_single_multiply as a
import recover_single_multiply as first
import recover_single_multiply_sticky as sticky

class Multiplication(unittest.TestCase):
    def trace(self,n):
        root=a.DEFAULT if n in a.CASES else a.STICKY_DEFAULT
        return (root/n/'TRACE.BIN').read_bytes()
    def case(self,n):return a.CASES[n] if n in a.CASES else a.STICKY_CASES[n]
    def reject(self,n,raw):
        with self.assertRaises(AssertionError):a.verify_trace(bytes(raw),self.case(n))
    def output(self,n,value):
        raw=bytearray(self.trace(n));raw[21:25]=bytes.fromhex(value);return raw
    def test_complete(self):
        d=a.verify();self.assertEqual(len(d['cases']),115);self.assertEqual(sum(c['output'] is None for c in d['cases']),9)
    def test_independent_sources_and_payloads(self):
        for writer,cases in ((first,a.CASES),(sticky,a.STICKY_CASES)):
            self.assertEqual(writer.cases(),cases)
            for c in cases.values():self.assertEqual(writer.payload(c),a.expected_payload(c))
    def test_zero_retains_fac_not_operand_or_canonical_zero(self):
        n='op8f-aliases';self.assertEqual(self.trace(n)[21:25].hex(),'5aa5d500')
        for bad in ('00000000','12345600','ffffff00'):self.reject(n,self.output(n,bad))
    def test_underflow_precedes_rounding_into_range(self):
        for n in ('op91-flush-before-round','op91-reverse-flush','op91-negative-flush','op8f-flush-before-round','op93-flush-before-round'):
            c=self.case(n);self.assertEqual(self.trace(n)[21:25].hex(),c['fac'][:6]+'00');self.reject(n,self.output(n,'00000001'))
    def test_independent_fac_zero_residues(self):
        for i in range(4):
            for suffix in ('aliases','right-zero','flush-before-round','min-half'):
                n=f'fac{i}-{suffix}';c=self.case(n);self.assertEqual(self.trace(n)[21:25].hex(),c['fac'][:6]+'00')
    def test_both_normalization_widths_have_even_ties(self):
        for n,want in (('op91-tie47-odd','02004081'),('op91-tie47-even','04004081'),('op91-tie48-odd','02001082'),('op91-tie48-even','04001082')):
            self.assertEqual(self.trace(n)[21:25].hex(),want)
            bad=bytearray.fromhex(want);bad[0]^=1;self.reject(n,self.output(n,bad.hex()))
    def test_guard_sticky_remainders_differ_from_false_ties(self):
        for n,want,bad in (('guard47-below-odd','55926481','56926481'),('guard48-below-odd','6f180082','70180082'),('guard48-above-even','c7010082','c6010082')):
            self.assertEqual(self.trace(n)[21:25].hex(),want);self.reject(n,self.output(n,bad))
            self.assertEqual(self.trace(n+'-negative')[21:23],self.trace(n)[21:23])
    def test_fac_operand_constraints(self):
        for op in (0x91,0x93):
            n=f'op{op:02x}-fraction';c=dict(self.case(n),fac='12345600');raw=bytearray(self.trace(n));raw[8:12]=bytes.fromhex(c['fac'])
            with self.assertRaises(AssertionError):a.verify_trace(raw,c)
    def test_every_trace_byte(self):
        for n in list(a.CASES)+list(a.STICKY_CASES):
            raw=self.trace(n)
            for i in range(len(raw)):
                changed=bytearray(raw);changed[i]^=1;self.reject(n,changed)
    def test_error_addresses_and_no_fabricated_success(self):
        for n in ('op91-round-overflow','op8f-round-overflow','op93-round-overflow'):
            raw=self.trace(n);self.reject(n,raw.replace(b'00F3',b'00F4').replace(b'00F6',b'00F7'))
            self.reject(n,raw[:21]+bytes(17)+b'END!');self.reject(n,raw[:-1]);self.reject(n,raw.replace(b'\r\n',b'\n'))
    def test_static_caller_boundaries(self):
        calls,excluded=a.verify_inventory();self.assertEqual({op:sum(c['op']==op for c in calls)for op in (0x8f,0x91,0x93)},{0x8f:2,0x91:58,0x93:0});self.assertEqual(len(excluded),12)
    def test_complete_multiply_tail_mapping(self):
        raw=bytearray((a.ROOT/'archive/dos-original/BRUN30.EXE').read_bytes())
        for at in range(0xb71c,0xb720):
            changed=raw.copy();changed[at]^=1
            with self.assertRaises(AssertionError):a.verify_static(bytes(changed))
    def test_frozen_native_sources(self):
        for root in (a.DEFAULT,a.STICKY_DEFAULT):
            with tempfile.TemporaryDirectory() as d:
                p=Path(d)/'native';shutil.copytree(root,p);next((p/'sources').iterdir()).write_bytes(b'changed')
                with self.assertRaises(AssertionError):a.verify(p if root==a.DEFAULT else a.DEFAULT,sticky_directory=p if root==a.STICKY_DEFAULT else a.STICKY_DEFAULT)
    def test_fixture_cannot_invent_post_error_fac(self):
        with tempfile.TemporaryDirectory() as d:
            doc=json.loads(a.FIXTURE.read_text());row=next(c for c in doc['cases'] if c['output'] is None);row['output']='00000000';p=Path(d)/'fixture';p.write_text(json.dumps(doc))
            with self.assertRaises(AssertionError):a.verify(fixture=p)

if __name__=='__main__':unittest.main()
