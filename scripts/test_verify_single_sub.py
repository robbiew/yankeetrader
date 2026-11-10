"""Reject operand direction, FAC, zero-alias and native evidence substitutions."""
import json,shutil,tempfile,unittest
from pathlib import Path
import verify_single_sub as a
from recover_single_sub import payload,cases

class Subtraction(unittest.TestCase):
    def trace(self,name):return (a.DEFAULT/name/'TRACE.BIN').read_bytes()
    def reject(self,name,raw):
        with self.assertRaises(AssertionError):a.verify_trace(bytes(raw),a.CASES[name])
    def output(self,name,value):
        raw=bytearray(self.trace(name));raw[21:25]=bytes.fromhex(value);return raw
    def test_complete(self):self.assertEqual(len(a.verify()['cases']),266)
    def test_independent_payloads(self):
        self.assertEqual(cases(),a.CASES)
        for c in cases().values():self.assertEqual(payload(c),a.expected_payload(c))
    def test_zero_alias_sign_is_flipped_even_when_zero(self):
        n='op97-zero-aliases';self.assertEqual(self.trace(n)[21:25].hex(),'ffff7f00');self.reject(n,self.output(n,'ffffff00'))
    def test_direction_is_left_minus_right(self):
        n='op97-positive-sign-cross';c=a.CASES[n];wrong=a.expected_entry(bytes.fromhex(c['right']),bytes.fromhex(c['left']),bytes.fromhex(c['fac']))
        self.reject(n,self.output(n,wrong.hex()))
    def test_cancellation_preserves_independent_unnegated_fac(self):
        for index in range(4):
            for suffix in ('cancel','underflow','reverse-underflow'):
                n=f'fac{index}-{suffix}';c=a.CASES[n];self.assertEqual(self.trace(n)[21:25].hex(),c['fac'][:6]+'00')
                wrong=bytearray.fromhex(c['fac']);wrong[2]^=128;wrong[3]=0;self.reject(n,self.output(n,wrong.hex()))
    def test_entry_fac_constraints(self):
        for op in (0x99,0x9b):
            n=f'op{op:02x}-one-plus-one';c=dict(a.CASES[n],fac='12345600');raw=bytearray(self.trace(n));raw[8:12]=bytes.fromhex(c['fac'])
            with self.assertRaises(AssertionError):a.verify_trace(raw,c)
    def test_all_trace_bytes_authenticated(self):
        for n,c in a.CASES.items():
            original=self.trace(n)
            for index in range(len(original)):
                raw=bytearray(original);raw[index]^=1;self.reject(n,raw)
    def test_complete_framing(self):
        for n in ('op97-both-zero','op99-max-cancel','op9b-max-cancel'):
            raw=self.trace(n)
            for bad in (raw[:-1],raw+b'x',raw.replace(b'\r\n',b'\n') if b'\r\n' in raw else raw[1:]):self.reject(n,bad)
    def test_no_synthetic_success_on_overflow(self):
        n='op97-max-cancel';raw=self.trace(n)[:21]+bytes(17)+b'END!';self.reject(n,raw)
    def test_original_caller_coverage(self):
        calls=a.verify_inventory();self.assertEqual(len(calls),43);self.assertEqual({c['op'] for c in calls},{0x97,0x99,0x9b})
    def test_native_source_substitution(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'native';shutil.copytree(a.DEFAULT,p);(p/'sources/recover_single_sub.py').write_bytes(b'changed')
            with self.assertRaises(AssertionError):a.verify(p)
    def test_fixture_substitution(self):
        with tempfile.TemporaryDirectory() as d:
            doc=json.loads(a.FIXTURE.read_text());doc['cases'][0]['fac']='ffffffff';p=Path(d)/'fixture';p.write_text(json.dumps(doc))
            with self.assertRaises(AssertionError):a.verify(fixture=p)

if __name__=='__main__':unittest.main()
