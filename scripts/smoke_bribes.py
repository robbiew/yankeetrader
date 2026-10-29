"""Drive real GoDoors confirmations, recruitment, refusal and saved balances."""
from pathlib import Path
import copy,json,re,subprocess,tempfile
from smoke_newspaper import BINARY,play
ROOT=Path(__file__).resolve().parents[1]
CONFIRM=b'defeat forces emergency escape. [y/N] '
transcript=''
with tempfile.TemporaryDirectory(prefix='yt-bribes-smoke-') as temp:
 root=Path(temp);source=root/'seed'
 subprocess.run([BINARY,'-data',str(source),'-init','-sectors','8'],check=True,capture_output=True)
 transcript+=play(source,'Captain','q')+play(source,'Enemy','q')
 seed=json.loads((source/'world.json').read_text());seed['Players']['1'].update(Sector=8,Credits=10000,Fighters=1000)
 seed['Sectors']['8']['Defense']={'Owner':-2,'Fighters':100}
 def fixture(name,owner=-2):
  d=root/name;d.mkdir();w=copy.deepcopy(seed);w['Sectors']['8']['Defense']['Owner']=owner
  (d/'world.json').write_text(json.dumps(w));return d
 def saved(data):return json.loads((data/'world.json').read_text())
 for classic in (False,True):
  label='classic' if classic else 'compact';prompt=b'Main Command (?=Help)?' if classic else b'> '
  quit=b'q;y\r' if classic else b'q\r'
  data=fixture(label+'-cancel')
  if classic:
   text=play(data,'Captain','B',classic=True,followups=[(b'(blank cancels)? ',b'300\r'),(CONFIRM,b'n\r'),(prompt,quit)])
  else:
   text=play(data,'Captain','bribe 300;y',followups=[(CONFIRM,b'\r'),(prompt,quit)])
  transcript+=text;w=saved(data)
  assert 'Bribe cancelled.' in text and w['Players']['1']['Credits']==10000 and w['Players']['1']['Fighters']==1000 and w['Sectors']['8']['Defense']['Fighters']==100,text
  # A real Mercenary attempt has a recovered 5% pre-offer hostility risk.
  # Verify every outcome; use fresh worlds until recruitment is also exercised.
  for attempt in range(8):
   data=fixture(label+'-offer-'+str(attempt))
   w=saved(data);w['Players']['1']['Sector']=7;w['Sectors']['7']['Warps']=[8];(data/'world.json').write_text(json.dumps(w))
   text=play(data,'Captain','bribe 8 300',classic=classic,followups=[(CONFIRM,b'y\r'),(prompt,quit)])
   transcript+=text;w=saved(data);p=w['Players']['1']
   assert p['Turns']==499 and p['Sector']==8,text
   if '100 Mercenary fighters joined' in text:
    assert p['Credits']==9700 and p['Fighters']==1100 and not w['Sectors']['8'].get('Defense'),text
    # A separate process observes recruitment and cannot buy the cleared group again.
    text=play(data,'Captain','bribe 300;I;Q;Y' if classic else 'bribe 300;i;q',classic=classic);transcript+=text
    assert 'no hostile sector fighter group here' in text and saved(data)['Players']['1']['Credits']==9700,text
    break
   assert 'hostile refusal; no credits paid.' in text and 'Forced defense combat:' in text,text
   lost=int(re.search(r'Forced defense combat: (\d+) attackers lost',text)[1])
   assert p['Credits']==10000 and p['Fighters']==1000-lost,text
  else:raise AssertionError('Eight valid attempts all encountered hostility; recruitment path not exercised')
  data=fixture(label+'-human',owner=2)
  text=play(data,'Captain','bribe',classic=classic,followups=[(CONFIRM,b'y\r'),(prompt,quit)]);transcript+=text
  w=saved(data)
  assert 'faction refusal; no credits paid.' in text and 'Forced defense combat:' not in text,text
  assert w['Players']['1']['Credits']==10000 and w['Players']['1']['Fighters']==1000 and w['Sectors']['8']['Defense']['Fighters']==100,text
 (ROOT/'evidence/bribes-smoke.txt').write_text('\n'.join(line.rstrip() for line in transcript.splitlines())+'\n')
print('Bribery PTY passed: compact/classic confirmation, stacked approval rejection, recruitment/debit, reconnect, cleared-group replay and human refusal.')
