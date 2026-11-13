"""Native flags, actual branch outcomes and immutable provenance regressions."""
import json,tempfile,unittest
from pathlib import Path
import verify_single_compare as v
import recover_single_compare as writer

class SingleCompare(unittest.TestCase):
    def test_complete_native(self):
        d=v.verify();self.assertEqual(len(d['cases']),216)
        self.assertEqual({op:sum(c['op']==op for c in d['cases'])for op in (159,161,163)},{159:72,161:72,163:72})
    def test_independent_payload(self):
        self.assertEqual(writer.cases(),v.CASES)
        for c in v.CASES.values():self.assertEqual(writer.payload(c),v.expected_payload(c))
    def test_all_branch_and_defined_flag_bits(self):
        for n,c in v.CASES.items():
            raw=(v.DEFAULT/n/'TRACE.BIN').read_bytes()
            for pos in range(38,54):
                bad=bytearray(raw);bad[pos]^=1
                with self.assertRaises(AssertionError):v.verify_trace(bad,c)
            for bit in (1,4,64,128,2048,1024):
                bad=bytearray(raw);f=int.from_bytes(bad[36:38],'little')^bit;bad[36:38]=f.to_bytes(2,'little')
                with self.assertRaises(AssertionError):v.verify_trace(bad,c)
    def test_undefined_af_not_a_contract(self):
        c=v.CASES['op9f-zeros'];raw=bytearray((v.DEFAULT/'op9f-zeros'/'TRACE.BIN').read_bytes());raw[36]^=16
        v.verify_trace(raw,c) # Corpus pins still reject any alteration to the observation.
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'pins.json').write_bytes((v.DEFAULT/'pins.json').read_bytes());(p/'TRACE.BIN').write_bytes(raw)
            with self.assertRaises(AssertionError):v.verify(p,fixture=None)
    def test_inputs_abi_rng_and_frame_corruption(self):
        n='op9f-one-equal';c=v.CASES[n];raw=(v.DEFAULT/n/'TRACE.BIN').read_bytes()
        for pos in list(range(28))+list(range(38,97)):
            bad=bytearray(raw);bad[pos]^=1
            with self.assertRaises(AssertionError):v.verify_trace(bad,c)
    def test_no_unadmitted_opcode(self):
        c=v.CASES['op9f-zeros'];raw=(v.DEFAULT/'op9f-zeros'/'TRACE.BIN').read_bytes()
        for op in (160,162,164,165):
            with self.assertRaises(AssertionError):v.verify_trace(raw,dict(c,op=op))

if __name__=='__main__':unittest.main()
