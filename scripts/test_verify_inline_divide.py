"""Reject inline8d opcode, FAC-binding, addressing, error and evidence substitutions."""
import json,shutil,tempfile,unittest
from pathlib import Path
import verify_inline_divide as a
import recover_inline_divide as full
import recover_inline_divide_address as address

class InlineDivision(unittest.TestCase):
    def test_complete(self):
        d=a.verify();self.assertEqual(len(d['address_cases']),15);self.assertEqual(len(d['execution_cases']),78);self.assertEqual({k:sum(c['error']==k for c in d['execution_cases']) for k in (None,'overflow','division_by_zero')},{None:54,'overflow':10,'division_by_zero':14})
    def test_independent_payloads(self):
        for writer,cases,rebuild in ((full,a.CASES,a.expected_payload),(address,a.ADDRESS_CASES,a.expected_address_payload)):
            self.assertEqual(writer.cases(),cases)
            for c in cases.values():self.assertEqual(writer.payload(c),rebuild(c))
    def test_every_trace_byte(self):
        for root,cases,check in ((a.DEFAULT,a.CASES,a.verify_trace),(a.ADDRESS_DEFAULT,a.ADDRESS_CASES,a.verify_address_trace)):
            for n,c in cases.items():
                raw=(root/n/'TRACE.BIN').read_bytes()
                for i in range(len(raw)):
                    changed=bytearray(raw);changed[i]^=1
                    with self.assertRaises(AssertionError,msg=(n,i)):check(changed,c)
    def test_right_fac_is_destination_residue(self):
        for n in ('bm-underflow-80','bz-left-zero-ff'):
            c=a.CASES[n];raw=bytearray((a.DEFAULT/n/'TRACE.BIN').read_bytes());self.assertEqual(raw[58:62].hex(),c['fac'][:6]+'00');raw[58:62]=bytes.fromhex(c['left'][:6]+'00')
            with self.assertRaises(AssertionError):a.verify_trace(raw,c)
    def test_addition_cannot_replace_division(self):
        n='bm-fraction-80';c=dict(a.CASES[n],op=0x85);raw=bytearray((a.DEFAULT/n/'TRACE.BIN').read_bytes());raw[32:34]=(0x85).to_bytes(2,'little')
        with self.assertRaises(AssertionError):a.context.verify_trace(raw,c)
        with self.assertRaises(AssertionError):a.verify_trace(raw,c)
    def test_resolver_only_never_becomes_arithmetic(self):
        n='address-bm-wrap-01';c=dict(a.ADDRESS_CASES[n],kind='full');raw=(a.ADDRESS_DEFAULT/n/'TRACE.BIN').read_bytes()
        with self.assertRaises(AssertionError):a.verify_address_trace(raw,c)
        self.assertEqual(int.from_bytes(raw[32:34],'little'),0)
    def test_no_static_inline_callers_are_invented(self):
        self.assertEqual(a.verify_static((a.ROOT/'archive/dos-original/BRUN30.EXE').read_bytes()),[])
    def test_inline8d_dispatch_is_required(self):
        raw=bytearray((a.ROOT/'archive/dos-original/BRUN30.EXE').read_bytes());raw[0x58d+2*0x8d]^=1
        with self.assertRaises(AssertionError):a.verify_static(raw)
    def test_selector_is_consumed_in_error_address(self):
        for n in ('bm-positive-overflow-80','pad16-positive-overflow'):
            c=a.CASES[n];raw=(a.DEFAULT/n/'TRACE.BIN').read_bytes();at=a.context.error_address(c);bad=raw.replace(at.encode(),f'{int(at,16)-1:04X}'.encode())
            with self.assertRaises(AssertionError):a.verify_trace(bad,c)
    def test_padding_not_confused_with_saved_module_bp(self):
        for n in ('pad16-underflow','pad32-positive-overflow'):
            with self.assertRaises(AssertionError):a.verify_trace((a.DEFAULT/n/'TRACE.BIN').read_bytes(),dict(a.CASES[n],pad=0))
    def test_error_is_not_fabricated_return_or_shell_success(self):
        n='bm-positive-overflow-ff';c=a.CASES[n];raw=(a.DEFAULT/n/'TRACE.BIN').read_bytes()
        for bad in (raw[:46]+bytes(29)+b'END!',raw[:-1],raw.replace(b'\r\n',b'\n')):
            with self.assertRaises(AssertionError):a.verify_trace(bad,c)
        with self.assertRaises(AssertionError):a.verify_trace(raw,dict(c,expect='return'))
    def test_frozen_sources(self):
        for root in (a.DEFAULT,a.ADDRESS_DEFAULT):
            with tempfile.TemporaryDirectory() as d:
                p=Path(d)/'native';shutil.copytree(root,p);next((p/'sources').iterdir()).write_bytes(b'changed')
                with self.assertRaises(AssertionError):a.verify(p if root==a.DEFAULT else a.DEFAULT,address_directory=p if root==a.ADDRESS_DEFAULT else a.ADDRESS_DEFAULT)
    def test_fixture_profiles_cannot_be_swapped(self):
        with tempfile.TemporaryDirectory() as d:
            doc=json.loads(a.FIXTURE.read_text());doc['address_cases'],doc['execution_cases']=doc['execution_cases'],doc['address_cases'];p=Path(d)/'fixture';p.write_text(json.dumps(doc))
            with self.assertRaises(AssertionError):a.verify(fixture=p)
    def test_distinct_errors_and_zero_precedence(self):
        for n,error,label in (('bm-both-zero-80','division_by_zero',b'Division by zero'),('bz-right-zero-ff','division_by_zero',b'Division by zero'),('pad16-positive-overflow','overflow',b'Overflow')):
            c=a.CASES[n];raw=(a.DEFAULT/n/'TRACE.BIN').read_bytes();self.assertEqual(a.verify_trace(raw,c)['error'],error)
            with self.assertRaises(AssertionError):a.verify_trace(raw.replace(label,b'Other error'),c)
            with self.assertRaises(AssertionError):a.verify_trace(raw,dict(c,expect='overflow' if error=='division_by_zero' else 'division_by_zero'))
    def test_operand_order_is_required(self):
        c=a.CASES['bm-fraction-80'];raw=bytearray((a.DEFAULT/'bm-fraction-80'/'TRACE.BIN').read_bytes());raw[58:62]=(a.DEFAULT/'bm-reverse-80'/'TRACE.BIN').read_bytes()[58:62]
        with self.assertRaises(AssertionError):a.verify_trace(raw,c)
    def test_division_full_protocol_cannot_use_address_only_validator(self):
        c=dict(next(iter(a.ADDRESS_CASES.values())),kind='full')
        with self.assertRaises(AssertionError):a.address.expected_payload(c,'divide')
        with self.assertRaises(AssertionError):a.address.verify_trace(b'',c,'divide')
    def test_operation_selection_remains_closed(self):
        c=next(iter(a.ADDRESS_CASES.values()))
        with self.assertRaises(AssertionError):a.address.expected_payload(c,'unqualified')
        with self.assertRaises(AssertionError):a.address.verify_trace(b'',c,'unqualified')

if __name__=='__main__':unittest.main()
