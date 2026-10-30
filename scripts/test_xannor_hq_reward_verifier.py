"""Rehashed reward evidence corruptions must fail semantic verification."""
import gzip,hashlib,importlib.util,json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/'research/yt-xannor-hq-reward'
s=importlib.util.spec_from_file_location('mbf',ROOT/'archive/analysis/yt-maint/experiments.py');mbf=importlib.util.module_from_spec(s);s.loader.exec_module(mbf)
sha=lambda b:hashlib.sha256(b).hexdigest()

def read_side(path):return json.loads(gzip.decompress(path.read_bytes()))
def write_side(path,value):path.write_bytes(gzip.compress((json.dumps(value,indent=2)+'\n').encode(),mtime=0))


class SemanticControls(unittest.TestCase):
    def test_rehashed_corruptions(self):
        cases=[
            ('fighter-hq','after',[(2,81,1005)],'credit reward arithmetic/receipt without money'),
            ('fighter-team','after',[(3,81,1000000)],'reward changed another account'),
            ('fighter-hq','after',[(4052,117,250001)],'reward changed planetary bank'),
            ('fighter-hq','after',[(3053,89,1)],'reward changed port treasury'),
            ('fighter-hq','after',[(72,105,3)],'revenge recipient/order'),
            ('fighter-hq','after',[(151,81,1)],'intended victory did not occur'),
            ('fighter-balance-2p30-even','after',[(2,81,1074741888)],'credit reward arithmetic/receipt without money'),
            ('fighter-hq','receipt',[],'reward gate/receipt'),
            ('fighter-hq','stale-public',[],'new public reward announcement'),
            ('restored-hq-repeat','stale-broadcast',[],'fresh three-message broadcast block'),
            ('fighter-away','forged-broadcast',[],'fresh three-message broadcast block'),
            ('fighter-hq','address',[],'broadcast address'),
            ('reconnect-no-repeat','before',[(2,73,1)],'undeclared setup or broken world chain'),
            ('reconnect-no-repeat','parent-side',[],'auxiliary input chain'),
            ('fighter-hq','native',[],'native bytes'),
            ('fighter-mercenary','after',[(2,81,1001005)],'credit reward arithmetic/receipt without money'),
        ]
        with tempfile.TemporaryDirectory(prefix='yt-hq-negative-')as temp:
            root=Path(temp)/'research';shutil.copytree(SOURCE,root)
            for name,kind,patches,reason in cases:
                with self.subTest(name=name,kind=kind):
                    d=root/'dos'/name;c=json.loads((d/'result.json').read_text())
                    if kind in('before','after'):
                        file=kind+'.dat.gz';b=bytearray(gzip.decompress((d/file).read_bytes()))
                        for r,o,v in patches:mbf.put(b,r,o,v)
                        (d/file).write_bytes(gzip.compress(b,mtime=0));c[kind+'_sha256']=sha(b)
                    elif kind=='native':
                        file=None;p=root/'rea/target-paths.json';data=json.loads(p.read_text());r=data['observations'][0]['evidence']['normalized_result'];b=bytearray.fromhex(r['bytes_hex']);b[0]^=1;r['bytes_hex']=b.hex();p.write_text(json.dumps(data,indent=2)+'\n')
                    elif kind=='receipt':
                        file='transcript.txt';text=(d/file).read_text();assert text.count('Collect 1,000,000 credits bonus!')==1;(d/file).write_text(text.replace('Collect 1,000,000 credits bonus!','REMOVED'))
                    elif kind=='parent-side':
                        file='side-before.json.gz';data=read_side(d/file);data['YTNEWS.DAT']=bytes.fromhex(data['YTNEWS.DAT'])[:-2].hex();write_side(d/file,data)
                    else:
                        file='sidefiles.json.gz';data=read_side(d/file);initial=read_side(d/'side-before.json.gz')
                        field='YTNEWS.DAT'if kind=='stale-public'else'YTRMSG.DAT'
                        if kind in('stale-public','stale-broadcast'):b=bytes.fromhex(initial[field])
                        elif kind=='forged-broadcast':b=bytes.fromhex(read_side(SOURCE/'dos/fighter-hq/sidefiles.json.gz')[field]['hex'])
                        else:
                            b=bytearray.fromhex(data[field]['hex']);b[86+4:86+8]=mbf.enc(3)
                        data[field]['hex']=b.hex();data[field]['after_sha256']=sha(b);write_side(d/file,data)
                    if file:
                        c['files'][file]=sha((d/file).read_bytes());(d/'result.json').write_text(json.dumps(c,indent=2)+'\n')
                        manifest=json.loads((root/'dos/results.json').read_text());manifest['scenarios']=[c if r['name']==name else r for r in manifest['scenarios']];(root/'dos/results.json').write_text(json.dumps(manifest,indent=2)+'\n')
                    try:
                        proc=subprocess.run([sys.executable,str(ROOT/'scripts/verify_xannor_hq_reward.py'),'--research',str(root)],capture_output=True,text=True,timeout=15)
                        self.assertNotEqual(proc.returncode,0,proc.stdout);self.assertIn('AssertionError',proc.stderr);self.assertIn(reason,proc.stderr)
                    finally:
                        shutil.rmtree(d);shutil.copytree(SOURCE/'dos'/name,d);shutil.copy2(SOURCE/'dos/results.json',root/'dos/results.json')
                        if kind=='native':shutil.copy2(SOURCE/'rea/target-paths.json',root/'rea/target-paths.json')


if __name__=='__main__':unittest.main()
