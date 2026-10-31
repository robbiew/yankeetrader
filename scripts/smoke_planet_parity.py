"""Compare native planet menus/prompts with original DOS B800 screen captures."""
import argparse
import copy
import datetime
import gzip
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import smoke_startup as terminal

ROOT=terminal.ROOT
OUT=ROOT/'evidence/planet-parity'
sys.path.insert(0,str(ROOT/'archive/analysis/yt-maint'))
from experiments import get


def original(name,index):
    raw=(ROOT/'research/yt-planet-screens'/name/'SCREENS.BIN').read_bytes()[index*4016+16:(index+1)*4016]
    return [[[bytes([raw[(y*80+x)*2]]).decode('cp437'),raw[(y*80+x)*2+1]&15,(raw[(y*80+x)*2+1]>>4)&7] for x in range(80)] for y in range(25)]


def compare(actual,expected,first,last=24):
    for y in range(first-1,last):
        line=''.join(c[0] for c in expected[y])
        for x in range(80):
            a,e=actual[y][x],expected[y][x]
            if not (line.startswith('Time: ') and 6<=x<12):
                assert a[0]==e[0],('character',y+1,x+1,a,e)
            assert a[2]==e[2] and (a[0]==' ' or a[1]==e[1]),('color',y+1,x+1,a,e)


def seed(data,name,research='yt-planet-screens'):
    path=data/'world.json';w=json.loads(path.read_text());p=w['Players']['1']
    prov=json.loads((ROOT/'research'/research/name/'provenance.json').read_text())
    source=(ROOT/'archive/analysis/yt-combat/experiments'/prov['fixture']/'before.dat').read_bytes()
    for field,offset in [('Credits',81),('Turns',49),('Holds',65),('Fighters',61),('Shields',53),('Ground',121),('Missiles',97),('Mines',129),('Plasma',113)]:p[field]=int(get(source,2,offset))
    p.update(Sector=2,Cargo=[int(get(source,2,o)) for o in [69,73,77]])
    other=copy.deepcopy(p);other.update(ID=2,Identity='local:Enemy',Alias='Enemy')
    w['Players']['2']=other;w['NextPlayer']=3
    if name!='create':
        record=4053;start=(record-1)*137
        planet=dict(Generation=2,ID=2,Sector=2,Owner=int(get(source,record,73))-1,Name=source[start:start+41].decode('cp437').strip(),Updated=datetime.datetime.now(datetime.timezone.utc).isoformat(),Production=[get(source,record,o) for o in [45,49,53]],Cargo=[get(source,record,o) for o in [57,61,65]])
        for field,offset in [('Bank',117),('Ground',77),('Fighters',129),('Missiles',69),('Mines',125),('Plasma',113)]:planet[field]=int(get(source,record,offset))
        w['Planets']['2']=planet;w['Sectors']['2']['Planet']=2
    path.write_text(json.dumps(w))


