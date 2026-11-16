"""Run the compiled research CLI against all32 existing six-file fixture oracles."""
import hashlib,json,os,subprocess,tempfile
from pathlib import Path
import export_replay_cli_recipes as recipes
ROOT=recipes.ROOT
SHA=lambda b:hashlib.sha256(b).hexdigest()
def run():
    with tempfile.TemporaryDirectory(prefix='yt-replay-cli-')as tmp:
        tmp=Path(tmp);cases=tmp/'cases';assert recipes.export(cases)==32
        binary=tmp/('qbmaint-replay.exe'if os.name=='nt'else'qbmaint-replay')
        subprocess.run(['go','build','-o',str(binary),'./cmd/qbmaint-replay'],cwd=ROOT,check=True)
        profiles={};count=0;rejections=0
        for folder in sorted(cases.iterdir()):
            recipe=folder/'recipe.json';before=folder/'before';out=folder/'result';oracles=json.loads((folder/'oracles.json').read_text());document=json.loads(recipe.read_text())
            saved={n:SHA(p.read_bytes())for n,p in((p.name,p)for p in before.iterdir())};recipe_before=recipe.read_bytes()
            args=[str(binary),'-recipe',str(recipe),'-before',str(before),'-source-root',str(ROOT),'-out',str(out)]
            result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=60)
            assert result.returncode==0,(folder.name,result.stderr)
            bundle=out/'replay';assert{p.name for p in bundle.iterdir()}==set(oracles['native_files'])|{'receipt.json'}
            receipt=json.loads((bundle/'receipt.json').read_text());assert receipt['format']=='qbmaint-receipt-v1'
            for n,h in oracles['native_files'].items():assert SHA((bundle/n).read_bytes())==h and receipt['output_sha256'][n]==h,(folder.name,n)
            assert receipt['recipe_sha256']==SHA(recipe_before)and receipt['before_sha256']==saved
            assert receipt['source_sha256']==document['source_sha256']and receipt['profile']==document['profile']
            assert receipt['final_state']==oracles['final_state']and receipt['draws']==oracles['draws']
            assert len(receipt['encounters']or[])==oracles['encounters']and receipt['state_evidence']=='modeled-not-native-endpoint'
            again=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=60);assert again.returncode!=0,'existing output must be refused'
            assert{p.name:SHA(p.read_bytes())for p in before.iterdir()}==saved and recipe.read_bytes()==recipe_before
            # Corrupt a before-file identity: reject with no output publication.
            bad=dict(document);bad['before_sha256']=dict(document['before_sha256']);bad['before_sha256']['YTNEWS.DAT']='0'*64
            bad_path=folder/'bad.json';bad_path.write_text(json.dumps(bad));bad_out=folder/'bad-result'
            result=subprocess.run([str(binary),'-recipe',str(bad_path),'-before',str(before),'-source-root',str(ROOT),'-out',str(bad_out)],cwd=ROOT,capture_output=True,text=True,timeout=60)
            assert result.returncode!=0 and not bad_out.exists()and'before hash differs'in result.stderr
            rejections+=2;count+=1;profiles[document['profile']]=profiles.get(document['profile'],0)+1
        assert profiles=={'initial':29,'initial-wanderer':3}
        # A late recipe may never silently fall back from the strict profile.
        folder=cases/'matrix-late-observed-a';doc=json.loads((folder/'recipe.json').read_text());doc['profile']='initial';path=folder/'strict.json';path.write_text(json.dumps(doc));out=folder/'strict-result'
        result=subprocess.run([str(binary),'-recipe',str(path),'-before',str(folder/'before'),'-source-root',str(ROOT),'-out',str(out)],capture_output=True,text=True,timeout=60)
        assert result.returncode!=0 and not out.exists()and'entered encounter'in result.stderr
        # A source fingerprint mismatch fails independently of before hashes.
        doc=json.loads((folder/'recipe.json').read_text());key=next(k for k in doc['source_sha256']if k!='archive/dos-original/YTMAINT.EXE');doc['source_sha256'][key]='0'*64;path=folder/'source-mismatch.json';path.write_text(json.dumps(doc));out=folder/'source-result'
        result=subprocess.run([str(binary),'-recipe',str(path),'-before',str(folder/'before'),'-source-root',str(ROOT),'-out',str(out)],capture_output=True,text=True,timeout=60)
        assert result.returncode!=0 and not out.exists()and'source hash differs'in result.stderr
        print('Verified',count,'CLI replays /',count*6,'complete native files, model receipts and',rejections+2,'no-publication rejection controls')
if __name__=='__main__':run()
