from pathlib import Path
import struct,re
root=Path(__file__).resolve().parent;b=(root.parent.parent/'YT.EXE').read_bytes()
def desc(v):
 p=v-0x6190+0x23240
 if p<0x23240 or p+4>0x2a070:return ''
 x=b[p:p+4];n,ptr=struct.unpack('<HH',x);q=ptr-0x6190+0x23240
 if 0<n<200 and 0x23240<=q and q+n<=0x2a070 and all(c in (9,10,13) or 32<=c<127 for c in b[q:q+n]):return repr(b[q:q+n].decode('ascii'))
 mant=int.from_bytes(x[:3],'little');e=x[3];v=0 if e==0 else (-1 if mant&0x800000 else 1)*(1+(mant&0x7fffff)/8388608)*2.0**(e-129)
 y=b[p:p+8];m64=int.from_bytes(y[:7],'little');e64=y[7] if len(y)==8 else 0
 v64=0 if e64==0 else (-1 if m64&(1<<55) else 1)*(1+(m64&((1<<55)-1))/(1<<55))*2.0**(e64-129)
 return f'MBF32 candidate={v:g}; MBF64 candidate={v64:g}'
for part in ['main','sub','sub2']:
 p=root/part/'qb-listing.txt'
 if not p.exists():continue
 out=[]
 for l in p.read_text().splitlines():
  vals=re.findall(r'0x([a-f0-9]{4})',l);notes=[f'{v}: {desc(int(v,16))}' for v in vals if desc(int(v,16))]
  m=re.search(r'0x([a-f0-9]+):([a-f0-9]+)',l)
  if m:
   physical=int(m[1],16)*16+int(m[2],16)
   for seg,size in [(0x1000,0xf420),(0x1f42,0xf370),(0x2e79,0x3b70)]:
    if seg*16<=physical<seg*16+size: notes.append(f'target {seg:04x}:{physical-seg*16:04x}');break
  out.append(l+('  ; '+' | '.join(notes) if notes else ''))
 (p.parent/'qb-annotated.txt').write_text('\n'.join(out)+'\n')
