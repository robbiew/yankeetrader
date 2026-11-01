"""Real unseeded GoDoors disruption: sensors, consent, ordering and saved receipts."""
import copy
import errno
import json
import os
import pty
import re
import select
import subprocess
import tempfile
import time
from pathlib import Path
from smoke_newspaper import BINARY, play, run_on_stable_date


def encounter(data,classic,mode):
    master,slave=pty.openpty()
    proc=subprocess.Popen([BINARY,'-ascii' if classic else '-compact','-data',str(data),'-local','Captain'],stdin=slave,stdout=slave,stderr=slave)
    os.close(slave)
    output=pending=b'';keys=0;phase='startup';target=None
    prompt=b'Main Command (?=Help)?' if classic else b'> '
    end=time.monotonic()+20
    try:
        while time.monotonic()<end:
            if not select.select([master],[],[],.1)[0]:continue
            try:chunk=os.read(master,65536)
            except OSError as error:
                if error.errno==errno.EIO:break
                raise
            if not chunk:break
            output+=chunk;pending+=chunk
            if classic and keys<3 and b'[ Press any Key ]' in pending:
                pending=pending.split(b'[ Press any Key ]',1)[1];os.write(master,b' ');keys+=1
            if phase=='startup' and prompt in pending:
                pending=pending.split(prompt,1)[1]
                os.write(master,b'q;y\r' if mode=='zero' and classic else b'q\r' if mode=='zero' else b's\r')
                phase='quit' if mode=='zero' else 'scan'
            elif phase=='scan' and prompt in pending:
                text=pending.split(prompt,1)[0].decode(errors='replace')
                rows=list(re.finditer(r'Sector: (\d+) \| Warps:',text));holes=[]
                for i,row in enumerate(rows):
                    body=text[row.end():rows[i+1].start() if i+1<len(rows) else len(text)]
                    if 'Space-time disruption detected!' in body:holes.append(int(row[1]))
                assert holes,(mode,text)
                target=holes[0];path=Path(data)/'world.json';w=json.loads(path.read_text())
                if mode!='auto':
                    w['Sectors'][str(target)]['Minefield']=[dict(Owner=0,Count=3)]
                    w['Sectors'][str(target)]['Defense']=dict(Owner=-1,Fighters=100)
                else:
                    w['Sectors']['1']['Warps']=[target];w['Sectors'][str(target)]['Warps']=[8]
                path.write_text(json.dumps(w));pending=b''
                cmd='auto 8;y;i;q' if mode=='auto' else f'm {target};i;q'
                os.write(master,cmd.encode()+b'\r');phase='travel'
            elif phase=='travel':
                decision=b'Move into sector' if mode in ('accept','decline') else b'Enter this dangerous sector?'
                if mode!='auto' and decision in pending and b'[y/N]' in pending:
                    os.write(master,b'n\r' if mode=='decline' else b'y\r');pending=b'';phase='result'
                elif mode=='auto' and b'Disruption arrival saved:' in pending:phase='result'
            if phase=='result' and prompt in pending:
                os.write(master,b'q;y\r' if classic else b'q\r');phase='quit';pending=b''
        proc.wait(timeout=2)
        text=output.decode(errors='replace').replace('\r','')
        assert proc.returncode==0 and phase=='quit',(mode,text)
        return text,target
    finally:
        if proc.poll() is None:proc.kill();proc.wait()
        os.close(master)


def exercise(guard):
    with tempfile.TemporaryDirectory(prefix='yt-disruption-smoke-') as temp:
        root=Path(temp);seed=root/'seed'
        guard.run(subprocess.run,[BINARY,'-data',str(seed),'-init','-sectors','8'],check=True,capture_output=True)
        guard.run(play,seed,'Captain','q')
        original=json.loads((seed/'world.json').read_text())
        for classic in (False,True):
            for mode in ('move','accept','decline','auto'):
                data=root/f'{classic}-{mode}';data.mkdir();path=data/'world.json';w=copy.deepcopy(original)
                p=w['Players']['1'];p.update(Sector=1,Turns=500,Shields=1000000,DangerScanner=mode in ('accept','decline'),DockToken='',PlanetToken='',LandedPlanet=0)
                w['Sectors']['1']['Warps']=list(range(2,8))
                path.write_text(json.dumps(w));text,target=guard.run(encounter,data,classic,mode)
                saved=json.loads(path.read_text());p=saved['Players']['1']
                assert saved['Version']==27 and p['Credits']==w['Players']['1']['Credits']
                if mode=='decline':
                    assert 'Scanner entry cancelled.' in text and 'Forced warp saved:' not in text and p['Sector']==1 and p['Turns']==500
                else:
                    steps=re.findall(r'Forced warp saved: sector (\d+) -> (\d+); heat (\d+)/31; recharge (\d+) turns; meltdown (true|false)',text)
                    assert 1<=len(steps)<=32,text
                    recharge=0
                    for source,to,heat,cost,meltdown in steps:
                        heat,cost=int(heat),int(cost);available=499-recharge
                        assert 0<=heat<=31 and (cost==available if meltdown=='true' else min(available,4*heat)<=cost<=min(available,4*heat+3))
                        recharge+=cost
                    assert p['Turns']==499-recharge and p['WarpSequence']==len(steps) and p['Sector']==int(steps[-1][1]),text
                    assert f'final sector {p["Sector"]}; total action turns spent {1+recharge}; remaining {p["Turns"]}' in text,text
                    assert 'Moved to sector 8.' not in text and 'Queued travel stopped.' in text
                    assert not p.get('DockToken') and not p.get('PlanetToken')
                if mode!='auto':
                    assert saved['Sectors'][str(target)]['Minefield']==[dict(Owner=0,Count=3)]
                    assert saved['Sectors'][str(target)]['Defense']==dict(Owner=-1,Fighters=100)
                new=[n for n in saved.get('News',[]) if n['ID']>=w['NextNews']]
                assert all(n['Kind']=='login' for n in new),new
                print(f'Disruption {"classic" if classic else "compact"} {mode}: passed')
            # Observe an actual zero-turn startup encounter; fresh logins choose
            # their own pair, so quiet runs are explicitly separate attempts.
            data=root/f'{classic}-zero';data.mkdir();path=data/'world.json';w=copy.deepcopy(original);w['Players']['1'].update(Sector=2,Turns=0,Cloak=.5)
            for attempt in range(64):
                path.write_text(json.dumps(w));text,_=guard.run(encounter,data,classic,'zero')
                if 'Forced warp saved:' in text:break
            else:raise AssertionError('No zero-turn startup encounter across 64 login controls')
            saved=json.loads(path.read_text());p=saved['Players']['1']
            assert p['Turns']==0 and p['Cloak']==.5 and p['WarpSequence']>=1 and 'recharge 0 turns' in text
            print(f'Disruption {"classic" if classic else "compact"} zero-turn startup: passed')
    print('Disruption PTY passed: real session sensors, fresh accept/refuse, hole-first mine/fighter bypass, bounded recharge, autopilot interruption, zero-turn startup and private saved receipts.')

if __name__=='__main__':run_on_stable_date(exercise)
