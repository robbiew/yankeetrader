"""Exercise port buyout and remote collection through actual PTY/GoDoors I/O."""
from smoke_arrival_control import without_disruption, reject_disruption
from pathlib import Path
import errno, json, os, pty, select, subprocess, tempfile, time
root = Path(__file__).resolve().parents[1]
binary = str(root/'bin/yt')

@without_disruption
def play(data, alias, commands):
    master, slave = pty.openpty()
    proc = subprocess.Popen([binary,'-compact','-data',str(data),'-local',alias],stdin=slave,stdout=slave,stderr=slave)
    os.close(slave); output=b''; sent=False; deadline=time.monotonic()+20
    try:
        while time.monotonic()<deadline:
            if select.select([master],[],[],.1)[0]:
                try: chunk=os.read(master,65536)
                except OSError as e:
                    if e.errno==errno.EIO: break
                    raise
                if not chunk: break
                output+=chunk
                reject_disruption(output)
                if not sent and b'> ' in output:
                    os.write(master,commands.encode()+b'\r');sent=True
        proc.wait(timeout=2)
        assert proc.returncode==0 and b'Saved. Safe travels' in output,output
        return output.decode(errors='replace').replace('\r','')
    finally:
        if proc.poll() is None:proc.kill();proc.wait()
        os.close(master)

with tempfile.TemporaryDirectory(prefix='yt-ownership-smoke-') as temp:
    data=Path(temp)/'world'
    subprocess.run([binary,'-data',str(data),'-init','-sectors','8'],check=True,capture_output=True)
    play(data,'Buyer','q');play(data,'Seller','q')
    path=data/'world.json';w=json.loads(path.read_text())
    w['Players']['1'].update(Sector=2,Credits=100000)
    w['Players']['2']['Credits']=2000
    w['Ports']['2'].update(Owner=2,Treasury=777)
    path.write_text(json.dumps(w))
    transcript=play(data,'Buyer','b;y;treasury;$;q')
    w=json.loads(path.read_text())
    assert (w['Players']['1']['Credits'],w['Players']['2']['Credits'],w['Ports']['2']['Owner'],w['Ports']['2']['Treasury'])==(99969,2808,1,0),w
    # A later trading commission must belong to the new owner, not the seller.
    transcript+=play(data,'Seller','m 2;p;buy ore 5;q')
    w=json.loads(path.read_text());commission=w['Ports']['2']['Treasury'];assert commission>0
    transcript+=play(data,'Buyer','m 1;treasury;collect;collect;q')
    w=json.loads(path.read_text())
    assert w['Players']['1']['Credits']==99969+commission and w['Ports']['2']['Treasury']==0
    assert w['Players']['1']['Sector']==1
    transcript+=play(data,'Buyer','i;treasury;q')
    (root/'evidence/ownership-smoke.txt').write_text(transcript)
    print('PTY ownership passed: buyout payout, persisted owner, new-owner trading commission, remote collection, repeat collection and reconnect.')
