"""Reject precision/profile substitution, wrong address/FAC state and forged errors."""
import json,shutil,tempfile,unittest
from pathlib import Path
import verify_inline_multiply_double as a
import recover_inline_multiply_double as full
import recover_inline_multiply_double_address as address

class InlineDoubleMultiplication(unittest.TestCase):
    def raw(self,n):return (a.DEFAULT/n/'TRACE.BIN').read_bytes()
    def reject(self,n,raw,c=None):
        with self.assertRaises(AssertionError):a.verify_trace(bytes(raw),a.CASES[n] if c is None else c)
    def test_complete(self):
        d=a.verify();self.assertEqual(len(d['address_cases']),15);self.assertEqual(len(d['execution_cases']),138);self.assertEqual(sum(c['output']is None for c in d['execution_cases']),10)
    def test_independent_payloads(self):
        for writer,cases in ((full,a.CASES),(address,a.ADDRESS_CASES)):
            self.assertEqual(writer.cases(),cases)
            for c in cases.values():self.assertEqual(writer.payload(c),a.expected_payload(c))
    def test_every_trace_byte(self):
        for root,cases in ((a.DEFAULT,a.CASES),(a.ADDRESS_DEFAULT,a.ADDRESS_CASES)):
            for n,c in cases.items():
                raw=(root/n/'TRACE.BIN').read_bytes()
                for i in range(len(raw)):
                    bad=bytearray(raw);bad[i]^=1
                    with self.assertRaises(AssertionError,msg=(n,i)):a.verify_trace(bad,c)
    def test_all_seven_fac_residue_bytes(self):
        for n in ('bm-left-zero-80','bz-flush-before-round-8a','pad16-flush-before-round'):
            c=a.CASES[n];raw=bytearray(self.raw(n));self.assertEqual(raw[66:74].hex(),c['fac'][:14]+'00')
            bad=raw.copy();bad[66:74]=bytes(8);self.reject(n,bad)
            for i in range(7):
                bad=raw.copy();bad[66+i]^=1;self.reject(n,bad)
    def test_zero_is_not_operand_selection(self):
        n='bm-left-zero-80';c=a.CASES[n];raw=bytearray(self.raw(n));self.assertEqual(raw[66:74].hex(),c['fac'][:14]+'00')
        for value in (bytes.fromhex(c['left']),bytes.fromhex(c['fac']),bytes(8)):
            bad=raw.copy();bad[66:74]=value;self.reject(n,bad)
    def test_low_bits_beyond_float64(self):
        n='bm-tie111-1-80';raw=bytearray(self.raw(n));self.assertEqual(raw[66:74].hex(),'0200000000004081');raw[66:74]=bytes.fromhex('0000000000004081');self.reject(n,raw)
    def test_pre_round_underflow_is_not_binade_carry(self):
        n='bm-flush-before-round-80';raw=bytearray(self.raw(n));raw[66:74]=bytes.fromhex('0000000000000001');self.reject(n,raw)
    def test_no_normal_inline_callers_are_invented(self):
        calls=a.verify_static((a.ROOT/'archive/dos-original/BRUN30.EXE').read_bytes());self.assertEqual(calls,[])
        self.assertFalse(any((c['base10'],c['base12'])==(0x7e00,0x08c3) for c in a.ADDRESS_CASES.values()))
    def test_dispatch_and_post_resolver_fac_mapping(self):
        original=(a.ROOT/'archive/dos-original/BRUN30.EXE').read_bytes()
        for at in (0x58d+2*0x96,0xb140,0xb143,0xb148):
            bad=bytearray(original);bad[at]^=1
            with self.assertRaises(AssertionError):a.verify_static(bad)
    def test_consumed_selector_continuation(self):
        for n,at in (('bm-round-overflow-80','01C4'),('pad16-round-overflow','01C7')):
            c=a.CASES[n];raw=self.raw(n);self.assertEqual(a.error_address(c),at);self.reject(n,raw.replace(at.encode(),f'{int(at,16)-1:04X}'.encode()))
    def test_padding_is_not_original_module_bp(self):
        for n in ('pad16-flush-before-round','pad32-round-overflow'):self.reject(n,self.raw(n),dict(a.CASES[n],pad=0))
    def test_resolver_only_never_claims_full_reads(self):
        n='address-bm-wrap-01';c=a.ADDRESS_CASES[n];raw=(a.ADDRESS_DEFAULT/n/'TRACE.BIN').read_bytes();self.assertEqual(int.from_bytes(raw[40:42],'little'),0)
        with self.assertRaises(AssertionError):a.verify_trace(raw,dict(c,kind='full',op=0x96,expect='return'))
        with self.assertRaises(AssertionError):address.payload(dict(c,kind='full'))
    def test_single_protocols_cannot_replace_double(self):
        import verify_inline_add as single
        import verify_inline_overflow as single_full
        c=next(iter(a.ADDRESS_CASES.values()));raw=(a.ADDRESS_DEFAULT/next(iter(a.ADDRESS_CASES))/'TRACE.BIN').read_bytes()
        with self.assertRaises(AssertionError):single.verify_trace(raw,c)
        n='bm-fraction-80'
        with self.assertRaises(AssertionError):single_full.verify_trace(self.raw(n),a.CASES[n])
        self.reject(n,self.raw(n).replace(b'DMF1',b'IOF1',1))
    def test_full_eight_byte_memory_blocks_are_preserved(self):
        n='bm-raw-align-80';raw=bytearray(self.raw(n))
        for at in (79,82,86,87,90,94):
            bad=raw.copy();bad[at]^=1;self.reject(n,bad)
    def test_error_is_not_shell_success_or_fabricated_state(self):
        n='bm-round-overflow-8a';raw=self.raw(n)
        for bad in (raw[:54]+bytes(41)+b'END!',raw[:-1],raw.replace(b'\r\n',b'\n')):self.reject(n,bad)
        self.reject(n,raw,dict(a.CASES[n],expect='return'))
    def test_frozen_sources_and_profiles(self):
        for root in (a.DEFAULT,a.ADDRESS_DEFAULT):
            with tempfile.TemporaryDirectory() as d:
                p=Path(d)/'native';shutil.copytree(root,p);next((p/'sources').iterdir()).write_bytes(b'changed')
                with self.assertRaises(AssertionError):a.verify(p if root==a.DEFAULT else a.DEFAULT,address_directory=p if root==a.ADDRESS_DEFAULT else a.ADDRESS_DEFAULT)
        with tempfile.TemporaryDirectory() as d:
            doc=json.loads(a.FIXTURE.read_text());doc['address_cases'],doc['execution_cases']=doc['execution_cases'],doc['address_cases'];p=Path(d)/'fixture';p.write_text(json.dumps(doc))
            with self.assertRaises(AssertionError):a.verify(fixture=p)
    def test_closed_operation_selection(self):
        n='bm-fraction-80';raw=self.raw(n)
        for op in (0x86,0x90,0x92,0x95,0x9e,0xff):
            c=dict(a.CASES[n],op=op);bad=bytearray(raw);bad[40:42]=op.to_bytes(2,'little');self.reject(n,bad,c)
            with self.assertRaises(AssertionError):a.expected_payload(c)
    def test_default_error_hook_and_route_boundary(self):
        n='bm-round-overflow-80';raw=bytearray(self.raw(n))
        for at in (42,44,48):
            bad=raw.copy();bad[at]^=1;self.reject(n,bad)

    def test_raw_ties_sticky_and_product_sign(self):
        for n in ('bm-tie111-1-80','bz-tie112-6-8a','bm-sticky111--1-80','bz-sticky112-1-8a','bm-one-negative-80','bz-both-negative-8a'):
            bad=bytearray(self.raw(n));bad[66]^=1;self.reject(n,bad)
            bad=bytearray(self.raw(n));bad[72]^=128;self.reject(n,bad)

if __name__=='__main__':unittest.main()
