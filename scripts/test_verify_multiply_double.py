"""Reject lost precision/residue, wrong product rounding and forged provenance."""
import json,shutil,tempfile,unittest
from pathlib import Path
import verify_multiply_double as a
import recover_multiply_double as writer

class DoubleMultiplication(unittest.TestCase):
    def trace(self,n):return (a.DEFAULT/n/'TRACE.BIN').read_bytes()
    def reject(self,n,raw,c=None):
        with self.assertRaises(AssertionError):a.verify_trace(bytes(raw),a.CASES[n] if c is None else c)
    def output(self,n,value):
        raw=bytearray(self.trace(n));raw[33:41]=bytes.fromhex(value);return raw
    def test_complete_native_coverage(self):
        d=a.verify();self.assertEqual(len(d['cases']),118);self.assertEqual(sum(c['output']is None for c in d['cases']),7)
        self.assertEqual({op:sum(c['op']==op for c in d['cases']) for op in (0x90,0x92,0x94)},{0x90:34,0x92:66,0x94:18})
    def test_independent_payload_and_closed_recipe(self):
        self.assertEqual(writer.cases(),a.CASES)
        for c in a.CASES.values():self.assertEqual(writer.payload(c),a.expected_payload(c))
    def test_every_native_trace_byte(self):
        for n in a.CASES:
            raw=self.trace(n)
            for i in range(len(raw)):
                bad=bytearray(raw);bad[i]^=1;self.reject(n,bad)
    def test_all_seven_prior_fac_residue_bytes(self):
        for n in ('op90-aliases','op90-flush-before-round','op94-min-half','fac1-right-zero','fac3-flush-before-round'):
            c=a.CASES[n];raw=self.trace(n);self.assertEqual(raw[33:41].hex(),c['fac'][:14]+'00')
            for i in range(7):
                bad=bytearray(raw);bad[33+i]^=1;self.reject(n,bad)
    def test_zero_is_not_operand_selection(self):
        n='op90-aliases';c=a.CASES[n]
        for wrong in (c['left'],c['right'],'0000000000000000'):self.reject(n,self.output(n,wrong))
    def test_pre_round_flush_is_not_minimum_binade_carry(self):
        n='op92-flush-before-round';c=a.CASES[n];left,right=(bytes.fromhex(c[k]) for k in ('left','right'))
        from fractions import Fraction
        self.assertLess(abs(a.decode(left)*a.decode(right)),Fraction(2)**-128)
        self.assertEqual(self.trace(n)[33:41].hex(),c['fac'][:14]+'00');self.reject(n,self.output(n,'0000000000000001'))
    def test_both_product_widths_and_even_odd_ties(self):
        for width,inc,parity in ((111,1,1),(111,3,0),(112,2,1),(112,6,0)):
            for suffix in ('','-negative'):
                n=f'op92-tie{width}-{inc}'+suffix;c=a.CASES[n]
                m=lambda raw:(int.from_bytes(bytes.fromhex(raw)[:7],'little')&((1<<55)-1))|(1<<55)
                p=m(c['left'])*m(c['right']);shift=width-56;q,r=divmod(p,1<<shift)
                self.assertEqual(p.bit_length(),width);self.assertEqual(r,1<<(shift-1));self.assertEqual(q%2,parity)
                bad=bytearray(self.trace(n));bad[33]^=1;self.reject(n,bad)
    def test_adjacent_sticky_bits_at_both_product_widths(self):
        for width in (111,112):
            for delta in (-1,1):
                for suffix in ('','-negative'):
                    n=f'op92-sticky{width}-{delta}'+suffix;c=a.CASES[n]
                    m=lambda raw:(int.from_bytes(bytes.fromhex(raw)[:7],'little')&((1<<55)-1))|(1<<55)
                    p=m(c['left'])*m(c['right']);shift=width-56
                    self.assertEqual(p.bit_length(),width);self.assertEqual(p% (1<<shift),(1<<(shift-1))+delta)
                    bad=bytearray(self.trace(n));bad[33]^=1;self.reject(n,bad)
    def test_precision_beyond_float64(self):
        n='op92-tie111-1';self.assertEqual(self.trace(n)[33:41].hex(),'0200000000004081')
        self.reject(n,self.output(n,'0000000000004081'))
    def test_word_boundary_partial_products(self):
        for k in (0,1,7,8,15,16,23,24,31,32,39,40,47,48,54):
            n=f'op92-partial-word-bit{k}';bad=bytearray(self.trace(n));bad[33]^=1;self.reject(n,bad)
    def test_original_fac_binding(self):
        for op in (0x92,0x94):
            n=f'op{op:02x}-raw-align';c=dict(a.CASES[n],fac='123456789abcde00');bad=bytearray(self.trace(n));bad[8:16]=bytes.fromhex(c['fac']);self.reject(n,bad,c)
    def test_readonly_memory_and_rng_mode(self):
        n='op90-raw-align';raw=self.trace(n)
        for at in range(41,62):
            bad=bytearray(raw);bad[at]^=1;self.reject(n,bad)
    def test_exact_error_continuation_without_post_state(self):
        for n in ('op90-round-overflow','op92-max-two','op94-round-overflow'):
            c=a.CASES[n];raw=self.trace(n);at=a.error_address(c);self.assertEqual(at,'0117' if c['op']==0x94 else '011A')
            for bad in (raw.replace(at.encode(),b'0000'),raw[:-1],raw.replace(b'\r\n',b'\n'),raw[:33]+bytes(29)+b'END!'):self.reject(n,bad)
    def test_source_dispatch_and_complete_helper(self):
        original=(a.ROOT/'archive/dos-original/BRUN30.EXE').read_bytes();a.verify_static(original)
        for at in (0x58d+2*0x90,0xb13b,0xb167,0xb28c,0xb3cd):
            bad=bytearray(original);bad[at]^=1
            with self.assertRaises(AssertionError):a.verify_static(bad)
    def test_original_caller_inventory(self):
        direct,inline=a.verify_inventory();self.assertEqual(len(direct),5);self.assertTrue(all(c['op']==0x92 for c in direct));self.assertEqual(inline,[])
    def test_fixed_manifest_and_frozen_source(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'native';shutil.copytree(a.DEFAULT,p);next((p/'sources').iterdir()).write_bytes(b'changed')
            with self.assertRaises(AssertionError):a.verify(directory=p)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'native';shutil.copytree(a.DEFAULT,p);(p/'pins.json').write_text('{}')
            with self.assertRaises(AssertionError):a.verify(directory=p)
    def test_fixture_cannot_invent_error_fac(self):
        with tempfile.TemporaryDirectory() as d:
            doc=json.loads(a.FIXTURE.read_text());next(c for c in doc['cases'] if c['output']is None)['output']='0000000000000000';p=Path(d)/'fixture';p.write_text(json.dumps(doc))
            with self.assertRaises(AssertionError):a.verify(fixture=p)
    def test_other_operations_are_not_admitted(self):
        n='op92-one';c=a.CASES[n];raw=self.trace(n)
        for op in (0x80,0x91,0x96,0x98,0xff):
            self.reject(n,raw,dict(c,op=op))
            with self.assertRaises(AssertionError):a.expected_payload(dict(c,op=op))
            with self.assertRaises(AssertionError):writer.payload(dict(c,op=op))

if __name__=='__main__':unittest.main()
