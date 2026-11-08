"""Native SINGLE FIX identity, raw-zero and truncation corruption controls."""
import unittest
import verify_single_fix as audit
from recover_single_fix import payload
from verify_single_int import expected_int


class SingleFIX(unittest.TestCase):
    def trace(self,name):return(audit.DEFAULT/name/'TRACE.BIN').read_bytes()
    def corrupt(self,name,result):
        trace=bytearray(self.trace(name));trace[16:20]=bytes.fromhex(result)
        with self.assertRaises(AssertionError):audit.verify_trace(bytes(trace),*audit.CASES[name])

    def test_complete_native_and_portable_corpus(self):
        doc=audit.verify();self.assertEqual(len(doc['cases']),8);self.assertEqual(doc['samples_per_case'],64)

    def test_payload_is_independently_reconstructed(self):
        for _,args in audit.CASES.values():self.assertEqual(payload(args),audit.expected_payload(args))

    def test_negative_fix_is_not_int_floor(self):
        trace=bytearray(self.trace('negative-fractions'));trace[16:20]=expected_int(bytes(trace[8:12]))
        with self.assertRaises(AssertionError):audit.verify_trace(bytes(trace),*audit.CASES['negative-fractions'])

    def test_negative_subunit_zero_is_not_canonicalized(self):
        self.corrupt('negative-subunit','00000000')
        self.corrupt('negative-subunit','00008081')

    def test_positive_zero_and_zero_aliases_are_not_normalized(self):
        self.corrupt('zero-residues','00000000')
        trace=bytearray(self.trace('positive-subunit'));at=8+12;trace[at+8:at+12]=bytes(4)
        with self.assertRaises(AssertionError):audit.verify_trace(bytes(trace),*audit.CASES['positive-subunit'])

    def test_negative_boundary_cannot_round_away_from_zero(self):
        self.corrupt('negative-byte-boundaries','00008089') # FIX(-255.5) is -255

    def test_rng_and_input_substitution_rejected(self):
        original=self.trace('mixed-max-rng')
        for offset in(8,12):
            trace=bytearray(original);trace[offset]^=1
            with self.assertRaises(AssertionError):audit.verify_trace(bytes(trace),*audit.CASES['mixed-max-rng'])

    def test_framing_and_initial_state_rejected(self):
        original=self.trace('mixed-max-rng')
        for trace in(original[:-1],original+b'x',b'XXXX'+original[4:],original[:4]+bytes(4)+original[8:]):
            with self.assertRaises(AssertionError):audit.verify_trace(trace,*audit.CASES['mixed-max-rng'])

if __name__=='__main__':unittest.main()
