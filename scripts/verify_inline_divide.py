"""Authenticate bounded inline8d addressing, division and distinct fatal errors."""
import json,struct
from pathlib import Path
import verify_inline_add as address
import verify_inline_overflow as context
import verify_single_divide as division
ROOT=address.ROOT
DEFAULT=ROOT/'research/yt-mbf-inline-divide/native'
ADDRESS_DEFAULT=ROOT/'research/yt-mbf-inline-divide/address-native'
FIXTURE=ROOT/'internal/qbmbf/testdata/native_inline_divide.json'
PINS_SHA='266bbfaa4035db4007edebf0bade615ba305beee0ec318a258da3352e9399e28'
ADDRESS_PINS_SHA='b02015dbef16080beff074d2c7a48c83780466d611153db3e58496bbc8176ab3'
PAIRS={'both-zero': ('00000000', '00000000', 'division_by_zero'),
 'aliases': ('12345600', 'ffffff00', 'division_by_zero'),
 'left-zero': ('12345600', '00004081', 'return'),
 'right-zero': ('00004081', '12345600', 'division_by_zero'),
 'fraction': ('00004082', '00000082', 'return'),
 'reverse': ('00000082', '00004082', 'return'),
 'negative': ('0000c082', '00000082', 'return'),
 'both-negative': ('0000c082', '00008082', 'return'),
 'underflow': ('00000001', 'ffff7fff', 'return'),
 'align': ('56341291', 'ac681380', 'return'),
 'guard23-below': ('9ff50b81', 'd7440881', 'return'),
 'guard23-above': ('f12d1681', '0fb61481', 'return'),
 'guard24-below': ('868d1281', '7b4d6c81', 'return'),
 'guard24-above': ('6d2b2281', 'c3622e81', 'return'),
 'min-boundary': ('00000001', '00000081', 'return'),
 'max-boundary': ('00000080', 'ffff7f01', 'return'),
 'positive-overflow': ('ffff7fff', '00000080', 'overflow'),
 'negative-overflow': ('ffffffff', '00000080', 'overflow')}


def execution_cases():
    result={}
    for label,magic in (('bm',0x6d62),('bz',0x7a62)):
        for name,(left,fac,expect) in PAIRS.items():
            for selector in (0x80,0xff):
                result[f'{label}-{name}-{selector:02x}']=dict(op=0x8d,expect=expect,kind='full',magic=magic,base10=0x6000,base12=0x6800,selector=selector,left=left,fac=fac,initial=16777215 if name in ('negative-overflow','guard24-above') else 5)
    for pad,magic in ((16,0x6d62),(32,0x7a62)):
        for name in ('positive-overflow','both-zero','underflow'):
            left,fac,expect=PAIRS[name]
            result[f'pad{pad}-{name}']=dict(op=0x8d,expect=expect,pad=pad,kind='full',magic=magic,base10=0x6000,base12=0x6800,selector=0x84,left=left,fac=fac,initial=16777215)
    return result

def address_cases():
    result={}
    contexts=(('bm',0x6d62,0x6000,0x6800,(0,128,127,255)),('bz',0x7a62,0x6000,0x6800,(0,128,127,255)),('bm-wrap',0x6d62,0xfff8,0x6800,(0,1,127)),('bz-wrap',0x7a62,0x6000,0xfff8,(0,1,127)),('fallback',0,0x6000,0x6800,(0x84,)))
    for label,magic,base10,base12,selectors in contexts:
        for selector in selectors:
            result[f'address-{label}-{selector:02x}']=dict(kind='address',magic=magic,base10=base10,base12=base12,selector=selector,left='00000000',fac='a55a3288',initial=16777215)
    return result

CASES=execution_cases()
ADDRESS_CASES=address_cases()


def expected_payload(c):return context.expected_payload(c)
def verify_trace(raw,c):
    assert c['op']==0x8d,'only qualified inline division operation'
    return context.verify_trace(raw,c)
def expected_address_payload(c):return address.expected_payload(c,'divide')
def verify_address_trace(raw,c):
    assert c['kind']=='address','resolver-only profile'
    return address.verify_trace(raw,c,'divide')


def verify_static(runtime):
    division.verify_static(runtime) # existing quotient, entry mappings, errors and static inventory
    context.verify_static(runtime) # existing common resolver/frame and default error dispatch
    assert struct.unpack_from('<H',runtime,0x58d+2*0x8d)[0]==0xb525,'original inline8d dispatch'
    assert runtime[0xb725:0xb72e]==bytes.fromhex('e89b69bf1a00e83d6a'),'same resolver, right FAC, then division ABI'
    _,calls=division.verify_inventory()
    assert calls==[],'no inline8d sites in the bounded maintenance listing; controls are synthetic'
    return calls


def verify(directory=DEFAULT,fixture=FIXTURE,address_directory=ADDRESS_DEFAULT):
    assert all(c['op']==0x8d and c['kind']=='full' for c in CASES.values()) and all(c['kind']=='address' for c in ADDRESS_CASES.values())
    verify_static((ROOT/'archive/dos-original/BRUN30.EXE').read_bytes())
    execution=context.verify_corpus(directory,CASES,PINS_SHA,'brun30-inline-divide-v1','recover_inline_divide.py')
    addresses=address.verify_corpus(address_directory,ADDRESS_CASES,ADDRESS_PINS_SHA,'brun30-inline-divide-address-v1','recover_inline_divide_address.py','divide')
    doc=dict(format='qb-native-inline-divide-v1',address_cases=addresses,execution_cases=execution)
    if fixture is not None:assert json.loads(Path(fixture).read_text())==doc,'portable fixture equals both complete inline8d corpora'
    return doc

if __name__=='__main__':
    d=verify();print('Verified',len(d['address_cases']),'resolver-only controls and',len(d['execution_cases']),'full inline8d outcomes:',{k:sum(c['error']==k for c in d['execution_cases']) for k in (None,'overflow','division_by_zero')})
