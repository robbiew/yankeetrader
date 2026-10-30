"""Rehashed corruptions must fail event semantics rather than only file hashes."""
import gzip,hashlib,importlib.util,json,re,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/'research/yt-plague-civil-war'
spec=importlib.util.spec_from_file_location('mbf',ROOT/'archive/analysis/yt-maint/experiments.py');mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)
sha=lambda b:hashlib.sha256(b).hexdigest()


class SemanticControls(unittest.TestCase):
    def test_rehashed_corruptions(self):
        controls=[
            ('port-total-999999','after',[(3053,61,500000)],'port unchanged rate'),
            ('port-total-1000001','after',[(3053,61,2000000)],'port plague rate'),
            ('port-mixed-cap','after',[(3053,49,10000000)],'port cargo cap/growth'),
            ('port-zero-after-3','after',[(3053,41,3)],'zero-stock stale selection'),
            ('planet-owner-2','after',[(4053,73,0)],'event changed title/name'),
            ('planet-owner-0','after',[(4053,77,101)],'ground damage range'),
            ('planet-owner-0','after',[(4053,117,12000)],'plague bank debit'),
            ('planet-civil-bank-1000000000','after',[(4053,117,1000000000)],'insurrection report/reset'),
            ('planet-stock-cap','after',[(4053,57,1000000000)],'planet warehouse cap'),
            ('planet-owner-0','after',[(4053,129,1000)],'event changed weapon stock'),
            ('planet-next-day','before',[(4053,77,1)],'undeclared setup or broken world chain'),
            ('quiet','native',[],'native bytes'),
            ('planet-order-quiet','stale-log',[],'insurrection report/reset'),
            ('planet-owner-0','ground-log',[],'required ground report'),
            ('planet-same-day','stale-public',[],'missing public event body'),
            ('planet-owner-2','private',[],'unexpected private event'),
        ]
        with tempfile.TemporaryDirectory(prefix='yt-event-negative-')as temp:
            root=Path(temp)/'research';shutil.copytree(SOURCE,root)
            for name,kind,patches,reason in controls:
                with self.subTest(case=name,kind=kind):
                    d=root/'dos'/name;c=json.loads((d/'result.json').read_text())
                    if kind in('before','after'):
                        file=kind+'.dat.gz';data=bytearray(gzip.decompress((d/file).read_bytes()))
                        for r,o,v in patches:mbf.put(data,r,o,v)
                        (d/file).write_bytes(gzip.compress(data,mtime=0));c[kind+'_sha256']=sha(data)
                    elif kind=='native':
                        file=None;path=root/'rea/target-paths.json';data=json.loads(path.read_text())
                        r=data['observations'][0]['evidence']['normalized_result'];raw=bytearray.fromhex(r['bytes_hex']);raw[0]^=1;r['bytes_hex']=raw.hex();path.write_text(json.dumps(data,indent=2)+'\n')
                    elif kind=='ground-log':
                        file='transcript.txt';text=(d/file).read_text();text,count=re.subn(r'  -  Ground forces reduced from[^\n]+\n','',text)
                        assert count==1;(d/file).write_text(text)
                    elif kind=='stale-public':
                        file='sidefiles.json';side=json.loads((d/file).read_text());initial=json.loads((d/'side-before.json').read_text());raw=bytes.fromhex(initial['YTNEWS.DAT'])
                        side['YTNEWS.DAT']['hex']=raw.hex();side['YTNEWS.DAT']['after_sha256']=sha(raw);(d/file).write_text(json.dumps(side,indent=2)+'\n')
                    elif kind=='stale-log':
                        file='transcript.txt';text=(d/file).read_text();needle='  -  771511168 credits were spent putting down the insurrection!'
                        assert text.count(needle)==2;text=text[::-1].replace(needle[::-1],'REMOVED'[::-1],1)[::-1];(d/file).write_text(text)
                    else:
                        file='sidefiles.json';side=json.loads((d/file).read_text());initial=json.loads((d/'side-before.json').read_text())
                        raw=mbf.enc(1)+mbf.enc(2)+mbf.enc(-2)+b'CIVIL WAR'.ljust(72,b' ')+bytes(2)
                        side['YTRMSG.DAT']={'before_sha256':sha(bytes.fromhex(initial['YTRMSG.DAT'])),'after_sha256':sha(raw),'hex':raw.hex()}
                        (d/file).write_text(json.dumps(side,indent=2)+'\n')
                    if file:
                        c['files'][file]=sha((d/file).read_bytes());(d/'result.json').write_text(json.dumps(c,indent=2)+'\n')
                        manifest=json.loads((root/'dos/results.json').read_text());manifest['scenarios']=[c if row['name']==name else row for row in manifest['scenarios']]
                        (root/'dos/results.json').write_text(json.dumps(manifest,indent=2)+'\n')
                    try:
                        proc=subprocess.run([sys.executable,str(ROOT/'scripts/verify_plague_civil_war.py'),'--research',str(root)],capture_output=True,text=True,timeout=15)
                        self.assertNotEqual(proc.returncode,0,proc.stdout)
                        self.assertIn('AssertionError',proc.stderr)
                        self.assertIn(reason,proc.stderr)
                    finally:
                        shutil.rmtree(d);shutil.copytree(SOURCE/'dos'/name,d)
                        shutil.copy2(SOURCE/'dos/results.json',root/'dos/results.json')
                        if kind=='native':shutil.copy2(SOURCE/'rea/target-paths.json',root/'rea/target-paths.json')


if __name__=='__main__':unittest.main()
