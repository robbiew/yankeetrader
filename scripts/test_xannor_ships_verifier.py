"""Rehashed corruptions must fail semantic checks, not just checksum checks."""
import gzip, hashlib, importlib.util, json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/'research/yt-xannor-ships/dos'
spec=importlib.util.spec_from_file_location('mbf',ROOT/'archive/analysis/yt-maint/experiments.py')
mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)
sha=lambda b:hashlib.sha256(b).hexdigest()


class SemanticControls(unittest.TestCase):
    def test_rehashed_corruption(self):
        controls=[
            ('hq-ship','after',[(2,61,999)],'saved fighter casualties'),
            ('weak-ship','after',[(2,53,0)],'DOS exhausted-shield persistence defect'),
            ('kill-assets','after',[(4053,73,0)],'planet title remains'),
            ('kill-team-captain','after',[(52,117,0)],'team removal with stale captain'),
            ('mines-after-loss','after',[(153,129,0)],'post-battle route continuation'),
            ('two-ships','after',[(3,61,999)],'record-order survivor stopping'),
            ('unarmed','after',[(1165,81,102)],'post-victory group conservation'),
            ('strong-next-day','before',[(2,81,1)],'broken exact-world chain'),
            ('strong-ship','message',[],'private casualty delivery'),
        ]
        with tempfile.TemporaryDirectory(prefix='yt-xships-negative-')as tmp:
            evidence=Path(tmp)/'dos';shutil.copytree(SOURCE,evidence)
            for name,kind,patches,reason in controls:
                with self.subTest(case=name,kind=kind):
                    d=evidence/name;shutil.rmtree(d);shutil.copytree(SOURCE/name,d)
                    c=json.loads((d/'result.json').read_text())
                    if kind=='message':
                        file='sidefiles.json';side=json.loads((d/file).read_text())
                        raw=bytearray.fromhex(side['YTRMSG.DAT']['hex'])
                        # Fixed private record header: sender, recipient, cause.
                        raw[4:8]=mbf.enc(3)
                        side['YTRMSG.DAT']['hex']=raw.hex();side['YTRMSG.DAT']['after_sha256']=sha(raw)
                        (d/file).write_text(json.dumps(side,indent=2)+'\n')
                    else:
                        file=kind+'.dat.gz';raw=bytearray(gzip.decompress((d/file).read_bytes()))
                        for r,o,v in patches:mbf.put(raw,r,o,v)
                        c[kind+'_sha256']=sha(raw);(d/file).write_bytes(gzip.compress(raw,mtime=0))
                    c['files'][file]=sha((d/file).read_bytes())
                    (d/'result.json').write_text(json.dumps(c,indent=2)+'\n')
                    manifest=json.loads((SOURCE/'results.json').read_text())
                    manifest['scenarios']=[c if x['name']==name else x for x in manifest['scenarios']]
                    (evidence/'results.json').write_text(json.dumps(manifest,indent=2)+'\n')
                    result=subprocess.run([sys.executable,str(ROOT/'scripts/verify_xannor_ships.py'),'--evidence',str(evidence)],capture_output=True,text=True,timeout=15)
                    try:
                        self.assertNotEqual(result.returncode,0,result.stdout)
                        self.assertIn('AssertionError',result.stderr)
                        self.assertIn(reason,result.stderr)
                    finally:
                        shutil.rmtree(d);shutil.copytree(SOURCE/name,d)

if __name__=='__main__':unittest.main()
