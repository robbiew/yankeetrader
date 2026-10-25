"""Extract the original BRUN30 math dispatch entries for review."""
from pathlib import Path
import struct,subprocess,hashlib
root=Path(__file__).resolve().parent
b=(root.parent.parent/'BRUN30.EXE').read_bytes()
out=['BRUN30.EXE SHA256 '+hashlib.sha256(b).hexdigest(),
     'INT 3F dispatch table: file 0x200 + CS:038D; each entry is a near offset.',
     'See runtime 00F3 dispatcher; offsets below are runtime CS offsets.','']
for op,name in {0x87:'single SI/DI',0x88:'double SI/DI',0x8a:'double FAC/DI',0x8f:'single SI*DI',0x90:'double SI*DI',0x91:'single FAC*DI',0x97:'single SI-DI',0x98:'double SI-DI'}.items():
 a=struct.unpack_from('<H',b,0x200+0x38d+op*2)[0]
 p=root/'runtime-fragment.bin';p.write_bytes(b[0x200+a:0x200+a+96])
 out+=['',f'3F/{op:02X} at {a:04X}: {name}',subprocess.check_output(['ndisasm','-b16','-o',str(a),str(p)],text=True)]
p.unlink();(root/'runtime-math.txt').write_text('\n'.join(out))
