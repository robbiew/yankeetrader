"""Rehashed semantic corruptions must be rejected by the evidence verifier."""
import gzip,hashlib,importlib.util,json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/'research/yt-maintenance-lottery'
spec=importlib.util.spec_from_file_location('mbf',ROOT/'archive/analysis/yt-maint/experiments.py');mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)
sha=lambda b:hashlib.sha256(b).hexdigest()


class SemanticControls(unittest.TestCase):
    def test_rehashed_corruptions(self):
        controls=[
            ('inactive-age-14-death-1','after',[(2,85,2)],'name activation'),
            ('inactive-age-13-death-1','after',[(2,85,0)],'name activation'),
            ('inactive-age-14-death-1','after',[(4053,73,2)],'planet release'),
            ('inactive-age-14-death-1','after',[(52,77,3)],'roster vs captain'),
            ('lottery-dirty-free-slots','after',[(4096,129,0)],'reused slot retention'),
            ('inactive-port-deleted','after',[(3053,97,0)],'ordinary port title/treasury'),
            ('lottery-dirty-free-slots','after',[(4096,41,298)],'reused slot retention'),
            ('lottery-all-clock-0','occupied',[],'occupied lottery destination'),
            ('inactive-age-14-death-1','radio',[],'radio compression/deletion order'),
            ('inactive-deleted-next-day','aux-chain',[],'broken auxiliary provenance/chain'),
            ('lottery-next-day','before',[(4096,129,0)],'undeclared mutation or broken world chain'),
        ]
        with tempfile.TemporaryDirectory(prefix='yt-maint-negative-')as temp:
            root=Path(temp)/'research';shutil.copytree(SOURCE,root)
            for name,kind,patches,reason in controls:
                with self.subTest(case=name,kind=kind):
                    d=root/'dos'/name;c=json.loads((d/'result.json').read_text())
                    if kind in('before','after'):
                        file=kind+'.dat.gz';data=bytearray(gzip.decompress((d/file).read_bytes()))
                        for r,o,v in patches:mbf.put(data,r,o,v)
                        (d/file).write_bytes(gzip.compress(data,mtime=0));c[kind+'_sha256']=sha(data)
                    elif kind=='occupied':
                        file='after.dat.gz';data=bytearray(gzip.decompress((d/file).read_bytes()))
                        mbf.put(data,2216,93,0);mbf.put(data,1165,93,45)
                        (d/file).write_bytes(gzip.compress(data,mtime=0));c['after_sha256']=sha(data)
                        side=json.loads((d/'sidefiles.json').read_text());raw=bytes.fromhex(side['YTRMSG.DAT']['hex']).replace(b'2165',b'1114')
                        side['YTRMSG.DAT']['hex']=raw.hex();side['YTRMSG.DAT']['after_sha256']=sha(raw)
                        (d/'sidefiles.json').write_text(json.dumps(side,indent=2)+'\n')
                        c['files']['sidefiles.json']=sha((d/'sidefiles.json').read_bytes())
                    elif kind=='radio':
                        file='sidefiles.json';side=json.loads((d/file).read_text());raw=bytearray.fromhex(side['YTRMSG.DAT']['hex']);mbf.put(raw,1,0,1)
                        side['YTRMSG.DAT']['hex']=raw.hex();side['YTRMSG.DAT']['after_sha256']=sha(raw)
                        (d/file).write_text(json.dumps(side,indent=2)+'\n')
                    else:
                        file='side-before.json';side=json.loads((d/file).read_text());raw=bytearray.fromhex(side['YTRMSG.DAT']);mbf.put(raw,1,0,1);side['YTRMSG.DAT']=raw.hex()
                        (d/file).write_text(json.dumps(side,indent=2)+'\n')
                    c['files'][file]=sha((d/file).read_bytes());(d/'result.json').write_text(json.dumps(c,indent=2)+'\n')
                    manifest=json.loads((root/'dos/results.json').read_text());manifest['scenarios']=[c if row['name']==name else row for row in manifest['scenarios']]
                    (root/'dos/results.json').write_text(json.dumps(manifest,indent=2)+'\n')
                    try:
                        proc=subprocess.run([sys.executable,str(ROOT/'scripts/verify_maintenance_lottery.py'),'--research',str(root)],capture_output=True,text=True,timeout=15)
                        self.assertNotEqual(proc.returncode,0,proc.stdout)
                        self.assertIn('AssertionError',proc.stderr)
                        self.assertIn(reason,proc.stderr)
                    finally:
                        shutil.rmtree(d);shutil.copytree(SOURCE/'dos'/name,d)
                        shutil.copy2(SOURCE/'dos/results.json',root/'dos/results.json')


if __name__=='__main__':unittest.main()
