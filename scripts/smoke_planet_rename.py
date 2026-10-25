"""Compare the native planet rename flow with original DOS screens and saved names."""
import argparse
import gzip
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import smoke_startup as terminal
import smoke_planet_parity as planets

ROOT=terminal.ROOT
OUT=ROOT/'evidence/planet-rename'
sys.path.insert(0,str(ROOT/'archive/analysis/yt-maint'))
from experiments import get

CASES={
 'owner':('New Eden','New Eden'),
 'blank':('','Test Planet'),
 'retry':('First Name','Second Name'),
 'reserved':('The Wanderer','Test Planet'),
 'lowercase':('the wanderer','Test Planet'),
 'team':('New Eden','New Eden'),
 'foreign':('New Eden','New Eden'),
 'unowned':('New Eden','New Eden'),
 'long':('12345678901234567890123456789012345678901234567890','12345678901234567890123456789012345678901'),
 'last-slot':(None,'Test Planet'),
 'other-reserved':('Xannoron','Test Planet'),
 'spaces':('   Test  Name   ','Test Name'),
 'case':('mIxEd nAME','Mixed Name'),
 'punctuation':("o'brien alpha-beta x_Y 42base","O'brien Alpha-Beta X_Y 42Base"),
}


def original(name,index):
    raw=(ROOT/'research/yt-planet-rename'/name/'SCREENS.BIN').read_bytes()[index*4016+16:(index+1)*4016]
    return [[[bytes([raw[(y*80+x)*2]]).decode('cp437'),raw[(y*80+x)*2+1]&15,(raw[(y*80+x)*2+1]>>4)&7] for x in range(80)] for y in range(25)]


def scenario(name):
    prompt='Planet command (?=help) [A]? '
    typed,expected=CASES[name]
    phases=[('sector','Main Command (?=Help)? ',b'L\r'),('land',prompt,b'N\r')]
    if name=='last-slot':return phases+[('denied',prompt,b'L;Q;Y\r')],[('denied',0,20)]
    phases += [('name','What do you want to name this planet? -=>',(typed+'\r').encode())]
    checks=[('name',0,24)]
    if name=='blank':return phases+[('done',prompt,b'L;Q;Y\r')],checks+[('done',1,20)]
    if name in ['reserved','other-reserved']:
        phases += [('rejected',prompt,b'N;Mercenary Base\r' if name=='other-reserved' else b'L;Q;Y\r')]
        checks += [('rejected',1,18)]
        if name=='other-reserved':phases += [('again',prompt,b'L;Q;Y\r')];checks += [('again',2,18)]
        return phases,checks
    if name=='lowercase':
        # The DOS probe then sent an irrelevant Y. Only its reserved-name
        # rejection is part of the comparison; native input is staged normally.
        return phases+[('rejected',prompt,b'L;Q;Y\r')],[('rejected',0,18)]
    if name=='retry':
        phases += [('confirm','Is this OK? (Y/n) [Y] ?',b'N\r'),('retry','What do you want to name this planet? -=>',b'Second Name\r'),('confirm-again','Is this OK? (Y/n) [Y] ?',b'\r'),('done',prompt,b'L;Q;Y\r')]
        return phases,checks+[('confirm',1,22),('retry',2,20),('confirm-again',3,18),('done',4,18)]
    phases += [('confirm','Is this OK? (Y/n) [Y] ?',b'Y\r'),('done',prompt,b'D\r' if name in ['owner','spaces','case','punctuation'] else b'L;Q;Y\r')]
    checks += [('confirm',1,24 if name=='long' else 22),('done',2,20 if name=='long' else 18)]
    if name in ['owner','spaces','case','punctuation']:
        phases += [('display',prompt,b'L;Q;Y\r')];checks += [('display',3,8)]
    return phases,checks


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--render',action='store_true');parser.add_argument('--ascii',action='store_true');parser.add_argument('--only',nargs='+');args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    for name,(_,expected) in CASES.items():
        if args.only and name not in args.only:continue
        with tempfile.TemporaryDirectory(prefix='yt-rename-parity-') as temp:
            data=Path(temp)/'world';subprocess.run([str(ROOT/'bin/yt'),'-data',str(data),'-init','-sectors','8'],capture_output=True,check=True)
            terminal.capture(data,'Caller',new=True);planets.seed(data,name,research='yt-planet-rename')
            path=data/'world.json';w=json.loads(path.read_text());p=w['Players']['1']
            source=(ROOT/'archive/analysis/yt-combat/experiments'/json.loads((ROOT/'research/yt-planet-rename'/name/'provenance.json').read_text())['fixture']/'before.dat').read_bytes()
            p['Team']=int(get(source,2,89));w['Players']['2']['Team']=int(get(source,3,89))
            if name=='unowned':w['Planets']['2'].update(Owner=0,Ground=0)
            planet_id='2'
            if name=='last-slot':
                planet_id='100';planet=w['Planets'].pop('2');planet['ID']=100;w['Planets']['100']=planet;w['Sectors']['2']['Planet']=100
            path.write_text(json.dumps(w));before=json.loads(path.read_text());phases,checks=scenario(name)
            text,frames=terminal.capture(data,'Caller',after_info=phases,ascii=args.ascii)
            if args.ascii:assert '\x1b' not in text and all(ord(c)<128 for c in text)
            else:
                for frame,index,first in checks:
                    try:planets.compare(frames[frame],original(name,index),first)
                    except AssertionError as e:raise AssertionError((name,frame,*e.args)) from e
                if name in ['reserved','lowercase','other-reserved','last-slot']:
                    warning="You can't re-name this planet!" if name=='last-slot' else "I Don't think so!"
                    assert '\x1b[0;1;5;36;40m'+warning in text
            saved=json.loads(path.read_text());player=saved['Players']['1'];planet=saved['Planets'][planet_id]
            assert planet['Name']==expected,(name,planet)
            assert player['Turns']==before['Players']['1']['Turns'] and player['Credits']==before['Players']['1']['Credits'] and not player['PlanetToken'],player
            for field in ['Cargo','Fighters','Ground','Shields','Missiles','Mines','Plasma']:assert player[field]==before['Players']['1'][field],(name,field)
            assert planet['Owner']==before['Planets'][planet_id]['Owner'] and planet['Ground']==before['Planets'][planet_id]['Ground'],planet
            suffix='-ascii' if args.ascii else ''
            (OUT/(name+suffix+'.json')).write_text(json.dumps(frames,ensure_ascii=False))
            (OUT/(name+suffix+'.txt.gz')).write_bytes(gzip.compress(text.encode(),mtime=0))
            if args.render and name in ['owner','retry','reserved','long']:
                terminal.OUT=OUT;tag,index,_=checks[1] if len(checks)>1 else checks[0]
                terminal.render({name+'-dos':original(name,index),name+'-go':frames[tag]})
            print(name+': rename terminal, saved-name and '+('ASCII' if args.ascii else 'DOS character/color')+' checks passed.')


if __name__=='__main__':main()
