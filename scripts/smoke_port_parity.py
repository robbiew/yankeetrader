"""Compare real-terminal port screens with captured original DOS characters/colors."""
import argparse
import copy
import datetime
import gzip
import json
from pathlib import Path
import subprocess
import tempfile
import smoke_startup as terminal

ROOT=terminal.ROOT
OUT=ROOT/'evidence/port-parity'


def original(name,index):
    raw=(ROOT/'research/yt-port-screens'/name/'SCREENS.BIN').read_bytes()[index*4016+16:(index+1)*4016]
    return [[[bytes([raw[(y*80+x)*2]]).decode('cp437'),raw[(y*80+x)*2+1]&15,(raw[(y*80+x)*2+1]>>4)&7] for x in range(80)] for y in range(25)]


def compare(actual,expected,first,earth=False,last=24):
    """Ignore live clock fields and assert current Earth equipment availability."""
    masks=set()
    for y,row in enumerate(expected[:24]):
        text=''.join(c[0] for c in row)
        if text.startswith('Commerce report for '):
            start=text.index(': ')+2
            masks.update((y,x) for x in range(start,start+19))
        if earth and text.startswith('[5]'):
            # These fixtures have no scanner and enough credits before/after each purchase.
            assert ''.join(c[0] for c in actual[y][33:]).strip()=='1'
            masks.update((y,x) for x in range(33,80))
        if earth and text.startswith(('[1]','[4]','[6]')):
            assert ''.join(c[0] for c in actual[y][33:]).strip()=='N/A'
            masks.update((y,x) for x in range(33,80))
    for y in range(first-1,last):
        for x in range(80):
            a,e=actual[y][x],expected[y][x]
            if (y,x) not in masks:assert a[0]==e[0],('character',y+1,x+1,a,e)
            # DOS leaves previous foreground attributes on empty cells during
            # scrolling. Their black backgrounds must still match exactly.
            assert a[2]==e[2] and (a[0]==' ' or a[1]==e[1]),('color',y+1,x+1,a,e)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--render',action='store_true')
    parser.add_argument('--only',nargs='+')
    args=parser.parse_args();OUT.mkdir(parents=True,exist_ok=True)
    for name in ['earth','holds','holds-buy','forces','shields','buy','sell','owned','self','decline']:
        if args.only and name not in args.only:continue
        earth=name in ['earth','holds','holds-buy','forces','shields']
        with tempfile.TemporaryDirectory(prefix='yt-port-parity-') as temp:
            data=Path(temp)/'world'
            subprocess.run([str(ROOT/'bin/yt'),'-data',str(data),'-init','-sectors','8'],capture_output=True,check=True)
            terminal.capture(data,'Caller',new=True)
            path=data/'world.json';world=json.loads(path.read_text());p=world['Players']['1']
            p.update(Credits=2000000 if earth else 1000000,Holds=10 if name=='holds-buy' else 1000,Turns=500,Fighters=25 if earth else 10000,Shields=10000,Sector=1 if earth else 2,Cargo=[100 if name=='sell' else 0,0,0])
            port=world['Ports']['2'];port['Name']='Test Port'
            # Match the captured quote amounts using supported Go coefficients;
            # the DOS randomized reference-price RNG is a separate known gap.
            port.update(Coefficient=[-50 if name=='sell' else 50,-46.6666666667,-55],Supply=[1000,1000,1000],Production=[100,100,100],Updated=datetime.datetime.now(datetime.timezone.utc).isoformat())
            if name in ['owned','self']:
                if name=='owned':
                    other=copy.deepcopy(p);other.update(ID=2,Identity='local:Enemy',Alias='Enemy')
                    world['Players']['2']=other;world['NextPlayer']=3
                port['Owner']=2 if name=='owned' else 1
                port['Treasury']=0
            path.write_text(json.dumps(world))
            if earth:
                choice,prompt,quantity={'earth':('3','Buy how many fighters? [0]? ','1'),'holds':('2','unused','0'),'holds-buy':('2','Buy how many holds? [0]? ','1'),'forces':('7','Buy how many ground force units? [0]? ','1'),'shields':('8','Buy how much shield power? [0]? ','1')}[name]
                phases=[('sector','Main Command (?=Help)? ',b'P\r'),('earth','Buy Which Item? -=>',(choice+'\r').encode()),('quantity',prompt,(quantity+'\r').encode()),('redraw','Buy Which Item? -=>',b'0;Q;Y\r')]
                checks=[('earth',0,4),('quantity',1,2),('redraw',2,4)]
                if name=='holds':
                    phases=[('sector','Main Command (?=Help)? ',b'P\r'),('earth','Buy Which Item? -=>',b'2\r'),('full','Buy Which Item? -=>',b'0;Q;Y\r')]
                    checks=[('earth',0,4),('full',1,4)]
            else:
                phases=[('sector','Main Command (?=Help)? ',b'P\r'),('quantity','do you want to '+('sell' if name=='sell' else 'buy')+' [ ',b'10\r'),('agreement','Do you agree? [Y/n] ',b'N\r' if name=='decline' else b'Y\r'),('done','Main Command (?=Help)? ',b'Q;Y\r')]
                checks=[('quantity',0,9 if name in ['owned','self'] else 11),('agreement',1,5 if name in ['owned','self'] else 7),('done',2,2)]
            text,frames=terminal.capture(data,'Caller',after_info=phases)
            for frame,index,first in checks:
                compare(frames[frame],original(name,index),first,earth=earth,last=18 if frame=='done' else 24)
            saved=json.loads(path.read_text());final=saved['Players']['1']
            if name in ['self','owned']:
                assert saved['Ports']['2']['Treasury']==(1 if name=='self' else 100),saved['Ports']['2']
            assert final['Turns']==499 and not final['DockToken'],final
            if earth:
                cost={'earth':100,'holds':0,'holds-buy':500,'forces':750,'shields':50}[name]
                assert final['Credits']==2000000-cost,final
                assert final['Fighters']==(26 if name=='earth' else 25),final
                assert final['Holds']==(11 if name=='holds-buy' else 1000),final
                assert final['Ground']==(1 if name=='forces' else 0),final
                assert final['Shields']==(10001 if name=='shields' else 10000),final
            elif name=='decline':assert final['Credits']==1000000 and final['Cargo']==[0,0,0],final
            elif name in ['buy','owned','self']:assert final['Credits']==999900 and final['Cargo']==[10,0,0],final
            else:assert final['Credits']==1000300 and final['Cargo']==[90,0,0],final
            (OUT/(name+'.json')).write_text(json.dumps(frames,ensure_ascii=False))
            (OUT/(name+'.txt.gz')).write_bytes(gzip.compress(text.encode(),mtime=0))
            if args.render:
                terminal.OUT=OUT
                terminal.render({name+'-dos':original(name,0),name+'-go':frames[checks[0][0]]})
            print(name+': DOS port characters, spacing, visible colors and saved transaction match.')


if __name__=='__main__':main()
