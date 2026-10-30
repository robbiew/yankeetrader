"""Real terminals: exact cloak debit, fresh login-only reveal, repeat cost and reconnect."""
import copy,json,re,subprocess,tempfile
from pathlib import Path
from smoke_newspaper import BINARY,play,run_on_stable_date


def exercise(guard):
 with tempfile.TemporaryDirectory(prefix='yt-cloak-equipment-smoke-')as temp:
  root=Path(temp);seed=root/'seed'
  guard.run(subprocess.run,[BINARY,'-data',str(seed),'-init','-sectors','12'],check=True,capture_output=True)
  guard.run(play,seed,'Captain','q');guard.run(play,seed,'Enemy','q')
  original=json.loads((seed/'world.json').read_text())
  def fixture(name,cash=1000000,cloak=0,turns=500):
   data=root/name;data.mkdir();path=data/'world.json';w=copy.deepcopy(original)
   w['Players']['1'].update(Sector=1,Credits=cash,Cloak=cloak,Turns=turns)
   w['Players']['2'].update(Sector=2,Cloak=1)
   w['Sectors']['1']['Warps']=[2];w['Sectors']['2']['Warps']=[1]
   path.write_text(json.dumps(w));return data,path,w
  def scan(text):
   matches=re.findall(r'\[ Sensors Activated \](.*?)\[ End Sensor Scan \]',text,re.S)
   assert len(matches)==1,text
   return matches[0]
  for classic in (False,True):
   prompt=b'Main Command (?=Help)?'if classic else b'> ';ending='q;y'if classic else'q'
   for cash in (999,1000,1001):
    data,path,w=fixture('energy'+str(classic)+str(cash),cash=cash)
    command='p;1;1;0;i;'+ending if classic else'p;equip cloak 1;i;'+ending
    text=guard.run(play,data,'Captain',command,classic=classic)
    saved=json.loads(path.read_text());p=saved['Players']['1'];bought=cash>=1000
    assert p['Credits']==cash-1000*int(bought) and abs(p.get('Cloak',0)-.01*int(bought))<1e-12 and p['Turns']==499 and saved['Version']==22,text
    assert text.count('Cloak energy purchased and saved:')==int(bought),text
    if bought:assert f'credits spent: 1000. Balance: {cash-1000}.'in text,text
   if classic:
    data,path,w=fixture('blank',cash=10000,cloak=.9)
    text=guard.run(play,data,'Captain','p;1',classic=True,followups=[(b'(0 cancels)? ',b'\r'),(b'Buy Which Item? -=>',b'0;i;q;y\r')])
    p=json.loads(path.read_text())['Players']['1'];assert p['Credits']==0 and p.get('Cloak',0)==1 and '10 points; credits spent: 10000'in text,text
   data,path,w=fixture('active'+str(classic),cloak=.75)
   initial='p;6;y'if classic else'p;anticloak;y'
   again=b'6;y\r'if classic else b'anticloak;y\r'
   continuation=('0;i;s;'+ending+'\r').encode()if classic else('i;s;'+ending+'\r').encode()
   shop=b'Buy Which Item? -=>'if classic else prompt
   text=guard.run(play,data,'Captain',initial,classic=classic,followups=[(b'Activate? [y/N]',b'y\r'),(shop,again),(b'Activate? [y/N]',b'y\r'),(shop,continuation)])
   saved=json.loads(path.read_text());p=saved['Players']['1']
   assert p['Credits']==0 and p.get('Cloak',0)==.75 and p['Turns']==499 and saved['Players']['2']['Cloak']==1,text
   assert text.count('Anti-cloak activation saved for this login.')==2 and 'Balance: 500000. Newly revealed: 1.'in text and 'Balance: 0. Newly revealed: 0.'in text,text
   assert 'Enemy'in scan(text) and 'Anti-cloak active for this login'in text and 'FAIL'not in text,text
   reload=guard.run(play,data,'Captain','i;s;'+ending,classic=classic)
   assert 'Enemy'not in scan(reload)and 'Anti-cloak active for this login'not in reload,reload
   # The other account never loses stored energy or inherits the buyer's effect.
   other=guard.run(play,data,'Enemy','i;'+ending,classic=classic)
   assert 'Anti-cloak active for this login'not in other
   assert json.loads(path.read_text())['Players']['2']['Cloak']==1
   for label,answer in (('no',b'n\r'),('stacked',b'y;q\r')):
    data,path,w=fixture(label+str(classic),cloak=1)
    text=guard.run(play,data,'Captain',initial,classic=classic,followups=[(b'Activate? [y/N]',answer),(shop,('0;s;'+ending+'\r').encode()if classic else('s;'+ending+'\r').encode())])
    p=json.loads(path.read_text())['Players']['1'];assert p['Credits']==1000000 and p.get('Cloak',0)==1 and p['Turns']==499 and 'activation saved'not in text and 'Enemy'not in scan(text),text
   data,path,w=fixture('decay'+str(classic),cloak=1,turns=477)
   text=guard.run(play,data,'Captain',initial,classic=classic,followups=[(b'Activate? [y/N]',b'y\r'),(shop,('0;move 2;i;'+ending+'\r').encode()if classic else('move 2;i;'+ending+'\r').encode())])
   p=json.loads(path.read_text())['Players']['1'];assert p['Turns']==475 and abs(p.get('Cloak',0)-.99)<1e-12 and p['Credits']==500000,text
 print('Cloak equipment PTY passed: compact/classic exact purchases, blank default, fresh paid activation/repeat, actual reveal counts, cancellation/typeahead safety, normal decay, victim energy and reconnect isolation.')


if __name__=='__main__':run_on_stable_date(exercise)
