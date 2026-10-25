from pathlib import Path
import struct,re
root=Path(__file__).resolve().parent;b=(root.parent.parent/'RMT-INIT.EXE').read_bytes()
# Runtime near-data descriptors map to file offset +0x1af0; 1b40 is at file3630.
def desc(v):
 p=0x1af0+v
 if p<0x3630 or p+4>len(b):return ''
 x=b[p:p+4];n,ptr=struct.unpack('<HH',x);q=0x1af0+ptr
 if 0<n<220 and 0<=q and q+n<=len(b) and all(c in (9,10,13) or 32<=c<127 for c in b[q:q+n]):return repr(b[q:q+n].decode('ascii'))
 m=int.from_bytes(x[:3],'little');e=x[3];v=0 if not e else (-1 if m&0x800000 else 1)*(1+(m&0x7fffff)/8388608)*2.**(e-129)
 return f'MBF32={v:g}'
out=[]
for line in (root/'qb-listing.txt').read_text().splitlines():
 notes=[f'{v}: {desc(int(v,16))}' for v in re.findall(r'0x([a-f0-9]{4})',line) if desc(int(v,16))]
 out.append(line+('  ; '+' | '.join(notes) if notes else ''))
(root/'qb-annotated.txt').write_text('\n'.join(out)+'\n')
