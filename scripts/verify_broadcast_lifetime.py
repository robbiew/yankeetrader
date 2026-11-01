"""Independently verify retained DOS broadcast routing, packet state and provenance."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import struct

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'archive/analysis/yt-combat/experiments/fixture-team-captain'
RECIPE='broadcast-radio-v1'
BASE_SHA='04eaf42c54d4f35c3412737e27fa968b5abcd22eb295cb5d8b45ab8045fcd0ec'
BINS={'BRUN30.EXE':'3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8','KEYFEED.COM':'06dd2b9fcb91502185f6f4a2123ad7fdac144f47f5170df203760b86db127596','LOCAL.EXE':'bb970c43eb29fb80e7252f3968884f1c43543a5e39c6714b209ffca7dbf2d93a','YT.EXE':'c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037'}
RECIPE_SHA='0ac9bea06e6200f8d599beec50e16f2eaa548545f352a660aa6f171a4eb9a3eb'
DECLARATIONS={'broadcast-send': {'name': 'broadcast-send',
                    'command': 'C;5;ALL\r~~YT BROADCAST PROBE\r\r~~S\r~~~~6;1',
                    'patches': []},
 'broadcast-abort': {'name': 'broadcast-abort',
                     'command': 'C;5;ALL\r'
                                '~~YT BROADCAST PROBE\r'
                                '\r'
                                '~~A;Y\r'
                                '~~~~6;1',
                     'patches': []},
 'broadcast-lowercase': {'name': 'broadcast-lowercase',
                         'command': 'C;5;all\r'
                                    '~~YT BROADCAST PROBE\r'
                                    '\r'
                                    '~~S\r'
                                    '~~~~6;1',
                         'patches': []},
 'broadcast-zero-turns': {'name': 'broadcast-zero-turns',
                          'command': 'C;5;ALL\r'
                                     '~~YT BROADCAST PROBE\r'
                                     '\r'
                                     '~~S\r'
                                     '~~~~6;1',
                          'patches': [[2, 49, 0]]},
 'broadcast-team-member': {'name': 'broadcast-team-member',
                           'command': 'C;5;ALL\r'
                                      '~~YT BROADCAST PROBE\r'
                                      '\r'
                                      '~~S\r'
                                      '~~~~6;1',
                           'patches': [[2, 89, 1]]},
 'blank-recipient': {'name': 'blank-recipient',
                     'command': 'C;5\r~~\r~~~1',
                     'patches': []},
 'blank-body-abort': {'name': 'blank-body-abort',
                      'command': 'C;5;ALL\r~~\r~~A;Y\r~~~~1',
                      'patches': []},
 'two-lines': {'name': 'two-lines',
               'command': 'C;5;ALL\r'
                          '~~YT BROADCAST FIRST\r'
                          'YT BROADCAST SECOND\r'
                          '\r'
                          '~~S\r'
                          '~~~~6;1',
               'patches': []},
 'recipient-read': {'name': 'recipient-read',
                    'command': '\r~~~~C;6;1',
                    'patches': [],
                    'parent': 'broadcast-send',
                    'actor': 'ENEMY'},
 'sender-read': {'name': 'sender-read',
                 'command': '\r~~~~C;6;1',
                 'patches': [],
                 'parent': 'broadcast-send'},
 'recipient-repeat': {'name': 'recipient-repeat',
                      'command': '\r~~~~C;6;6;1',
                      'patches': [],
                      'parent': 'recipient-read',
                      'actor': 'ENEMY'},
 'sender-after-recipient': {'name': 'sender-after-recipient',
                            'command': '\r~~~~C;6;1',
                            'patches': [],
                            'parent': 'recipient-read'},
 'budget-two': {'name': 'budget-two',
                'command': '\r~~~~C;6;1',
                'patches': [],
                'parent': 'broadcast-send',
                'actor': 'ENEMY',
                'mail_budget': 2},
 'budget-one': {'name': 'budget-one',
                'command': '\r~~~~C;6;1',
                'patches': [],
                'parent': 'broadcast-send',
                'actor': 'ENEMY',
                'mail_budget': 1},
 'budget-zero': {'name': 'budget-zero',
                 'command': '\r~~~~C;6;1',
                 'patches': [],
                 'parent': 'broadcast-send',
                 'actor': 'ENEMY',
                 'mail_budget': 0},
 'budget-negative-one': {'name': 'budget-negative-one',
                         'command': '\r~~~~C;6;1',
                         'patches': [],
                         'parent': 'broadcast-send',
                         'actor': 'ENEMY',
                         'mail_budget': -1}}
WITNESSES={'broadcast-send': {'world': '026b41cbebf3a7422c64a5a415dfa8b78f78b64281501cf2657177720a87d12e',
                    'transcript': 'b32fb165dbac724d765cbc35396a984f0035a3b76fa28755f82e721fe55c603b',
                    'aux': 'a03eaed1724d1b3c4b49f0123070c4c6058be49351aa1b52307d674a092f4768'},
 'broadcast-abort': {'world': '026b41cbebf3a7422c64a5a415dfa8b78f78b64281501cf2657177720a87d12e',
                     'transcript': '396a26f734e99999a746e139cd3854b0ae199d1db33c2d8f3f13b20590d5d9c6',
                     'aux': '1ff811102b140513be3b9ae7bcd525ca18e31a85568cedde158a3f0abe30f7f2'},
 'broadcast-lowercase': {'world': '026b41cbebf3a7422c64a5a415dfa8b78f78b64281501cf2657177720a87d12e',
                         'transcript': 'f49876cb5abc79931a05b633045d9c67fe790c89876079e703c9604297cbca1e',
                         'aux': 'a03eaed1724d1b3c4b49f0123070c4c6058be49351aa1b52307d674a092f4768'},
 'broadcast-zero-turns': {'world': 'a1b76ade8cd531f105ac88f0ada0c415d5c767b513bcacd5a62d1508cbf4cfdd',
                          'transcript': '5127c46957904f05ab9e9549f5cc30e6fbcda0287f2c078533836c060bff9834',
                          'aux': 'a03eaed1724d1b3c4b49f0123070c4c6058be49351aa1b52307d674a092f4768'},
 'broadcast-team-member': {'world': '8b4c5abe5271a0bb22962d909414e1d158e353d3b9a3881ae6fd407e3c13554c',
                           'transcript': '7ed16643eeeef00a889b563b41c62bb5c707897ff9efeba2bc7ccb5c5af0fff8',
                           'aux': '96c5dd5bb68a844ce38d50f85281d4f58fc77f1cc201a8ce1912f5efb3bbd3bf'},
 'blank-recipient': {'world': '026b41cbebf3a7422c64a5a415dfa8b78f78b64281501cf2657177720a87d12e',
                     'transcript': 'c105db54db0aea307ea521857521e2e785c8ec4d7f5d1659b0d6365c08e4c628',
                     'aux': '9d943efefd48fd7c35193608d0d21a96923c6ba8a35ea587879c37c5a180abb2'},
 'blank-body-abort': {'world': '026b41cbebf3a7422c64a5a415dfa8b78f78b64281501cf2657177720a87d12e',
                      'transcript': 'c6deca387856a0d08cdf46bb84a10b3a6beb3f24fb8658a17457fd9d84f3a61d',
                      'aux': '63259135bd811e721bbb617e5b40ed6c78d75a9d5abdd63960d8087bde9f2a66'},
 'two-lines': {'world': '026b41cbebf3a7422c64a5a415dfa8b78f78b64281501cf2657177720a87d12e',
               'transcript': '4eeacbd9d339abcade39ad28516ce780ccf4b339eb801f1e8a6d252305dd464c',
               'aux': '005ab982a30539bd344dfc6070807932d3ad45b84b39f631e4e2bbf28dbee46c'},
 'recipient-read': {'world': '026b41cbebf3a7422c64a5a415dfa8b78f78b64281501cf2657177720a87d12e',
                    'transcript': 'a96852bb8de87316458797a6552eedc6062fa8a487fa75389e59baae67c83d24',
                    'aux': '95dff75d795d08d9a902e7146e4dbbd5bf2d446d8c2f84438d1577047fdd8a8e'},
 'sender-read': {'world': '026b41cbebf3a7422c64a5a415dfa8b78f78b64281501cf2657177720a87d12e',
                 'transcript': 'ed2bab48a38926ecdfdba475fabd56877699b299cc58875436e0b4284c0b9ecb',
                 'aux': '75b933566646a9c30655df258120b0fb15d8a3e4b94d97e3252c3aa4b51233ab'},
 'recipient-repeat': {'world': '026b41cbebf3a7422c64a5a415dfa8b78f78b64281501cf2657177720a87d12e',
                      'transcript': 'a30d9eb221fe916c7434b30eae48292f42c2e1e7634be6b606361ba882c2226b',
                      'aux': '44a16cd5e8a7096cae139f84ccd6fc6bf14edb4f46d98cf947863bbe96f63ba7'},
 'sender-after-recipient': {'world': '026b41cbebf3a7422c64a5a415dfa8b78f78b64281501cf2657177720a87d12e',
                            'transcript': 'ed2bab48a38926ecdfdba475fabd56877699b299cc58875436e0b4284c0b9ecb',
                            'aux': '7fa1651edcc36d3fb46ff750589e478254846d88166ae671d497efdaedecbae0'},
 'budget-two': {'world': '026b41cbebf3a7422c64a5a415dfa8b78f78b64281501cf2657177720a87d12e',
                'transcript': 'c8d038bf9a3433a5107ebefb0a9984de55da8dc4a7b793d4fe088dd58b3f56a9',
                'aux': '48427b5fbb0b2d3b5eab9df54a98de89066186649597d8f84e76fb074712b8a7'},
 'budget-one': {'world': '026b41cbebf3a7422c64a5a415dfa8b78f78b64281501cf2657177720a87d12e',
                'transcript': '05ce639dc2e2cf9b6d0cd331fb358ba26595abcf7b7ea9589fec090511944ad4',
                'aux': '807c7f7a2121bc3d730d68c9359ef650af2a48b1ae7ee9f238f03a63a08027ed'},
 'budget-zero': {'world': '026b41cbebf3a7422c64a5a415dfa8b78f78b64281501cf2657177720a87d12e',
                 'transcript': '05ce639dc2e2cf9b6d0cd331fb358ba26595abcf7b7ea9589fec090511944ad4',
                 'aux': '48427b5fbb0b2d3b5eab9df54a98de89066186649597d8f84e76fb074712b8a7'},
 'budget-negative-one': {'world': '026b41cbebf3a7422c64a5a415dfa8b78f78b64281501cf2657177720a87d12e',
                         'transcript': '05ce639dc2e2cf9b6d0cd331fb358ba26595abcf7b7ea9589fec090511944ad4',
                         'aux': '2dca8a92f81775124a0eed156cf7bc9d1d25c75944af9185080a33e5f93f12db'}}
FOOTPRINT={'broadcast-send': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109]],
 'broadcast-abort': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109]],
 'broadcast-lowercase': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109]],
 'broadcast-zero-turns': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109]],
 'broadcast-team-member': [[2, 109],
                           [3, 109],
                           [4, 109],
                           [5, 109],
                           [6, 109],
                           [52, 77]],
 'blank-recipient': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109]],
 'blank-body-abort': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109]],
 'two-lines': [[2, 109], [3, 109], [4, 109], [5, 109], [6, 109]],
 'recipient-read': [],
 'sender-read': [],
 'recipient-repeat': [],
 'sender-after-recipient': [],
 'budget-two': [],
 'budget-one': [],
 'budget-zero': [],
 'budget-negative-one': []}
EXPECTED={'broadcast-send': {'packets': [[30, -2, 2, 'YT BROADCAST PROBE']],
                    'required': ['This will be a broadcast message to ALL '
                                 'players',
                                 'Transmission successful!'],
                    'body_count': 2,
                    'news_counts': {'YT BROADCAST PROBE': 1},
                    'news_block': '  -  Message from: Q \r\n'
                                  '  -  YT BROADCAST PROBE\r\n'},
 'broadcast-abort': {'packets': [],
                     'required': [],
                     'body_count': 1,
                     'news_counts': {'YT BROADCAST': 0},
                     'news_block': ''},
 'broadcast-lowercase': {'packets': [[30, -2, 2, 'YT BROADCAST PROBE']],
                         'required': ['This will be a broadcast message to ALL '
                                      'players',
                                      'Transmission successful!'],
                         'body_count': 2,
                         'news_counts': {'YT BROADCAST PROBE': 1},
                         'news_block': '  -  Message from: Q \r\n'
                                       '  -  YT BROADCAST PROBE\r\n'},
 'broadcast-zero-turns': {'packets': [[30, -2, 2, 'YT BROADCAST PROBE']],
                          'required': ['This will be a broadcast message to '
                                       'ALL players',
                                       'Transmission successful!'],
                          'body_count': 2,
                          'news_counts': {'YT BROADCAST PROBE': 1},
                          'news_block': '  -  Message from: Q \r\n'
                                        '  -  YT BROADCAST PROBE\r\n'},
 'broadcast-team-member': {'packets': [[30, -2, 2, 'YT BROADCAST PROBE']],
                           'required': ['This will be a broadcast message to '
                                        'ALL players',
                                        'Transmission successful!'],
                           'body_count': 2,
                           'news_counts': {'YT BROADCAST PROBE': 1},
                           'news_block': '  -  Message from: Q \r\n'
                                         '  -  YT BROADCAST PROBE\r\n'},
 'blank-recipient': {'packets': [],
                     'required': [],
                     'body_count': 0,
                     'news_counts': {'YT BROADCAST': 0},
                     'news_block': ''},
 'blank-body-abort': {'packets': [],
                      'required': [],
                      'body_count': 0,
                      'news_counts': {'YT BROADCAST': 0},
                      'news_block': ''},
 'two-lines': {'packets': [[30, -2, 2, 'YT BROADCAST FIRST'],
                           [30, -2, 2, 'YT BROADCAST SECOND']],
               'required': ['This will be a broadcast message to ALL players',
                            'Transmission successful!'],
               'body_count': 0,
               'news_counts': {'YT BROADCAST FIRST': 1,
                               'YT BROADCAST SECOND': 1},
               'news_block': '  -  Message from: Q \r\n'
                             '  -  YT BROADCAST FIRST\r\n'
                             '  -  YT BROADCAST SECOND\r\n',
               'display_counts': {'YT BROADCAST FIRST': 2,
                                  'YT BROADCAST SECOND': 2}},
 'recipient-read': {'packets': [[28, -2, 2, 'YT BROADCAST PROBE']],
                    'required': ['Message to: All * From: Q'],
                    'body_count': 2,
                    'news_counts': {'YT BROADCAST PROBE': 1},
                    'news_block': '  -  Message from: Q \r\n'
                                  '  -  YT BROADCAST PROBE\r\n'},
 'sender-read': {'packets': [[28, -2, 2, 'YT BROADCAST PROBE']],
                 'required': ['Message to: All * From: Q'],
                 'body_count': 2,
                 'news_counts': {'YT BROADCAST PROBE': 1},
                 'news_block': '  -  Message from: Q \r\n'
                               '  -  YT BROADCAST PROBE\r\n'},
 'recipient-repeat': {'packets': [[26, -2, 2, 'YT BROADCAST PROBE']],
                      'required': ['Message to: All * From: Q'],
                      'body_count': 3,
                      'news_counts': {'YT BROADCAST PROBE': 1},
                      'news_block': '  -  Message from: Q \r\n'
                                    '  -  YT BROADCAST PROBE\r\n'},
 'sender-after-recipient': {'packets': [[26, -2, 2, 'YT BROADCAST PROBE']],
                            'required': ['Message to: All * From: Q'],
                            'body_count': 2,
                            'news_counts': {'YT BROADCAST PROBE': 1},
                            'news_block': '  -  Message from: Q \r\n'
                                          '  -  YT BROADCAST PROBE\r\n'},
 'budget-two': {'packets': [[0, -2, 2, 'YT BROADCAST PROBE']],
                'required': ['Message to: All * From: Q'],
                'body_count': 1,
                'news_counts': {'YT BROADCAST PROBE': 1},
                'news_block': '  -  Message from: Q \r\n'
                              '  -  YT BROADCAST PROBE\r\n'},
 'budget-one': {'packets': [[1, -2, 2, 'YT BROADCAST PROBE']],
                'required': [],
                'body_count': 0,
                'news_counts': {'YT BROADCAST PROBE': 1},
                'news_block': '  -  Message from: Q \r\n'
                              '  -  YT BROADCAST PROBE\r\n'},
 'budget-zero': {'packets': [[0, -2, 2, 'YT BROADCAST PROBE']],
                 'required': [],
                 'body_count': 0,
                 'news_counts': {'YT BROADCAST PROBE': 1},
                 'news_block': '  -  Message from: Q \r\n'
                               '  -  YT BROADCAST PROBE\r\n'},
 'budget-negative-one': {'packets': [[-1, -2, 2, 'YT BROADCAST PROBE']],
                         'required': [],
                         'body_count': 0,
                         'news_counts': {'YT BROADCAST PROBE': 1},
                         'news_block': '  -  Message from: Q \r\n'
                                       '  -  YT BROADCAST PROBE\r\n'}}
NATIVE_LEDGER_SHA=''
NATIVE_RANGES={'yt.json': {'0x193a1': 3055,
             '0x21981': 1114,
             '0x21479': 75,
             '0x10802': 29,
             '0x18c77': 45,
             '0x35cf0': 960,
             '0x36b20': 500,
             '0x20ebb': 225,
             '0x36590': 1200},
 'maint.json': {'0x1672d': 499, '0x17155': 85}}
NATIVE_TARGETS={'yt.json': {'binary': 'YT.EXE',
             'binary_sha256': 'c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037',
             'ledger': 'ledger.json',
             'ledger_sha256': '9d8e1b1f2f34883a884496c4ca757fe601bdd0c2ed84f2d3dedd8a87db382a35'},
 'maint.json': {'binary': 'YTMAINT.EXE',
                'binary_sha256': '8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6',
                'ledger': 'maint-ledger.json',
                'ledger_sha256': '580045a945203e23a8179b9995a60bb91b666a2beca484743d6413d500fcfa19'}}
KEEP={'before.dat.gz','after.dat.gz','side-before.json.gz','sidefiles.json.gz','transcript.txt','game.log.gz','DOSDATE.LOG','DOSTIME.LOG','RETURN.LOG','KEYS.TXT','dosbox.log'}
GRAPH={1:[2,100],2:[1,3],3:[2],100:[101,102,103,104,105,106],101:[107],102:[108],103:[100],104:[100],105:[100],106:[100],107:[109],108:[109],109:[110],110:[100]}

def sha(value):return hashlib.sha256(value).hexdigest()
def read(path):
    if path.exists():return json.loads(path.read_text())
    return json.loads(gzip.decompress(path.with_suffix(path.suffix+'.gz').read_bytes()))
def zipped(path):return gzip.decompress(path.read_bytes())
def get(data,record,offset):
    raw=data[(record-1)*137+offset:(record-1)*137+offset+4]
    assert len(raw)==4, 'MBF field bounds'
    if not raw[3]:return 0.0
    m=int.from_bytes(raw[:3],'little')
    v=math.ldexp(1+(m&0x7fffff)/(1<<23),raw[3]-129)
    return -v if m&0x800000 else v

def enc(value):
    if not value:return bytes(4)
    f,e=math.frexp(abs(value));m=round((2*f-1)*(1<<23))
    if m==1<<23:m=0;e+=1
    return (m|(0x800000 if value<0 else 0)).to_bytes(3,'little')+bytes([e+128])
def put(data,record,offset,value):
    at=(record-1)*137+offset;assert 0<=at<at+4<=len(data), 'MBF patch bounds'
    data[at:at+4]=enc(value)

def packets(data):
    assert len(data)%86==0, 'radio packet alignment'
    result=[]
    for at in range(0,len(data),86):
        raw=data[at:at+86];fields=[get(raw,1,o) for o in (0,4,8)]
        assert all(math.isfinite(v) and v==int(v) for v in fields), 'integer radio fields'
        result.append([*[int(v) for v in fields],raw[12:86].rstrip(b' ').decode('cp437')])
    return result

def setup(case,baseline):
    b=bytearray(baseline)
    for sector,warps in GRAPH.items():
        start=(51+sector-1)*137;b[start:start+137]=bytes(137)
        for o,v in zip(range(41,65,4),warps):put(b,51+sector,o,v)
    patches=[[2,o,v] for o,v in {45:0,49:500,57:1,89:0,93:0,105:0,125:0}.items()]
    patches += [[3,o,v] for o,v in {45:0,57:2,61:42,53:7,89:0,125:1}.items()]
    patches += [[52,65,1],[152,65,2],[3053,93,101],[153,93,2],[4053,73,0],[4053,77,12]]
    if case.get('roster') is not None:
        start=51*137;b[start:start+41]=b'Orion'.ljust(41,b' ');b[start+113:start+117]=b'ABCD'
        for o,v in [(73,5),(77,case['roster'][0])]+list(zip((109,117,121,125),case['roster']+[0]*(4-len(case['roster'])))):put(b,52,o,v)
    patches+=case['patches']
    for r,o,v in patches:put(b,r,o,v)
    return bytes(b),patches

def witness_aux(files):return sha(b''.join(n.encode()+b'\0'+v+b'\0' for n,v in sorted(files.items())))
def clock(directory,case):
    assert case['date']=='10/24/2026', 'declared DOS date'
    assert re.search(r'Current date: [A-Za-z]{3} '+re.escape(case['date'])+r'(?:\n|$)',(directory/'DOSDATE.LOG').read_text()), 'DOS date'
    match=re.search(r'Current time: (\d+):(\d+):(\d+)\.(\d+)(am|pm)',(directory/'DOSTIME.LOG').read_text())
    assert match, 'DOS clock'
    h,m,s,f,ampm=match.groups();actual=(int(h)%12+(12 if ampm=='pm' else 0))*3600+int(m)*60+int(s)+int(f)/10**len(f)
    h,m,s=map(int,case['time'].split(':'));assert abs(actual-(3600*h+60*m+s))<=.06, 'DOS clock mismatch'

def loaded(data):
    """Reconstruct the exact observed MZ load image including segment fixups."""
    assert data[:2] == b'MZ', 'native MZ identity'
    image = bytearray(data[struct.unpack_from('<H', data, 8)[0]*16:])
    table = struct.unpack_from('<H', data, 24)[0]
    for i in range(struct.unpack_from('<H', data, 6)[0]):
        offset, segment = struct.unpack_from('<HH', data, table+4*i)
        at = segment*16+offset
        value = struct.unpack_from('<H', image, at)[0]
        struct.pack_into('<H', image, at, (value+0x1000) & 0xffff)
    return image

def verify_load_image(e,binary,image):
    value=e['normalized_result'];observed=value['observations']
    assert e['subject']['digest']['sha256']==sha(binary), 'native image target'
    header=struct.unpack_from('<H',binary,8)[0]*16
    assert value['status']=='verified' and value['format']=='dos-mz' and value['target_sha256']==sha(binary), 'native image verification'
    assert value['header_bytes']==header and value['module_bytes']==len(binary)-header and value['overlay_bytes']==0 and value['load_segment']==0x1000, 'native image bounds'
    ip,cs=struct.unpack_from('<HH',binary,20)
    assert value['entry']==dict(linear_address=hex(0x10000+cs*16+ip),offset=ip,relative_segment=cs), 'native entry mapping'
    assert observed['entry_points']==[value['entry']['linear_address']] and observed['language_id']=='x86:LE:16:Real Mode', 'native entry observations'
    assert len(observed['source_files'])==1, 'native source count'
    source=observed['source_files'][0]
    assert source['size']==len(binary) and source['original_sha256']==sha(binary) and source['modified_sha256']==sha(binary[:header]+image), 'native source digests'
    records=observed['relocations'];count=struct.unpack_from('<H',binary,6)[0];table=struct.unpack_from('<H',binary,24)[0]
    assert len(records)==count, 'native relocation count'
    for i,r in enumerate(records):
        offset,segment=struct.unpack_from('<HH',binary,table+4*i);at=segment*16+offset
        old=binary[header+at:header+at+2];new=bytes(image[at:at+2])
        assert r['address']==hex(0x10000+at) and r['segment']==segment+0x1000 and r['offset']==offset, 'native relocation address'
        assert r['original_bytes_hex']==old.hex() and r['memory_bytes_hex']==new.hex() and r['values']==[segment,offset,int.from_bytes(new,'little')] and r['status']=='APPLIED', 'native relocation bytes'
    coverage=[]
    for m in observed['mappings']:
        if not m['initialized']:
            assert m['file_offset'] is None and m['source_file_index'] is None and m['sha256'] is None, 'native uninitialized mapping'
            continue
        offset=m['file_offset'];size=m['length'];coverage.append((offset,offset+size))
        assert m['source_file_index']==0 and 0<=offset<offset+size<=len(binary), 'native file mapping'
        if m['address_space']=='HEADER':
            assert m['start']=='HEADER:0x0' and m['end']=='HEADER:'+hex(header-1) and offset==0 and size==header and not m['loaded'] and m['overlay'], 'native header mapping'
            raw=binary[:header]
        else:
            start=int(m['start'],16);end=int(m['end'],16)
            assert m['address_space']=='ram' and start==0x10000+offset-header and end==start+size-1 and m['loaded'] and not m['overlay'], 'native module mapping'
            raw=bytes(image[start-0x10000:end-0x10000+1])
        assert sha(raw)==m['sha256'], 'native mapped bytes'
    coverage.sort();assert coverage[0][0]==0 and coverage[-1][1]==len(binary) and all(coverage[i][1]==coverage[i+1][0] for i in range(len(coverage)-1)), 'native mapping coverage'
    assert value['checks'] and all(c['matched'] and c['expected']==c['observed'] for c in value['checks']), 'native self-check consistency'


def verify_native(root):
    assert NATIVE_RANGES and set(NATIVE_RANGES)==set(NATIVE_TARGETS), 'unfrozen native declarations'
    count=0
    for filename,ranges in NATIVE_RANGES.items():
        declaration=NATIVE_TARGETS[filename]
        binary=(ROOT/'archive/dos-original'/declaration['binary']).read_bytes()
        assert sha(binary)==declaration['binary_sha256'], 'native binary identity'
        image=loaded(binary)
        ledger_path=root/'rea'/declaration['ledger']
        assert sha(ledger_path.read_bytes())==declaration['ledger_sha256'], 'native ledger identity'
        ledger=read(ledger_path)
        assert ledger['target']=='archive/dos-original/'+declaration['binary'] and ledger['target_sha256']==sha(binary), 'native ledger target'
        header=struct.unpack_from('<H',binary,8)[0]*16
        assert ledger['header_bytes']==header and ledger['module_bytes']==len(image) and ledger['relocations']==struct.unpack_from('<H',binary,6)[0] and ledger['load_segment']=='0x1000', 'native ledger geometry'
        records=read(root/'rea'/filename)['records'];seen=set()
        assert len(records)==len(ranges)+1, 'native observation count'
        images=[r for r in records if r['operation']=='inspect_native_load_image']
        assert len(images)==1, 'native load image count'
        verify_load_image(images[0],binary,image)
        assert images[0]['evidence_id']==ledger['load_image_evidence_id'], 'native image evidence identity'
        ledger_reads={r['address']:r for r in ledger['reads']}
        assert set(ledger_reads)==set(ranges) and len(ledger_reads)==len(ledger['reads']), 'native ledger ranges'
        for e in records:
            if e['operation']!='read_bytes':continue
            v=e['normalized_result'];address=v['address']
            assert address in ranges and address not in seen, 'native address set';seen.add(address)
            size=ranges[address];at=int(address,16)-0x10000
            assert e['subject']['digest']['sha256']==sha(binary), 'native target identity'
            assert v['complete'] and v['requested_bytes']==v['returned_bytes']==size, 'incomplete native bytes'
            assert 0<=at<at+size<=len(image) and bytes.fromhex(v['bytes_hex'])==image[at:at+size], 'native bytes'
            r=ledger_reads[address]
            assert r['evidence_id']==e['evidence_id'] and r['length']==size and r['file_offset']==header+at, 'native source mapping'
            assert r['file_bytes_sha256']==sha(binary[header+at:header+at+size]) and r['loaded_bytes_sha256']==sha(bytes(image[at:at+size])), 'native source/loaded digests'
            assert e['analysis_profile']['digest']==ledger['analysis_profile_digest'], 'native analysis profile'
        assert seen==set(ranges), 'native address set';count+=len(seen)
    return count

def semantics(case,before,after,initial,final,text):
    name=case['name'];expected=EXPECTED[name]
    # Packet interpretation is independent of the original capture writer.
    assert packets(final.get('YTRMSG.DAT',b''))==expected['packets'], 'broadcast packet semantics'
    for record in expected.get('resource_players',[2,3,4,5,6]):
        for offset in (49,53,57,61,65,69,73,77,81,93,97,105,113,121,125,129):
            assert get(before,record,offset)==get(after,record,offset), ('conserved resources',record,offset)
    for phrase in expected.get('required',[]):assert phrase in text, 'required radio receipt: '+phrase
    for phrase in expected.get('forbidden',[]):assert phrase not in text, 'forbidden radio receipt: '+phrase
    if 'body_count' in expected:assert text.count('YT BROADCAST PROBE')==expected['body_count'], 'broadcast display count'
    if expected.get('news_block'):
        assert final.get('YTNEWS.DAT',b'').count(expected['news_block'].encode('cp437'))==1, 'broadcast newspaper publication'
    for phrase,count in expected.get('display_counts',{}).items():
        assert text.count(phrase)==count, 'broadcast display count'
    for phrase,count in expected.get('news_counts',{}).items():
        assert final.get('YTNEWS.DAT',b'').count(phrase.encode('cp437'))==count, 'broadcast newspaper publication'
    masked=bytearray(after)
    for r,o in FOOTPRINT[name]:
        at=(r-1)*137+o;masked[at:at+4]=before[at:at+4]
    assert bytes(masked)==before, 'unrelated world mutation'

def auxiliary_start(case,initial):
    initial=dict(initial)
    if 'mail_budget' in case:
        raw=bytearray(initial['YTRMSG.DAT']);put(raw,1,0,case['mail_budget']);initial['YTRMSG.DAT']=bytes(raw)
    for patch in case.get('aux_patches',[]):
        # Final capture schema is frozen below; only declared packet field changes.
        name,record,offset,value=patch
        raw=bytearray(initial[name]);put(raw,record,offset,value);initial[name]=bytes(raw)
    return initial

def verify_control(directory,decl,case,baseline,worlds,auxiliaries):
    name=case['name'];d=directory/name
    assert re.fullmatch(r'[a-z0-9-]+',name), 'scenario path'
    assert case==read(d/'result.json') and all(case[k]==v for k,v in decl.items()), 'manifest/declaration mismatch'
    assert case['recipe']==RECIPE and case['baseline_sha256']==BASE_SHA and case['binaries']==BINS, 'binary/session identity'
    assert case['date']==decl.get('date','10/24/2026') and case['time']==decl.get('time','00:00:00'), 'declared clock identity'
    assert case['timeout_seconds']==150, 'capture timeout declaration'
    assert case['complete'] and case['program_returned'] and not case['timed_out'], 'incomplete DOS control'
    assert set(case['files'])==KEEP and {p.name for p in d.iterdir()}==KEEP|{'result.json'}, 'retained file set'
    for file,digest in case['files'].items():assert sha((d/file).read_bytes())==digest, ('file hash',name,file)
    clock(d,case)
    assert (d/'RETURN.LOG').read_bytes()==b'BROADCAST_PROGRAM_RETURNED\r\n', 'DOS return marker'
    before,after=zipped(d/'before.dat.gz'),zipped(d/'after.dat.gz');assert len(before)==len(after)==568687, 'world size'
    if case.get('parent'):
        assert case['parent'] in worlds, 'parent ordering'
        expected=bytearray(worlds[case['parent']]);patches=decl['patches']
        for r,o,v in patches:put(expected,r,o,v)
        initial=auxiliaries[case['parent']]
    else:
        expected,patches=setup(decl,baseline)
        initial={p.name:p.read_bytes() for p in SOURCE.iterdir() if p.suffix.upper() in ('.DAT','.ASC','.DEF','.TMP') and p.name!='YTDATA.DAT'}
    initial=auxiliary_start(decl,initial)
    assert case['applied_patches']==patches, 'declared patch list'
    assert before==expected, 'undeclared setup or broken world chain'
    assert {n:bytes.fromhex(v) for n,v in read(d/'side-before.json').items()}==initial, 'auxiliary input chain'
    auxiliary=read(d/'sidefiles.json');final={n:bytes.fromhex(v['hex']) for n,v in auxiliary.items()}
    assert all(v['after_sha256']==sha(final[n]) and v['before_sha256']==(sha(initial[n]) if n in initial else None) for n,v in auxiliary.items()), 'auxiliary identity'
    tail='\r0\r~Q;Y\r~~' if decl.get('port_rescue') else '\rQ;Y\r~~'
    assert (d/'KEYS.TXT').read_bytes()==('\r~~~~~\r~'+decl['command']+'\r~~~~'+tail*24).encode(), 'exact input stream'
    text=(d/'transcript.txt').read_text()
    assert zipped(d/'game.log.gz').decode('cp437').replace('\r\n','\n')==text, 'raw transcript identity'
    assert 'Returning to Yankee Trader Local Logon Program...' in text, 'normal program return'
    semantics(case,before,after,initial,final,text)
    assert sha(after)==WITNESSES[name]['world'], 'frozen complete world witness'
    assert sha(text.encode())==WITNESSES[name]['transcript'], 'frozen complete transcript witness'
    assert witness_aux(final)==WITNESSES[name]['aux'], 'frozen complete auxiliary witness'
    return after,final

def verify(root):
    assert RECIPE_SHA and DECLARATIONS and WITNESSES and BINS and FOOTPRINT, 'unfrozen broadcast declarations'
    directory=root/'dos';baseline=(SOURCE/'YTDATA.DAT').read_bytes()
    assert sha(baseline)==BASE_SHA and zipped(directory/'baseline.dat.gz')==baseline, 'baseline identity'
    recipe_bytes=(directory/'recipe.json').read_bytes();assert sha(recipe_bytes)==RECIPE_SHA, 'frozen declarations'
    recipe=json.loads(recipe_bytes);manifest=read(directory/'results.json')
    assert recipe['recipe']==manifest['recipe']==RECIPE, 'recipe identity'
    declarations={c['name']:c for c in recipe['scenarios']};rows={c['name']:c for c in manifest['scenarios']}
    assert declarations==DECLARATIONS, 'frozen scenario declarations'
    assert len(rows)==len(manifest['scenarios'])==len(declarations)==len(WITNESSES), 'scenario count'
    assert set(rows)==set(declarations)==set(WITNESSES)==set(FOOTPRINT)==set(EXPECTED), 'scenario identity'
    binaries={n:(ROOT/('archive/analysis/yt-combat' if n=='KEYFEED.COM' else 'archive/dos-original')/n).read_bytes() for n in BINS}
    assert {n:sha(b) for n,b in binaries.items()}==BINS, 'archived binary identity'
    worlds={};auxiliaries={}
    for name,decl in declarations.items():
        try:worlds[name],auxiliaries[name]=verify_control(directory,decl,rows[name],baseline,worlds,auxiliaries)
        except AssertionError as error:raise AssertionError(f'{name}: {error}') from error
    reads=verify_native(root)
    chains=sum(bool(c.get('parent')) for c in declarations.values())
    print(f'Verified {len(rows)} returned broadcast controls, {chains} declared world/auxiliary chains and {reads} native byte observations.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--research',type=Path,default=ROOT/'research/yt-broadcast-radio/extended');verify(p.parse_args().research)
