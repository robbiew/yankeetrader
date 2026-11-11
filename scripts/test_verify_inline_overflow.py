"""Reject fake success, altered error context and source/protocol substitutions."""
import json,shutil,tempfile,unittest
from pathlib import Path
import verify_inline_overflow as a
import recover_inline_overflow as first
import recover_inline_overflow_depth as depth

class InlineOverflow(unittest.TestCase):
    def test_complete(self):
        d=a.verify();self.assertEqual(len(d['cases']),20);self.assertEqual(sum(c['output'] is None for c in d['cases']),12)
    def test_independent_acquisition_payloads(self):
        for writer,cases in ((first,a.CASES),(depth,a.DEPTH_CASES)):
            self.assertEqual(writer.cases(),cases)
            for c in cases.values():self.assertEqual(writer.payload(c),a.expected_payload(c))
    def test_every_native_trace_byte(self):
        for root,cases in ((a.DEFAULT,a.CASES),(a.DEPTH_DEFAULT,a.DEPTH_CASES)):
            for n,c in cases.items():
                raw=(root/n/'TRACE.BIN').read_bytes()
                for i in range(len(raw)):
                    changed=bytearray(raw);changed[i]^=1
                    with self.assertRaises(AssertionError,msg=(n,i)):a.verify_trace(changed,c)
    def test_error_address_consumes_selector(self):
        for root,cases in ((a.DEFAULT,a.CASES),(a.DEPTH_DEFAULT,a.DEPTH_CASES)):
            for n,c in cases.items():
                if c['expect']!='overflow':continue
                raw=(root/n/'TRACE.BIN').read_bytes();address=a.error_address(c)
                bad=raw.replace(address.encode(),f'{int(address,16)-1:04X}'.encode())
                with self.assertRaises(AssertionError):a.verify_trace(bad,c)
    def test_no_fabricated_fatal_return_frame(self):
        n='op85-bm-positive-overflow';c=a.CASES[n];raw=(a.DEFAULT/n/'TRACE.BIN').read_bytes()
        for bad in (raw[:46]+bytes(29)+b'END!',raw+b'END!',raw[:-1],raw.replace(b'\r\n',b'\n')):
            with self.assertRaises(AssertionError):a.verify_trace(bad,c)
    def test_arithmetic_predicts_error_not_recipe_label(self):
        for n,c in a.CASES.items():
            wrong=dict(c,expect='return' if c['expect']=='overflow' else 'overflow')
            with self.assertRaises(AssertionError):a.verify_trace((a.DEFAULT/n/'TRACE.BIN').read_bytes(),wrong)
    def test_operation_cannot_be_swapped(self):
        n='op85-bm-positive-overflow';c=dict(a.CASES[n],op=0x9d);raw=bytearray((a.DEFAULT/n/'TRACE.BIN').read_bytes());raw[32:34]=(0x9d).to_bytes(2,'little')
        with self.assertRaises(AssertionError):a.verify_trace(raw,c)
    def test_frame_depth_is_independent_of_module_context(self):
        for n,c in a.DEPTH_CASES.items():
            wrong=dict(c,pad=0)
            with self.assertRaises(AssertionError):a.verify_trace((a.DEPTH_DEFAULT/n/'TRACE.BIN').read_bytes(),wrong)
    def test_finite_control_cannot_be_fatal(self):
        n='op9d-bz-finite-control';c=a.CASES[n];raw=(a.DEFAULT/n/'TRACE.BIN').read_bytes()
        fatal=(a.DEFAULT/'op9d-bz-positive-overflow'/'TRACE.BIN').read_bytes()
        with self.assertRaises(AssertionError):a.verify_trace(raw[:46]+fatal[46:],c)
    def test_frozen_sources(self):
        for root in (a.DEFAULT,a.DEPTH_DEFAULT):
            with tempfile.TemporaryDirectory() as d:
                p=Path(d)/'native';shutil.copytree(root,p);next((p/'sources').iterdir()).write_bytes(b'changed')
                with self.assertRaises(AssertionError):a.verify(p if root==a.DEFAULT else a.DEFAULT,depth_directory=p if root==a.DEPTH_DEFAULT else a.DEPTH_DEFAULT)
    def test_exact_inventory(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'native';shutil.copytree(a.DEFAULT,p);(p/'extra').write_bytes(b'x')
            with self.assertRaises(AssertionError):a.verify(p)
    def test_fixture_cannot_claim_post_error_fac(self):
        with tempfile.TemporaryDirectory() as d:
            doc=json.loads(a.FIXTURE.read_text());doc['cases'][0]['output']='00000000';p=Path(d)/'fixture';p.write_text(json.dumps(doc))
            with self.assertRaises(AssertionError):a.verify(fixture=p)

if __name__=='__main__':unittest.main()
