"""Exercise real PTY/GoDoors I/O, Door32 identity, and persistence in a temp world."""
from pathlib import Path
import tempfile,subprocess,os,pty,select,time,json,errno
root=Path(__file__).resolve().parents[1]
binary=str(root/'bin/yt')
def play(args,commands):
 master,slave=pty.openpty()
 proc=subprocess.Popen([binary,'-compact',*args],stdin=slave,stdout=slave,stderr=slave,close_fds=True)
 os.close(slave);chunks=[];sent=False;end=time.monotonic()+20
 try:
  while time.monotonic()<end:
   if select.select([master],[],[],.1)[0]:
    try:b=os.read(master,65536)
    except OSError as ex:
     if ex.errno==errno.EIO:break
     raise
    if not b:break
    chunks.append(b)
    if not sent and b'> ' in b''.join(chunks):
     os.write(master,commands.encode()+b'\r');sent=True
  proc.wait(timeout=2)
 finally:
  if proc.poll() is None:proc.kill();proc.wait()
  os.close(master)
 text=b''.join(chunks).decode(errors='replace').replace('\r','')
 assert proc.returncode==0,text
 assert 'Saved. Safe travels' in text,text
 return text
with tempfile.TemporaryDirectory(prefix='yt-smoke-') as temp:
 data=Path(temp)/'world'
 subprocess.run([binary,'-data',str(data),'-init','-sectors','8'],check=True,capture_output=True)
 transcript=play(['-data',str(data),'-local','Tester'],'p;equip fighters 1;m 2;p;buy ore 5;m 3;p;sell ore 5;q')
 world=json.loads((data/'world.json').read_text());p=world['Players']['1']
 assert (p['Credits'],p['Fighters'],p['Cargo'],p['Sector'],p['Turns'])==(1005,26,[0,0,0],3,495),p
 transcript+=play(['-data',str(data),'-local','Tester'],'i;q')
 before=(data/'world.json').read_bytes()
 for _ in range(2):
  result=subprocess.run([binary,'-data',str(data),'-maint'],check=True,capture_output=True,text=True)
  assert 'already current' in result.stdout,result
 assert (data/'world.json').read_bytes()==before,'same-day maintenance changed state'
 drop=Path(temp)/'node1';drop.mkdir()
 def write_drop(alias):
  (drop/'DOOR32.SYS').write_text(f'0\n0\n38400\nSmoke BBS\n42\nReal Name\n{alias}\n10\n60\n0\n1\n')
 write_drop('RemoteTrader')
 transcript+=play(['-data',str(data),'-drop',str(drop),'-system','smoke'],'p;equip fighters 1;q')
 write_drop('RemoteRenamed')
 transcript+=play(['-data',str(data),'-drop',str(drop),'-system','smoke'],'i;q')
 world=json.loads((data/'world.json').read_text());p=world['Players']['2']
 assert len(world['Players'])==2 and p['Identity']=='door32:smoke:42' and p['Alias']=='RemoteRenamed',world['Players']
 assert (p['Credits'],p['Fighters'],p['Turns'])==(905,26,499),p
 # Controlled builder fixture; the production CLI has no free-credit/debug flag.
 p=world['Players']['1'];p['Credits']=100000;p['Holds']=100;p['Cargo']=[10,20,30];p['Sector']=1;p['DockToken']='';p['PlanetToken']='';p['LandedPlanet']=0
 (data/'world.json').write_text(json.dumps(world))
 transcript+=play(['-data',str(data),'-local','Tester'],'create New Eden;land;bank 15000;invest 251;transfer cargo;a;planet;leave;q')
 world=json.loads((data/'world.json').read_text());p=world['Players']['1'];planet=world['Planets']['2']
 assert p['Credits']==59749 and p['Cargo']==[20,30,40] and planet['Bank']==15000,(p,planet)
 transcript+=play(['-data',str(data),'-local','Tester'],'land;bank 0;q')
 world=json.loads((data/'world.json').read_text());assert world['Players']['1']['Credits']==74749 and world['Planets']['2']['Bank']==0
 (root/'evidence/local-smoke.txt').write_text(transcript)
 print('PTY/GoDoors smoke passed: trade/equipment loop, reconnect, repeat maintenance, Door32 local transport and stable identity across alias changes; planet creation, upgrades, transfers, banking and reconnect.')
