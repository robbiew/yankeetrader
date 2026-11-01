"""Drive the opt-in multiline composer through real compact/classic GoDoors."""
from pathlib import Path
import json
import subprocess
import tempfile
from smoke_newspaper import BINARY,play
ROOT=Path(__file__).resolve().parents[1]
MENU=b'[L] List [S] Send [A] Abort [C] Continue [E] Edit -=> '
FINAL=b'[S] Send [A] Abort -=> '
with tempfile.TemporaryDirectory(prefix='yt-editor-pty-')as temp:
 data=Path(temp)/'world';subprocess.run([BINARY,'-data',str(data),'-init','-sectors','8'],check=True,capture_output=True)
 for alias in ('Sender','Enemy','Visitor'):play(data,alias,'q')
 path=data/'world.json';before=json.loads(path.read_text())
 transcript=play(data,'Sender','radio EDIT Enemy;y',followups=[
 (b' 1: ',b'alpha alpha; literal/\rSECOND\r\r'),(MENU,b'E\r'),
 (b'Edit Which line?',b'1\ralpha\rBETA\ry\r'),(MENU,b'L\r'),(MENU,b'C\r'),
 (b' 2: SECOND',b' PLUS\r\r'),(MENU,b'S\r'),(FINAL,b's\r'),(b'2 lines saved',b'q\r')])
 saved=json.loads(path.read_text());assert saved['Version']==27 and [m['Text']for m in saved['Radio']]==['BETA alpha; literal/','SECOND PLUS']
 assert saved['Players']==before['Players'] and not any(n['Kind']=='radio-broadcast'for n in saved.get('News',[]))
 out=play(data,'Visitor','messages;q');transcript+=out;assert 'BETA alpha; literal/'not in out
 out=play(data,'Enemy','messages;q');transcript+=out;assert 'BETA alpha; literal/'in out and 'SECOND PLUS'in out
 transcript+=play(data,'Sender','radio EDIT Enemy;y',followups=[(b' 1: ',b'ABORTED\r\r'),(MENU,b'A\ry\r'),(b'Radio cancelled.',b'q\r')])
 assert len(json.loads(path.read_text())['Radio'])==2
 transcript+=play(data,'Sender','team;2;Orion',followups=[(b'Team password (4 characters; entered separately): ',b'ABCD\r'),(b'Team change saved.',b'1;q\r')])
 transcript+=play(data,'Enemy','team;3;1',followups=[(b'Team password (4 characters; entered separately): ',b'ABCD\r'),(b'Team change saved.',b'1;q\r')])
 transcript+=play(data,'Sender','radio EDIT TEAM;y',followups=[(b' 1: ',b'TEAM FIRST\rTEAM SECOND\r\r'),(MENU,b'S\r'),(FINAL,b's\r'),(b'2 lines saved',b'q\r')])
 saved=json.loads(path.read_text());assert len(saved['Radio'])==6 and not any(n['Kind']=='radio-broadcast'for n in saved['News'])
 out=play(data,'Visitor','messages;q');transcript+=out;assert 'TEAM FIRST'not in out
 transcript+=play(data,'Sender','c;5;EDIT ALL;y',classic=True,followups=[
 (b' 1: ',b'PUBLIC FIRST\rPUBLIC SECOND\r\r'),(MENU,b'S\r'),
 (FINAL,b's\r'),(b'2 lines saved',b'1;q;y\r')])
 saved=json.loads(path.read_text());assert len(saved['Radio'])==12
 news=[n for n in saved['News']if n['Kind']=='radio-broadcast'];assert [n['BroadcastText']for n in news]==['PUBLIC FIRST','PUBLIC SECOND']
 assert 'PUBLIC:'in transcript and '2 public entries'in transcript
 out=play(data,'Visitor','messages;q');transcript+=out;assert 'PUBLIC FIRST'in out and 'PUBLIC SECOND'in out and 'BETA alpha; literal/'not in out
 (ROOT/'evidence/radio-editor-smoke.txt').write_text('\n'.join(line.rstrip()for line in transcript.splitlines())+'\n')
 print('Multiline PTY passed: compact/classic entry, List/Edit/Continue, direct/team/public atomic lines, confirmation, abort and privacy.')
