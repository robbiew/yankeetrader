"""Multi-process Door32 campaign through simulated TCP BBS callers.

Only the production initializer and callers mutate the disposable game world.
The planner reads snapshots to select legal paths; it never grants assets/titles.
"""
import argparse
import collections
import concurrent.futures
import errno
import hashlib
import json
import os
from pathlib import Path
import pty
import re
import select
import socket
import subprocess
import threading
import time

ROOT=Path(__file__).resolve().parents[1]
ANSI=re.compile(rb'\x1b(?:\[[0-?]*[ -/]*[@-~]|[@-_])')
MAIN=rb'(?:Main Command \(\?=Help\)\? |Sector \d+ \| \d+ credits \| \d+ turns > )'
PAGER=rb'More (?:news|messages)\? \[Enter=more, Q=stop\] '

class CampaignExhausted(Exception):
    """A committed black-hole receipt proves this disposable attempt cannot continue."""


class Caller:
    """A TCP caller attached to a BBS node, then a real Door32 child process."""
    def __init__(self, campaign, uid, alias, classic=False, minutes=30, emulation=0):
        self.campaign=campaign;self.uid=uid;self.alias=alias;self.classic=classic
        self.hazards=set();self.started=time.monotonic()
        with campaign.lock:
            self.index=len(campaign.callers)+1;campaign.callers.append(self)
        self.node=campaign.root/f'node-{self.index}'
        self.node.mkdir()
        (self.node/'DOOR32.SYS').write_text(f'2\n0\n38400\nSimulated TCP BBS\n{uid}\n{alias}\n{alias}\n10\n{minutes}\n{emulation}\n{self.index}\n')
        listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen(1)
        self.endpoint=listener.getsockname();self.client=socket.create_connection(self.endpoint)
        self.server,_=listener.accept();listener.close()
        self.master,slave=pty.openpty()
        options=[] if classic else ['-compact']
        if not emulation:options.append('-ascii')
        self.proc=subprocess.Popen([str(campaign.binary),*options,'-data',str(campaign.data),'-drop',str(self.node),'-system','campaign-bbs'],stdin=slave,stdout=slave,stderr=slave,env={**os.environ,'GORACE':f'halt_on_error=1 log_path={self.node}/race'})
        os.close(slave)
        with campaign.lock:campaign.peak_processes=max(campaign.peak_processes,sum(getattr(c,'proc',None)is not None and c.proc.poll()is None for c in campaign.callers))
        self.probes=0;self.raw=bytearray();self.clean=b'';self.cursor=0;self.inputs=[];self.closed=False
        self.bridge_error=None;self.expected_exit=0;self.forced_stop=False
        self.thread=threading.Thread(target=self.bridge,daemon=True);self.thread.start()
        self.login()
    def bridge(self):
        try:
            while True:
                ready,_,_=select.select([self.server,self.master],[],[],.2)
                if self.server in ready:
                    chunk=self.server.recv(65536)
                    if not chunk:break
                    pending=memoryview(chunk)
                    while pending:pending=pending[os.write(self.master,pending):]
                if self.master in ready:
                    try:chunk=os.read(self.master,65536)
                    except OSError as e:
                        if e.errno==errno.EIO:break
                        raise
                    if not chunk:break
                    self.server.sendall(chunk)
                if self.proc.poll() is not None and not ready:break
        except (BrokenPipeError,ConnectionResetError):pass
        except Exception as e:self.bridge_error=repr(e)
        finally:
            try:self.server.shutdown(socket.SHUT_RDWR)
            except OSError:pass
            self.server.close()
            try:os.close(self.master)
            except OSError:pass
    def send(self, data):
        if isinstance(data,str):data=data.encode()+b'\r'
        self.inputs.append({'at':time.time(),'hex':data.hex()})
        self.client.sendall(data)
    def read(self, timeout=.2):
        if select.select([self.client],[],[],timeout)[0]:
            chunk=self.client.recv(65536)
            if not chunk:return False
            self.raw.extend(chunk);self.clean=ANSI.sub(b'',bytes(self.raw)).replace(b'\r',b'')
            probes=bytes(self.raw).count(b'\x1b[c')
            while self.probes<probes:
                self.probes+=1;self.send(b'\x1b[?1;2c')
        return True
    def expect(self, pattern, timeout=12, pages=True):
        pattern=re.compile(pattern);end=time.monotonic()+timeout
        while True:
            segment=self.clean[self.cursor:];match=pattern.search(segment)
            page=re.search(PAGER,segment) if pages else None
            if page and (match is None or page.start()<match.start()):
                self.cursor+=page.end();self.send(b'\r');continue
            if match:
                value=segment[:match.end()];self.cursor+=match.end();return value.decode('ascii',errors='replace')
            if time.monotonic()>end:raise AssertionError(f'{self.alias} timeout {pattern.pattern!r}: {segment[-1800:]!r}')
            if not self.read():raise AssertionError(f'{self.alias} EOF before {pattern.pattern!r}: {segment[-1800:]!r}')
    def login(self):
        pattern=MAIN+rb'|\[ Press any Key \]|-\+> |Is this OK \(Y/\[N\]\)\? |Do you want instructions \(Y/N\) \[N\]\? '
        for _ in range(12):
            out=self.expect(pattern)
            if re.search(MAIN,out.encode()):return
            if out.endswith('[ Press any Key ]'):self.send(b' ')
            elif out.endswith('-+> '):self.send(self.alias)
            elif out.endswith('Is this OK (Y/[N])? '):self.send('Y')
            elif 'Do you want instructions' in out:self.send('N')
        raise AssertionError('unbounded startup dialogue')
    def command(self, value, timeout=12):
        self.send(value);out=self.expect(MAIN,timeout)
        self.campaign.record(self,value,out)
        return out
    def finish(self):
        if self.closed:return
        self.closed=True
        try:
            if self.proc.poll() is None:
                self.send('q;y' if self.classic else 'q')
                end=time.monotonic()+3
                while time.monotonic()<end and self.read(.1):pass
                self.proc.wait(timeout=3)
        except (OSError,AssertionError,subprocess.TimeoutExpired):
            self.forced_stop=True;self.proc.terminate()
            try:self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:self.proc.kill();self.proc.wait()
        finally:
            self.client.close();self.thread.join(timeout=3)
            self.save()
    def disconnect(self):
        self.expected_exit="carrier-loss"
        self.client.shutdown(socket.SHUT_RDWR);self.client.close();self.closed=True
        try:
            try:code=self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired as error:
                self.forced_stop=True;self.proc.terminate()
                try:self.proc.wait(timeout=2)
                except subprocess.TimeoutExpired:self.proc.kill();self.proc.wait()
                raise AssertionError('door failed to exit naturally after carrier loss') from error
            assert code==0,('unexpected carrier loss exit',code)
        finally:
            self.thread.join(timeout=2);self.save()
    def save(self):
        (self.node/'terminal.bin').write_bytes(self.raw)
        (self.node/'terminal.txt').write_text(self.clean.decode('ascii',errors='replace'))
        (self.node/'inputs.json').write_text(json.dumps(self.inputs,indent=2)+'\n')

