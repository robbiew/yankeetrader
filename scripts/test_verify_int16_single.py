"""Reject numeric substitutions, hidden overflow and damaged provenance."""
import json, shutil, tempfile, unittest
from pathlib import Path
import verify_int16_single as audit
from recover_int16_single import payload, cases


class Int16Controls(unittest.TestCase):
    def trace(self,name): return (audit.DEFAULT/name/'TRACE.BIN').read_bytes()
    def reject(self,name,trace):
        with self.assertRaises(AssertionError): audit.verify_trace(bytes(trace),audit.CASES[name])

    def test_complete_native_and_portable_corpus(self):
        doc=audit.verify(); self.assertEqual(len(doc['cases']),96)
        self.assertEqual(sum(c['value'] is None for c in doc['cases']),26)

    def test_independent_recipe_and_payload(self):
        self.assertEqual(cases(),audit.CASES)
        for case in audit.CASES.values(): self.assertEqual(payload(case),audit.expected_payload(case))

    def test_ties_do_not_truncate_or_round_to_even(self):
        for name in ('op75-17','op75-18','op77-17','op77-18'):
            trace=bytearray(self.trace(name)); want=audit.verify_trace(bytes(trace),audit.CASES[name])
            self.assertEqual(abs(want),3)
            trace[13:15]=(2 if want>0 else -2).to_bytes(2,'little',signed=True)
            self.reject(name,trace)

    def test_input_rng_mode_and_fac_residue_corruption(self):
        name='op75-17'; original=self.trace(name)
        for at in (4,8,12,15,17,19,23):
            trace=bytearray(original); trace[at]^=1; self.reject(name,trace)

    def test_framing_and_missing_return(self):
        name='op77-00'; trace=self.trace(name)
        for altered in (trace[:-1],trace+b'x',b'XXXX'+trace[4:],trace[:13]): self.reject(name,altered)

    def test_overflow_cannot_be_clamped_wrapped_or_called_success(self):
        name='op75-29'; trace=self.trace(name)
        for altered in (trace[:13]+b'\xff\x7f'+bytes(9)+b'END!',trace[:13]+b'Overflow',trace.replace(b'Overflow',b'OVERFLOW'),trace+b'END!'):
            self.reject(name,altered)

    def test_error_address_tracks_actual_entry(self):
        self.reject('op77-29',self.trace('op75-29'))

    def test_manifest_rejects_modified_or_extra_observations(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'native'; shutil.copytree(audit.DEFAULT,root)
            (root/'op75-00/TRACE.BIN').write_bytes(b'changed')
            with self.assertRaises(AssertionError): audit.verify(root)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'native'; shutil.copytree(audit.DEFAULT,root); (root/'extra').write_bytes(b'')
            with self.assertRaises(AssertionError): audit.verify(root)

    def test_portable_fixture_substitution(self):
        with tempfile.TemporaryDirectory() as temp:
            file=Path(temp)/'fixture.json'; doc=json.loads(audit.FIXTURE.read_text()); doc['cases'][0]['value']=1
            file.write_text(json.dumps(doc))
            with self.assertRaises(AssertionError): audit.verify(fixture=file)

if __name__=='__main__': unittest.main()
