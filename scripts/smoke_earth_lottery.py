"""Paid lottery through real terminals: fresh choices, saved receipts and daily quota."""
import collections
import copy
import json
import re
import subprocess
import tempfile
from pathlib import Path
from smoke_newspaper import BINARY,play,run_on_stable_date

PRIZES=[0,100,1000,10000,100000,1000000,100000000]
RECEIPT=re.compile(r'Lottery saved: ticket ([0-9]{6}); drawn ([0-9]{6}); matches ([0-6]). Fee: ([0-9]+). Gross prize: ([0-9]+). Awarded: ([0-9]+). Credit cap reduction: ([0-9]+). Balance: ([0-9]+). Plays remaining: ([0-9]+) \(UTC\)[.]')


def exercise(guard):
 with tempfile.TemporaryDirectory(prefix='yt-earth-lottery-smoke-')as temp:
  root=Path(temp);seed=root/'seed'
  guard.run(subprocess.run,[BINARY,'-data',str(seed),'-init','-sectors','8'],check=True,capture_output=True)
  guard.run(play,seed,'Captain','q');original=json.loads((seed/'world.json').read_text())
  for classic in (False,True):
   data=root/str(classic);data.mkdir();path=data/'world.json';world=copy.deepcopy(original)
   world['Players']['1'].update(Credits=100000,Turns=500);path.write_text(json.dumps(world))
   prompt=b'Buy Which Item? -=>'if classic else b'> '
   initial='p;4;000000;y;0;q;y'if classic else'p;lottery 000000;y;q'
   again=b'4;000000;y\r'if classic else b'lottery 000000;y\r'
   bad=b'4;12A456\r'if classic else b'lottery 12A456\r'
   steps=[(b'Buy this ticket? [y/N]',b'n\r'),(prompt,bad),(prompt,again)]
   for i in range(5):
    steps.append((b'Buy this ticket? [y/N]',b'y\r'))
    if i<4:steps.append((prompt,again))
   # A sixth request is refused without a confirmation or draw.
   steps.extend([(prompt,again),(prompt,b'0;q;y\r'if classic else b'q\r')])
   text=guard.run(play,data,'Captain',initial,classic=classic,followups=steps)
   assert 'Lottery cancelled; no credits or plays spent.'in text and 'enter exactly six digits'in text,text
   assert 'no paid lottery plays remaining'in text,text
   receipts=RECEIPT.findall(text);assert len(receipts)==5 and text.count('Buy this ticket? [y/N]')==6,text
   balance=100000;public=[]
   for i,row in enumerate(receipts):
    ticket,draw,*values=row;matches,fee,gross,award,capped,saved,remaining=map(int,values)
    correct=sum((collections.Counter(ticket)&collections.Counter(draw)).values())
    assert ticket=='000000'and matches==correct and fee==5 and gross==PRIZES[correct] and capped==0 and award==gross,row
    balance+=award-fee;assert saved==balance and remaining==4-i,row
    if matches>=4:public.append((matches,award))
   saved=json.loads(path.read_text());p=saved['Players']['1']
   assert saved['Version']==22 and p['Credits']==balance and p['LotteryDay']==guard.day.isoformat()and p['LotteryPlays']==5 and p['LotterySequence']==5 and p['Turns']==499,(p,text)
   events=[e for e in saved.get('News',[])if e['Kind']=='paid-lottery']
   assert [(e['LotteryMatches'],e['LotteryPrize'])for e in events]==public,events
   assert all(set(e)<=set(('ID','At','Kind','Alias','LotteryMatches','LotteryPrize'))for e in events)
   reconnect='p;4;000000;0;q;y'if classic else'p;lottery 000000;q'
   again_text=guard.run(play,data,'Captain',reconnect,classic=classic)
   p=json.loads(path.read_text())['Players']['1']
   assert p['Credits']==balance and p['LotteryPlays']==5 and p['LotterySequence']==5 and p['Turns']==498 and not RECEIPT.search(again_text)and'no paid lottery plays remaining'in again_text,again_text
   # Typed public history fixture verifies a capped award is printed as actual
   # credits, without account balances or ticket/draw numbers in the journal.
   news=json.loads(path.read_text());news['News']=[];news['NextNews']=1
   path.write_text(json.dumps(news))
   guard.run(play,data,'Captain','q')
   news=json.loads(path.read_text());event=dict(news['News'][-1]);event.update(ID=news['NextNews'],Kind='paid-lottery',LotteryMatches=6,LotteryPrize=5);news['News'].append(event);news['NextNews']+=1
   path.write_text(json.dumps(news))
   printed=guard.run(play,data,'Captain','news today;q;y'if classic else'news today;q',classic=classic)
   assert 'Won 5 credits in the paid lottery (6 matches; gross prize 100000000).'in printed and 'drawn 'not in printed,printed
 print('Paid lottery PTY passed: compact/classic fresh confirmation, invalid/cancelled/queued input, five exact saved receipts, observed RNG/multiset/prizes/news, exhausted quota across reconnect and capped public-news rendering.')


if __name__=='__main__':run_on_stable_date(exercise)
