"""Direct DOUBLE flags, four-word ordering, actual Jcc and provenance controls."""
import copy,json,tempfile,unittest
from pathlib import Path
import verify_double_compare as v
import recover_double_compare as writer

class DoubleCompare(unittest.TestCase):
    def test_complete_native(self):
        d=v.verify();self.assertEqual(len(d['cases']),486)
        self.assertEqual({op:sum(c['op']==op for c in d['cases'])for op in (160,162,164)},{160:162,162:162,164:162})
    def test_independent_payload_and_relocation_admission(self):
        self.assertEqual(writer.cases(),v.CASES)
        import struct
        original=(v.ROOT/'archive/dos-original/YT-INIT.EXE').read_bytes();table=struct.unpack_from('<H',original,24)[0]
        for c in v.CASES.values():
            stub=v.expected_payload(c);self.assertEqual(writer.payload(c),stub)
            for i in range(struct.unpack_from('<H',original,6)[0]):
                off,seg=struct.unpack_from('<HH',original,table+4*i);at=16*seg+off
                self.assertTrue(all(not(at<end and at+2>start)for start,end in ((0x3a,0x3f),(0x6d,0x6d+len(stub)))))
    def test_every_branch_and_defined_flag_bit(self):
        for n,c in v.CASES.items():
            raw=(v.DEFAULT/n/'TRACE.BIN').read_bytes()
            for pos in range(46,62):
                bad=bytearray(raw);bad[pos]^=1
                with self.assertRaises(AssertionError):v.verify_trace(bad,c)
            for bit in (1,4,64,128,2048,1024):
                bad=bytearray(raw);f=int.from_bytes(bad[44:46],'little')^bit;bad[44:46]=f.to_bytes(2,'little')
                with self.assertRaises(AssertionError):v.verify_trace(bad,c)
    def test_undefined_af_is_not_predicted(self):
        c=v.CASES['opa0-zeros'];raw=bytearray((v.DEFAULT/'opa0-zeros'/'TRACE.BIN').read_bytes());raw[44]^=16
        v.verify_trace(raw,c)
    def test_observation_integrity_includes_unpredicted_bits(self):
        # A complete hardlink copy saves disk; replace the tested file before writing.
        import shutil,os
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'native';shutil.copytree(v.DEFAULT,p,copy_function=os.link)
            trace=p/'opa0-zeros'/'TRACE.BIN';raw=bytearray(trace.read_bytes());raw[44]^=16;trace.unlink();trace.write_bytes(raw)
            with self.assertRaisesRegex(AssertionError,'immutable observed artifact'):v.verify(p,fixture=None)
    def test_inputs_abi_rng_and_frame_corruption(self):
        n='opa0-full-equal';c=v.CASES[n];raw=(v.DEFAULT/n/'TRACE.BIN').read_bytes()
        for pos in list(range(36))+list(range(46,113)):
            bad=bytearray(raw);bad[pos]^=1
            with self.assertRaises(AssertionError):v.verify_trace(bad,c)
    def test_initial_flags_and_direction_admission(self):
        for n in ('opa0-zeros','seeded-opa2-full-equal'):
            c=v.CASES[n];raw=(v.DEFAULT/n/'TRACE.BIN').read_bytes()
            for bit in (1,4,16,64,128,1024,2048):
                bad=bytearray(raw);bad[42:44]=(int.from_bytes(raw[42:44],'little')^bit).to_bytes(2,'little')
                with self.assertRaises(AssertionError):v.verify_trace(bad,c)
    def test_no_unadmitted_opcode_or_fac_binding(self):
        c=v.CASES['opa0-zeros'];raw=(v.DEFAULT/'opa0-zeros'/'TRACE.BIN').read_bytes()
        for op in (159,161,163,165,166):
            with self.assertRaises(AssertionError):v.verify_trace(raw,dict(c,op=op))
        for op in (162,164):
            c=dict(v.CASES[f'op{op:02x}-one-equal']);c['fac']='ffffffffffffffff'
            with self.assertRaises(AssertionError):v.verify_trace(raw,c)
    def test_low_words_drive_flags_and_precedence(self):
        for offset in range(3):
            for sign in (0,128):
                c=v.CASES[f'opa0-word{offset}-signed-{sign}-0'];flags=v.flags_for(bytes.fromhex(c['left']),bytes.fromhex(c['right']))
                self.assertEqual(bool(flags&1),sign==0);self.assertTrue(flags&2048)
        for offset in (1,2,3):
            c=v.CASES[f'opa0-word{offset}-precedence-0-0']
            # In word1-precedence, the untouched word2 is ffff versus 0000:
            # it wins before the nominated word1. Preserve that first outcome.
            self.assertEqual(bool(v.flags_for(bytes.fromhex(c['left']),bytes.fromhex(c['right']))&1),offset!=1)
    def test_seeds_and_entry_bindings_do_not_change_flags(self):
        for n,c in v.CASES.items():
            if n.startswith('seeded-'):
                base=n[7:];a=v.verify_trace((v.DEFAULT/n/'TRACE.BIN').read_bytes(),c);b=v.verify_trace((v.DEFAULT/base/'TRACE.BIN').read_bytes(),v.CASES[base]);self.assertEqual(a,b)
        for n,c in v.CASES.items():
            if n.startswith('opa0-'):
                want=v.verify_trace((v.DEFAULT/n/'TRACE.BIN').read_bytes(),c)
                for op in ('a2','a4'):
                    name='op'+op+n[4:];self.assertEqual(v.verify_trace((v.DEFAULT/name/'TRACE.BIN').read_bytes(),v.CASES[name]),want)
    def test_portable_fixture_cannot_drop_cases(self):
        d=json.loads(v.FIXTURE.read_text());d['cases'].pop()
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'fixture.json';p.write_text(json.dumps(d))
            with self.assertRaisesRegex(AssertionError,'portable fixture'):v.verify(fixture=p)

if __name__=='__main__':unittest.main()
