"""Exercise committed spy triggers, charged reports and private shared visibility."""
from pathlib import Path
import json
import subprocess
import tempfile
from smoke_spies import play, BINARY, ROOT


def fixture(data, cloak=0):
    subprocess.run([BINARY, '-data', str(data), '-init', '-sectors', '8'], check=True, capture_output=True)
    play(data, 'Caller', 'q')
    play(data, 'Enemy', 'q')
    path=data/'world.json'
    w=json.loads(path.read_text())
    w['Players']['1'].update(Sector=1,Credits=3000000,Turns=500,Missiles=5,Plasma=3,Mines=0)
    w['Players']['2'].update(Sector=8,Cloak=cloak,Fighters=42,Shields=10000,Missiles=0)
    for sector, warps in [(1,[2,8]),(2,[1]),(8,[7]),(7,[6]),(6,[])]:
        w['Sectors'][str(sector)]['Warps']=warps
        w['Sectors'][str(sector)]['Minefield']=[]
        w['Sectors'][str(sector)]['Defense']=None
    w['Sectors']['2']['Defense']=dict(Owner=-2,Fighters=10)
    w['Sectors']['7']['Minefield']=[dict(Count=7)]
    w['Sectors']['6']['Minefield']=[dict(Count=11)]
    empty=next(n for n in range(3,6) if not w['Sectors'][str(n)].get('Planet'))
    path.write_text(json.dumps(w))
    return path,empty


def main():
    transcripts=[]
    with tempfile.TemporaryDirectory(prefix='yt-spy-trigger-smoke-')as tmp:
        for classic in (False,True):
            data=Path(tmp)/('classic'if classic else'compact')
            path,empty=fixture(data)
            first=(f'p;9;1;8;0;f;0;c;15;9;{empty};15;1;!;2;1'if classic else
                   f'p;hire 8;f 0;spies;planetreport {empty};spies;missile 2 1')
            followups=[(b'[y/N] ',b'y\r'),
                (b'Missile launch saved:',(f'c;15;1;+;{empty};1\r'if classic else f'spies;plasma {empty} 1\r').encode()),
                (b'Confirm? [y/N] ',b'y\r'),
                (b'No course reached the requested destination; the accepted launch was spent.',b'c;15;1;s;q;y\r'if classic else b'spies;s;q\r')]
            out=play(data,'Caller',first,classic=classic,followups=followups)
            assert 'RADIO MESSAGE FROM SPY'not in out.split('Planet report saved:',1)[0],out
            assert 'One turn spent: no planet exists in that sector.'in out,out
            assert out.count('RADIO MESSAGE FROM SPY #1')==3,out
            assert 'found in sector 8:'in out and 'SECTOR HAS 7 MINES'in out and 'SECTOR HAS 11 MINES'in out,out
            assert 'Spy # 1 will hunt in sector 7.'in out and 'Spy # 1 will hunt in sector 6.'in out,out
            w=json.loads(path.read_text());p=w['Players']['1']
            assert p['Turns']==496 and p['Credits']==2667000 and p['Missiles']==4 and p['Plasma']==2,p
            assert w['Players']['2'].get('Cloak',0)==0 and not w.get('Radio') and w['Version']==28
            assert not any('spy' in e['Kind']for e in w.get('News',[]))
            transcripts.append(out)
            reconnect=play(data,'Caller','spies;intel;q')
            assert 'You do not have any spies!'in reconnect and 'No intelligence reports this login.'in reconnect,reconnect
            transcripts.append(reconnect)
        for classic in (False,True):
            data=Path(tmp)/('anti-classic'if classic else'anti-compact')
            path,empty=fixture(data,cloak=1)
            first='p;6'if classic else'p;anticloak'
            after=(f'9;1;8;0;c;9;{empty};15;1;intel;q;y\r'if classic else f'hire 8;planetreport {empty};spies;intel;q\r')
            out=play(data,'Caller',first,classic=classic,followups=[
                (b'[y/N] ',b'y\r'),(b'Anti-cloak activation saved for this login.',after.encode())])
            assert 'Enemy - Team: 0 - Fighters: 42 - Shields: 10000'in out,out
            assert 'The spy detected the shimmering'not in out,out
            w=json.loads(path.read_text());p=w['Players']['1']
            assert p['Credits']==2167000 and p['Turns']==498 and w['Players']['2']['Cloak']==1,p
            assert not w.get('Radio')
            transcripts.append(out)
            out=play(data,'Caller','spies;s;intel;q')
            assert 'Enemy - Team:'not in out and '2: Enemy'not in out and 'No intelligence reports this login.'in out,out
            transcripts.append(out)
    (ROOT/'evidence/spy-triggers-smoke.txt').write_text('\n'.join(line.rstrip() for line in '\n'.join(transcripts).splitlines())+'\n')
    print('Spy-trigger PTY passed: compact/classic free fighter transfers, charged missing reports, one missile/plasma step, spent unreachable launch, anti-cloak sharing and reconnect privacy.')


if __name__=='__main__':main()
