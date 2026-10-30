"""Rehashed scanner/warp corruption controls must reach semantic assertions."""
import gzip,hashlib,importlib.util,json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/'research/yt-scanner-warp'
s=importlib.util.spec_from_file_location('mbf',ROOT/'archive/analysis/yt-maint/experiments.py');mbf=importlib.util.module_from_spec(s);s.loader.exec_module(mbf)
sha=lambda b:hashlib.sha256(b).hexdigest()


class SemanticControls(unittest.TestCase):
    def test_rehashed_corruptions(self):
        cases=[
            ('shop-above','after',[(2,81,2)],'scanner debit'),
            ('shop-exact','after',[(2,93,0)],'scanner installation'),
            ('shop-exact','after',[(2,49,500)],'docking-only turns'),
            ('shop-exact','after',[(3,81,1)],'other player changed'),
            ('shop-exact','after',[(4053,117,1)],'planet bank changed'),
            ('scanner-autopilot-first-yes','after',[(2,53,10000)],'accepted mine aftermath'),
            ('scanner-autopilot-second-no','after',[(2,57,107)],'declined second hop'),
            ('scanner-combined','quantity',[],'mine warning quantity'),
            ('scanner-combined','duplicate',[],'mine warning count'),
            ('scanner-combined','order',[],'warning order'),
            ('scanner-human','extra-header',[],'warning count'),
            ('scanner-human','prompt',[],'fresh prompt'),
            ('shop-reconnect','before',[(2,73,1)],'undeclared setup or broken world chain'),
            ('shop-reconnect','side-input',[],'auxiliary input chain'),
            ('shop-exact','native',[],'native bytes'),
            ('warp-clear','after',[(2,81,100001)],'actor asset/death conservation'),
            ('warp-clear','receipt',[],'recharge receipt/state'),
            ('warp-clear','false-cap',[],'heat/recharge relationship'),
            ('warp-landing-mines','after',[(111,129,3)],'warp mine aftermath'),
            ('warp-avoided-landing','lockout',[],'avoided-sector landing'),
            ('warp-landing-fighters','after',[(111,85,2)],'warp changed deployed fighters'),
            ('warp-installed-fighters','encounter',[],'hostile arrival encounter'),
            ('warp-meltdown','after',[(2,49,1)],'meltdown accounting'),
        ]
        with tempfile.TemporaryDirectory(prefix='yt-scanner-negative-')as temp:
            root=Path(temp)/'research';shutil.copytree(SOURCE,root)
            for name,kind,patches,reason in cases:
                with self.subTest(name=name,kind=kind):
                    d=root/'dos'/name;c=json.loads((d/'result.json').read_text());files=[]
                    if kind in ('before','after','false-cap'):
                        file=('after'if kind=='false-cap'else kind)+'.dat.gz';b=bytearray(gzip.decompress((d/file).read_bytes()))
                        for r,o,v in ([(2,49,0)]if kind=='false-cap'else patches):mbf.put(b,r,o,v)
                        (d/file).write_bytes(gzip.compress(b,mtime=0));files.append(file)
                    if kind=='native':
                        path=root/'rea/yt.json';data=json.loads(path.read_text());v=data['records'][0]['normalized_result'];b=bytearray.fromhex(v['bytes_hex']);b[0]^=1;v['bytes_hex']=b.hex();path.write_text(json.dumps(data)+'\n')
                    elif kind=='side-input':
                        file='side-before.json.gz';data=json.loads(gzip.decompress((d/file).read_bytes()));data['YTRMSG.DAT']='01';(d/file).write_bytes(gzip.compress(json.dumps(data).encode(),mtime=0));files.append(file)
                    elif kind not in ('before','after'):
                        file='transcript.txt';text=(d/file).read_text()
                        if kind=='quantity':text=text.replace('** 10 SECTOR MINES! **','** 999 SECTOR MINES! **')
                        elif kind=='duplicate':text=text.replace('** 10 SECTOR MINES! **','** 10 SECTOR MINES! **\n** 10 SECTOR MINES! **')
                        elif kind=='order':
                            a='** 10 SECTOR MINES! **';b='*** 100 Fighters Belonging to Enemy '
                            assert a in text and b in text;text=text.replace(a,'PLACEHOLDER').replace(b,a).replace('PLACEHOLDER',b)
                        elif kind=='extra-header':text+='\nDanger Scanner has detected the following in sector 999!\n'
                        elif kind=='prompt':text=text.replace('Move into sector 101? [y/N]','REMOVED')
                        elif kind=='receipt':text=text.replace('takes you 55 turns','takes you 54 turns')
                        elif kind=='false-cap':text=text.replace('takes you 55 turns','takes you 500 turns')
                        elif kind=='lockout':text=text.replace('Sector 881 now locked out.','REMOVED')
                        elif kind=='encounter':text=text.replace('You have to defeat the fighters before you can enter this sector.','REMOVED')
                        (d/file).write_text(text);files.append(file)
                    for file in files:c['files'][file]=sha((d/file).read_bytes())
                    if files:
                        (d/'result.json').write_text(json.dumps(c,indent=2)+'\n');manifest=json.loads((root/'dos/results.json').read_text());manifest['scenarios']=[c if v['name']==name else v for v in manifest['scenarios']];(root/'dos/results.json').write_text(json.dumps(manifest,indent=2)+'\n')
                    try:
                        result=subprocess.run([sys.executable,str(ROOT/'scripts/verify_scanner_manual_warp.py'),'--research',str(root)],capture_output=True,text=True,timeout=15)
                        self.assertNotEqual(result.returncode,0,result.stdout);self.assertIn('AssertionError',result.stderr);self.assertIn(reason,result.stderr)
                    finally:
                        shutil.rmtree(d);shutil.copytree(SOURCE/'dos'/name,d);shutil.copy2(SOURCE/'dos/results.json',root/'dos/results.json')
                        if kind=='native':shutil.copy2(SOURCE/'rea/yt.json',root/'rea/yt.json')


if __name__=='__main__':unittest.main()
