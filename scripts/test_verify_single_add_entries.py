"""Reject collapsed FAC state, operand swapping and false direct-entry claims."""
import json,shutil,tempfile,unittest
from pathlib import Path
import verify_single_add_entries as audit
from recover_single_add_entries import payload,cases


class AdditionEntries(unittest.TestCase):
    def trace(self,name):return (audit.DEFAULT/name/'TRACE.BIN').read_bytes()
    def reject(self,name,trace):
        with self.assertRaises(AssertionError):audit.verify_trace(bytes(trace),audit.CASES[name])
    def result(self,name,value):
        trace=bytearray(self.trace(name));trace[21:25]=bytes.fromhex(value);return trace

    def test_complete_native_and_portable_entry_corpus(self):
        doc=audit.verify();self.assertEqual(len(doc['cases']),184);self.assertEqual(sum(c['output'] is None for c in doc['cases']),8)

    def test_recipe_and_payload_are_independently_reconstructed(self):
        self.assertEqual(cases(),audit.CASES)
        for c in cases().values():self.assertEqual(payload(c),audit.expected_payload(c))

    def test_memory_cancellation_keeps_prior_fac_not_operand(self):
        n='op7f-fraction-cancel';c=audit.CASES[n];self.assertEqual(self.trace(n)[21:25].hex(),c['fac'][:6]+'00')
        self.reject(n,self.result(n,c['left'][:6]+'00'))
        self.reject(n,self.result(n,c['right'][:6]+'00'))

    def test_prior_fac_zero_alias_and_underflow_residues(self):
        for index in (1,2,3):
            for suffix in ('fraction-cancel','minimum-one-bit','minimum-near-binade-reverse'):
                n=f'fac{index}-{suffix}';self.reject(n,self.result(n,'00000000'))

    def test_entry83_zero_aliases_must_not_swap_arguments(self):
        n='op83-zero-aliases';c=audit.CASES[n];self.assertEqual(self.trace(n)[21:25].hex(),c['right'])
        self.reject(n,self.result(n,c['left']))

    def test_entry83_right_operand_is_initial_fac_not_memory_shadow(self):
        n='op83-one-plus-one';c=dict(audit.CASES[n]);c['fac']='5aa5d592'
        trace=bytearray(self.trace(n));trace[8:12]=bytes.fromhex(c['fac'])
        with self.assertRaises(AssertionError):audit.verify_trace(bytes(trace),c)

    def test_zero_operand_path_does_not_borrow_arbitrary_fac(self):
        n='op7f-zero-aliases';c=audit.CASES[n];self.reject(n,self.result(n,c['fac'][:6]+'00'))

    def test_operand_memory_rng_mode_and_state_corruption(self):
        n='op7f-raw-align-positive';original=self.trace(n)
        for offset in (4,8,12,16,20,21,25,29,33,37):
            trace=bytearray(original);trace[offset]^=1;self.reject(n,trace)

    def test_error_address_must_match_entry(self):
        n='op83-max-pair';self.reject(n,self.trace(n).replace(b'00F3',b'00F6'))
        n='op7f-max-pair';self.reject(n,self.trace(n).replace(b'00F6',b'00F3'))

    def test_error_cannot_be_clamped_or_replaced_with_return(self):
        for n in ('op7f-max-pair','op83-negative-max-pair'):
            c=audit.CASES[n];forged=self.trace(n)[:21]+bytes(4)+bytes.fromhex(c['left']+c['right'])+c['initial'].to_bytes(4,'little')+b'\x00END!'
            self.reject(n,forged);self.reject(n,self.trace(n).replace(b'\r\n',b'\n'))

    def test_manifest_and_fixture_substitution_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'native';shutil.copytree(audit.DEFAULT,root);(root/'sources/recover_single_add_entries.py').write_bytes(b'changed')
            with self.assertRaises(AssertionError):audit.verify(root)
        with tempfile.TemporaryDirectory() as temp:
            doc=json.loads(audit.FIXTURE.read_text());doc['cases'][0]['fac']='00000000';p=Path(temp)/'fixture.json';p.write_text(json.dumps(doc))
            with self.assertRaises(AssertionError):audit.verify(fixture=p)

    def test_complete_framing_not_parent_entry_format(self):
        n='op7f-both-zero';t=self.trace(n)
        for bad in (t[:-1],t+b'x',b'ADD1'+t[4:],t[:21]):self.reject(n,bad)

if __name__=='__main__':unittest.main()
