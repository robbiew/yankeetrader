"""Reject precision loss, directional-zero/FAC substitutions and false native errors."""
import json,shutil,tempfile,unittest
from pathlib import Path
import verify_subtract_double as a
import recover_subtract_double as writer

class DoubleSubtraction(unittest.TestCase):
    def trace(self,n):return (a.DEFAULT/n/'TRACE.BIN').read_bytes()
    def reject(self,n,raw):
        with self.assertRaises(AssertionError):a.verify_trace(bytes(raw),a.CASES[n])
    def output(self,n,value):
        raw=bytearray(self.trace(n));raw[33:41]=bytes.fromhex(value);return raw
    def test_complete(self):
        d=a.verify();self.assertEqual(len(d['cases']),148);self.assertEqual(sum(c['output']is None for c in d['cases']),9)
    def test_independent_acquisition_and_payload(self):
        self.assertEqual(writer.cases(),a.CASES)
        for c in a.CASES.values():self.assertEqual(writer.payload(c),a.expected_payload(c))
    def test_every_trace_byte(self):
        for n in a.CASES:
            raw=self.trace(n)
            for i in range(len(raw)):
                bad=bytearray(raw);bad[i]^=1;self.reject(n,bad)
    def test_prior_fac_keeps_all_seven_residue_bytes(self):
        for n in ('op98-cancel','op98-minimum-one-bit','op9c-minimum-one-bit'):
            c=a.CASES[n];self.assertEqual(self.trace(n)[33:41].hex(),c['fac'][:14]+'00')
            bad=bytearray(self.trace(n));bad[33]^=1;self.reject(n,bad)
        for i in range(4):
            for suffix in ('cancel','minimum-one-bit','minimum-cancel'):
                n=f'fac{i}-{suffix}';self.assertEqual(self.trace(n)[33:41].hex(),a.CASES[n]['fac'][:14]+'00')
    def test_zero_alias_selection_is_directional(self):
        n='op98-aliases';self.assertEqual(self.trace(n)[33:41].hex(),(bytes.fromhex(a.CASES[n]['right'])[:6]+bytes([bytes.fromhex(a.CASES[n]['right'])[6]^128])+b'\x00').hex())
        for bad in (a.CASES[n]['left'],a.CASES[n]['fac'],'0000000000000000'):self.reject(n,self.output(n,bad))
    def test_bits_beyond_float64_and_near_half_sticky(self):
        n='op9a-half-odd0-tail1';self.assertEqual(self.trace(n)[33:41].hex(),'0100000000000081');self.reject(n,self.output(n,'0000000000000081'))
    def test_even_ties(self):
        for n,want in (('op9a-half-odd0-tail0','0000000000000081'),('op9a-half-odd1-tail0','0200000000000081')):
            self.assertEqual(self.trace(n)[33:41].hex(),want);bad=bytearray(self.trace(n));bad[33]^=1;self.reject(n,bad)
    def test_gap56_and_gap57_are_distinct(self):
        n='op9a-boundary-opposite-gap56';self.assertEqual(self.trace(n)[33:41].hex(),'feffffffffff7f80')
        n='op9a-boundary-opposite-gap57';self.assertEqual(self.trace(n)[33:41].hex(),'0000000000000081');self.reject(n,self.output(n,'ffffffffffff7f80'))
    def test_word_and_byte_alignment_low_bits(self):
        for gap in (5,6,7,13,14,15,16,17,31,32,33,47,48,49,55,56):
            for sign in ('same','opposite'):
                n=f'op9a-{sign}-gap{gap}';raw=bytearray(self.trace(n));raw[33]^=1;self.reject(n,raw)
    def test_fac_operand_binding(self):
        for op in (0x9a,0x9c):
            n=f'op{op:02x}-raw';c=dict(a.CASES[n],fac='123456789abcde00');raw=bytearray(self.trace(n));raw[8:16]=bytes.fromhex(c['fac'])
            with self.assertRaises(AssertionError):a.verify_trace(raw,c)
    def test_exact_errors_and_continuations(self):
        for n in ('op98-overflow','op9a-overflow-round','op9c-negative-overflow'):
            c=a.CASES[n];raw=self.trace(n);at=a.error_address(c);self.assertEqual(at,'0117' if c['op']==0x9c else '011A')
            self.reject(n,raw.replace(at.encode(),b'0000'));self.reject(n,raw[:-1]);self.reject(n,raw.replace(b'\r\n',b'\n'));self.reject(n,raw[:33]+bytes(29)+b'END!')
    def test_original_caller_inventory(self):
        calls,inline=a.verify_inventory();self.assertEqual({op:sum(c['op']==op for c in calls) for op in (0x98,0x9a,0x9c)},{0x98:12,0x9a:4,0x9c:5});self.assertEqual(len(inline),0)
    def test_complete_kernel_and_dispatch_mapping(self):
        original=(a.ROOT/'archive/dos-original/BRUN30.EXE').read_bytes()
        for at in (0xaf81,0xaf8c,0xaf92,0xaf95,0xafda,0xafdb,0xb13a,0x58d+2*0x9a):
            raw=bytearray(original);raw[at]^=1
            with self.assertRaises(AssertionError):a.verify_static(raw)
    def test_frozen_source_and_fixed_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'native';shutil.copytree(a.DEFAULT,root);next((root/'sources').iterdir()).write_bytes(b'changed')
            with self.assertRaises(AssertionError):a.verify(root)
    def test_fixture_cannot_invent_post_error_fac(self):
        with tempfile.TemporaryDirectory() as d:
            doc=json.loads(a.FIXTURE.read_text());next(c for c in doc['cases'] if c['output']is None)['output']='0000000000000000';p=Path(d)/'fixture';p.write_text(json.dumps(doc))
            with self.assertRaises(AssertionError):a.verify(fixture=p)
    def test_single_and_inline_entries_not_admitted(self):
        n='op9a-one';c=a.CASES[n];raw=self.trace(n)
        for op in (0x80,0x82,0x84,0x99,0x9e,0xff):
            with self.assertRaises(AssertionError):a.verify_trace(raw,dict(c,op=op))

    def test_register_sign_flip_is_not_memory_mutation_or_addition(self):
        import verify_add_double as addition
        for n in ('op9a-both-zero','op9a-reverse-aliases','op9a-sub-one-three','op9a-sub-three-one','op9c-raw'):
            c=a.CASES[n];raw=self.trace(n);left,right,fac=(bytes.fromhex(c[k]) for k in ('left','right','fac'))
            incorrect=addition.expected_entry(left,right,fac)
            if incorrect is not None:self.reject(n,self.output(n,incorrect.hex()))
            bad=bytearray(raw);bad[55]^=128;self.reject(n,bad)
            for op in (0x80,0x82,0x84,0x9e):
                with self.assertRaises(AssertionError):a.expected_payload(dict(c,op=op))

if __name__=='__main__':unittest.main()