class Campaign:
    def __init__(self,root,binary,seed=36,threshold=20,sectors=32):
        self.root=root;root.mkdir(parents=True,exist_ok=False);self.data=root/'world';self.binary=binary
        self.callers=[];self.actions=[];self.findings=[];self.lock=threading.Lock();self.started=time.time();self.snapshots_checked=0;self.peak_processes=0
        self.driver_source=Path(__file__).read_bytes()
        (root/'driver.py').write_bytes(self.driver_source)
        self.runtime_patch=subprocess.check_output(['git','diff','HEAD','--','internal','cmd'],cwd=ROOT)
        (root/'build-metadata.txt').write_bytes(subprocess.check_output(['go','version','-m',str(binary)]))
        subprocess.run([str(binary),'-data',str(self.data),'-init','-seed',str(seed),'-sectors',str(sectors),'-genesis-ports',str(threshold)],check=True,capture_output=True)
        self.initial=(self.data/'world.json').read_bytes();(root/'initial-world.json').write_bytes(self.initial)
    def world(self):
        w=json.loads((self.data/'world.json').read_text())
        with self.lock:self.snapshots_checked+=1
        for key,p in w['Players'].items():
            assert p['ID']==int(key) and 0<=p['Credits']<=9_000_000_000_000_000 and 0<=p['Turns']<=500,p
            assert sum(p['Cargo'])<=p['Holds'] and min(p['Cargo'])>=0,p
        for port in w['Ports'].values():
            assert port['Owner']==0 or str(port['Owner'])in w['Players'],port
            assert port['Treasury']>=0,port
        for planet in w['Planets'].values():
            assert w['Sectors'][str(planet['Sector'])]['Planet']==planet['ID'],planet
        for field,next_id in [('Radio','NextRadio'),('News','NextNews')]:
            ids=[entry['ID']for entry in w.get(field,[])];assert ids==sorted(set(ids)),(field,ids)
            assert not ids or w[next_id]>ids[-1],field
        assert len(w.get('Radio',[]))<=4096 and len(w.get('News',[]))<=1024
        return w
    def player(self,caller):return next(p for p in self.world()['Players'].values() if p['Identity']==f'door32:campaign-bbs:{caller.uid}')
    def record(self,caller,command,out):
        w=self.world()
        with self.lock:self.actions.append({'at':time.time(),'node':caller.index,'uid':caller.uid,'command':command,'output':out})
        # Only this exact committed receipt plus the authoritative zero balance
        # permits a fresh-world retry. Timeouts/assertions never do.
        depleted=re.search(r'Disruption arrival saved: final sector (\d+); total action turns spent \d+; remaining 0\. Queued travel stopped\.',out)
        if depleted and 'Forced warp saved:' in out:
            p=next(p for p in w['Players'].values() if p['Identity']==f'door32:campaign-bbs:{caller.uid}')
            assert p['Turns']==0 and p['Sector']==int(depleted[1]),('inconsistent exhaustion receipt',p,out)
            raise CampaignExhausted(f'{caller.alias}: committed black-hole arrival exhausted turns')
    def checkpoint(self,name):
        raw=(self.data/'world.json').read_bytes();(self.root/(name+'-world.json')).write_bytes(raw)
        return json.loads(raw)
    def goto(self,caller,target):
        for _ in range(128):
            w=self.world();p=next(p for p in w['Players'].values() if p['Identity']==f'door32:campaign-bbs:{caller.uid}')
            current=p['Sector']
            if current==target:return True
            if target in caller.hazards:return False
            assert p['Turns']>0,('legitimate daily turn limit reached',p)
            queue=collections.deque([[current]]);seen={current};path=None
            while queue:
                candidate=queue.popleft()
                if candidate[-1]==target:path=candidate;break
                for to in w['Sectors'][str(candidate[-1])]['Warps']:
                    if to not in seen and to not in caller.hazards:seen.add(to);queue.append(candidate+[to])
            assert path and len(path)>1,('unreachable',current,target)
            out=caller.command(f'm {path[1]}')
            caller.hazards.update(int(x) for x in re.findall(r'Forced warp saved: sector (\d+) ->',out))
        raise AssertionError('movement failed to converge with live disruptions')
    def buy(self,caller):
        caller.send('b');out=caller.expect(rb'Do you wish to buy it\? \[y/N\] ')
        caller.send('y');out+=caller.expect(MAIN);self.record(caller,'b [separate y]',out)
        return out
    def report(self, outcome):
        for c in self.callers:c.save()
        (self.root/'actions.json').write_text(json.dumps(self.actions,indent=2)+'\n')
        summary={'outcome':outcome,'started':self.started,'ended':time.time(),'callers':len(self.callers),'pre_reset_callers':6,'peak_processes':self.peak_processes,'snapshots_checked':self.snapshots_checked,'actions':len(self.actions),'findings':self.findings,'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'binary_sha256':hashlib.sha256(self.binary.read_bytes()).hexdigest(),'initial_sha256':hashlib.sha256(self.initial).hexdigest(),'final_sha256':hashlib.sha256((self.data/'world.json').read_bytes()).hexdigest()}
        summary['nodes']=[{'node':node.index,'uid':node.uid,'classic':node.classic,'tcp_endpoint':node.endpoint,'returncode':node.proc.poll(),'expected_exit':node.expected_exit,'forced_stop':node.forced_stop,'known_hazards':sorted(node.hazards),'race_logs':[str(p.relative_to(self.root))for p in node.node.glob('race.*')]}for node in self.callers]
        summary['script_sha256']=hashlib.sha256(self.driver_source).hexdigest()
        patch=self.runtime_patch
        (self.root/'source.patch').write_bytes(patch);summary['source_patch_sha256']=hashlib.sha256(patch).hexdigest()
        post_failures=[]
        for node in summary['nodes']:
            if node['race_logs']:post_failures.append({'race_logs':node['race_logs']})
            expected=0 if node['expected_exit']=='carrier-loss' else node['expected_exit']
            if node['forced_stop'] or node['returncode']!=expected:post_failures.append({'unexpected_exit':node})
        if post_failures:
            summary['outcome']='failed';summary['findings'].extend(post_failures)
        (self.root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
        manifest={str(path.relative_to(self.root)):hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(self.root.rglob('*')) if path.is_file() and path.name!='manifest.json'}
        (self.root/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        assert not post_failures,post_failures
        return summary

def run(c):
    a=Caller(c,101,'Atlas');b=Caller(c,102,'Broker');observer=Caller(c,103,'Observer',classic=True)
    short=Caller(c,104,'ShortTimer',minutes=1)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        extra=list(pool.map(lambda spec:Caller(c,*spec),[(105,'WatchANSI',True,30,1),(106,'TraderANSI',False,30,1)]))
    # Initial simultaneous writers/readers; all sessions remain alive.
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(lambda x:x.command('i'),[a,b,observer,short,*extra]))
    c.checkpoint('four-active')
    # Two confirmed previews race for the same previously unowned title.
    for market_port in range(2,9):
        if c.goto(a,market_port) and c.goto(b,market_port) and c.goto(observer,market_port):break
    assert c.player(a)['Sector']==c.player(b)['Sector']==c.player(observer)['Sector']==market_port
    for caller in (a,b):caller.send('b');caller.expect(rb'Do you wish to buy it\? \[y/N\] ')
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        def approve(caller):caller.send('y');out=caller.expect(MAIN);c.record(caller,'competing buyout y',out);return out
        outcomes=list(pool.map(approve,(a,b)))
    assert sum('Sold!'in x for x in outcomes)==1,outcomes
    w=c.checkpoint('competing-buyouts');assert sum(p['Credits'] for p in w['Players'].values())==6*1005-31
    if w['Ports'][str(market_port)]['Owner']!=c.player(b)['ID']:c.buy(b)
    # A simultaneous reader holds a quote that another buyer invalidates.
    assert c.goto(observer,market_port)
    observer.send('b');observer.expect(rb'Do you wish to buy it\? \[y/N\] ')
    c.buy(a);stale_before=c.world();observer.send('y');stale=observer.expect(MAIN);c.record(observer,'stale buyout y',stale);assert 'changed' in stale,stale
    assert c.player(observer)['Credits']==next(p['Credits']for p in stale_before['Players'].values()if p['Identity']==f'door32:campaign-bbs:{observer.uid}')
    assert len(c.world().get('Radio',[]))==len(stale_before.get('Radio',[]))
    # Seller reads his private snapshot while the unrelated observer cannot.
    notices=b.command('messages');assert 'Atlas bought your port' in notices,notices
    seen=observer.command('messages');assert 'bought your port'not in seen,seen
    # Actual trade, not edited starting credits or cargo.
    good=next(i for i,v in enumerate(c.world()['Ports'][str(market_port)]['Coefficient']) if v>0)
    commodity=('ore','organics','equipment')[good]
    b.command('p');trade=b.command(f'buy {commodity} 1');assert c.player(b)['Cargo'][good]==1,trade
    for destination,port in c.world()['Ports'].items():
        if int(destination)!=1 and port['Coefficient'][good]<0 and c.goto(b,int(destination)):break
    b.command('p');b.command(f'sell {commodity} 1');assert c.player(b)['Cargo'][good]==0
    # An aborted document and abrupt connection loss never publish draft text.
    b.send('radio EDIT Atlas;y');b.expect(rb' 1: ');b.send('DISCONNECTED DRAFT');b.expect(rb' 2: ')
    b.disconnect()
    assert not any(m.get('Text')=='DISCONNECTED DRAFT' for m in c.world().get('Radio',[]))
    b=Caller(c,102,'Broker');assert c.player(b)['Identity']=='door32:campaign-bbs:102'
    # Concurrent commands from several active nodes serialize one shared world.
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        def browse(caller):
            for _ in range(8):caller.command('i');caller.command('messages')
        list(pool.map(browse,(b,observer,*extra)))
    # Independently confirmed public text and private text stay in their scopes.
    a.send('radio Broker;y');a.expect(rb'Message \(one line,.*?: ');a.send('PRIVATE CAMPAIGN');a.expect(rb'\[S\] Send \[A\] Abort -=> ');a.send('s');a.expect(MAIN)
    a.send('radio ALL;y');a.expect(rb'Message \(one line,.*?: ');a.send('PUBLIC CAMPAIGN');a.expect(rb'\[S\] Send \[A\] Abort -=> ');a.send('s');a.expect(MAIN)
    assert 'PRIVATE CAMPAIGN'not in observer.command('messages')
    assert 'PUBLIC CAMPAIGN'in observer.command('news today')
    # Team play: masked credentials, private roster mail, and a teammate title
    # that must not satisfy Atlas's personal Genesis threshold.
    a.send('team;2;TCP Crew');a.expect(rb'Team password \(4 characters; entered separately\): ');a.send('TEST');a.expect(rb'Team Command\? ');a.send('1');a.expect(MAIN)
    b.send('team;3;1');b.expect(rb'Team password \(4 characters; entered separately\): ');b.send('TEST');b.expect(rb'Team Command\? ');b.send('1');b.expect(MAIN)
    a.send('radio TEAM;y');a.expect(rb'Message \(one line,.*?: ');a.send('TEAM CAMPAIGN');a.expect(rb'\[S\] Send \[A\] Abort -=> ');a.send('s');a.expect(MAIN)
    assert 'TEAM CAMPAIGN'not in observer.command('messages')
    assert 'TEAM CAMPAIGN'in b.command('messages')
    for team_port in range(32,25,-1):
        if c.goto(b,team_port):break
    assert 'Sold!'in c.buy(b)
    # Legitimately acquire nineteen ports through caller commands while other
    # processes continue to inspect the same world.
    targets=iter(range(2,33))
    while sum(port['Owner']==c.player(a)['ID'] for i,port in c.world()['Ports'].items() if i!='1')<19:
        target=next(targets)
        if target==team_port or c.world()['Ports'][str(target)]['Owner']==c.player(a)['ID']:continue
        if not c.goto(a,target):continue
        assert 'Sold!'in c.buy(a)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(lambda caller:caller.command('i'),(b,observer)))
    p=c.player(a)
    assert sum(port['Owner']==c.player(b)['ID'] for i,port in c.world()['Ports'].items() if i!='1')>=1
    denied=a.command('genesis');assert '1 short'in denied and 'Type GENESIS'not in denied,denied
    while True:
        target=next(targets)
        if target==team_port or c.world()['Ports'][str(target)]['Owner']==c.player(a)['ID']:continue
        if c.goto(a,target):break
    assert 'Sold!'in c.buy(a)
    before_reset=c.checkpoint('earned-victory');assert sum(port['Owner']==p['ID'] for i,port in before_reset['Ports'].items() if i!='1')==20
    # Let the real one-minute Door32 allowance expire with the caller idle.
    short.command('p');short_before=c.player(short).copy();short.send(b'equip fighters 1')
    short.expect(rb'session time expired',timeout=75)
    short.proc.wait(timeout=3);short.expected_exit=1
    assert c.player(short)==short_before,'idle expiry mutated the player'
    # Both remaining live callers hold stale input across the winning reset.
    observer.send('b');observer.expect(rb'Do you wish to buy it\? \[y/N\] ')
    b.send('radio EDIT Atlas;y');b.expect(rb' 1: ');b.send('OLD SEASON DRAFT');b.expect(rb' 2: ')
    a.send('genesis');a.expect(rb'Type GENESIS to confirm this reset \(blank cancels\): ');a.send('GENESIS')
    receipt=a.expect(rb'This login has ended; reconnect to join.');assert 'won season 1 with 20 ports'in receipt,receipt
    saved=c.checkpoint('victory-reset');assert saved['Season']==2 and not saved['Players'] and len(saved['SeasonResults'])==1
    assert not saved.get('Radio') and not saved.get('News') and not saved.get('Teams')
    assert all(port['Owner']==0 and port['Treasury']==0 for port in saved['Ports'].values())
    assert saved['SeasonResults'][0]['Winner']=='Atlas' and saved['SeasonResults'][0]['Ports']==20
    a.proc.wait(timeout=3)
    # Recreate the same numeric player IDs and initial ship generations while
    # the old Broker/Observer still hold input. This must not reauthorize them.
    fresh=Caller(c,101,'Atlas');new_b=Caller(c,102,'Broker');new_observer=Caller(c,103,'Observer')
    assert c.player(new_b)['ID']==next(p['ID']for p in before_reset['Players'].values()if p['Identity']=='door32:campaign-bbs:102')
    assert c.player(new_observer)['ID']==next(p['ID']for p in before_reset['Players'].values()if p['Identity']=='door32:campaign-bbs:103')
    for replacement in (new_b,new_observer):
        old=next(p for p in before_reset['Players'].values()if p['Identity']==f'door32:campaign-bbs:{replacement.uid}')
        assert c.player(replacement).get('ShipGeneration',0)==old.get('ShipGeneration',0)
    c.checkpoint('new-identities-before-stale-input')
    b.send(b'\rS\r');observer.send('y')
    for caller in extra:caller.send('i')
    for caller in (b,observer,*extra):
        result=caller.expect(rb'this season has ended; reconnect to join the new season');assert 'season has ended'in result
        caller.expected_exit=1;caller.proc.wait(timeout=3)
    assert (c.data/'world.json').read_bytes()==(c.root/'new-identities-before-stale-input-world.json').read_bytes(),'old callers mutated new season'
    # Reused numeric IDs and generations still cannot authorize stale nodes.
    history=fresh.command('seasons');assert 'Season 1: Atlas'in history,history
    assert 'you own 0'in fresh.command('genesis')
    c.checkpoint('new-season-reconnect')
    return {'winner':'Atlas','owned_ports':20,'threshold':20,'season':2}

def run_attempt(c,play):
    result='failed'
    try:
        result=play(c)
        return result
    except CampaignExhausted as error:
        result='exhausted';c.findings.append({'gameplay_exhaustion':str(error)})
        raise
    except BaseException as error:
        c.findings.append({'error':repr(error)});raise
    finally:
        for caller in c.callers:caller.finish()
        # Cleanup/race/exit failures override exhaustion and must never retry.
        c.report(result)

def run_campaigns(root,binary,seed,attempts=3,make_campaign=Campaign,play=run):
    assert 1<=attempts<=3
    root.mkdir(parents=True,exist_ok=False)
    history=[]
    for number in range(1,attempts+1):
        path=root/f'attempt-{number}'
        c=make_campaign(path,binary,seed)
        try:
            result=run_attempt(c,play)
        except CampaignExhausted as error:
            history.append({'path':path.name,'outcome':'exhausted','reason':str(error)})
            (root/'summary.json').write_text(json.dumps({'outcome':'exhausted','attempts':history},indent=2)+'\n')
            continue
        except BaseException:
            history.append({'path':path.name,'outcome':'failed'})
            (root/'summary.json').write_text(json.dumps({'outcome':'failed','attempts':history},indent=2)+'\n')
            raise
        history.append({'path':path.name,'outcome':'passed'})
        (root/'summary.json').write_text(json.dumps({'outcome':result,'attempts':history,'winning_attempt':path.name},indent=2)+'\n')
        return result
    raise AssertionError(f'black-hole turns exhausted in all {attempts} fresh campaign attempts; evidence retained')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);parser.add_argument('--seed',type=int,default=36);args=parser.parse_args()
    print(json.dumps(run_campaigns(args.out,ROOT/'bin/yt',args.seed)))
if __name__=='__main__':main()
