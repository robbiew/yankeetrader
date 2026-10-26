"""Verify idle clock refreshes preserve the real PTY input cursor and partial input."""
import codecs
import errno
import fcntl
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
import smoke_startup as terminal

ROOT=terminal.ROOT


def main():
    with tempfile.TemporaryDirectory(prefix='yt-clock-smoke-') as temp:
        data=Path(temp)/'world'
        subprocess.run([str(ROOT/'bin/yt'),'-data',str(data),'-init','-sectors','8'],capture_output=True,check=True)
        terminal.capture(data,'Caller',new=True)
        master,slave=pty.openpty();fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',25,80,0,0))
        proc=subprocess.Popen([str(ROOT/'bin/yt'),'-data',str(data),'-local','Caller'],stdin=slave,stdout=slave,stderr=slave);os.close(slave)
        # Model terminals that implement VT100 DECSC/DECRC but ignore CSI s/u.
        screen=terminal.Screen(csi_save_restore=False);decoder=codecs.getincrementaldecoder('utf-8')();text=''
        def until(predicate):
            nonlocal text
            end=time.monotonic()+12
            while not predicate():
                assert time.monotonic()<end,('terminal timeout',text[-1500:])
                if select.select([master],[],[],.1)[0]:
                    try:raw=os.read(master,65536)
                    except OSError as e:
                        if e.errno==errno.EIO:raise AssertionError(('early terminal exit',text[-1500:])) from e
                        raise
                    assert raw,'early EOF'
                    chunk=decoder.decode(raw);text+=chunk;screen.feed(chunk)
        def wait_marker(marker,start):until(lambda:marker in text[start:])
        def send(keys):os.write(master,keys)
        def tick():
            start=len(text)
            until(lambda:re.search(r'\x1b\[25;70H.*?(?:\x1b8|\x1b\[u)',text[start:],re.S) is not None)
        def check(label,typed=''):
            row=''.join(c[0] for c in screen.cells[23]);at=row.index(label)+len(label)+1
            assert (screen.x,screen.y)==(at+len(typed),23),('cursor left at clock',label,typed,(screen.x+1,screen.y+1),'expected',(at+len(typed)+1,24))
            assert row[at:at+len(typed)]==typed,('partial command overwritten',row)
            inline=row[6:row.index('  '+label)].strip();status=''.join(c[0] for c in screen.cells[24][69:79]).strip()
            assert inline==status,('clock fields disagree',inline,status)
        try:
            ready='\x1b[?25h\x1b[1;24r\x1b[24;1H'
            wait_marker(ready,0);start=len(text);send(b'\r');wait_marker('[ Press any Key ]',start)
            start=len(text);send(b' ');wait_marker(ready,start)
            start=len(text);send(b' ');wait_marker('Main Command (?=Help)? ',start)
            tick();check('Main Command (?=Help)?')
            start=len(text);send(b'LO');wait_marker('LO',start);tick();check('Main Command (?=Help)?','LO')
            start=len(text);send(b'OK\r');wait_marker('Main Command (?=Help)? ',start)
            assert 'That command is not available' not in text,text[-1500:]
            start=len(text);send(b'C\r');wait_marker('Computer command (?=help)? ',start)
            tick();check('Computer command (?=help)?')
            start=len(text);send(b'1');wait_marker('1',start);tick();check('Computer command (?=help)?','1')
            start=len(text);send(b'\r');wait_marker('Main Command (?=Help)? ',start)
            send(b'Q;Y\r');until(lambda:'Saved. Safe travels' in text)
            proc.wait(timeout=3);assert proc.returncode==0
        finally:
            if proc.poll() is None:proc.kill();proc.wait()
            os.close(master)
    print('Clock PTY passed: VT100 cursor restore, idle main/computer prompts, partial LOOK/exit input and synchronized clock fields.')


if __name__=='__main__':main()
