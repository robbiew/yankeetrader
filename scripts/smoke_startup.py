"""Drive DOS-style startup over real PTYs; compare title cells and capture live screens."""
import argparse
import codecs
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pty
import re
import select
import struct
import subprocess
import tempfile
import termios
import time

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evidence/startup'


class Screen:
    def __init__(self):
        self.cells=[[[' ',7,0] for _ in range(80)] for _ in range(25)]
        self.x=self.y=0;self.fg=7;self.bg=0;self.top=0;self.bottom=24
        self.saved=(0,0);self.wrap=True;self.deferred=False;self.pending=''
    def lf(self):
        self.deferred=False
        if self.y==self.bottom:
            self.cells.pop(self.top);self.cells.insert(self.bottom,[[' ',self.fg,self.bg] for _ in range(80)])
        else:self.y=min(24,self.y+1)
    def feed(self,text):
        self.pending+=text
        while self.pending:
            c=self.pending[0]
            if c=='\x1b':
                match=re.match(r'\x1b\[([0-9;?]*)([@-~])',self.pending)
                if not match:
                    if len(self.pending)==1 or (self.pending.startswith('\x1b[') and not re.search(r'[@-~]',self.pending[2:])):break
                    self.pending=self.pending[2:];continue
                raw,op=match.groups();private=raw.startswith('?');values=[int(v or 0) for v in raw.lstrip('?').split(';')];n=values[0] or 1
                self.pending=self.pending[match.end():]
                if op in 'Hf':self.y=min(24,(values[0] or 1)-1);self.x=min(79,(values[1] or 1)-1 if len(values)>1 else 0);self.deferred=False
                elif op=='A':self.y=max(self.top,self.y-n);self.deferred=False
                elif op=='B':self.y=min(self.bottom,self.y+n);self.deferred=False
                elif op=='C':self.x=min(79,self.x+n);self.deferred=False
                elif op=='D':self.x=max(0,self.x-n);self.deferred=False
                elif op=='s':self.saved=(self.x,self.y)
                elif op=='u':self.x,self.y=self.saved;self.deferred=False
                elif op=='J':
                    if values[0]==2:self.cells=[[[' ',self.fg,self.bg] for _ in range(80)] for _ in range(25)]
                elif op=='K':
                    start=0 if values[0] in (1,2) else self.x
                    end=80 if values[0] in (0,2) else self.x+1
                    for x in range(start,end):self.cells[self.y][x]=[' ',self.fg,self.bg]
                elif op=='m':
                    mapping=[0,4,2,6,1,5,3,7]
                    for v in values:
                        if v==0:self.fg,self.bg=7,0
                        elif v==1:self.fg|=8
                        elif v==22:self.fg&=7
                        elif 30<=v<=37:self.fg=(self.fg&8)|mapping[v-30]
                        elif 90<=v<=97:self.fg=mapping[v-90]+8
                        elif 40<=v<=47:self.bg=mapping[v-40]
                elif op=='r':
                    self.top=(values[0] or 1)-1;self.bottom=(values[1] or 25)-1 if len(values)>1 else 24;self.x=0;self.y=self.top;self.deferred=False
                elif private and op in 'hl' and values[0]==7:self.wrap=op=='h'
                continue
            self.pending=self.pending[1:]
            if c=='\r':self.x=0;self.deferred=False
            elif c=='\n':self.lf()
            elif c=='\b':self.x=max(0,self.x-1);self.deferred=False
            elif c>=' ' and c!='\x7f':
                if self.deferred and self.wrap:self.x=0;self.lf()
                self.cells[self.y][self.x]=[c,self.fg,self.bg]
                if self.x==79:self.deferred=True
                else:self.x+=1
    def snapshot(self):return json.loads(json.dumps(self.cells))


