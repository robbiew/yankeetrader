"""Rehashed corruptions must fail semantic checks, not merely file hashes."""
import gzip,hashlib,importlib.util,json,re,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/'research/yt-xannor-revenge'
spec=importlib.util.spec_from_file_location('mbf',ROOT/'archive/analysis/yt-maint/experiments.py');mbf=importlib.util.module_from_spec(spec);spec.loader.exec_module(mbf)
sha=lambda b:hashlib.sha256(b).hexdigest()


class SemanticControls(unittest.TestCase):
    def test_rehashed_corruption(self):
        controls=[
            ('dos','revenge-active','after',[(72,105,2)],'pointer consumption'),
            ('dos','ordinary-cloak-1','after',[(2,125,1)],'cloak decay'),
            ('dos','ordinary','after',[(1165,81,1000001)],'target-only force conservation'),
            ('dos','revenge-top-other','override',[],'top vs revenge override'),
            ('dos','revenge-arrival-cloak-10','attack',[],'revenge bypassed interception cloak'),
            ('dos','revenge-next-day','before',[(2,125,1)],'undeclared setup or broken world chain'),
            ('dos','ordinary','clock',[],'DOS time mismatch'),
            ('dos','revenge-arrival-cloak-0','mail',[],'private battle recipient attribution'),
            ('queue','xannor-hq-win','after',[(72,105,0)],'HQ revenge producer'),
            ('queue','xannor-hq-win','exit',[],'Returning to Yankee Trader Local Logon Program'),
        ]
        with tempfile.TemporaryDirectory(prefix='yt-revenge-negative-')as temp:
            root=Path(temp)
            for scope in('dos','queue'):shutil.copytree(SOURCE/scope,root/scope)
            for scope,name,kind,patches,reason in controls:
                with self.subTest(case=name,kind=kind):
                    evidence=root/scope;d=evidence/name
                    manifest=json.loads((SOURCE/scope/'results.json').read_text())
                    result=json.loads((d/'result.json').read_text())
                    if kind in('before','after'):
                        file=kind+'.dat.gz';data=bytearray(gzip.decompress((d/file).read_bytes()))
                        for record,offset,value in patches:mbf.put(data,record,offset,value)
                        result[kind+'_sha256']=sha(data);(d/file).write_bytes(gzip.compress(data,mtime=0))
                    elif kind=='clock':
                        file='DOSTIME.LOG';text=(d/file).read_text();(d/file).write_text(re.sub(r'Current time: [^\n]+','Current time: 01:00:00.00am',text))
                    elif kind=='mail':
                        file='sidefiles.json';side=json.loads((d/file).read_text());raw=bytearray.fromhex(side['YTRMSG.DAT']['hex']);mbf.put(raw,1,4,3)
                        side['YTRMSG.DAT']['hex']=raw.hex();side['YTRMSG.DAT']['after_sha256']=sha(raw);(d/file).write_text(json.dumps(side,indent=2)+'\n')
                    else:
                        file='transcript.txt';text=(d/file).read_text()
                        if kind=='override':
                            needle='from sector 216 to sector  260';assert needle in text;text=text.replace(needle,'from sector 216 to sector  250')
                        elif kind=='attack':text+='\nQ : lost 100, dstrd 1 (Xannor Lost)\n'
                        else:text=text.replace('Returning to Yankee Trader Local Logon Program...','EXIT REMOVED')
                        (d/file).write_text(text)
                    result['files'][file]=sha((d/file).read_bytes());(d/'result.json').write_text(json.dumps(result,indent=2)+'\n')
                    manifest['scenarios']=[result if c['name']==name else c for c in manifest['scenarios']]
                    (evidence/'results.json').write_text(json.dumps(manifest,indent=2)+'\n')
                    proc=subprocess.run([sys.executable,str(ROOT/'scripts/verify_xannor_revenge.py'),'--evidence',str(root/'dos'),'--queue-evidence',str(root/'queue')],capture_output=True,text=True,timeout=15)
                    try:
                        self.assertNotEqual(proc.returncode,0,proc.stdout)
                        self.assertIn('AssertionError',proc.stderr)
                        self.assertIn(reason,proc.stderr)
                    finally:
                        shutil.rmtree(d);shutil.copytree(SOURCE/scope/name,d)
                        shutil.copy2(SOURCE/scope/'results.json',evidence/'results.json')


if __name__=='__main__':unittest.main()
