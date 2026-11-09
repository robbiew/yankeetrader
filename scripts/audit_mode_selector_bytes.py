"""Ordinary byte-signature inventory, not a disassembly or REA reference graph.

Scan complete post-header MZ file payloads. Candidate byte matches can be data;
indirect writes, copies and later computed addresses are explicitly out of scope.
"""
import hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NAMES=('BRUN30.EXE','LOCAL.EXE','PORTNAME.EXE','RMT-INIT.EXE','YT-INIT.EXE','YT.EXE','YTCONFIG.EXE','YTMAINT.EXE')


def locations(data,pattern,start):
    found=[];at=start
    while (at:=data.find(pattern,at))>=0:found.append(at);at+=1
    return found


def stores():
    signatures=[]
    # Enumerated 8086 absolute 8/16-bit destination forms, not an exhaustive ISA
    # proof. Word stores at 001e overlap selector 001f and are included.
    for width,addresses in [(1,(0x1f,)),(2,(0x1e,0x1f))]:
        for address in addresses:
            addr=struct.pack('<H',address)
            for opcode in ([0x88,0x86,0x00,0x08,0x10,0x18,0x20,0x28,0x30] if width==1 else [0x89,0x87,0x01,0x09,0x11,0x19,0x21,0x29,0x31]):
                for register in range(8):signatures.append(bytes([opcode,6+8*register])+addr)
            signatures.append(bytes([0xa2 if width==1 else 0xa3])+addr)
            signatures.append(bytes([0xc6 if width==1 else 0xc7,6])+addr)
            for opcode in ([0x80] if width==1 else [0x81,0x83]):
                for operation in range(7):signatures.append(bytes([opcode,6+8*operation])+addr) # Exclude CMP.
            for opcode,operations in ((0xfe if width==1 else 0xff,(0,1)),(0xf6 if width==1 else 0xf7,(2,3))):
                for operation in operations:signatures.append(bytes([opcode,6+8*operation])+addr)
            for opcode in ([0xd0,0xd2] if width==1 else [0xd1,0xd3]):
                for operation in range(8):signatures.append(bytes([opcode,6+8*operation])+addr)
            if width==2:signatures.append(bytes.fromhex('8f06')+addr)
    return sorted(set(signatures))


def store_candidates(data,start):
    return sorted([dict(file_offset=at,signature=pattern.hex()) for pattern in stores() for at in locations(data,pattern,start)],key=lambda r:(r['file_offset'],r['signature']))


def build():
    rows=[]
    for name in NAMES:
        data=(ROOT/'archive/dos-original'/name).read_bytes();assert data[:2]==b'MZ'
        header=struct.unpack_from('<H',data,8)[0]*16
        candidates=store_candidates(data,header)
        rows.append(dict(program=name,sha256=hashlib.sha256(data).hexdigest(),file_bytes=len(data),scan_start=header,scan_end_exclusive=len(data),
                         literal_001f_offsets=locations(data,bytes.fromhex('1f00'),header),
                         compare_mode4_offsets=locations(data,bytes.fromhex('803e1f0004'),header),
                         enumerated_store_candidates=sorted(candidates,key=lambda r:(r['file_offset'],r['signature']))))
    return dict(format='ordinary-mode-selector-byte-inventory-v1',signature_count=len(stores()),signatures=[p.hex() for p in stores()],programs=rows,
                limitations=['Byte signatures are not decoded instructions or a complete reference graph.','Indirect writes, string copies, computed addresses and later runtime selection are not ruled out.','Literal address matches can be immediate values, relative calls, data or overlays.'])

if __name__=='__main__':print(json.dumps(build(),indent=2))
