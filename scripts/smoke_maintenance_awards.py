"""Exercise persisted award privacy and actual maintenance retirement in real PTYs."""
import copy,datetime,json,subprocess,tempfile
from pathlib import Path
from smoke_newspaper import BINARY,play,run_on_stable_date


def exercise(guard):
    with tempfile.TemporaryDirectory(prefix='yt-daily-awards-smoke-')as temp:
        root=Path(temp);seed=root/'seed'
        guard.run(subprocess.run,[BINARY,'-data',str(seed),'-init','-sectors','12'],check=True,capture_output=True)
        guard.run(play,seed,'Captain','q');guard.run(play,seed,'Visitor','q')
        original=json.loads((seed/'world.json').read_text())
        for classic in (False,True):
            data=root/str(classic);data.mkdir();path=data/'world.json';w=copy.deepcopy(original)
            now=guard.clock();stamp=now.isoformat();old=now-datetime.timedelta(days=30);dead=now-datetime.timedelta(days=14)
            w['Created']=old.isoformat();w['LastMaintenance']=(guard.day-datetime.timedelta(days=1)).isoformat()
            for p in w['Players'].values():p['StoredScore']=0
            w['Xannor']=dict(HQ=8,Reserve=0)
            w['Sectors']['8']['Defense']=dict(Owner=-1,Fighters=1)
            for sector in range(8,13):w['Sectors'][str(sector)]['Warps']=[]
            for slot,sector,owner,home,name in [(99,11,-2,'mercenaries','Mercenary Base'),(100,12,-1,'xannor','Xannoron')]:
                w['Planets'][str(slot)]=dict(ID=slot,Sector=sector,Owner=owner,FactionHome=home,Name=name,Updated=stamp,Production=[0,0,0],Cargo=[0,0,0],Fighters=0,Missiles=0,Mines=0,Plasma=0,Ground=1,Bank=1)
                w['Sectors'][str(sector)]['Planet']=slot
            q=w['Players']['2'];q.update(Death=dict(At=dead.isoformat(),Cause='hazard',Killer=0,Sector=1),Sector=0,ShipGeneration=1,LastLogin=dead.date().isoformat(),LastActivity=dead.date().isoformat())
            w['Planets']['2']=dict(ID=2,Sector=10,Owner=1,Name="Captain's Planet",Updated=stamp,Production=[750,750,750],Cargo=[0,0,0],Fighters=0,Missiles=0,Mines=0,Plasma=0,Ground=1,Bank=250000)
            w['Sectors']['10']['Planet']=2
            w['Planets']['3']=dict(ID=3,Sector=9,Owner=2,Name='Released Estate',Updated=stamp,Production=[0,0,0],Cargo=[0,0,0],Fighters=0,Missiles=0,Mines=0,Plasma=0,Ground=99,Bank=0)
            w['Sectors']['9']['Planet']=3;w['Ports']['2'].update(Owner=2,Treasury=900)
            message='You won a PLANET in the SUPER-LOTTERY! Look in sector 10!'
            w['Radio']=[dict(System='super-planet',ID=1,RequestID='00000000000000000000000000000001',From=0,To=1,FromAlias='Super Lottery',ToAlias='Captain',Text=message,Sent=stamp,Unread=True)];w['NextRadio']=2
            w['News']=[dict(ID=1,At=stamp,Kind='super-planet',Alias='Captain')];w['NextNews']=2
            path.write_text(json.dumps(w))
            guard.run(subprocess.run,[BINARY,'-data',str(data),'-maint'],check=True,capture_output=True,timeout=10)
            saved=json.loads(path.read_text());retired=saved['Players']['2']
            assert saved['Version']==19 and retired['RetiredAt'].startswith(guard.day.isoformat()) and retired['Turns']==0
            assert saved['Planets']['3']['Owner']==0 and saved['Ports']['2']['Owner']==0
            text=guard.run(play,data,'Captain','messages;news today;q;y'if classic else'messages;news;q',classic=classic)
            assert message in text and 'Won a PLANET in the SUPER LOTTERY!'in text and 'Retired after inactivity'in text,text
            saved=json.loads(path.read_text());assert not saved['Radio'][0]['Unread']
            # Returning identity gets a new ship; no other account's award mail.
            commands='messages;news today;q;y'if classic else'messages;news;q'
            text=guard.run(play,data,'Visitor',commands,classic=classic)
            assert message not in text and 'returned from retirement'in text,text
            saved=json.loads(path.read_text());returned=saved['Players']['2']
            assert not returned.get('Death') and returned['ShipGeneration']==2 and returned['Turns']==500
            assert returned['Identity']==original['Players']['2']['Identity'] and returned['LastActivity']==guard.day.isoformat() and saved['Planets']['3']['Owner']==0
            # Public snapshots never carry the location; mail remains recipient-only.
            for event in saved['News']:
                if event['Kind']=='super-planet':assert not event.get('PlanetName') and not event.get('Outcome')
    print('Maintenance PTY passed: actual retirement, classic/compact award delivery, private location, acknowledgement and same-identity reactivation.')


if __name__=='__main__':run_on_stable_date(exercise)
