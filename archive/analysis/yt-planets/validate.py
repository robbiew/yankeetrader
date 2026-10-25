"""Assertions against preserved original DOS sessions; no live game mutations."""
from pathlib import Path
import sys,math,json,hashlib
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis/yt-maint'))
from experiments import get,record
R=ROOT/'analysis/yt-combat/experiments';checks=0
CASES=['takeall','transfer-cargo','transfer-weapons','create','poor','full','bank-deposit','bank-withdraw','bank-negative','bank-over','bank-halfday','invest1','invest251','foreign','team-bank','unguarded-bank','ground','ground90','ground0','move-yes','move-collision','lazy-production','bank-large','bank-large-relogin']
def ck(v,msg):
 global checks
 assert v,msg
 checks+=1
def load(n,f='YTDATA.DAT'):return (R/('planet-'+n)/f).read_bytes()
def log(n):return (R/('planet-'+n)/'GAME.LOG').read_text(errors='replace').replace('\\r\\n','\n')
def near(a,b,t=.03):return abs(a-b)<=t
for n in CASES:
 b=load(n);ck(len(b)==4151*137,n+' file layout')
 ck(get(b,2,49)==(490 if n=='move-yes' else 500),n+' turn accounting')
 ck(hashlib.sha256((R/('planet-'+n)/'YT.EXE').read_bytes()).hexdigest()==hashlib.sha256((ROOT/'YT.EXE').read_bytes()).hexdigest(),n+' executable identity')
# Creation allocates first free slot, initializes stocks and charges credits.
b=load('create');slot=int(get(b,151,93));p=4051+slot
ck(slot==3,'creation skips existing slot 2');ck(record(b,p)['text']=='New Eden','creation name')
for o,w in [(45,1),(49,1),(53,1),(57,10),(61,10),(65,10),(129,30)]:ck(near(get(b,p,o),w,.002),'creation starting value '+str(o))
for o,w in [(73,2),(77,1),(69,0),(113,0),(117,0),(125,0),(85,8)]:ck(get(b,p,o)==w,'creation identity/defense '+str(o))
ck(get(b,2,81)==75000,'creation costs 25000');ck('created with Genesis Device!' in log('create'),'creation completed')
for n,phrase,cash in [('poor',"too poor",24999),('full','all planets are taken',100000)]:
 b=load(n);ck(phrase in log(n),n+' rejected');ck(get(b,2,81)==cash and get(b,151,93)==0,n+' no charge/link')
# Take-all fills remaining holds with equipment and takes weapons separately.
b=load('takeall')
for o,w in [(69,10),(73,20),(77,70),(61,10600),(97,77),(129,88),(113,99)]:ck(get(b,2,o)==w,'takeall aboard '+str(o))
ck(near(get(b,4053,65),260),'takeall equipment remainder');ck(0<=get(b,4053,129)<.03,'takeall fighter fraction retained')
# Depositing cargo conserves all three categories and raises production at surplus threshold.
b=load('transfer-cargo');a=load('transfer-cargo','before.dat')
for po,so,rate,total in [(57,69,45,110),(61,73,49,220),(65,77,53,330)]:
 ck(get(b,2,so)==0,'cargo removed '+str(so));ck(near(get(b,4053,po),total),'cargo deposited '+str(po))
 ck(get(b,4053,rate)=={45:12,49:23,53:34}[rate],'cargo surplus increases rate '+str(rate))
b=load('transfer-weapons')
for so,po,aboard,ground in [(113,113,0,99),(97,69,0,77),(129,125,0,88),(61,129,9877,723)]:
 ck(get(b,2,so)==aboard,'weapon removed '+str(so));ck(near(get(b,4053,po),ground),'weapon deposited '+str(po))
# Bank target balances, authorization, and rejection cases.
for n,cash,bank in [('bank-deposit',95000,15000),('bank-withdraw',110000,0),('bank-negative',100000,10000),('bank-over',100000,10000),('team-bank',110000,0),('unguarded-bank',110000,0)]:
 b=load(n);ck(get(b,2,81)==cash,n+' cash');ck(get(b,4053,117)==bank,n+' bank');ck(cash+bank==110000,n+' conservation')
