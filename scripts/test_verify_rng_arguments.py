"""RND(argument) native acceptance and independent semantic corruption controls."""
import json
import unittest
import verify_rng_arguments as audit
from recover_rng_arguments import payload


class RNDArguments(unittest.TestCase):
    def trace(self,name):return(audit.DEFAULT/name/'TRACE.BIN').read_bytes()

    def test_complete_corpus_and_portable_fixture(self):
        doc=audit.verify();self.assertEqual(len(doc['cases']),16);self.assertEqual(sum((len(bytes.fromhex(c['trace_hex']))-12)//12 for c in doc['cases']),1024)

    def test_writer_payload_matches_independent_machine_code_contract(self):
        for _,args in audit.CASES.values():self.assertEqual(payload(args),audit.expected_payload(args))

    def test_truncated_or_extra_trace_rejected(self):
        trace=self.trace('positive-one')
        for changed in(trace[:-1],trace+b'x',b'XXXX'+trace[4:]):
            with self.assertRaises(AssertionError):audit.verify_trace(changed,*audit.CASES['positive-one'])

    def test_coherent_state_value_forgery_rejected(self):
        trace=bytearray(self.trace('positive-one'));state=int.from_bytes(trace[12:16],'little')^1;trace[12:16]=state.to_bytes(4,'little')
        from replay_qb_graph import mbf
        trace[16:20]=mbf.enc(state/(1<<24))
        with self.assertRaises(AssertionError):audit.verify_trace(bytes(trace),*audit.CASES['positive-one'])

    def test_negative_call_cannot_keep_old_low_byte(self):
        trace=bytearray(self.trace('negative-one'));raw=trace[8:12];old=5
        seed=(old&255)|(((raw[0]|raw[1]<<8)^(raw[2]|raw[3]<<8))<<8)
        state=(214013*seed+1744579)&0xffffff;trace[12:16]=state.to_bytes(4,'little')
        with self.assertRaises(AssertionError):audit.verify_trace(bytes(trace),*audit.CASES['negative-one'])

    def test_residual_zero_cannot_advance(self):
        trace=bytearray(self.trace('negative-zero'));state=(214013*0x1234ab+1744579)&0xffffff;trace[12:16]=state.to_bytes(4,'little')
        with self.assertRaises(AssertionError):audit.verify_trace(bytes(trace),*audit.CASES['negative-zero'])

    def test_negative_reseed_carry_cannot_be_discarded(self):
        trace=bytearray(self.trace('negative-low-carry'));raw=trace[8:12]
        seed=((raw[0]+raw[3])&255)|(raw[1]<<8)|(raw[2]<<16);state=(214013*seed+1744579)&0xffffff;trace[12:16]=state.to_bytes(4,'little')
        with self.assertRaises(AssertionError):audit.verify_trace(bytes(trace),*audit.CASES['negative-low-carry'])

    def test_argument_and_fac_mutations_rejected_independently(self):
        original=self.trace('mixed')
        for offset in(8,16):
            trace=bytearray(original);trace[offset]^=1
            with self.assertRaises(AssertionError):audit.verify_trace(bytes(trace),*audit.CASES['mixed'])

if __name__=='__main__':unittest.main()
