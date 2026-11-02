"""Real GoDoors scanner purchase, warning/autopilot and manual-warp receipts."""
import copy,json,re,subprocess,tempfile
from pathlib import Path
from smoke_newspaper import BINARY,play,run_on_stable_date


def exercise(guard):
 with tempfile.TemporaryDirectory(prefix='yt-scanner-warp-smoke-')as temp:
  root=Path(temp);seed=root/'seed'
  guard.run(subprocess.run,[BINARY,'-data',str(seed),'-init','-sectors','12'],check=True,capture_output=True)
  guard.run(play,seed,'Captain','q')
  original=json.loads((seed/'world.json').read_text())
  def fixture(name):
   data=root/name;data.mkdir();return data,data/'world.json',copy.deepcopy(original)
  for classic in (False,True):
   prompt=b'Main Command (?=Help)?'if classic else b'> ';ending=b'q;y\r'if classic else b'q\r'
   data,path,w=fixture('buy'+str(classic));w['Players']['1']['Credits']=250001;path.write_text(json.dumps(w))
   command='p;5;5;0;i;q;y'if classic else'p;equip scanner 1;equip scanner 1;i;q'
   text=guard.run(play,data,'Captain',command,classic=classic)
   saved=json.loads(path.read_text());p=saved['Players']['1']
   assert saved['Version']==28 and p['DangerScanner']and p['Credits']==1 and p['Turns']==499
   assert text.count('Credits spent: 250000. Balance: 1.')==1 and 'already installed'in text,text
   reconnect=guard.run(play,data,'Captain','i;q;y'if classic else'i;q',classic=classic)
   assert 'Installed'in reconnect if classic else'Danger scanner installed: true'in reconnect
   assert json.loads(path.read_text())['Players']['1']['Credits']==1
   for mode in ('accept','decline','auto-accept','auto-decline'):
    data,path,w=fixture(mode+str(classic));p=w['Players']['1'];p.update(Sector=8,Turns=500,DangerScanner=True,Shields=1000000)
    for a,b in ((8,9),(9,10),(10,11)):w['Sectors'][str(a)]['Warps']=[b]
    target=10 if mode.startswith('auto')else 9
    w['Sectors'][str(target)]['Minefield']=[dict(Owner=0,Count=1)]
    if not mode.startswith('auto'):w['Sectors'][str(target)]['Defense']=dict(Owner=-1,Fighters=100)
    path.write_text(json.dumps(w));command='auto 11;y'if mode.startswith('auto')else'move 9';yes=mode.endswith('accept')
    text=guard.run(play,data,'Captain',command,classic=classic,followups=[(f'Move into sector {target}? [y/N]'.encode(),b'y\r'if yes else b'n\r'),(prompt,ending)])
    saved=json.loads(path.read_text());p=saved['Players']['1'];first=1 if mode.startswith('auto')else 0
    assert p['Sector']==(target if yes else 8+first)and p['Turns']==500-first-int(yes),(mode,text)
    assert text.count('Danger scanner has detected')==1 and 'Moved to sector 11.'not in text
    if yes:
     assert not saved['Sectors'][str(target)].get('Minefield')
     if not mode.startswith('auto'):assert saved['Sectors'][str(target)]['Defense']['Fighters']==100 and 'Hostile sector fighters block'in text
    else:assert saved['Sectors'][str(target)]['Minefield'][0]['Count']==1
   for turns,answer in ((500,b'y\r'),(1,b'y\r'),(500,b'n\r'),(500,b'y;q\r')):
    data,path,w=fixture('warp'+str(turns)+answer.hex()+str(classic));p=w['Players']['1'];p.update(Sector=8,Turns=turns,DangerScanner=False)
    path.write_text(json.dumps(w))
    text=guard.run(play,data,'Captain','warp;y',classic=classic,followups=[(b'Engage? [y/N]',answer),(prompt,ending)])
    saved=json.loads(path.read_text());p=saved['Players']['1'];before=w['Players']['1']
    if answer!=b'y\r':
     assert p['Turns']==turns and p['Sector']==8 and not p.get('WarpSequence')and 'Emergency warp saved:'not in text,text
    else:
     m=re.search(r'Emergency warp saved: landed in sector (\d+); heat (\d+)/31; recharge (\d+) turns; aftermath (\d+) turns; total spent (\d+)[.]',text);assert m,text
     destination,heat,cost,aftermath,total=map(int,m.groups())
     assert p['Sector']==destination and p['Turns']==turns-total and p['WarpSequence']==1 and total==cost and aftermath==0
     assert (cost==turns if heat==31 else min(turns,4*heat)<=cost<=min(turns,4*heat+3))and 0<=p['Turns']<=turns
     assert p['Credits']==before['Credits']and not p.get('DockToken')and not p.get('PlanetToken')
     for k in ('Holds','Fighters','Shields','Cargo','Ground','Missiles','Mines','Plasma'):assert p[k]==before[k],(k,text)
     assert ('Engine meltdown consumed'in text)==(heat==31)
 print('Scanner/warp PTY passed: purchase/reload, exact debit, duplicate refusal, fresh warnings, partial autopilot, hostile gates, normal/short-budget random warps, cancellation and saved receipts in both interfaces.')


if __name__=='__main__':run_on_stable_date(exercise)
