"""Exercise opt-in DOS maps, independent economy and saved/reset compatibility."""
import json
from pathlib import Path
import subprocess
import tempfile
import smoke_newspaper as terminal

ROOT=Path(__file__).resolve().parents[1]

def connected(world,reverse=False):
    links={int(i):[] for i in world['Sectors']}
    for key,sector in world['Sectors'].items():
        for to in sector['Warps']:
            if reverse:links[to].append(int(key))
            else:links[int(key)].append(to)
    seen={1};queue=[1]
    for sector in queue:
        for to in links[sector]:
            if to not in seen:seen.add(to);queue.append(to)
    return len(seen)==len(links)

def main():
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp);binary=root/'yt'
        subprocess.run(['go','build','-o',str(binary),'./cmd/yt'],cwd=ROOT,check=True)
        terminal.BINARY=str(binary)
        def run(data,*args,ok=True):
            out=subprocess.run([str(binary),'-data',str(data),*args],capture_output=True,text=True)
            assert (out.returncode==0)==ok,(args,out.stdout,out.stderr)
        for ports in (False,True):
            data=root/('both' if ports else 'warps')
            run(data,'-init','-dos-warps','-sectors','32',*(['-dos-ports'] if ports else []))
            path=data/'world.json';original=path.read_bytes();w=json.loads(original)
            assert w['Version']==35 and w['WarpGeneration']=='dos'
            assert w.get('PortGeneration','')==('dos' if ports else '')
            assert w['Sectors']['1']['Warps']==[2,3,4,5,6]
            assert any(len(s['Warps'])<6 for s in w['Sectors'].values())
            assert connected(w) and connected(w,True)
            if not ports:assert w['Ports']['2']['Production']==[100,100,100]
            for args in [('-init','-dos-warps'),('-maint','-dos-warps'),('-dos-warps=false',)]:run(data,*args,ok=False)
            assert path.read_bytes()==original
            archive=root/('both-season.json' if ports else 'warp-season.json')
            run(data,'-admin-reset','1','-season-export',str(archive),'-seed','77')
            reset=json.loads(path.read_bytes())
            assert json.loads(archive.read_bytes())['World']==w
            assert reset['Season']==2 and reset['WarpGeneration']=='dos'
            assert reset.get('PortGeneration','')==('dos' if ports else '')
            assert connected(reset) and connected(reset,True)
            assert reset['Sectors']!=w['Sectors']
            terminal.play(data,'Navigator','q')
            for classic in (False,True):
                current=json.loads(path.read_bytes());current['Players']['1']['Sector']=1;path.write_text(json.dumps(current))
                terminal.play(data,'Navigator','m;3;i;q;y' if classic else 'm 3;i;q',classic=classic)
                saved=json.loads(path.read_bytes())
                assert saved['Players']['1']['Sector']==3 and saved['WarpGeneration']=='dos'
        legacy=root/'legacy';run(legacy,'-init','-sectors','8','-dos-ports')
        path=legacy/'world.json';old=json.loads(path.read_bytes());old['Version']=33;path.write_text(json.dumps(old))
        run(legacy,'-maint');saved=json.loads(path.read_bytes())
        assert saved['Version']==35 and not saved.get('WarpGeneration')
        assert saved['Sectors']==old['Sectors'] and saved['PortGeneration']=='dos'
        print('DOS warp CLI/PTY passed: independent profiles, connectivity, persistence, archive/reset, legacy map preservation and both navigation interfaces.')

if __name__=='__main__':main()