def capture(data,alias,new=False,ascii=False,abort=False):
    master,slave=pty.openpty();fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',25,80,0,0))
    command=[str(ROOT/'bin/yt'),'-data',str(data),'-local',alias]
    if ascii:command.append('-ascii')
    proc=subprocess.Popen(command,stdin=slave,stdout=slave,stderr=slave);os.close(slave)
    screen=Screen();decoder=codecs.getincrementaldecoder('utf-8')();text='';frames={};step=0;phase_start=0;end=time.monotonic()+25
    phases=[('title','REGISTER THIS GAME.' if ascii else '\x1b[?25h\x1b[1;24r\x1b[24;1H',b'\r')]
    if new:
        phases += [('alias','-+> ',b'\x1b' if abort else b'Pilot\r')]
        if not abort:phases += [('confirm','Is this OK (Y/[N])? ',b'Y\r'),('instructions','Do you want instructions (Y/N) [N]? ',b'N\r')]
    if not abort:
        phases += [('info','[ Press any Key ]' if ascii else '\x1b[?25h\x1b[1;24r\x1b[24;1H',b' '),('sector','Main Command (?=Help)? ',b'?\r'),
                   ('help','Main Command (?=Help)? ',b'C\r'),('computer','Computer command (?=help)? ',b'?\r'),
                   ('computer-help','Computer command (?=help)? ',b'1;Q;Y\r')]
    try:
        while time.monotonic()<end:
            if select.select([master],[],[],.1)[0]:
                try:raw=os.read(master,65536)
                except OSError as e:
                    if e.errno==errno.EIO:break
                    raise
                if not raw:break
                chunk=decoder.decode(raw);text+=chunk;screen.feed(chunk)
                if step<len(phases):
                    name,marker,keys=phases[step]
                    if marker in text[phase_start:]:
                        frames[name]=screen.snapshot();os.write(master,keys);step+=1;phase_start=len(text)
            if proc.poll() is not None:break
        proc.wait(timeout=2)
    finally:
        if proc.poll() is None:proc.kill();proc.wait()
        os.close(master)
    assert proc.returncode==0,(proc.returncode,text[-3000:])
    assert step==len(phases),(step,phases[step:],text[-2000:])
    if not abort:assert 'Saved. Safe travels' in text,text[-2000:]
    return text,frames


def render(frames):
    from PIL import Image,ImageDraw,ImageFont
    font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',19)
    palette=['#000000','#0000aa','#00aa00','#00aaaa','#aa0000','#aa00aa','#aa5500','#aaaaaa','#555555','#5555ff','#55ff55','#55ffff','#ff5555','#ff55ff','#ffff55','#ffffff']
    for name,cells in frames.items():
        im=Image.new('RGB',(960,600));draw=ImageDraw.Draw(im)
        for y,row in enumerate(cells):
            for x,(char,fg,bg) in enumerate(row):
                draw.rectangle((x*12,y*24,x*12+11,y*24+23),fill=palette[bg])
                draw.text((x*12,y*24),char,font=font,fill=palette[fg],anchor='la')
        im.save(OUT/(name+'.png'))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--render',action='store_true');args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='yt-startup-smoke-') as temp:
        data=Path(temp)/'world'
        subprocess.run([str(ROOT/'bin/yt'),'-data',str(data),'-init','-sectors','8'],capture_output=True,check=True)
        text,frames=capture(data,'Caller',new=True)
        world=json.loads((data/'world.json').read_text());p=world['Players']['1']
        assert (p['Alias'],p['Credits'],p['Turns'])==('Pilot',1005,500),p
        raw=(ROOT/'archive/analysis/art-menus/screen-recovery/run-main/SCREENS.BIN').read_bytes()[16:4016]
        for y,row in enumerate(frames['title']):
            for x,cell in enumerate(row):
                ch,attr=raw[(y*80+x)*2:(y*80+x)*2+2];expected=[bytes([ch]).decode('cp437') if ch>=32 else ' ',attr&15,(attr>>4)&7]
                assert cell==expected,('title cell mismatch',y,x,cell,expected)
        source=(ROOT/'archive/analysis/art-menus/screen-recovery/run-main/SCREENS.BIN').read_bytes()
        original_help=source[3*4016+16:4*4016]
        for y in range(23):
            for x,cell in enumerate(frames['help'][y]):
                ch,attr=original_help[(y*80+x)*2:(y*80+x)*2+2]
                expected=[bytes([ch]).decode('cp437') if ch>=32 else ' ',attr&15,(attr>>4)&7]
                assert cell==expected,('help cell mismatch',y,x,cell,expected)
        info=[''.join(c[0] for c in row) for row in frames['info']]
        assert 'Name  : Pilot' in info[6] and '1005' in info[13] and 'Orion' not in '\n'.join(info),info
        assert info[13][26]=='║' and info[13][49]=='║',info[13]
        before=(data/'world.json').read_bytes();cancelled,_=capture(data,'Aborted',new=True,abort=True)
        assert (data/'world.json').read_bytes()==before,'cancelled alias created/changed player'
        returning,return_frames=capture(data,'Caller')
        assert 'You are a new player.' not in returning and 'You have been on today.' in returning
        plain,_=capture(data,'Caller',ascii=True)
        assert '\x1b' not in plain and all(ord(c)<128 for c in plain),'plain mode emitted ANSI/CP437'
        assert len(json.loads((data/'world.json').read_text())['Players'])==1
        (OUT/'transcript.txt').write_text(text.replace('\r',''))
        (OUT/'returning.txt').write_text(returning.replace('\r',''))
        (OUT/'ascii.txt').write_text(plain.replace('\r',''))
        (OUT/'cells.json').write_text(json.dumps(frames,ensure_ascii=False))
        if args.render:render(frames)
        print('Startup PTY passed: original title and 23 menu rows/attributes, alias registration, real stats, key pause, main/computer menus, reconnect, Escape rollback and ASCII fallback.')


if __name__=='__main__':main()
