"""Native mode-4 floor, explicit setting and precision corruption controls."""
import json,math,shutil,tempfile,unittest
from pathlib import Path
import verify_int16_mode4 as audit
from recover_int16_mode4 import payload,cases
from recover_int16_mode4_precision import payload as precision_payload,cases as precision_cases


class Mode4Controls(unittest.TestCase):
    def case(self,name):return (audit.PRECISION_CASES if name.startswith('precision-') else audit.CASES)[name]
    def trace(self,name):return ((audit.PRECISION if name.startswith('precision-') else audit.DEFAULT)/name/'TRACE.BIN').read_bytes()
    def reject(self,name,trace):
        with self.assertRaises(AssertionError):audit.verify_trace(bytes(trace),self.case(name))
    def fake_return(self,name,integer):
        c=self.case(name);raw=bytes.fromhex(c['raw']);at=len(raw)+10;word=0 if c['kind']=='single' else 4
        fac=bytearray(raw);fac[word:word+2]=(integer&65535).to_bytes(2,'little')
        return self.trace(name)[:at]+(integer&65535).to_bytes(2,'little')+fac+c['initial'].to_bytes(4,'little')+b'\x04END!'

    def test_complete_native_and_portable_corpora(self):
        doc=audit.verify();self.assertEqual(len(doc['cases']),224);self.assertEqual(sum(c['value'] is None for c in doc['cases']),56)

    def test_independent_both_recipes_and_payloads(self):
        self.assertEqual(cases(),audit.CASES);self.assertEqual(precision_cases(),audit.PRECISION_CASES)
        for c in cases().values():self.assertEqual(payload(c),audit.expected_payload(c))
        for c in precision_cases().values():self.assertEqual(precision_payload(c),audit.expected_payload(c))

    def test_positive_fraction_does_not_use_default_rounding(self):
        for n in ('single-op75-17','double-op76-17'):
            self.assertEqual(audit.verify_trace(self.trace(n),self.case(n)),2)
            self.reject(n,self.fake_return(n,3))

    def test_negative_fraction_does_not_truncate(self):
        for n in ('single-op77-02','double-op78-02'):
            self.assertEqual(audit.verify_trace(self.trace(n),self.case(n)),-1)
            self.reject(n,self.fake_return(n,0))

    def test_original_and_applied_modes_are_distinct(self):
        for n in ('single-op75-00','double-op76-00'):
            original=self.trace(n);size=len(bytes.fromhex(self.case(n)['raw']))
            for at in (8+size,9+size,len(original)-5):
                t=bytearray(original);t[at]^=4;self.reject(n,t)

    def test_rng_input_and_fac_residue_corruption(self):
        for n in ('single-op75-17','double-op76-17'):
            original=self.trace(n);size=len(bytes.fromhex(self.case(n)['raw']));at=size+10
            for offset in (4,8,at,at+2,at+size+1,at+size+2):
                t=bytearray(original);t[offset]^=1;self.reject(n,t)

    def test_framing_and_operation_magic(self):
        n='single-op75-00';t=self.trace(n)
        for altered in (t[:-1],t+b'x',b'M4D!'+t[4:],t[:14]):self.reject(n,altered)

    def test_error_cannot_be_clamped_or_replaced_with_success(self):
        for n in ('single-op75-36','precision-double-op76-11'):
            self.assertIsNone(audit.verify_trace(self.trace(n),self.case(n)))
            for altered in (self.fake_return(n,-32768),self.trace(n).replace(b'Overflow',b'OVERFLOW'),self.trace(n)+b'END!'):
                self.reject(n,altered)

    def test_error_call_address_substitution(self):
        self.reject('single-op77-36',self.trace('single-op75-36'))

    def test_float64_changes_floor_or_overflow(self):
        for suffix in ('00','03','08','11'):
            n='precision-double-op76-'+suffix;c=self.case(n);raw=bytes.fromhex(c['raw'])
            mantissa=(int.from_bytes(raw[:7],'little')&0x7fffffffffffff)|(1<<55)
            value=math.ldexp(float(mantissa),raw[7]-184)
            if raw[6]&128:value=-value
            integer=math.floor(value);wrong=integer if -32768<=integer<=32767 else None
            actual=audit.verify_trace(self.trace(n),c);self.assertNotEqual(wrong,actual)
            self.reject(n,self.fake_return(n,integer))

    def test_manifest_rejects_modified_source_or_extra_observations(self):
        for source,cases_,pins,recipe,name in ((audit.DEFAULT,audit.CASES,audit.PINS_SHA,'brun30-int16-mode4-v1','recover_int16_mode4.py'),(audit.PRECISION,audit.PRECISION_CASES,audit.PRECISION_PINS_SHA,'brun30-int16-mode4-precision-v1','recover_int16_mode4_precision.py')):
            with tempfile.TemporaryDirectory() as temp:
                root=Path(temp)/'native';shutil.copytree(source,root);(root/'sources'/name).write_bytes(b'changed source')
                with self.assertRaises(AssertionError):audit.verify_corpus(root,cases_,pins,recipe,name)
            with tempfile.TemporaryDirectory() as temp:
                root=Path(temp)/'native';shutil.copytree(source,root);(root/'extra').write_bytes(b'')
                with self.assertRaises(AssertionError):audit.verify_corpus(root,cases_,pins,recipe,name)

    def test_portable_fixture_cannot_replace_native_outcome(self):
        with tempfile.TemporaryDirectory() as temp:
            file=Path(temp)/'fixture.json';doc=json.loads(audit.FIXTURE.read_text());doc['cases'][0]['value']=1;file.write_text(json.dumps(doc))
            with self.assertRaises(AssertionError):audit.verify(fixture=file)

if __name__=='__main__':unittest.main()
