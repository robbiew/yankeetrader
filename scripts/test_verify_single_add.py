"""Reject float32 substitution, lost zero residues and damaged addition evidence."""
import json,shutil,tempfile,unittest
from pathlib import Path
import verify_single_add as audit
from recover_single_add import cases,payload


class SingleAddition(unittest.TestCase):
    def trace(self,name):return (audit.DEFAULT/name/'TRACE.BIN').read_bytes()
    def reject(self,name,trace):
        with self.assertRaises(AssertionError):audit.verify_trace(bytes(trace),audit.CASES[name])
    def result(self,name,raw):
        trace=bytearray(self.trace(name));trace[17:21]=bytes.fromhex(raw);return bytes(trace)

    def test_complete_new_and_reused_native_evidence(self):
        doc=audit.verify();self.assertEqual(len(doc['cases']),82);self.assertEqual(len(doc['reused_rewards']),9)
        self.assertEqual(sum(c['output'] is None for c in doc['cases']),4)

    def test_recipe_and_payload_independently_reconstructed(self):
        self.assertEqual(cases(),audit.CASES)
        for case in audit.CASES.values():self.assertEqual(payload(case),audit.expected_payload(case))

    def test_even_ties_are_not_half_away_or_truncation(self):
        for label in ('positive','negative'):
            for odd in (0,1):
                name=f'{label}-lsb{odd}-tie';trace=bytearray(self.trace(name));trace[17]^=1;self.reject(name,trace)

    def test_native_exponent_cutoff_is_not_ieee_rounding(self):
        for name,ieee in [('positive-gap25-subtract','ffff7f80'),('negative-gap25-subtract','ffffff80')]:
            self.assertEqual(self.trace(name)[17:21],bytes.fromhex(audit.CASES[name]['left']))
            self.reject(name,self.result(name,ieee))

    def test_zero_aliases_select_right_encoding(self):
        for name in ('zero-aliases','reverse-zero-aliases'):
            case=audit.CASES[name];self.assertEqual(self.trace(name)[17:21].hex(),case['right'])
            self.reject(name,self.result(name,case['left']));self.reject(name,self.result(name,'00000000'))

    def test_cancellation_does_not_canonicalize_fac_residue(self):
        for name in ('fraction-cancel','reverse-fraction-cancel','max-cancel','negative-max-cancel'):
            self.reject(name,self.result(name,'00000000'))

    def test_underflow_retains_initial_fac_mantissa(self):
        for name in ('minimum-one-bit','negative-minimum-one-bit','minimum-near-binade-reverse'):
            self.reject(name,self.result(name,'00000000'))

    def test_input_memory_rng_and_mode_substitution(self):
        name='raw-align-positive';original=self.trace(name)
        for offset in (4,8,12,16,17,21,25,29):
            trace=bytearray(original);trace[offset]^=1;self.reject(name,trace)

    def test_framing_and_missing_return(self):
        name='both-zero';trace=self.trace(name)
        for bad in (trace[:-1],trace+b'x',b'XXXX'+trace[4:],trace[:17]):self.reject(name,bad)

    def test_overflow_cannot_be_wrapped_clamped_or_called_success(self):
        for name in ('max-pair','negative-max-round-overflow'):
            trace=self.trace(name);case=audit.CASES[name]
            for value in ('00000000','ffff7fff','ffffffff'):
                forged=trace[:17]+bytes.fromhex(value)+bytes.fromhex(case['right'])+case['initial'].to_bytes(4,'little')+b'\x00END!'
                self.reject(name,forged)
            self.reject(name,trace.replace(b'\r\n',b'\n'))

    def test_modified_source_or_extra_native_artifact_rejected(self):
        for changed in ('sources/recover_single_add.py','extra'):
            with tempfile.TemporaryDirectory() as temp:
                root=Path(temp)/'native';shutil.copytree(audit.DEFAULT,root);(root/changed).write_bytes(b'changed')
                with self.assertRaises(AssertionError):audit.verify(root)

    def test_portable_reward_or_new_result_cannot_replace_native(self):
        for field in ('cases','reused_rewards'):
            with tempfile.TemporaryDirectory() as temp:
                doc=json.loads(audit.FIXTURE.read_text());doc[field][0]['output']='ffffffff';p=Path(temp)/'fixture.json';p.write_text(json.dumps(doc))
                with self.assertRaises(AssertionError):audit.verify(fixture=p)

if __name__=='__main__':unittest.main()
