"""Independent loss-receipt, surviving-stock and exact handoff regressions."""
import copy,gzip,json,shutil,tempfile,unittest
from pathlib import Path
import verify_maintenance_defender_stock as v

class DefenderStockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary=v.verify();cls.observer=(v.DEFAULT/'sources/observe_maintenance_departure.js').read_text()
        cls.rows={}
        for case in v.CASES:
            for stage in v.STAGES:
                folder=v.DEFAULT/case/stage/'unobserved-a'
                cls.rows[case,stage]=({n:gzip.decompress((folder/('before-'+n+'.gz')).read_bytes())for n in v.FILES},
                  {n:gzip.decompress((folder/('after-'+n+'.gz')).read_bytes())for n in v.FILES},(folder/'TRACE.BIN').read_bytes())

    def qualify(self,mutate,case='one-versus-37-whole',stage='child-1'):
        stats=copy.deepcopy(self.summary[case][stage]);before,after,trace=copy.deepcopy(self.rows[case,stage]);stats,before,after,trace=mutate(stats,before,after,trace)
        with self.assertRaises(AssertionError):v.qualify(case,stage,stats,before,after,trace)

    def test_all_eight_stages_are_six_mode_equal(self):
        self.assertEqual(len(self.summary),4)
        self.assertTrue(all(s['paired']['equal']for stages in self.summary.values()for s in stages.values()))

    def test_balanced_defender_survives_with_one_fighter(self):
        self.assertEqual(self.summary['balanced-37-whole']['child-1']['gateway_defenders'],1)
        self.assertEqual(self.summary['37-versus-1000-whole']['child-1']['gateway_defenders'],964)

    def test_next_day_stock_is_produced_without_pickup(self):
        self.assertEqual(self.summary['one-versus-37-whole']['child-2']['saved_stock'],'40')
        self.assertEqual(self.summary['one-versus-37-empty']['child-2']['saved_stock'],'3')

    def test_wrong_winner_is_rejected(self):
        def mutate(s,b,a,t):s['offenses'][0]['won']=True;return s,b,a,t
        self.qualify(mutate)

    def test_wrong_defender_survivor_is_rejected(self):
        def mutate(s,b,a,t):s['gateway_defenders']-=1;return s,b,a,t
        self.qualify(mutate)

    def test_resurrected_attacker_is_rejected(self):
        def mutate(s,b,a,t):s['physical'][-2]=1;return s,b,a,t
        self.qualify(mutate)

    def test_fake_pickup_is_rejected(self):
        def mutate(s,b,a,t):s['pickup']=37;return s,b,a,t
        self.qualify(mutate)

    def test_missing_loss_receipt_is_rejected(self):
        self.qualify(lambda s,b,a,t:(s,b,a,t.replace(b' *** The Mercenaries Lost!',b'')))

    def test_raw_governor_alias_is_rejected(self):
        def mutate(s,b,a,t):
            w=bytearray(a['YTDATA.DAT']);w[4053*137+73:4053*137+77]=bytes.fromhex('aabbcc00');a['YTDATA.DAT']=bytes(w);return s,b,a,t
        self.qualify(mutate)

    def test_empty_stock_cannot_be_replaced_by_pickup_clear_zero(self):
        def mutate(s,b,a,t):
            w=bytearray(a['YTDATA.DAT']);w[4053*137+129:4053*137+133]=bytes.fromhex('00008000');a['YTDATA.DAT']=bytes(w);return s,b,a,t
        self.qualify(mutate,case='one-versus-37-empty')

    def test_next_day_cannot_invent_an_activation(self):
        def mutate(s,b,a,t):s['activations'].append(dict(force=1,sector=2368));return s,b,a,t
        self.qualify(mutate,stage='child-2')

    def corrupt(self,mutation,stage='child-1'):
        case='one-versus-37-whole';mode='observed-a'
        with tempfile.TemporaryDirectory()as tmp:
            folder=Path(tmp)/mode;shutil.copytree(v.DEFAULT/case/stage/mode,folder)
            meta=json.loads((folder/'capture.json').read_text());mutation(folder,meta)
            meta['files']={name:v.SHA((folder/name).read_bytes())for name in meta['files']};(folder/'capture.json').write_text(json.dumps(meta))
            prior=None
            if stage=='child-2':prior={n:gzip.decompress((v.DEFAULT/case/'child-1'/mode/('after-'+n+'.gz')).read_bytes())for n in v.FILES}
            with self.assertRaises((AssertionError,ValueError,KeyError)):v.verify_case(folder,case,mode,self.observer,stage,prior)

    def test_rehashed_command_substitution_is_rejected(self):self.corrupt(lambda f,m:(f/'COMMANDS.TXT').write_text('ytmaint\n'))
    def test_rehashed_observer_substitution_is_rejected(self):self.corrupt(lambda f,m:(f/'loaded-observer.js').write_text('substitute'))
    def test_changed_clock_is_rejected(self):self.corrupt(lambda f,m:m.update(clock='00:00:04'))
    def test_second_day_cannot_claim_another_fixture(self):self.corrupt(lambda f,m:m.update(applied_fixture=True),stage='child-2')

    def test_rehashed_second_day_sidefile_repair_is_rejected(self):
        def mutation(f,m):
            raw=b'invented journal';(f/'before-YTNEWS.DAT.gz').write_bytes(gzip.compress(raw,mtime=0));m['inputs']['YTNEWS.DAT']=v.SHA(raw)
        self.corrupt(mutation,stage='child-2')

    def test_changed_manifest_is_rejected(self):
        with tempfile.TemporaryDirectory()as tmp:
            (Path(tmp)/'pins.json').write_text('{}')
            with self.assertRaises(AssertionError):v.verify(tmp)

if __name__=='__main__':unittest.main()
