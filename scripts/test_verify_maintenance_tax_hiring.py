"""Native tax/hiring acceptance and independent corruption controls."""
import copy
import gzip
import unittest
import verify_maintenance_tax_hiring as audit


class TaxHiringTests(unittest.TestCase):
    def inputs(self,case='ten-groups',stage='child-1'):
        folder=audit.DEFAULT/case/stage/'unobserved-a'
        before={n:gzip.decompress((folder/('before-'+n+'.gz')).read_bytes())for n in audit.FILES}
        after={n:gzip.decompress((folder/('after-'+n+'.gz')).read_bytes())for n in audit.FILES}
        return before,after,(folder/'TRACE.BIN').read_bytes()

    def test_complete_native_matrix(self):
        rows=audit.verify()
        expected={'one-group':[(10,1,1,90),(9,0,0,81)],'ten-groups':[(100,10,1,900),(90,1,9,810)]}
        for case,stages in expected.items():
            for stage,want in zip(audit.STAGES,stages):
                row=rows[case][stage]
                self.assertEqual(tuple(row[k]for k in('tax','groups','group_size','treasury')),want)

    def test_unexplained_treasury_change_rejected(self):
        before,after,trace=self.inputs();world=bytearray(after['YTDATA.DAT']);at=(3053-1)*137+89
        world[at:at+4]=audit.encode(901);after['YTDATA.DAT']=bytes(world)
        with self.assertRaises(AssertionError):audit.verify_semantics('ten-groups','child-1',before,after,trace)

    def test_zero_residue_normalization_rejected(self):
        before,after,trace=self.inputs();world=bytearray(after['YTDATA.DAT']);at=(3054-1)*137+89
        self.assertNotEqual(world[at:at+4],bytes(4));world[at:at+4]=bytes(4);after['YTDATA.DAT']=bytes(world)
        with self.assertRaises(AssertionError):audit.verify_semantics('ten-groups','child-1',before,after,trace)

    def test_forged_hiring_receipt_rejected(self):
        before,after,trace=self.inputs();changed=trace.replace(b'hired 10 mercenaries',b'hired 11 mercenaries');self.assertNotEqual(changed,trace)
        with self.assertRaises(AssertionError):audit.verify_semantics('ten-groups','child-1',before,after,changed)

    def test_fixture_cannot_change_side_file(self):
        before=audit.fixture_inputs('one-group','unobserved-a');folder=audit.DEFAULT/'one-group/child-1/unobserved-a'
        import json
        edits=json.loads((folder/'capture.json').read_text())['fixture_edits'];before['YTNAME.DAT']+=b'x'
        with self.assertRaises(AssertionError):audit.verify_fixture(before,'one-group','unobserved-a',edits)

    def test_fixture_ledger_cannot_hide_extra_edit(self):
        before=audit.fixture_inputs('one-group','unobserved-a');folder=audit.DEFAULT/'one-group/child-1/unobserved-a'
        import json
        edits=json.loads((folder/'capture.json').read_text())['fixture_edits'];edits.append(copy.deepcopy(edits[0]))
        with self.assertRaises(AssertionError):audit.verify_fixture(before,'one-group','unobserved-a',edits)

if __name__=='__main__':unittest.main()
