"""Exercise daily port plague and typed public events in real classic/compact PTYs."""
import copy, datetime, json, subprocess, tempfile
from pathlib import Path
from smoke_newspaper import BINARY, play, run_on_stable_date


def exercise(guard):
    with tempfile.TemporaryDirectory(prefix='yt-overcrowding-smoke-') as temp:
        root=Path(temp); seed=root/'seed'
        guard.run(subprocess.run,[BINARY,'-data',str(seed),'-init','-sectors','12'],check=True,capture_output=True)
        guard.run(play,seed,'Captain','q')
        original=json.loads((seed/'world.json').read_text())
        for classic in (False,True):
            data=root/str(classic);data.mkdir();path=data/'world.json';w=copy.deepcopy(original)
            now=guard.clock();stamp=now.isoformat()
            w['LastMaintenance']=(guard.day-datetime.timedelta(days=1)).isoformat()
            # Every eligible port is strictly over threshold, so this assertion
            # is deterministic despite the production RNG used by the real CLI.
            for p in w['Ports'].values():
                p.update(Updated=stamp,Production=[2000000,100,100],Supply=[0,0,0])
            # Existing quiet homes and no routes isolate economic maintenance
            # from fresh faction creation/assault news and newspaper paging.
            w['Xannor']=dict(HQ=8,Reserve=0)
            w['Sectors']['8']['Defense']=dict(Owner=-1,Fighters=1)
            for sector in w['Sectors'].values():sector['Warps']=[]
            for slot,sector,owner,home,name in [(99,11,-2,'mercenaries','Mercenary Base'),(100,12,-1,'xannor','Xannoron')]:
                w['Planets'][str(slot)]=dict(ID=slot,Sector=sector,Owner=owner,FactionHome=home,Name=name,Updated=stamp,Production=[0,0,0],Cargo=[0,0,0],Fighters=0,Missiles=0,Mines=0,Plasma=0,Ground=1,Bank=1)
                w['Sectors'][str(sector)]['Planet']=slot
            # Retained typed planet announcements test rendering without needing
            # a probabilistic native CLI outbreak to hit a fixed test seed.
            w['News']=[dict(ID=1,At=stamp,Kind='planet-plague',PlanetName='Plague World'),dict(ID=2,At=stamp,Kind='civil-war',PlanetName='Civil World')]
            w['NextNews']=3
            path.write_text(json.dumps(w))
            guard.run(subprocess.run,[BINARY,'-data',str(data),'-maint'],check=True,capture_output=True,timeout=10)
            saved=json.loads(path.read_text());assert saved['Version']==21
            news=[e for e in saved['News'] if e['Kind']=='port-plague']
            assert len(news)==1 and news[0]['PortCount']==12 and news[0]['ID']==3
            for p in saved['Ports'].values():
                assert 500<=p['Production'][0]<=2000500 and p['Production'][1:]==[100,100]
                assert all(s<=10*r for s,r in zip(p['Supply'],p['Production']))
                assert sum(c>0 for c in p['Coefficient'])==1
            maintained=path.read_bytes()
            guard.run(subprocess.run,[BINARY,'-data',str(data),'-maint'],check=True,capture_output=True,timeout=10)
            assert path.read_bytes()==maintained,'same-day maintenance repeated damage or news'
            text=guard.run(play,data,'Captain','news today;q;y' if classic else 'news;q',classic=classic)
            for expected in ('Ports struck by plague: 12.','Plague struck Plague World.','Civil war erupted on Civil World.'):
                assert expected in text,text
            assert 'insurrection' not in text and 'bank balance' not in text
    print('Overcrowding PTY passed: actual bounded port outbreaks, caps, stable commodity signs, replay, and classic/compact typed public news.')


if __name__=='__main__':run_on_stable_date(exercise)
