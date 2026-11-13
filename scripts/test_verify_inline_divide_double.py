"""Reject precision/profile substitution, wrong address/FAC state and forged errors."""
import json,shutil,tempfile,unittest
from pathlib import Path
import verify_inline_divide_double as a
import recover_inline_divide_double as full
import recover_inline_divide_double_address as address

class InlineDoubleDivision(unittest.TestCase):
    def raw(self,n):return (a.DEFAULT/n/'TRACE.BIN').read_bytes()
    def reject(self,n,raw,c=None):
        with self.assertRaises(AssertionError):a.verify_trace(bytes(raw),a.CASES[n] if c is None else c)
    def test_complete(self):
        d=a.verify();self.assertEqual(len(d['address_cases']),15);self.assertEqual(len(d['execution_cases']),148);self.assertEqual(sum(c['output']is None for c in d['execution_cases']),28)
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
    def test_original_fac_residue_before_staging(self):
        for n in ('bm-left-zero-80','bz-uf0-early-8a','pad16-uf0-early'):
            c=a.CASES[n];raw=bytearray(self.raw(n));self.assertEqual(raw[66:74].hex(),c['fac'][:14]+'00')
            for i in range(7):
                bad=raw.copy();bad[66+i]^=1;self.reject(n,bad)
    def test_late_underflow_uses_shifted_divisor_residue(self):
        for n in ('bm-uf0-late-80','bz-uf1-late-8a','pad16-uf0-late'):
            c=a.CASES[n];raw=bytearray(self.raw(n));want=b'\x00'+bytes.fromhex(c['fac'])[:6]+b'\x00';self.assertEqual(raw[66:74],want)
            for value in (bytes.fromhex(c['fac'][:14]+'00'),bytes(8)):
                bad=raw.copy();bad[66:74]=value;self.reject(n,bad)
    def test_low_bits_beyond_float64(self):
        n='bm-guard55-above-0-80';raw=bytearray(self.raw(n));self.assertEqual(raw[66]&1,1);raw[66]&=248;self.reject(n,raw)
    def test_minimum_normal_countercontrols(self):
        for n in ('bm-uf0-minimum-80','bz-uf2-minimum-8a'):
            raw=bytearray(self.raw(n));self.assertEqual(raw[66:74].hex(),'0000000000000001');raw[73]=0;self.reject(n,raw)
    def test_no_normal_inline_callers_are_invented(self):
        calls=a.verify_static((a.ROOT/'archive/dos-original/BRUN30.EXE').read_bytes());self.assertEqual(calls,[])
        self.assertFalse(any((c['base10'],c['base12'])==(0x7e00,0x08c3) for c in a.ADDRESS_CASES.values()))
    def test_dispatch_and_post_resolver_fac_mapping(self):
        original=(a.ROOT/'archive/dos-original/BRUN30.EXE').read_bytes()
        for at in (0x58d+2*0x8e,0xb18e,0xb191,0xb196):
            bad=bytearray(original);bad[at]^=1
            with self.assertRaises(AssertionError):a.verify_static(bad)
    def test_consumed_selector_continuation(self):
        for n,at in (('bm-max-half-80','01C4'),('pad16-max-half','01C7')):
            c=a.CASES[n];raw=self.raw(n);self.assertEqual(a.error_address(c),at);self.reject(n,raw.replace(at.encode(),f'{int(at,16)-1:04X}'.encode()))
    def test_padding_is_not_original_module_bp(self):
        for n in ('pad16-uf0-late','pad32-max-half'):self.reject(n,self.raw(n),dict(a.CASES[n],pad=0))
    def test_resolver_only_never_claims_full_reads(self):
        n='address-bm-wrap-01';c=a.ADDRESS_CASES[n];raw=(a.ADDRESS_DEFAULT/n/'TRACE.BIN').read_bytes();self.assertEqual(int.from_bytes(raw[40:42],'little'),0)
        with self.assertRaises(AssertionError):a.verify_trace(raw,dict(c,kind='full',op=0x8e,expect='return'))
        with self.assertRaises(AssertionError):address.payload(dict(c,kind='full'))
    def test_single_protocols_cannot_replace_double(self):
        import verify_inline_add as single
        import verify_inline_overflow as single_full
        c=next(iter(a.ADDRESS_CASES.values()));raw=(a.ADDRESS_DEFAULT/next(iter(a.ADDRESS_CASES))/'TRACE.BIN').read_bytes()
        with self.assertRaises(AssertionError):single.verify_trace(raw,c)
        n='bm-three-two-80'
        with self.assertRaises(AssertionError):single_full.verify_trace(self.raw(n),a.CASES[n])
        self.reject(n,self.raw(n).replace(b'DVF1',b'IOF1',1))
    def test_full_eight_byte_memory_blocks_are_preserved(self):
        n='bm-raw-80';raw=bytearray(self.raw(n))
        for at in (79,82,86,87,90,94):
            bad=raw.copy();bad[at]^=1;self.reject(n,bad)
    def test_error_is_not_shell_success_or_fabricated_state(self):
        n='bm-max-half-8a';raw=self.raw(n)
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
        n='bm-three-two-80';raw=self.raw(n)
        for op in (0x88,0x8a,0x8d,0x96,0xff):
            c=dict(a.CASES[n],op=op);bad=bytearray(raw);bad[40:42]=op.to_bytes(2,'little');self.reject(n,bad,c)
            with self.assertRaises(AssertionError):a.expected_payload(c)
    def test_default_error_hook_and_route_boundary(self):
        n='bm-max-half-80';raw=bytearray(self.raw(n))
        for at in (42,44,48):
            bad=raw.copy();bad[at]^=1;self.reject(n,bad)

    def test_divisor_zero_priority_and_distinct_error_kind(self):
        for n in ('bm-both-zero-80','bz-aliases-8a','pad16-both-zero'):
            raw=self.raw(n);self.assertIn(b'Division by zero',raw)
            self.reject(n,raw.replace(b'Division by zero',b'Overflow'))
            self.reject(n,raw,dict(a.CASES[n],expect='return'))
    def test_operand_order_guard_brackets_and_signs(self):
        for n in ('bm-one-three-80','bz-raw-reversed-8a','bm-guard55-below-1-80','bz-guard56-above-0-8a','bm-negative-right-80','bz-both-negative-8a'):
            c=a.CASES[n];raw=self.raw(n);left,fac=bytes.fromhex(c['left']),bytes.fromhex(c['fac'])
            wrong=a.arithmetic.expected_entry(fac,left,fac)
            if isinstance(wrong,bytes) and wrong!=raw[66:74]:
                bad=bytearray(raw);bad[66:74]=wrong;self.reject(n,bad)
            bad=bytearray(raw);bad[66]^=1;self.reject(n,bad)

if __name__=='__main__':unittest.main()
