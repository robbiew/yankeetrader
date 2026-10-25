"""Controlled, isolated DOS maintenance experiments; originals never mounted."""
from pathlib import Path
import math,struct,shutil,subprocess,os,json,hashlib
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent/'dos-validation/evidence'
SOURCE=ROOT.parent.parent

def dec(raw):
 m=int.from_bytes(raw[:3],'little');e=raw[3]
 return 0.0 if e==0 else (-1 if m&0x800000 else 1)*(1+(m&0x7fffff)/2**23)*2.0**(e-129)
def enc(v):
 if not v:return bytes(4)
 s=v<0;frac,exp=math.frexp(abs(v));mant=round((frac*2-1)*2**23)
 if mant==2**23:mant=0;exp+=1
 return (mant|(0x800000 if s else 0)).to_bytes(3,'little')+bytes([exp+128])
def get(data,rec,off):return dec(data[(rec-1)*137+off:(rec-1)*137+off+4])
def put(data,rec,off,val):
 p=(rec-1)*137+off;data[p:p+4]=enc(val)
def record(data,rec):
 p=(rec-1)*137;return {'text':bytes(data[p:p+41]).decode('cp437').rstrip(),'fields':{str(41+i*4):get(data,rec,41+i*4) for i in range(23)}}
def setup(name):
 d=ROOT/'experiments'/name;d.mkdir(parents=True,exist_ok=False)
 for p in BASE.iterdir():
  if p.suffix.upper() in ('.DAT','.ASC'):shutil.copy2(p,d/p.name)
 for name in ['YTMAINT.EXE','BRUN30.EXE','YTCONFIG.EXE']:shutil.copy2(SOURCE/name,d/name)
 return d

def run(d,date='10/25/2026',time='00:00:00',tag='maint'):
 subprocess.run(['/opt/homebrew/bin/dosbox-staging','--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true','-c',f'mount c {d}','-c','c:','-c',f'date {date}','-c',f'time {time}','-c',f'date > {tag}date.log','-c',f'time > {tag}time.log','-c',f'ytmaint > {tag}.log','-c','exit'],env={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'},stdout=(d/f'{tag}-dosbox.log').open('w'),stderr=subprocess.STDOUT,timeout=90,check=True)

def fixtures():
 d=setup('production-v2');data=bytearray((d/'YTDATA.DAT').read_bytes())
 specs=[('zero-bank',0,0,1),('million-bank',1000000,0,1),('25m-bank',25000000,0,1),('surplus',0,20000,1),('two-days',1000000,0,2),('clamp-20days',0,0,20)]
 # Neutral planets in protected sectors, complete original code paths retained.
 for i,(name,bank,stock,days) in enumerate(specs):
  rec=4054+i;p=(rec-1)*137;data[p:p+137]=bytes(137);data[p:p+41]=name.encode().ljust(41,b' ')
  for off,val in {41:298-days,45:1000,49:2000,53:3000,57:stock,61:stock,65:stock,69:0,73:0,77:100,85:len(name),89:0,113:0,117:bank,125:0,129:0}.items():put(data,rec,off,val)
  put(data,51+2+i,93,3+i)
 (d/'YTDATA.DAT').write_bytes(data);(d/'BEFORE.DAT').write_bytes(data)
 run(d)
 after=(d/'YTDATA.DAT').read_bytes();rows=[]
 for i,spec in enumerate(specs):
  rows.append({'name':spec[0],'bank':spec[1],'stock':spec[2],'days':spec[3],'record':4054+i,'before':record(data,4054+i),'after':record(after,4054+i)})
 (d/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
 print(json.dumps(rows,indent=2))
if __name__=='__main__':fixtures()
