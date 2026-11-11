"""Reject resolver, frame-state and evidence substitutions independently of arithmetic."""
import json,shutil,tempfile,unittest
from pathlib import Path
import verify_inline_sub as a
import verify_inline_add as parent
import recover_inline_sub as first
import recover_inline_sub_callers as supplement

class InlineSubtraction(unittest.TestCase):
    def test_complete(self):self.assertEqual(len(a.verify()['cases']),89)
    def test_independent_payloads(self):
        for writer,cases in ((first,a.CASES),(supplement,a.CALLER_CASES)):
            self.assertEqual(writer.cases(),cases)
            for c in cases.values():self.assertEqual(writer.payload(c),a.expected_payload(c))
    def test_every_trace_field_is_authenticated(self):
        for root,cases in ((a.DEFAULT,a.CASES),(a.CALLER_DEFAULT,a.CALLER_CASES)):
            for name,c in cases.items():
                raw=(root/name/'TRACE.BIN').read_bytes()
                for index in range(len(raw)):
                    changed=bytearray(raw);changed[index]^=1
                    # DS/ES/descriptor/BP are observed relational context, not fixed addresses.
                    with self.assertRaises(AssertionError,msg=(name,index)):a.verify_trace(bytes(changed),c)
    def test_framing(self):
        for name,c in a.CASES.items():
            raw=(a.DEFAULT/name/'TRACE.BIN').read_bytes()
            for bad in (raw[:-1],raw+b'x',raw[1:]):
                with self.assertRaises(AssertionError):a.verify_trace(bad,c)
    def test_address_is_not_arithmetic(self):
        name=next(n for n,c in a.CASES.items() if c['kind']=='address');c=dict(a.CASES[name],kind='full')
        with self.assertRaises(AssertionError):a.verify_trace((a.DEFAULT/name/'TRACE.BIN').read_bytes(),c)
    def test_inventory_includes_all_maintenance_selectors(self):
        self.assertEqual({r['selector'] for r in a.verify_inventory()},{c['selector'] for c in list(a.CASES.values())+list(a.CALLER_CASES.values()) if (c['base10'],c['base12'])==(0x7e00,0x08c3)})
    def test_sources_are_immutable(self):
        for root in (a.DEFAULT,a.CALLER_DEFAULT):
            with tempfile.TemporaryDirectory() as d:
                copy=Path(d)/'native';shutil.copytree(root,copy);next((copy/'sources').iterdir()).write_bytes(b'changed')
                with self.assertRaises(AssertionError):a.verify(copy if root==a.DEFAULT else a.DEFAULT,caller_directory=copy if root==a.CALLER_DEFAULT else a.CALLER_DEFAULT)
    def test_fixture_is_exact(self):
        with tempfile.TemporaryDirectory() as d:
            doc=json.loads(a.FIXTURE.read_text());doc['cases'][0]['resolved']^=1;p=Path(d)/'fixture';p.write_text(json.dumps(doc))
            with self.assertRaises(AssertionError):a.verify(fixture=p)

    def test_addition_cannot_replace_inline_subtraction(self):
        n='full-bm-cancel-83';c=a.CASES[n];raw=(a.DEFAULT/n/'TRACE.BIN').read_bytes()
        with self.assertRaises(AssertionError):parent.verify_trace(raw,c)
        # Even with the other marker, the original FAC subtraction result must differ.
        with self.assertRaises(AssertionError):parent.verify_trace(b'IA85'+raw[4:],c)
    def test_payload_uses_inline9d_not_inline85(self):
        for c in a.CASES.values():
            self.assertIn(bytes.fromhex('cd3f9d9090')+bytes([c['selector']]),a.expected_payload(c))
            self.assertNotEqual(a.expected_payload(c),parent.expected_payload(c))

    def test_operation_selection_is_closed(self):
        c=next(iter(a.CASES.values()))
        with self.assertRaises(AssertionError):parent.expected_payload(c,'unqualified')
        with self.assertRaises(AssertionError):parent.verify_trace(b'',c,'unqualified')

if __name__=='__main__':unittest.main()