def scenario(name):
    # Each tuple names a captured original stage and drives the next actual key.
    initial=('sector','Main Command (?=Help)? ',b'L\r')
    prompt='Planet command (?=help) [A]? '
    if name=='menu':return [initial,('land',prompt,b'?\r'),('help',prompt,b'D\r'),('display',prompt,b'L;Q;Y\r')],[('land',0,4,24),('help',1,3,24),('display',2,8,24)]
    if name=='transfer':return [initial,('land',prompt,b'T\r'),('transfer','-=>',b'F\r'),('quantity','Transfer how many -=>',b'123\r'),('done',prompt,b'L;Q;Y\r')],[('transfer',0,14,24),('quantity',1,12,24),('done',2,6,24)]
    if name=='cargo':return [initial,('land',prompt,b'T;C\r'),('done',prompt,b'D\r'),('display',prompt,b'L;Q;Y\r')],[('done',0,8,24),('display',1,8,24)]
    if name=='bank':return [initial,('land',prompt,b'B\r'),('quantity','Available ->',b'15000\r'),('done',prompt,b'L;Q;Y\r')],[('quantity',0,22,24),('done',1,16,24)]
    if name=='invest':return [initial,('land',prompt,b'$\r'),('quantity','Spend how much to raise productivity? -+> ',b'251\r'),('done',prompt,b'D\r'),('display',prompt,b'L;Q;Y\r')],[('quantity',0,20,24),('done',1,13,24),('display',2,8,24)]
    if name=='garrison':return [initial,('land',prompt,b'F\r'),('quantity','Available ->',b'90\r'),('done',prompt,b'L;Q;Y\r')],[('quantity',0,24,24),('done',1,18,24)]
    if name=='takeall':return [initial,('land',prompt,b'\r'),('done',prompt,b'D\r'),('display',prompt,b'L;Q;Y\r')],[('done',0,10,24),('display',1,8,24)]
    if name=='create':return [initial,('purchase','Do you wish to buy a planet(Y/N) [N]? ',b'Y\r'),('name','What do you want to name this planet? -=>',b'New Eden\r'),('confirm','Is this OK? (Y/n) [Y] ?',b'Y\r'),('done','Main Command (?=Help)? ',b'Q;Y\r')],[('purchase',0,19,24),('name',1,17,24),('confirm',2,15,24),('done',3,4,17)]
    if name=='foreign':return [initial,('denied','Do you wish to try to force a landing? [y/N] ',b'N\r'),('done','Main Command (?=Help)? ',b'Q;Y\r')],[('denied',0,20,24),('done',1,9,17)]
    choices=['1','2','3'] if name=='take-cargo' else ['4','5','6','9']
    phases=[initial,('land',prompt,(choices[0]+'\r').encode())];checks=[]
    for i,choice in enumerate(choices):
        phases += [(choice+'-quantity','How much [ ',b'5\r'),(choice+'-done',prompt,(choices[i+1]+'\r').encode() if i+1<len(choices) else b'L;Q;Y\r')]
        checks += [(choice+'-quantity',i*2,22,24),(choice+'-done',i*2+1,18,24)]
    return phases,checks


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--render',action='store_true');parser.add_argument('--ascii',action='store_true');parser.add_argument('--only',nargs='+');args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    for name in ['menu','transfer','cargo','bank','invest','garrison','takeall','create','foreign','take-cargo','take-weapons']:
        if args.only and name not in args.only:continue
        with tempfile.TemporaryDirectory(prefix='yt-planet-parity-') as temp:
            data=Path(temp)/'world';subprocess.run([str(ROOT/'bin/yt'),'-data',str(data),'-init','-sectors','8'],capture_output=True,check=True)
            terminal.capture(data,'Caller',new=True);seed(data,name)
            phases,checks=scenario(name)
            text,frames=terminal.capture(data,'Caller',after_info=phases,ascii=args.ascii)
            if args.ascii:assert '\x1b' not in text and all(ord(c)<128 for c in text)
            else:
                for frame,index,first,last in checks:
                    try:compare(frames[frame],original(name,index),first,last)
                    except AssertionError as e:raise AssertionError((name,frame,*e.args)) from e
            saved=json.loads((data/'world.json').read_text());p=saved['Players']['1']
            assert p['Turns']==500 and not p['PlanetToken'],p
            planet=saved['Planets'].get('2')
            expected_cash=75000 if name=='create' else 95000 if name=='bank' else 99749 if name=='invest' else 100000
            assert p['Credits']==expected_cash,p
            if name=='transfer':assert p['Fighters']==9877 and int(planet['Fighters'])==723,(p,planet)
            if name=='cargo':assert p['Cargo']==[0,0,0] and [int(v) for v in planet['Cargo']]==[110,220,330],(p,planet)
            if name=='bank':assert planet['Bank']==15000,planet
            if name=='invest':assert all(abs(a-b)<.001 for a,b in zip(planet['Production'],[11.004,21.004,31.004])),planet
            if name=='garrison':assert p['Ground']==25 and planet['Ground']==90,(p,planet)
            if name=='takeall':assert p['Cargo']==[10,20,70] and (p['Fighters'],p['Missiles'],p['Mines'],p['Plasma'])==(10600,77,88,99),p
            if name=='create':assert len(saved['Planets'])==1 and planet['Name']=='New Eden' and planet['Owner']==1 and planet['Ground']==1,planet
            if name=='foreign':assert planet['Owner']==2 and planet['Ground']==100 and p['Ground']==15,(p,planet)
            if name=='take-cargo':assert p['Cargo']==[15,25,35] and [int(v) for v in planet['Cargo']]==[95,195,295],(p,planet)
            if name=='take-weapons':assert (p['Fighters'],p['Missiles'],p['Mines'],p['Plasma'])==(10005,12,13,14),p
            if not args.ascii:
                if name=='transfer':assert '\x1b[0;5;36;40mFighters Transferred!' in text
                if name=='garrison':assert '\x1b[0;1;5;36;40mGround force strength' in text
                if name=='foreign':assert '\x1b[0;1;5;33;40mDENIED!' in text
            (OUT/(name+('-ascii' if args.ascii else '')+'.json')).write_text(json.dumps(frames,ensure_ascii=False))
            (OUT/(name+('-ascii' if args.ascii else '')+'.txt.gz')).write_bytes(gzip.compress(text.encode(),mtime=0))
            if args.render:
                terminal.OUT=OUT
                images={name+'-dos':original(name,0),name+'-go':frames[checks[0][0]]}
                if name=='menu':images.update({'help-dos':original(name,1),'help-go':frames['help']})
                terminal.render(images)
            print(name+': planet terminal session passed'+(' ASCII checks.' if args.ascii else ' DOS character/color comparisons.'))


if __name__=='__main__':main()
