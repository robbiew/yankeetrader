"""Exercise atomic NPC death and private reports through real GoDoors terminals."""
import copy
import datetime
import json
import subprocess
import tempfile
from pathlib import Path

from smoke_newspaper import BINARY, play, run_on_stable_date


def exercise(guard):
    with tempfile.TemporaryDirectory(prefix='yt-xannor-ships-smoke-') as temp:
        root=Path(temp);seed=root/'seed'
        guard.run(subprocess.run,[BINARY,'-data',str(seed),'-init','-sectors','12'],check=True,capture_output=True)
        guard.run(play,seed,'Captain','q');guard.run(play,seed,'Visitor','q')
        original=json.loads((seed/'world.json').read_text())
        stamp=(guard.clock()+datetime.timedelta(days=2)).isoformat()
        for mode in ('death','survivor','planet-ground','defense-stop'):
            data=root/mode;data.mkdir();path=data/'world.json';world=copy.deepcopy(original)
            world['LastMaintenance']=(guard.day-datetime.timedelta(days=1)).isoformat()
            p=world['Players']['1'];p.update(Sector=10,Cloak=0,Fighters=10000 if mode=='survivor' else 0,Shields=10000 if mode=='survivor' else 0,StoredScore=4000,Mines=5,Credits=12345)
            world['Players']['2'].update(Sector=1,StoredScore=0)
            world['Xannor']=dict(HQ=8,Reserve=0)
            for i in range(8,13):world['Sectors'][str(i)]['Warps']=[]
            world['Sectors']['9']['Warps']=[10];world['Sectors']['10']['Warps']=[8]
            world['Sectors']['8']['Defense']=dict(Owner=-1,Fighters=1)
            world['Sectors']['9']['Defense']=dict(Owner=-1,Fighters=100)
            for slot,sector,owner,faction,name in [(99,11,-2,'mercenaries','Mercenary Base'),(100,8,-1,'xannor','Xannoron')]:
                world['Planets'][str(slot)]=dict(Generation=slot,ID=slot,Sector=sector,Owner=owner,FactionHome=faction,Name=name,Updated=stamp,Production=[0,0,0],Cargo=[0,0,0],Fighters=0,Missiles=0,Mines=0,Plasma=0,Ground=100,Bank=1)
                world['Sectors'][str(sector)]['Planet']=slot
            if mode=='planet-ground':
                # At the strict civil-war threshold: isolate NPC ground combat.
                world['Planets']['2']=dict(Generation=2,ID=2,Sector=10,Owner=0,Name='Neutral probe',Updated=stamp,Production=[0,0,0],Cargo=[0,0,0],Fighters=0,Missiles=0,Mines=0,Plasma=0,Ground=1000000,Bank=1234)
                world['Sectors']['10']['Planet']=2
                world['Sectors']['10']['Minefield']=[dict(Owner=1,Count=3)]
            if mode=='defense-stop':world['Sectors']['10']['Defense']=dict(Owner=2,Fighters=1000000)
            path.write_text(json.dumps(world))
            guard.run(subprocess.run,[BINARY,'-data',str(data),'-maint'],check=True,capture_output=True,timeout=10)
            saved=json.loads(path.read_text());p=saved['Players']['1']
            assert saved['Version']==24 and saved['Xannor']==dict(HQ=8,Reserve=0)
            if mode in ('planet-ground','defense-stop'):
                assert not p.get('Death') and not p.get('BattleReports'),p
                if mode=='planet-ground':
                    assert not saved['Sectors']['9'].get('Defense')
                    assert sum(x['Count'] for x in saved['Sectors']['10'].get('Minefield',[]))<3
                    assert saved['Planets']['2']['Ground']>=1000000-100
                continue
            reports=p['BattleReports'];assert len(reports)==1 and reports[0]['Unread']
            report=reports[0];assert report['Sector']==10 and saved['NextBattleReport']==2
            assert not saved['Sectors']['10'].get('Minefield'),'NPC death created wreck mines'
            if mode=='death':
                assert p['Death']['Cause']=='xannor' and p['Death']['Killer']==-1 and p['Death']['Sector']==10
                assert p['Sector']==0 and p['ShipGeneration']==1 and p['Fighters']==0 and p['Shields']==0 and p['Mines']==0 and p['Credits']==0
                assert report['Destroyed'] and saved['Sectors']['8']['Defense']['Fighters']==101
                assert len([e for e in saved['News'] if e['Kind']=='xannor-death'])==1
            else:
                assert not p.get('Death') and p['Fighters']==10000-report['FightersLost'] and p['Shields']==10000-report['ShieldsLost']
                assert p['Missiles']==world['Players']['1']['Missiles'] and p['Mines']==5
            # Same date replay preserves reports, inventory and force byte-for-byte.
            before=path.read_bytes()
            result=guard.run(subprocess.run,[BINARY,'-data',str(data),'-maint'],check=True,capture_output=True,text=True,timeout=10)
            assert 'no daily phases repeated' in result.stdout and path.read_bytes()==before
            private=f"Xannor lost {report['XannorLost']} fighters. You lost {report['FightersLost']} fighters and {report['ShieldsLost']} shields."
            other=guard.run(play,data,'Visitor','battles;news;q')
            assert private not in other and 'Private Xannor battle report'not in other
            if mode=='death':assert 'Captain  Destroyed by the Xannor'in other
            for classic in (False,True):
                # Re-arm unread delivery only in a disposable fixture so both interfaces run it.
                current=json.loads(path.read_text());current['Players']['1']['BattleReports'][0]['Unread']=True;path.write_text(json.dumps(current))
                text=guard.run(play,data,'Captain','battles;q;y'if classic else'battles;q',classic=classic)
                assert text.count(private)==2,text
                current=json.loads(path.read_text());assert not current['Players']['1']['BattleReports'][0]['Unread']
                if mode=='death':assert current['Players']['1']['Sector']==1 and current['Players']['1']['ShipGeneration']==2
            text=guard.run(play,data,'Captain','q')
            assert 'Private Xannor battle report'not in text


if __name__=='__main__':
    run_on_stable_date(exercise)
    print('Xannor ship PTY passed: atomic death/replacement, casualty reports, no wreck mines, replay, visitor privacy, compact/classic history and planetary ground defenses before ship detection.')
