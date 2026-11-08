"""Reject numeric substitutions, hidden overflow and damaged provenance."""
import json, shutil, tempfile, unittest, math
from pathlib import Path
import verify_int16_double as audit
from recover_int16_double import payload, cases


class DoubleInt16Controls(unittest.TestCase):
    def trace(self,name): return (audit.DEFAULT/name/'TRACE.BIN').read_bytes()
    def reject(self,name,trace):
        with self.assertRaises(AssertionError): audit.verify_trace(bytes(trace),audit.CASES[name])

    def test_complete_native_and_portable_corpus(self):
        doc=audit.verify(); self.assertEqual(len(doc['cases']),104)
        self.assertEqual(sum(c['value'] is None for c in doc['cases']),30)

    def test_independent_recipe_and_payload(self):
        self.assertEqual(cases(),audit.CASES)
        for case in audit.CASES.values(): self.assertEqual(payload(case),audit.expected_payload(case))

    def test_ties_do_not_truncate_or_round_to_even(self):
        for name in ('op76-17','op76-18','op78-17','op78-18'):
            trace=bytearray(self.trace(name)); want=audit.verify_trace(bytes(trace),audit.CASES[name])
            self.assertEqual(abs(want),3)
            trace[17:19]=(2 if want>0 else -2).to_bytes(2,'little',signed=True)
            self.reject(name,trace)

    def test_input_rng_mode_and_fac_residue_corruption(self):
        name='op76-17'; original=self.trace(name)
        for at in (4,8,16,19,23,25,27,31):
            trace=bytearray(original); trace[at]^=1; self.reject(name,trace)

    def test_framing_and_missing_return(self):
        name='op78-00'; trace=self.trace(name)
        for altered in (trace[:-1],trace+b'x',b'XXXX'+trace[4:],trace[:17]): self.reject(name,altered)

    def test_overflow_cannot_be_clamped_wrapped_or_called_success(self):
        name='op76-29'; trace=self.trace(name)
        for altered in (trace[:17]+b'\xff\x7f'+bytes(13)+b'END!',trace[:17]+b'Overflow',trace.replace(b'Overflow',b'OVERFLOW'),trace+b'END!'):
            self.reject(name,altered)

    def test_error_address_tracks_actual_entry(self):
        self.reject('op78-29',self.trace('op76-29'))

    def test_manifest_rejects_modified_or_extra_observations(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'native'; shutil.copytree(audit.DEFAULT,root)
            (root/'op76-00/TRACE.BIN').write_bytes(b'changed')
            with self.assertRaises(AssertionError): audit.verify(root)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'native'; shutil.copytree(audit.DEFAULT,root); (root/'extra').write_bytes(b'')
            with self.assertRaises(AssertionError): audit.verify(root)

    def test_portable_fixture_substitution(self):
        with tempfile.TemporaryDirectory() as temp:
            file=Path(temp)/'fixture.json'; doc=json.loads(audit.FIXTURE.read_text()); doc['cases'][0]['value']=1
            file.write_text(json.dumps(doc))
            with self.assertRaises(AssertionError): audit.verify(fixture=file)

    def test_float64_demotion_changes_native_result(self):
        for name in ('op76-15','op76-16','op78-15','op78-16','op76-27','op76-38'):
            case=audit.CASES[name]; raw=bytes.fromhex(case['raw'])
            mantissa=(int.from_bytes(raw[:7],'little')&0x7fffffffffffff)|(1<<55)
            lossy=math.ldexp(float(mantissa),raw[7]-184)
            rounded=math.floor(lossy+.5)
            if raw[6]&128: rounded=-rounded
            expected=audit.verify_trace(self.trace(name),case)
            self.assertNotEqual(rounded,expected)
            trace=bytearray(self.trace(name)); trace[17:19]=(rounded & 65535).to_bytes(2,'little')
            self.reject(name,trace)

if __name__=='__main__': unittest.main()
