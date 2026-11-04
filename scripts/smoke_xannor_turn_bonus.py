"""Confirm turn bonuses, receipts and public news through both real frontends."""
import copy,json,subprocess,tempfile
from pathlib import Path
from smoke_newspaper import BINARY,play,run_on_stable_date

def exercise(guard):
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp);seed=root/'seed'
  guard.run(subprocess.run,[BINARY,'-data',str(seed),'-init','-sectors','12'],check=True,capture_output=True)
  guard.run(play,seed,'Captain','q')
  original=json.loads((seed/'world.json').read_text())
  for classic in (False,True):
   for mode,initial,want in [('normal',100,2),('cap',500,1),('cancel',100,0),('bribe',100,2)]:
    data=root/(mode+str(classic));data.mkdir();w=copy.deepcopy(original)
    p=w['Players']['1'];p.update(Sector=7,Turns=initial,Fighters=10000,Shields=100000,Credits=1005,Cloak=0)
    w['Xannor']=dict(HQ=10,Reserve=0);w['Sectors']['7']['Warps']=[8];w['Sectors']['8']['Warps']=[7]
    w['Sectors']['8']['Defense']=dict(Owner=-1,Fighters=400)
    path=data/'world.json';path.write_text(json.dumps(w))
    prompt=b'Main Command (?=Help)?' if classic else b'> '
    if mode=='bribe':command='bribe 8 1';answers=[(b'[y/N] ',b'y\r')]
    else:
     command='breach 8 10000';answers=[(b'Accept human surrender if offered during this battle? [Y/n] ',b'y\r'),(b'defeat forces emergency escape. [y/N] ',b'n\r' if mode=='cancel' else b'y\r')]
    answers += [(prompt,b'news today\r' if classic else b'news\r'),(prompt,b'q;y\r' if classic else b'q\r')]
    text=guard.run(play,data,'Captain',command,classic=classic,followups=answers,page_news=True)
    saved=json.loads(path.read_text());p=saved['Players']['1']
    bonus=[e for e in saved['News'] if e.get('Combat',{}).get('Operation')=='xannor-turn-bonus']
    if mode=='cancel':assert not bonus and p['Turns']==initial and 'turns added.' not in text
    else:
     assert saved['Version']==35 and p['Turns']==initial-1+want and len(bonus)==1,(mode,text)
     assert bonus[0]['Combat']['Amount']==want and bonus[0]['Combat']['Secondary']==400
     assert f'{want} turns added.' in text and f'collected {want} turns bonus for destroying 400 Xannor' in text,text
     guard.run(play,data,'Captain','news;q',page_news=True)
     again=json.loads(path.read_text());assert again['Players']['1']['Turns']==p['Turns']
     assert len([e for e in again['News'] if e.get('Combat',{}).get('Operation')=='xannor-turn-bonus'])==1
  print('Xannor turn bonus PTY passed: classic/compact, exact cap, cancel, forced bribe combat, public news and reconnect without repayment.')
if __name__=='__main__':run_on_stable_date(exercise)