ck('SAVINGS not a LOAN' in log('bank-negative'),'negative rejected');ck("don't have that many Credits" in log('bank-over'),'overdraft rejected')
ck('Permission to land is DENIED' in log('foreign'),'foreign defenses deny');ck('Planet command' not in log('foreign'),'no foreign planet menu')
for n in ['team-bank','unguarded-bank']:ck(get(load(n),4053,73)==3,n+' ownership retained')
# Half-day lazy update: elapsed seconds give one extra interest credit.
b=load('bank-halfday');d=.5+get(b,4053,89)/1440
ck(get(b,2,81)==1105001 and get(b,4053,117)==0,'halfday interest withdrawn')
ck(abs(get(b,2,81)-(100000+math.floor(1000000*(1+.01*d))))<=1,'halfday interest model')
ck(get(b,4053,77)==150,'halfday bank-assisted ground growth')
for n,cost in [('invest1',1),('invest251',251)]:
 b=load(n);ck(get(b,2,81)==100000-cost,n+' cost')
 for o,old in [(45,10),(49,20),(53,30)]:ck(near(get(b,4053,o),old+cost/250,.002),n+' fractional rate '+str(o))
ck('increased by .004' in log('invest1'),'one-credit fractional display')
for n,g,aboard,owner in [('ground',100,15,2),('ground90',90,25,2),('ground0',0,115,0)]:
 b=load(n);ck(get(b,4053,77)==g and get(b,2,121)==aboard,n+' force conservation');ck(get(b,4053,73)==owner,n+' governor')
ck('Insuficient forces!' in log('ground'),'negative garrison rejected')
b=load('move-yes');ck(get(b,151,93)==0 and get(b,152,93)==2 and get(b,2,57)==101,'relocation links and ship');ck('moved! (Xannoron Movers' in log('move-yes'),'relocation completed')
b=load('move-collision');ck(get(b,151,93)==0 and get(b,4053,85)==0,'collision destroys moving planet');ck(get(b,152,93)==3 and get(b,4054,85)==11,'collision destination survives');ck(get(b,2,61)==9674 and get(b,2,57)==100,'collision fighter loss/position');ck('lost 326 fighters' in log('move-collision'),'collision damage output')
# Production during play uses grown rates, unlike the maintenance ordering.
b=load('lazy-production');a=load('lazy-production','before.dat')
d=.5+get(b,4053,89)/1440
for rate,stock,old in [(45,57,1000),(49,61,2000),(53,65,3000)]:
 ck(near(get(b,4053,rate),old*(1+.01*d),.02),'lazy growth '+str(rate))
 ck(near(get(b,4053,stock),old*(1+.01*d)*d,.03),'lazy grown-rate production '+str(stock))
 ck(abs(get(b,4053,stock)-old*d)>2,'lazy differs from old-rate maintenance '+str(stock))
# Unmodified persisted balances carried across an actual later-clock login.
a=load('bank-large','before.dat');b=load('bank-large');c=load('bank-large-relogin','before.dat');d=load('bank-large-relogin')
ck(b==c,'second login uses exact first persisted world')
ck(get(a,2,81)==100000000 and get(a,4053,117)==0,'large baseline')
ck(get(b,2,81)==100000000 and get(b,4053,117)==1,'first deposit mints one saved credit')
ck(get(d,2,81)==100000000 and get(d,4053,117)==2,'second deposit mints one more saved credit')
ck(get(d,4053,89)>get(b,4053,89),'second login clock advances')
ck(get(d,1,81)==get(b,1,81),'no maintenance/day change')
ck('Returning to Yankee Trader Local Logon Program' in log('bank-large') and 'Returning to Yankee Trader Local Logon Program' in log('bank-large-relogin'),'both rounding sessions log out normally')
for row in json.loads((ROOT/'analysis/executable-inventory.json').read_text()):ck(hashlib.sha256((ROOT/row['file']).read_bytes()).hexdigest()==row['sha256'],'original '+row['file'])
print(f'{checks} checks passed across {len(CASES)} original DOS sessions.')
