"""Corruption controls for ordered division, FAC residue and distinct fatal exits."""
import json,shutil,tempfile,unittest
from pathlib import Path
import verify_single_divide as a
import recover_single_divide as writer

class Division(unittest.TestCase):
    def trace(self,n):return (a.DEFAULT/n/'TRACE.BIN').read_bytes()
    def reject(self,n,raw):
        with self.assertRaises(AssertionError):a.verify_trace(bytes(raw),a.CASES[n])
    def output(self,n,value):
        raw=bytearray(self.trace(n));raw[21:25]=bytes.fromhex(value);return raw
    def test_complete(self):
        d=a.verify();self.assertEqual(len(d['cases']),105)
        self.assertEqual({k:sum(c['error']==k for c in d['cases']) for k in (None,'overflow','division_by_zero')},{None:75,'overflow':14,'division_by_zero':16})
    def test_independent_acquisition_recipe_and_payload(self):
        self.assertEqual(writer.cases(),a.CASES)
        for c in a.CASES.values():self.assertEqual(writer.payload(c),a.expected_payload(c))
    def test_every_trace_byte(self):
        for n in a.CASES:
            raw=self.trace(n)
            for i in range(len(raw)):
                bad=bytearray(raw);bad[i]^=1;self.reject(n,bad)
    def test_divisor_zero_precedes_numerator_zero(self):
        for n in ('op89-both-zero','op89-aliases','op87-aliases','op8b-aliases'):
            self.assertIn(b'Division by zero',self.trace(n));self.reject(n,self.trace(n).replace(b'Division by zero',b'Overflow'))
    def test_ordered_division_is_not_commutative(self):
        self.assertNotEqual(self.trace('op89-three-two')[21:25],self.trace('op89-two-three')[21:25])
        self.reject('op89-three-two',self.output('op89-three-two',self.trace('op89-two-three')[21:25].hex()))
    def test_zero_and_underflow_use_prior_fac(self):
        for n in ('op87-left-zero','op87-delta-128-below'):
            self.assertEqual(self.trace(n)[21:25].hex(),'5aa5d500');self.reject(n,self.output(n,'00000000'))
        for i in range(4):
            for suffix in ('left-zero','delta-128-below'):
                n=f'fac{i}-{suffix}';self.assertEqual(self.trace(n)[21:25].hex(),a.CASES[n]['fac'][:6]+'00')
    def test_exact_remainders_near_half(self):
        for n in ('guard23-below-odd','guard23-above-even','guard24-below-odd','guard24-above-even'):
            n='op89-'+n;raw=bytearray(self.trace(n));raw[21]^=1;self.reject(n,raw)
    def test_fac_operand_constraints(self):
        for op in (0x89,0x8b):
            n=f'op{op:02x}-three-two';c=dict(a.CASES[n],fac='12345600');raw=bytearray(self.trace(n));raw[8:12]=bytes.fromhex(c['fac'])
            with self.assertRaises(AssertionError):a.verify_trace(raw,c)
    def test_distinct_errors_and_no_fabricated_success(self):
        for n in ('op89-right-zero','op89-max-half','op87-delta127-equal','op8b-delta127-equal'):
            self.assertEqual(a.error_address(a.CASES[n]),'00F3' if a.CASES[n]['op']==0x8b else '00F6')
            raw=self.trace(n);self.reject(n,raw.replace(b'00F3',b'00F4').replace(b'00F6',b'00F7'))
            self.reject(n,raw[:21]+bytes(17)+b'END!');self.reject(n,raw[:-1]);self.reject(n,raw.replace(b'\r\n',b'\n'))
    def test_source_and_caller_boundaries(self):
        direct,inline=a.verify_inventory();self.assertEqual({op:sum(c['op']==op for c in direct) for op in (0x87,0x89,0x8b)},{0x87:8,0x89:16,0x8b:0});self.assertEqual(inline,[])
        original=(a.ROOT/'archive/dos-original/BRUN30.EXE').read_bytes()
        for at in (0xb720,0xb74f,0xb750,0xb7aa,0xbac,0x37f8):
            changed=bytearray(original);changed[at]^=1
            with self.assertRaises(AssertionError):a.verify_static(changed)
    def test_frozen_source_and_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'native';shutil.copytree(a.DEFAULT,root);next((root/'sources').iterdir()).write_bytes(b'changed')
            with self.assertRaises(AssertionError):a.verify(root)
    def test_fixture_cannot_invent_post_error_state(self):
        with tempfile.TemporaryDirectory() as d:
            doc=json.loads(a.FIXTURE.read_text());row=next(c for c in doc['cases'] if c['error']=='division_by_zero');row['output']='00000000';p=Path(d)/'fixture';p.write_text(json.dumps(doc))
            with self.assertRaises(AssertionError):a.verify(fixture=p)

if __name__=='__main__':unittest.main()
