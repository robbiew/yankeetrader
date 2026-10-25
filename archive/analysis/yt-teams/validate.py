"""Check preserved original-DOS team behavior; does not run or edit a game."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis/yt-maint'))
from experiments import get,record
R=ROOT/'analysis/yt-combat/experiments';checks=0
CASES=['create-confirm','join','wrong','full','quit','banish','member-privilege','password','last','defense','transfer-current','transfer-foreign','promote','port-account','withdraw-defense','rejoin','successor','short-name','lowercase','quit-assets','search']
def ck(v,msg):
 global checks
 assert v,msg
 checks+=1
def load(n,f='YTDATA.DAT'):return (R/('team-'+n)/f).read_bytes()
def log(n):return (R/('team-'+n)/'GAME.LOG').read_text(errors='replace').replace('\\r\\n','\n')
def slots(b):return [get(b,52,o) for o in [109,117,121,125]]
def pw(b):return b[51*137+113:51*137+117]
original=hashlib.sha256((ROOT/'YT.EXE').read_bytes()).hexdigest()
for n in CASES:
 a=load(n,'before.dat');b=load(n)
 ck(len(b)==4151*137,n+' record count/layout')
 ck(get(b,2,49)==(499 if n=='defense' else 500),n+' turns')
 ck(hashlib.sha256((R/('team-'+n)/'YT.EXE').read_bytes()).hexdigest()==original,n+' binary identity')
 ck(a[51*137+41:51*137+73]==b[51*137+41:51*137+73],n+' team overlay preserves warp/port fields')
b=load('create-confirm');ck(get(b,2,89)==1 and get(b,52,77)==2,'creator becomes captain')
ck(slots(b)==[2,0,0,0] and pw(b)==b'ABCD','created roster/password');ck(record(b,52)['text']=='Orion' and get(b,52,73)==5,'created name');ck(get(b,2,81)==100000,'creation free');ck('CREATED!' in log('create-confirm'),'creation output')
b=load('short-name');ck(get(b,2,89)==0 and slots(b)==[0,0,0,0],'short name no membership');ck('MUST more than 2 letters' in log('short-name'),'short name rejected')
for n in ['join','lowercase']:
 b=load(n);ck(get(b,2,89)==1 and slots(b)==[3,2,0,0],n+' first free member slot');ck(get(b,52,77)==3 and pw(b)==b'ABCD',n+' captain/password retained');ck('info has been recorded' in log(n),n+' successful join')
for n,phrase in [('wrong','Invalid Password'),('full','picked is full')]:
 a=load(n,'before.dat');b=load(n);ck(get(b,2,89)==0 and slots(b)==slots(a),n+' no membership change');ck(phrase in log(n),n+' rejection output')
b=load('member-privilege');ck(pw(b)==b'ABCD','member cannot change secret');ck('Invalid Choice!' in log('member-privilege'),'privileged option rejected');ck('8) Change Team Password' not in log('member-privilege'),'privileged option hidden')
b=load('password');ck(pw(b)==b'WXYZ' and slots(b)==[2,3,0,0],'captain can change secret')
b=load('banish');ck(get(b,3,89)==0 and slots(b)==[2,0,0,0],'banish updates both relations');ck(pw(b)==b'ABCD','banish leaves secret');ck('Now change your Team Password' in log('banish'),'banish warning');ck(get(b,4053,73)==3 and get(b,4053,117)==10000,'banishment does not confiscate planet')
ck(load('banish')==load('rejoin','before.dat'),'rejoin exact persisted predecessor')
b=load('rejoin');ck(get(b,3,89)==1 and slots(b)==[2,3,0,0],'kicked player rejoins with unchanged secret');ck('info has been recorded' in log('rejoin'),'rejoin output')
b=load('quit');ck(get(b,2,89)==0 and slots(b)==[0,3,0,0],'quit removes player/roster');ck(get(b,52,77)==2,'quit leaves stale captain until successor');ck('Permission to land is DENIED!' in log('quit'),'former teammate access revoked')
ck(load('quit')==load('successor','before.dat'),'successor exact persisted predecessor')
for n in ['successor','promote']:
 b=load(n);ck(get(b,52,77)==3 and get(b,3,89)==1,n+' new captain');ck('promoted to Captain!' in log(n),n+' promotion output')
b=load('last');ck(get(b,2,89)==0 and slots(b)==[0,0,0,0],'last member leaves');ck(get(b,52,77)==0 and pw(b)==b'    ','last member clears captain/password');ck(record(b,52)['text']=='Orion','inactive name can persist')
b=load('defense');ck(get(b,2,57)==101 and get(b,2,61)==1000,'friendly defense permits passage');ck(get(b,152,81)==100 and get(b,152,85)==3,'passage preserves defense')
for n,owner in [('transfer-current',3),('transfer-foreign',4)]:
 b=load(n);ck(get(b,2,61)==877 and get(b,151,81)==223,n+' fighter conservation');ck(get(b,151,85)==owner,n+' defense ownership');ck(get(b,2,57)==100,n+' current sector');ck('Fighters transferred!' in log(n),n+' completion')
ck('have to defeat the fighters' in log('transfer-foreign'),'reinforced hostile defense still blocks')
b=load('withdraw-defense');ck(get(b,2,61)==1000 and get(b,151,81)==100,'cannot withdraw ally defense');ck('already fighters in this sector' in log('withdraw-defense'),'withdrawal refused')
b=load('port-account');ck(get(b,2,81)==100000 and get(b,3053,89)==10000,'team treasury not collected');ck("don't OWN any ports" in log('port-account'),'no personal ports rejection')
b=load('quit-assets');ck(get(b,2,89)==0,'asset fixture quit committed');ck(get(b,4054,73)==2 and get(b,4054,117)==12000,'own planet retained');ck(get(b,153,81)==200 and get(b,153,85)==2,'own defense retained');ck(get(b,3053,97)==2 and get(b,2,117)==1,'own port retained');ck(get(b,2,81)==107000 and get(b,3053,89)==0,'own treasury still collectible');ck('Permission to land is DENIED!' in log('quit-assets'),'former teammate denied after collecting own cash')
ck('Locating Team Members, Planets & Defenses.' in log('search') and 'Planets; 100' in log('search'),'resource search lists teammate planet')
for row in json.loads((ROOT/'analysis/executable-inventory.json').read_text()):ck(hashlib.sha256((ROOT/row['file']).read_bytes()).hexdigest()==row['sha256'],'original '+row['file'])
print(f'{checks} checks passed across {len(CASES)} original DOS sessions.')
