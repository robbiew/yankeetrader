import copy,hashlib,json,os,subprocess,tempfile,unittest
from pathlib import Path
import export_chain_cli_recipes as e

class ChainCLI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.root=Path(cls.tmp.name);cls.binary=cls.root/'qbmaint-replay'
        env=dict(os.environ);env.setdefault('GOCACHE',str(cls.root/'go-cache'))
        subprocess.run(['go','build','-o',str(cls.binary),'./cmd/qbmaint-replay'],cwd=e.ROOT,env=env,check=True)
        cls.rows=e.build();cls.export=cls.root/'recipes';assert e.export(cls.export)==3
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def invoke(self,folder,out,source=None):
        return subprocess.run([str(self.binary),'-recipe',str(folder/'recipe.json'),'-before',str(folder/'before'),'-source-root',str(source or e.ROOT),'-out',str(out)],capture_output=True,text=True)
    def test_all_three_complete_chains_and_receipts(self):
        for row in self.rows:
            folder=self.export/row['name'];out=self.root/('output-'+row['name'])
            before={n:p.read_bytes()for n,p in ((n,folder/'before'/n)for n in row['before'])}
            # Oracles are comparison-side only, not a declared source or input.
            (folder/'oracles.json').write_text('poisoned comparison side file')
            run=self.invoke(folder,out);self.assertEqual(run.returncode,0,run.stderr)
            receipt=json.loads((out/'replay/receipt.json').read_text())
            self.assertEqual(receipt['format'],'qbmaint-receipt-v2');self.assertEqual(receipt['profile'],'convergence-three-day')
            self.assertEqual(receipt['state_evidence'],'modeled-not-native-endpoint');self.assertEqual(len(receipt['days']),3)
            self.assertEqual(len(receipt['output_sha256']),18)
            self.assertEqual(receipt['recipe_sha256'],e.SHA((folder/'recipe.json').read_bytes()))
            self.assertEqual(receipt['source_sha256'],row['recipe']['source_sha256'])
            total=0
            for i,oracle in enumerate(row['oracles'],1):
                for name,sha in oracle['files'].items():
                    path=f'day-{i}/{name}'
                    self.assertEqual(e.SHA((out/'replay'/path).read_bytes()),sha)
                    self.assertEqual(receipt['output_sha256'][path],sha)
                day=receipt['days'][i-1];self.assertEqual(day['day'],305+i)
                self.assertEqual(day['initial_state'],row['recipe']['days'][i-1]['initial_state'])
                self.assertEqual(day['final_state'],oracle['final_state']);self.assertEqual(day['draws'],oracle['draws']);total+=day['draws']
                if i>1:self.assertEqual((out/f'replay/day-{i}/YTYNEWS.DAT').read_bytes(),(out/f'replay/day-{i-1}/YTNEWS.DAT').read_bytes())
            self.assertEqual(receipt['draws'],total);self.assertEqual(receipt['final_state'],row['oracles'][-1]['final_state'])
            snapshot={str(p.relative_to(out)):p.read_bytes()for p in out.rglob('*')if p.is_file()}
            self.assertEqual(len(snapshot),19)
            again=self.invoke(folder,out);self.assertNotEqual(again.returncode,0)
            self.assertEqual(snapshot,{str(p.relative_to(out)):p.read_bytes()for p in out.rglob('*')if p.is_file()})
            self.assertEqual(before,{n:(folder/'before'/n).read_bytes()for n in before})
    def test_late_and_source_failures_publish_nothing(self):
        row=self.rows[0]
        for label in ('late-helper','late-report','before-hash','source-hash','unknown-endpoint'):
            folder=self.root/label;folder.mkdir();(folder/'before').mkdir()
            for n,b in row['before'].items():(folder/'before'/n).write_bytes(b)
            recipe=copy.deepcopy(row['recipe'])
            if label=='late-helper':recipe['days'][2]['tail_helpers'][0]['caller']^=1
            if label=='late-report':recipe['days'][2]['aux']['score_clock']='bad'
            if label=='before-hash':(folder/'before/YTNEWS.DAT').write_bytes(b'changed')
            if label=='source-hash':recipe['source_sha256']['scripts/export_chain_cli_recipes.py']='0'*64
            if label=='unknown-endpoint':recipe['days'][2]['final_state']=0
            (folder/'recipe.json').write_text(json.dumps(recipe));out=self.root/('failed-'+label)
            result=self.invoke(folder,out);self.assertNotEqual(result.returncode,0,label);self.assertFalse(out.exists(),label)
        self.assertFalse(list(self.root.glob('.qbmaint-replay-*')))
    def test_export_is_exclusive_and_clock_only(self):
        with self.assertRaises(FileExistsError):e.export(self.export)
        for row in self.rows:
            self.assertEqual(set(row['recipe']),{'format','profile','name','before_sha256','source_sha256','days'})
            for index,day in enumerate(row['recipe']['days']):
                self.assertEqual(set(day),{'day','initial_state','ports','planets','creation','home_helpers','tail_helpers','aux'})
                self.assertEqual(len(day['creation']),1 if index==0 else 0)
            for name,sha in row['recipe']['source_sha256'].items():self.assertEqual(e.SHA((e.ROOT/name).read_bytes()),sha)

if __name__=='__main__':unittest.main()
