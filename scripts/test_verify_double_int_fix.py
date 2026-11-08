"""Native DOUBLE operation, precision and raw-byte corruption controls."""
import unittest
import verify_double_int_fix as audit
from recover_double_int_fix import payload


class DoubleIntFix(unittest.TestCase):
    def trace(self,name):return(audit.DEFAULT/name/'TRACE.BIN').read_bytes()
    def corrupt(self,name,result,index=0):
        trace=bytearray(self.trace(name));at=8+20*index;trace[at+12:at+20]=bytes.fromhex(result)
        with self.assertRaises(AssertionError):audit.verify_trace(bytes(trace),*audit.CASES[name])

    def test_complete_native_and_portable_corpus(self):
        doc=audit.verify();self.assertEqual(len(doc['cases']),24);self.assertEqual(doc['samples_per_case'],64)
        self.assertEqual({c['operation']for c in doc['cases']},{'int','fix'})

    def test_payloads_are_independently_reconstructed(self):
        for op,_,args in audit.CASES.values():self.assertEqual(payload(op,args),audit.expected_payload(op,args))

    def test_double_precision_cannot_be_demoted_to_float64(self):
        # IEEE rounds 2^53-.5 to 2^53, erasing the fraction before INT/FIX.
        for op in('int','fix'):self.corrupt(op+'-positive-precision','00000000000000b6')

    def test_int_and_fix_are_not_interchangeable(self):
        for op in('int','fix'):
            name=op+'-negative-fractions';trace=self.trace(name);raw=trace[8:16]
            wrong=audit.expected_double(raw,'fix'if op=='int'else'int')
            self.corrupt(name,wrong.hex())

    def test_zero_aliases_cannot_be_normalized(self):
        for op in('int','fix'):self.corrupt(op+'-zero-aliases','0000000000000000',1)

    def test_fix_negative_subunit_retains_zero_residue(self):
        self.corrupt('fix-negative-subunit','0000000000000000')
        self.corrupt('fix-negative-subunit','0000000000008081')

    def test_int_negative_subunit_must_floor_to_minus_one(self):
        self.corrupt('int-negative-subunit','0000000000008000')

    def test_negative_precision_carry_is_required(self):
        self.corrupt('int-negative-precision','f8ffffffffffffb5')

    def test_argument_rng_and_raw_result_changes_rejected(self):
        original=self.trace('int-mixed-history')
        for offset in(8,16,20):
            trace=bytearray(original);trace[offset]^=1
            with self.assertRaises(AssertionError):audit.verify_trace(bytes(trace),*audit.CASES['int-mixed-history'])

    def test_framing_operation_and_initial_state_rejected(self):
        original=self.trace('int-mixed-history')
        for trace in(original[:-1],original+b'x',b'DFIX'+original[4:],original[:4]+bytes(4)+original[8:]):
            with self.assertRaises(AssertionError):audit.verify_trace(trace,*audit.CASES['int-mixed-history'])

    def test_integral_extremes_keep_all_eight_bytes(self):
        for raw in('ffffffffffffffff','ffffffffffff7fff','01000000000000b8'):
            for op in('int','fix'):self.assertEqual(audit.expected_double(bytes.fromhex(raw),op).hex(),raw)

if __name__=='__main__':unittest.main()
