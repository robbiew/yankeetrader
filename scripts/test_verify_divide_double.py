"""Reject wrong quotient precision/order, lost FAC residue and forged errors."""
import json,shutil,tempfile,unittest
from pathlib import Path
import verify_divide_double as a
import recover_divide_double as writer
import recover_divide_double_underflow as underflow

class DoubleDivision(unittest.TestCase):
    def trace(self,n):return (a.DEFAULT/n/'TRACE.BIN').read_bytes()
    def reject(self,n,raw,c=None):
        with self.assertRaises(AssertionError):a.verify_trace(bytes(raw),a.CASES[n] if c is None else c)
    def test_complete(self):
        d=a.verify();self.assertEqual(len(d['cases']),178)
        self.assertEqual({k:sum(c['error']==k for c in d['cases']) for k in (None,'overflow','division_by_zero')},{None:150,'overflow':12,'division_by_zero':16})
    def test_independent_payloads(self):
        self.assertEqual(writer.cases(),a.CASES)
        for c in a.CASES.values():self.assertEqual(writer.payload(c),a.expected_payload(c))
        self.assertEqual(underflow.cases(),a.UNDERFLOW_CASES)
        for c in a.UNDERFLOW_CASES.values():self.assertEqual(underflow.payload(c),a.expected_payload(c))
    def test_every_native_trace_byte(self):
        for n in a.CASES:
            raw=self.trace(n)
            for i in range(len(raw)):
                bad=bytearray(raw);bad[i]^=1;self.reject(n,bad)
    def test_zero_divisor_priority_including_both_zero_and_aliases(self):
        for op in (0x88,0x8a,0x8c):
            for suffix in ('lift-both-zero','lift-aliases','lift-max-zero'):
                n=f'op{op:02x}-{suffix}';raw=self.trace(n);self.assertIn(b'Division by zero',raw)
                self.reject(n,raw.replace(b'Division by zero',b'Overflow'))
                self.reject(n,raw[:33]+bytes(29)+b'END!')
    def test_all_seven_original_fac_residue_bytes(self):
        for n in ('op88-lift-left-zero','op88-lift-min-two','op8c-lift-min-max','fac1-lift-left-zero','fac3-lift-min-two'):
            c=a.CASES[n];raw=self.trace(n);self.assertEqual(raw[33:41].hex(),c['fac'][:14]+'00')
            for i in range(7):
                bad=bytearray(raw);bad[33+i]^=1;self.reject(n,bad)
    def test_order_is_not_commutative(self):
        for n in ('op8a-lift-one-three','op8a-lift-raw','op8a-lift-raw-reversed'):
            c=a.CASES[n];fac=bytes.fromhex(c['fac']);left,right=bytes.fromhex(c['left']),bytes.fromhex(c['right'])
            wrong=a.expected_entry(right,left,fac);self.assertIsInstance(wrong,bytes)
            bad=bytearray(self.trace(n));bad[33:41]=wrong;self.reject(n,bad)
    def test_guard_brackets_both_normalization_paths_and_parities(self):
        m=lambda s:(int.from_bytes(bytes.fromhex(s)[:7],'little')&((1<<55)-1))|(1<<55)
        for shift in (55,56):
            for side,delta in (('below',-1),('above',1)):
                for parity in (0,1):
                    for suffix in ('','-negative'):
                        n=f'op8a-guard{shift}-{side}-{parity}'+suffix;c=a.CASES[n];num,den=m(c['left']),m(c['right']);q,r=divmod(num<<shift,den)
                        self.assertEqual(num>=den,shift==55);self.assertEqual(q%2,parity);self.assertEqual(2*r-den,delta)
                        bad=bytearray(self.trace(n));bad[33]^=1;self.reject(n,bad)
    def test_no_nonintegral_tie_is_fabricated(self):
        for c in a.CASES.values():
            left,right=bytes.fromhex(c['left']),bytes.fromhex(c['right'])
            if not left[7] or not right[7]:continue
            m=lambda raw:(int.from_bytes(raw[:7],'little')&((1<<55)-1))|(1<<55)
            num,den=m(left),m(right);shift=55 if num>=den else 56;scaled=num<<shift
            self.assertNotEqual(2*(scaled%den),den)
            self.assertLess(scaled>>64,den);self.assertLessEqual(scaled.bit_length(),112)
    def test_precision_beyond_float64(self):
        n='op8a-guard55-above-0';raw=self.trace(n);self.assertEqual(raw[33]&1,1)
        bad=bytearray(raw);bad[33]&=248;self.reject(n,bad)
    def test_quotient_word_boundaries(self):
        for bit in (0,1,7,8,15,16,23,24,31,32,39,40,47,48,54):
            n=f'op8a-quotient-word-bit{bit}';bad=bytearray(self.trace(n));bad[33]^=1;self.reject(n,bad)
    def test_exponent_boundaries_and_preserved_memory(self):
        for delta in (-129,-128,-127,126,127,128):
            for side in ('below','equal','above'):
                n=f'op8a-lift-delta{delta}-{side}';raw=self.trace(n)
                for at in (16,24):
                    bad=bytearray(raw);bad[at]^=1;self.reject(n,bad)
                if len(raw)==66:
                    for at in range(41,62):
                        bad=bytearray(raw);bad[at]^=1;self.reject(n,bad)
    def test_original_fac_binding(self):
        for op in (0x8a,0x8c):
            n=f'op{op:02x}-lift-raw';c=dict(a.CASES[n],fac='123456789abcde00');bad=bytearray(self.trace(n));bad[8:16]=bytes.fromhex(c['fac']);self.reject(n,bad,c)
    def test_exact_both_error_messages_and_continuations(self):
        for n in ('op88-lift-max-half','op8a-lift-right-zero','op8c-lift-max-min'):
            c=a.CASES[n];raw=self.trace(n);at=a.error_address(c);self.assertEqual(at,'0117' if c['op']==0x8c else '011A')
            for bad in (raw.replace(at.encode(),b'0000'),raw[:-1],raw.replace(b'\r\n',b'\n'),raw[:33]+bytes(29)+b'END!'):self.reject(n,bad)
    def test_full_source_zero_precedence_and_correction_helper(self):
        original=(a.ROOT/'archive/dos-original/BRUN30.EXE').read_bytes();a.verify_static(original)
        for at in (0x58d+2*0x8a,0xb189,0xb19f,0xb205,0xb208,0xb28b):
            bad=bytearray(original);bad[at]^=1
            with self.assertRaises(AssertionError):a.verify_static(bad)
    def test_static_caller_inventory(self):
        direct,inline=a.verify_inventory();self.assertEqual(len(direct),9);self.assertTrue(all(c['op']==0x8a for c in direct));self.assertEqual(inline,[])
    def test_fixed_manifest_and_frozen_source(self):
        for change in ('source','manifest'):
            with tempfile.TemporaryDirectory() as d:
                root=Path(d)/'native';shutil.copytree(a.DEFAULT,root)
                p=next((root/'sources').iterdir()) if change=='source' else root/'pins.json';p.write_bytes(b'changed')
                with self.assertRaises(AssertionError):a.verify(directory=root)
    def test_fixture_error_kind_and_post_error_state(self):
        for key,value in (('error','overflow'),('output','0000000000000000')):
            with tempfile.TemporaryDirectory() as d:
                doc=json.loads(a.FIXTURE.read_text());next(c for c in doc['cases'] if c['error']=='division_by_zero')[key]=value;p=Path(d)/'fixture';p.write_text(json.dumps(doc))
                with self.assertRaises(AssertionError):a.verify(fixture=p)
    def test_unqualified_operation_substitutions(self):
        n='op8a-lift-one';c=a.CASES[n];raw=self.trace(n)
        for op in (0x89,0x8e,0x90,0x92,0xff):
            self.reject(n,raw,dict(c,op=op))
            with self.assertRaises(AssertionError):a.expected_payload(dict(c,op=op))
            with self.assertRaises(AssertionError):writer.payload(dict(c,op=op))

    def test_late_underflow_uses_staged_divisor_not_prior_fac(self):
        for n,c in a.UNDERFLOW_CASES.items():
            raw=(a.UNDERFLOW_DEFAULT/n/'TRACE.BIN').read_bytes();a.verify_trace(raw,c)
            if '-late-' in n or n.startswith('late-prior'):
                want=b'\x00'+bytes.fromhex(c['right'])[:6]+b'\x00';self.assertEqual(raw[33:41],want)
                bad=bytearray(raw);bad[33:41]=bytes.fromhex(c['fac'][:14]+'00')
                with self.assertRaises(AssertionError):a.verify_trace(bad,c)
                for i in range(len(raw)):
                    bad=bytearray(raw);bad[i]^=1
                    with self.assertRaises(AssertionError):a.verify_trace(bad,c)
            elif '-early-' in n:self.assertEqual(raw[33:41].hex(),c['fac'][:14]+'00')
            else:self.assertEqual(raw[33:41].hex(),'0000000000000001')
    def test_supplement_remains_a_separate_frozen_corpus(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'native';shutil.copytree(a.UNDERFLOW_DEFAULT,root);next((root/'sources').iterdir()).write_bytes(b'changed')
            with self.assertRaises(AssertionError):a.verify(underflow_directory=root)

if __name__=='__main__':unittest.main()
