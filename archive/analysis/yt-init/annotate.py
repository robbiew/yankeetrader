from pathlib import Path
import struct,re
root=Path(__file__).resolve().parent
b=(root.parent.parent/'YT-INIT.EXE').read_bytes()
def describe(v):
 p=v-0xa650+0x2990
 if p<0x2990 or p+4>0x4720:return ''
 x=b[p:p+4];n,ptr=struct.unpack('<HH',x);q=ptr-0xa650+0x2990
 if n==0 and ptr==0xa672:return "'' (empty string)"
 if 0<n<200 and 0x2990<=q and q+n<=0x4720 and all(c in (9,10,13) or 32<=c<127 for c in b[q:q+n]):return repr(b[q:q+n].decode('ascii'))
 mant=int.from_bytes(x[:3],'little'); e=x[3]
 value=0 if e==0 else (-1 if mant&0x800000 else 1)*(1+(mant&0x7fffff)/8388608)*2.0**(e-129)
 return f'MBF32={value:g} [file 0x{p:04x}]'
s=(root/'qb-listing.txt').read_text();out=[]
for line in s.splitlines():
 vals=re.findall(r'0x([a-f0-9]{4})',line)
 notes=[f'{v}: {describe(int(v,16))}' for v in vals if describe(int(v,16))]
 out.append(line+('  ; '+' | '.join(notes) if notes else ''))
(root/'qb-annotated.txt').write_text('\n'.join(out)+'\n')
