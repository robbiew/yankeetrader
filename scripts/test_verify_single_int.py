"""Native SINGLE INT acceptance and raw/numeric corruption controls."""
import unittest
import verify_single_int as audit
from recover_single_int import payload


class SingleINT(unittest.TestCase):
    def trace(self,name):return(audit.DEFAULT/name/'TRACE.BIN').read_bytes()
    def corrupt(self,name,result):
        trace=bytearray(self.trace(name));trace[16:20]=bytes.fromhex(result)
        with self.assertRaises(AssertionError):audit.verify_trace(bytes(trace),*audit.CASES[name])

    def test_complete_native_and_portable_corpus(self):
        document=audit.verify();self.assertEqual(len(document['cases']),16);self.assertEqual(document['samples_per_case'],64)

    def test_payload_independently_reconstructed(self):
        for _,args in audit.CASES.values():self.assertEqual(payload(args),audit.expected_payload(args))

    def test_positive_subunit_zero_must_preserve_mantissa(self):
        self.corrupt('positive-near-one','00000000')

    def test_negative_fraction_is_floor_not_truncation(self):
        self.corrupt('negative-fractions','00008081') # -1.5 must become -2

    def test_positive_fraction_is_not_nearest_rounding(self):
        self.corrupt('positive-fractions','00000082') # 1.5 must become +1

    def test_residual_zero_is_not_normalized_or_floor_minus_one(self):
        self.corrupt('zero-residues','00000000')
        self.corrupt('zero-residues','00008081')

    def test_negative_power_of_two_carry_is_required(self):
        self.corrupt('negative-byte-boundaries','0000ff88') # -255.5 must become -256

    def test_rng_mutation_and_input_substitution_rejected(self):
        original=self.trace('mixed-history')
        for offset in(8,12):
            trace=bytearray(original);trace[offset]^=1
            with self.assertRaises(AssertionError):audit.verify_trace(bytes(trace),*audit.CASES['mixed-history'])

    def test_trace_framing_and_initial_state_rejected(self):
        original=self.trace('mixed-history')
        for trace in(original[:-1],original+b'x',b'XXXX'+original[4:],original[:4]+bytes(4)+original[8:]):
            with self.assertRaises(AssertionError):audit.verify_trace(trace,*audit.CASES['mixed-history'])

    def test_large_finite_integer_bits_remain_unchanged(self):
        for raw in('ffffffff','ffff7fff','01008099','ffff7f98'):
            value=bytes.fromhex(raw);self.assertEqual(audit.expected_int(value),value)

if __name__=='__main__':unittest.main()
