import copy,json,os,subprocess,tempfile,unittest
from pathlib import Path
import export_occupied_cli_recipes as e
class OccupiedCLI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.root=Path(cls.tmp.name);cls.binary=cls.root/'qbmaint-replay'
        env=dict(os.environ);env.setdefault('GOCACHE',str(cls.root/'go-cache'))
        subprocess.run(['go','build','-o',str(cls.binary),'./cmd/qbmaint-replay'],cwd=e.ROOT,env=env,check=True)
        cls.rows=e.build();cls.export=cls.root/'recipes';assert e.export(cls.export)==30
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def invoke(self,folder,out):
        return subprocess.run([str(self.binary),'-recipe',str(folder/'recipe.json'),'-before',str(folder/'before'),'-source-root',str(e.ROOT),'-out',str(out)],capture_output=True,text=True)
    def test_all_thirty_outputs_and_receipts(self):
        events=0
        for row in self.rows:
            folder=self.export/row['name'];out=self.root/('output-'+row['name']);oracle=row['oracle']
            snapshot={n:(folder/'before'/n).read_bytes()for n in row['before']}
            (folder/'oracles.json').write_text('poisoned comparison file')
            run=self.invoke(folder,out);self.assertEqual(run.returncode,0,run.stderr)
            receipt=json.loads((out/'replay/receipt.json').read_text())
            self.assertEqual(receipt['format'],'qbmaint-receipt-v3');self.assertEqual(receipt['profile'],'occupied-day306')
            self.assertEqual(receipt['state_evidence'],'modeled-not-native-endpoint')
            self.assertEqual(receipt['recipe_sha256'],e.SHA((folder/'recipe.json').read_bytes()))
            self.assertEqual(receipt['source_sha256'],row['recipe']['source_sha256'])
            self.assertEqual(receipt['output_sha256'],oracle['files']);self.assertEqual(receipt['final_state'],oracle['final_state']);self.assertEqual(receipt['draws'],oracle['draws'])
            self.assertEqual(receipt['occupied'],dict(combat_events=oracle['combat_events'],faction_scores=oracle['scores'],faction_losses=oracle['losses'],mercenary_activations=oracle['activations'],lottery_candidate=oracle['candidate']))
            events+=receipt['occupied']['combat_events']
            for n,sha in oracle['files'].items():self.assertEqual(e.SHA((out/'replay'/n).read_bytes()),sha)
            self.assertEqual(len(list((out/'replay').iterdir())),7)
            self.assertEqual(snapshot,{n:(folder/'before'/n).read_bytes()for n in snapshot})
            original={p.name:p.read_bytes()for p in(out/'replay').iterdir()};again=self.invoke(folder,out);self.assertNotEqual(again.returncode,0)
            self.assertEqual(original,{p.name:p.read_bytes()for p in(out/'replay').iterdir()})
        self.assertEqual(events,120)
    def test_failures_publish_nothing(self):
        row=next(r for r in self.rows if r['recipe']['recipe']['tail_helpers'])
        for label in ('tail-helper','report','before-hash','source-hash','endpoint'):
            folder=self.root/label;folder.mkdir();(folder/'before').mkdir()
            for n,b in row['before'].items():(folder/'before'/n).write_bytes(b)
            recipe=copy.deepcopy(row['recipe'])
            if label=='tail-helper':recipe['recipe']['tail_helpers'][-1]['caller']^=1
            if label=='report':recipe['recipe']['aux']['score_clock']='bad'
            if label=='before-hash':(folder/'before/YTNEWS.DAT').write_bytes(b'changed')
            if label=='source-hash':recipe['source_sha256']['scripts/export_occupied_cli_recipes.py']='0'*64
            if label=='endpoint':recipe['recipe']['final_state']=0
            (folder/'recipe.json').write_text(json.dumps(recipe));out=self.root/('failed-'+label)
            run=self.invoke(folder,out);self.assertNotEqual(run.returncode,0,label);self.assertFalse(out.exists(),label)
        self.assertFalse(list(self.root.glob('.qbmaint-replay-*')))
    def test_clock_only_export_is_exclusive(self):
        with self.assertRaises(FileExistsError):e.export(self.export)
        for row in self.rows:
            self.assertEqual(set(row['recipe']),{'format','profile','name','before_sha256','source_sha256','recipe'})
            self.assertEqual(set(row['recipe']['recipe']),{'initial_state','ports','planets','creation','routing_helpers','tail_helpers','final_day','aux'})
            for n,h in row['recipe']['source_sha256'].items():self.assertEqual(e.SHA((e.ROOT/n).read_bytes()),h)
if __name__=='__main__':unittest.main()
