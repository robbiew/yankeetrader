"""Verify DOS3.6 acquisition controls and bounded native evidence for removed Mercenary sales.

This validates retained observations and provenance; it does not claim universal
absence from arbitrary binaries or recover historical3.3 sale runtime rules.
"""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import struct

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'archive/analysis/yt-combat/experiments/fixture-planet-transfer'
RECIPE='mercenary-plasma-acquisition-v1'
BASE_SHA='2a63d12af095a59227840946be57fd4b7e4dafb5724d4019de694da7c4194b19'
BINS={'BRUN30.EXE':'3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8','KEYFEED.COM':'06dd2b9fcb91502185f6f4a2123ad7fdac144f47f5170df203760b86db127596','LOCAL.EXE':'bb970c43eb29fb80e7252f3968884f1c43543a5e39c6714b209ffca7dbf2d93a','YT.EXE':'c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037'}
RECIPE_SHA='09682d84eb6703cf4459d133f151af684e20c07ffc8dd0bdd66bf0909a351ed7'
WITNESSES={'quiet': {'world': '37b46ace1ade400c2737e91c61a5678a0de30d5f3e34cebe25751577a25fdc02',
           'transcript': 'c3ba6355ab156c8c5d996a322816608286bffe567fde1e1947b8dc6073d0933c',
           'aux': '20c59de782cb704f077834cb174789dbe5b97076608406afafbca9fd4104c6f5'},
 'main-help': {'world': '37b46ace1ade400c2737e91c61a5678a0de30d5f3e34cebe25751577a25fdc02',
               'transcript': 'fa0587a722f7164d2c0741d400d89f5e8c7ebeb1ebd11081f4f1dab24ad2e814',
               'aux': '20c59de782cb704f077834cb174789dbe5b97076608406afafbca9fd4104c6f5'},
 'earth-menu': {'world': '474ecbc45174f096df7f832f1a93dd06f3c575ec8b5da62b6e933cf096c7d6e0',
                'transcript': '1c238654c4537cd1ea34493225dd19b7a2a455b267125848f4d7c0032b23d352',
                'aux': '20c59de782cb704f077834cb174789dbe5b97076608406afafbca9fd4104c6f5'},
 'earth-no-plasma-item': {'world': '474ecbc45174f096df7f832f1a93dd06f3c575ec8b5da62b6e933cf096c7d6e0',
                          'transcript': '7372ee62c966ddbc2ce12e7bda238a98742d3c6cf485945bc3f6c9fcc50f6f48',
                          'aux': '5e00159137b65a827e309f93a6b4a023e5350287d8bebce1813dd7ab2925e026'},
 'earth-poor-menu': {'world': '3a804496bb09a468b9f2935802f6df06b3f5835a1034c9bcbbe4de9b75c9a151',
                     'transcript': '94643d9494d72ebadaf7854f85ec20bf776bb8c7de6d062b42421184099af57e',
                     'aux': '6c707e53c9d8ba59df3dff9529993495879a9f1d4a8e2cdc7eaab90d10c17cd4'},
 'base-look': {'world': '67d3fccc6a7367c348c7450099cf0f9485f382eac58ba688438e0eed6f747e87',
               'transcript': '971c88dd7be426c271e4f8124f13b6488aa60f683f3ea79280585139b4d7963b',
               'aux': '20c59de782cb704f077834cb174789dbe5b97076608406afafbca9fd4104c6f5'},
 'base-land-refuse': {'world': 'a1a3e511cbc379131af5350aab9b594b223c44c70b1bf1a8453888a834b47270',
                      'transcript': 'cac33839cefc2749d37e9bbd16df2f7aeb0a698d6ed46bae35e43ae885ff32b1',
                      'aux': '8dfd1d2540f7ba9479b03181b2bd2c2e507481b800cc20542570ca5d558cd62c'},
 'captured-base-menu': {'world': '87264893f8926c6fc68452ef6e22bea14594788bb8e17cee61d92d0b0f4293f9',
                        'transcript': '0cf64da3f1ae54d3ab7c9e797a68235fe284821ec527507430843931b94f75c5',
                        'aux': '20c59de782cb704f077834cb174789dbe5b97076608406afafbca9fd4104c6f5'},
 'captured-base-take': {'world': 'f8909d27cf6d9ea437bdf5d1e4d9291b3c109ae1e423fe29b2f8840e1f726932',
                        'transcript': 'f90ee36bbdadd7af44fa04c230145bb2e9ad1fd00c82a01942dc259829a237cd',
                        'aux': 'f98f57236aa56ee6c8d09340a1f6d6e083ec47a6f6fe8b4042b2d54259cc34f5'},
 'ordinary-planet-take': {'world': 'aeeeb2e7098f4655fcccf50b2f236b6ed9dfe0137c2e298ff357ae33f96d7d23',
                          'transcript': 'ba443ef31fcfc9a2edc3fa7288430a378c30a91185969314566f869edeb45667',
                          'aux': 'f98f57236aa56ee6c8d09340a1f6d6e083ec47a6f6fe8b4042b2d54259cc34f5'},
 'ordinary-take-all': {'world': 'fa1bd9ad98bbbd62fa0cbdc954c628d7e990cf3ddd4c67848289d0c0bb4fbfbb',
                       'transcript': 'e983f80105e56189b714ef97b05ba471c16118bd47f32ef38fab700cd3d8b908',
                       'aux': '852149243efba0c80992843b54cf46bd52fc31de74c4f653ae5e3c42e13adb8c'},
 'unowned-planet-take': {'world': 'a60e7e6221f5b756be44ca994fcebaa3e7e2f348ce9c80cffd8f333c830c1d08',
                         'transcript': '51d7db3b8d92ea80a00327dea2df609f93968050b3a0f3cf4b13e05775186a28',
                         'aux': 'f98f57236aa56ee6c8d09340a1f6d6e083ec47a6f6fe8b4042b2d54259cc34f5'},
 'mother-ship-name': {'world': '7265b2db5693ab94667ba8d725267e5992486b5bbf8bebf8c9f032a29fe9008b',
                      'transcript': 'cb29cb8c56cc10081dba75c00c3177ebabe4f3eaa87b9f1c971f0f7e1ad917b5',
                      'aux': '20c59de782cb704f077834cb174789dbe5b97076608406afafbca9fd4104c6f5'},
 'take-zero': {'world': 'b893d2870fb864ca6e3cab75fcedb7dc8d07f8bb1690a237088f5af2a8c48c58',
               'transcript': 'b9304b181918f9dd6555b75c1ce22d49bbbdb69091168b7423823dadebea8017',
               'aux': '20c59de782cb704f077834cb174789dbe5b97076608406afafbca9fd4104c6f5'},
 'ordinary-deposit': {'world': '57a25d34ab22cf9a2242b0712a91dcb823bd8ed69cc070e82929843b7c919d50',
                      'transcript': 'e4cf95518f68abcd45ab9a45b8749ecd5f60849601bbbab2a35498fc5eea61cd',
                      'aux': 'db7e3b74c761479af7e402d04bffb57bfb66039c0444af22b51b2eb700c7dce3'},
 'take-reload': {'world': '5859e4c1a04cdb7f0a62d4aacd48cddc73a59f0f9a8394ccf5d2376ed5bcc8a1',
                 'transcript': '8018c9f3e1c7a70140ec1810e1427c0b29564992d2e7b824ee8951a35b0b7cf7',
                 'aux': '7e55c7e3a088d47d35a7875d102d685422efc53a7c448714f9b66c9b03eead47'},
 'deposit-reload': {'world': 'adcf83c7df42f88f9c047adec357dfda31a03d189db318bf73e454a82e92a401',
                    'transcript': 'a55141dd119e81d3bfc793a3d57a00f8f2c8daef070161f64e62822a8ad4551f',
                    'aux': '5569e6de8e4242d88d69f02fc5745737cced04293bd208d80c0de9d69139fa7c'}}
FOOTPRINT={'quiet': [[2, 109],
           [3, 109],
           [4150, 45],
           [4150, 49],
           [4150, 53],
           [4150, 57],
           [4150, 61],
           [4150, 65],
           [4150, 69],
           [4150, 89],
           [4150, 125],
           [4150, 129]],
 'main-help': [[2, 109],
               [3, 109],
               [4150, 45],
               [4150, 49],
               [4150, 53],
               [4150, 57],
               [4150, 61],
               [4150, 65],
               [4150, 69],
               [4150, 89],
               [4150, 125],
               [4150, 129]],
 'earth-menu': [[2, 49], [2, 109], [3, 109]],
 'earth-no-plasma-item': [[2, 49], [2, 109], [3, 109]],
 'earth-poor-menu': [[2, 49], [2, 109], [3, 109]],
 'base-look': [[2, 109],
               [3, 109],
               [4150, 45],
               [4150, 49],
               [4150, 53],
               [4150, 57],
               [4150, 61],
               [4150, 65],
               [4150, 69],
               [4150, 89],
               [4150, 125],
               [4150, 129]],
 'base-land-refuse': [[2, 109],
                      [3, 109],
                      [4150, 45],
                      [4150, 49],
                      [4150, 53],
                      [4150, 57],
                      [4150, 61],
                      [4150, 65],
                      [4150, 69],
                      [4150, 89],
                      [4150, 125],
                      [4150, 129]],
 'captured-base-menu': [[2, 109],
                        [3, 109],
                        [4150, 45],
                        [4150, 49],
                        [4150, 53],
                        [4150, 57],
                        [4150, 61],
                        [4150, 65],
                        [4150, 69],
                        [4150, 89],
                        [4150, 125],
                        [4150, 129]],
 'captured-base-take': [[2, 109],
                        [2, 113],
                        [3, 109],
                        [4150, 45],
                        [4150, 49],
                        [4150, 53],
                        [4150, 57],
                        [4150, 61],
                        [4150, 65],
                        [4150, 69],
                        [4150, 89],
                        [4150, 113],
                        [4150, 125],
                        [4150, 129]],
 'ordinary-planet-take': [[2, 109],
                          [2, 113],
                          [3, 109],
                          [4053, 45],
                          [4053, 49],
                          [4053, 53],
                          [4053, 57],
                          [4053, 61],
                          [4053, 65],
                          [4053, 69],
                          [4053, 89],
                          [4053, 113],
                          [4053, 125],
                          [4053, 129]],
 'ordinary-take-all': [[2, 61],
                       [2, 109],
                       [2, 113],
                       [3, 109],
                       [4053, 45],
                       [4053, 49],
                       [4053, 53],
                       [4053, 57],
                       [4053, 61],
                       [4053, 65],
                       [4053, 69],
                       [4053, 89],
                       [4053, 113],
                       [4053, 125],
                       [4053, 129]],
 'unowned-planet-take': [[2, 109],
                         [2, 113],
                         [3, 109],
                         [4053, 45],
                         [4053, 49],
                         [4053, 53],
                         [4053, 57],
                         [4053, 61],
                         [4053, 65],
                         [4053, 69],
                         [4053, 77],
                         [4053, 89],
                         [4053, 113],
                         [4053, 125],
                         [4053, 129]],
 'mother-ship-name': [[2, 109],
                      [3, 109],
                      [4053, 45],
                      [4053, 49],
                      [4053, 53],
                      [4053, 57],
                      [4053, 61],
                      [4053, 65],
                      [4053, 69],
                      [4053, 89],
                      [4053, 125],
                      [4053, 129]],
 'take-zero': [[2, 109],
               [3, 109],
               [4053, 45],
               [4053, 49],
               [4053, 53],
               [4053, 57],
               [4053, 61],
               [4053, 65],
               [4053, 69],
               [4053, 89],
               [4053, 125],
               [4053, 129]],
 'ordinary-deposit': [[2, 109],
                      [2, 113],
                      [3, 109],
                      [4053, 45],
                      [4053, 49],
                      [4053, 53],
                      [4053, 57],
                      [4053, 61],
                      [4053, 65],
                      [4053, 69],
                      [4053, 89],
                      [4053, 113],
                      [4053, 125],
                      [4053, 129]],
 'take-reload': [[4053, 45],
                 [4053, 49],
                 [4053, 53],
                 [4053, 57],
                 [4053, 61],
                 [4053, 65],
                 [4053, 69],
                 [4053, 77],
                 [4053, 89],
                 [4053, 113],
                 [4053, 117],
                 [4053, 125],
                 [4053, 129]],
 'deposit-reload': [[4053, 45],
                    [4053, 49],
                    [4053, 53],
                    [4053, 57],
                    [4053, 61],
                    [4053, 65],
                    [4053, 69],
                    [4053, 77],
                    [4053, 89],
                    [4053, 113],
                    [4053, 117],
                    [4053, 125],
                    [4053, 129]]}
EXPECTED={'quiet': {'planet_record': 4150, 'owner': -2, 'required': []},
 'main-help': {'planet_record': 4150,
               'owner': -2,
               'required': ['+ - Fire Plasma Bolt', 'P - Dock at a <P>ort (and trade)']},
 'earth-menu': {'planet_record': 4150,
                'owner': -2,
                'required': ['[9] Hire Spies (Each)', '[0] Leave Port']},
 'earth-no-plasma-item': {'planet_record': 4150,
                          'owner': -2,
                          'required': ['[9] Hire Spies (Each)', 'INAVLID CHOICE!']},
 'earth-poor-menu': {'planet_record': 4150,
                     'owner': -2,
                     'required': ['[9] Hire Spies (Each)', 'Credits: 0 -=*=- Buy Which Item?']},
 'base-look': {'planet_record': 4150,
               'owner': -2,
               'required': ['Planet: Mercenary Base', '[ Sensors Activated ]']},
 'base-land-refuse': {'planet_record': 4150,
                      'owner': -2,
                      'required': ['Permission to land is DENIED!',
                                   'Do you wish to try to force a landing?']},
 'captured-base-menu': {'planet_record': 4150,
                        'owner': 2,
                        'required': ['Planet: Mercenary Base', '9 - Take Plasma Bolts']},
 'captured-base-take': {'planet_record': 4150,
                        'owner': 2,
                        'required': ['Planet: Mercenary Base', '<Take Plasma Bolts>']},
 'ordinary-planet-take': {'planet_record': 4053,
                          'owner': 2,
                          'required': ['Planet: Supply World', '<Take Plasma Bolts>']},
 'ordinary-take-all': {'planet_record': 4053, 'owner': 2, 'required': ['<Take all>', 'Plasma bolts. 20']},
 'ordinary-deposit': {'planet_record': 4053, 'owner': 2, 'required': ['Plasma Bolts Transferred!']},
 'unowned-planet-take': {'planet_record': 4053,
                         'owner': 0,
                         'required': ['Planet: Supply World', '<Take Plasma Bolts>']},
 'mother-ship-name': {'planet_record': 4053,
                      'owner': 2,
                      'required': ['Planet: Mercenary Mother Ship', '9 - Take Plasma Bolts']},
 'take-zero': {'planet_record': 4053, 'owner': 2, 'required': ['<Take Plasma Bolts>']},
 'take-reload': {'planet_record': 4053, 'owner': 2, 'required': []},
 'deposit-reload': {'planet_record': 4053, 'owner': 2, 'required': []}}
NATIVE_LEDGER_SHA='ea259220a98c5546cc2384ce6806ceda13539946173903e7cd53e2c804446e80'
NATIVE_RANGES={'yt.json': {'0x11659': 528, '0x11ac0': 1152, '0x12079': 16, '0x13240': 1024, '0x13e61': 1536, '0x144a1': 320, '0x148b0': 1536, '0x1660d': 512, '0x168e0': 640, '0x16d00': 4096, '0x3415a': 800, '0x34ef6': 1480}}
KEEP={'before.dat.gz','after.dat.gz','side-before.json.gz','sidefiles.json.gz','transcript.txt','game.log.gz','DOSDATE.LOG','DOSTIME.LOG','RETURN.LOG','KEYS.TXT','dosbox.log'}

def sha(value):
    return hashlib.sha256(value).hexdigest()

def read(path):
    if path.exists():return json.loads(path.read_text())
    return json.loads(gzip.decompress(path.with_suffix(path.suffix+'.gz').read_bytes()))

def zipped(path):return gzip.decompress(path.read_bytes())

def get(data, record, offset):
    raw = data[(record-1)*137+offset:(record-1)*137+offset+4]
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
    assert 1<=record<=4151 and offset in range(41,134,4), 'patch bounds'
    at=(record-1)*137+offset;data[at:at+4]=enc(value)

def setup(case,baseline):
    """Independently reconstruct the declared copied-world preparation."""
    assert case['sectors']==3000 and case['standard'] is True and case['start']==100, 'full-width fixture geometry'
    b=bytearray(baseline)
    for r in range(4052,4152):b[(r-1)*137:r*137]=bytes(137)
    slot=case.get('slot',99);r=4051+slot
    name=case.get('planet_name','Mercenary Base' if slot==99 else 'Supply World').encode()
    b[(r-1)*137:(r-1)*137+41]=name.ljust(41,b' ')
    for o,v in {41:297,45:0,49:0,53:0,57:0,61:0,65:0,69:0,73:case.get('owner',-2),77:case.get('ground',1000),81:0,85:len(name),89:0,113:20,117:1234,125:0,129:20}.items():put(b,r,o,v)
    patches=[]
    for player in range(4,52):
        patches.extend((player,o,0) for o in range(41,137,4));patches.append((player,109,-1))
    patches.extend((51+s,o,0) for s in range(1,3001) for o in range(41,137,4))
    for s,links in {1:[100],100:[1,101],101:[100]}.items():
        patches.extend((51+s,o,links[i] if i<len(links) else 0) for i,o in enumerate(range(41,65,4)))
    for player,values in ((2,{41:297,45:0,49:500,53:1000000,57:case.get('location',100),61:10000,65:100,69:10,73:20,77:30,81:case.get('cash',20000000),89:0,93:0,97:7,105:0,109:0,113:9,117:0,121:1000,125:1,129:8}),(3,{41:297,45:0,49:500,57:200,61:0,53:0,65:100,69:0,73:0,77:0,85:6,89:0,97:0,109:0,125:1})):
        patches.extend((player,o,v) for o,v in values.items())
    patches.extend(((52,65,1),(151,93,slot)))
    patches.extend(tuple(p) for p in case['patches'])
    for r,o,v in patches:put(b,r,o,v)
    return bytes(b),[list(p) for p in patches]

def clock(directory,case):
    date=case['date'];wanted=case['time']
    assert date=='10/24/2026', 'declared DOS date'
    assert re.search(r'Current date: [A-Za-z]{3} '+re.escape(date)+r'(?:\n|$)',(directory/'DOSDATE.LOG').read_text()), 'DOS date'
    match=re.search(r'Current time: (\d+):(\d+):(\d+)\.(\d+)(am|pm)',(directory/'DOSTIME.LOG').read_text())
    assert match, 'DOS clock'
    h,m,s,f,ampm=match.groups();actual=(int(h)%12+(12 if ampm=='pm' else 0))*3600+int(m)*60+int(s)+int(f)/10**len(f)
    h,m,s=map(int,wanted.split(':'));assert abs(actual-(3600*h+60*m+s))<=.06, 'DOS clock mismatch'

def witness_aux(files):
    return sha(b''.join(n.encode()+b'\0'+v+b'\0' for n,v in sorted(files.items())))

def semantics(case,before,after,text):
    name=case['name'];expected=EXPECTED[name]
    # Acquisition is a stock transfer, never a five-million-credit shop purchase.
    planet=expected['planet_record']
    delta=1 if name in {'captured-base-take','ordinary-planet-take','unowned-planet-take'} else 0
    if name=='ordinary-take-all':delta=get(before,planet,113)
    if name=='ordinary-deposit':delta=-get(before,2,113)
    assert get(after,2,81)==get(before,2,81), 'saved credits'
    assert get(after,2,49)==get(before,2,49)-(1 if name.startswith('earth-') else 0), 'saved turns'
    assert get(after,2,113)==get(before,2,113)+delta, 'saved carried plasma'
    if case.get('parent'):
        assert math.floor(get(after,planet,113))==math.floor(get(before,planet,113)) and get(before,planet,113)<=get(after,planet,113)<get(before,planet,113)+1, 'reloaded planetary plasma projection'
    else:
        assert get(after,planet,113)==get(before,planet,113)-delta, 'saved planetary plasma'
    assert get(after,2,57)==get(before,2,57), 'ship sector preserved'
    assert get(after,2,45)==0, 'living ship preserved'
    assert get(after,planet,73)==expected['owner'], 'planet ownership preserved'
    if case.get('parent'):
        assert get(after,planet,117)>=get(before,planet,117), 'reloaded bank projection'
    else:
        assert get(after,planet,117)==get(before,planet,117), 'planet bank preserved'
    assert 'Plasma bolts targeted... firing' not in text, 'no unintended launch'
    assert 'buy PLASMA BOLTS' not in text, 'no current mother-ship sale receipt'
    for phrase in expected.get('required',[]):assert phrase in text, 'required acquisition receipt: '+phrase
    for phrase in expected.get('forbidden',[]):assert phrase not in text, 'forbidden acquisition receipt: '+phrase
    masked=bytearray(after)
    for r,o in FOOTPRINT[name]:
        at=(r-1)*137+o;masked[at:at+4]=before[at:at+4]
    assert bytes(masked)==before, 'unrelated world mutation'

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
    # Reviewed ranges are independently checked against the immutable MZ image.
    assert NATIVE_RANGES, 'unfrozen native declarations'
    binary=(ROOT/'archive/dos-original/YT.EXE').read_bytes()
    assert sha(binary)==BINS['YT.EXE'], 'native binary identity'
    image=loaded(binary)
    ledger_path=root/'rea/ledger.json'
    assert sha(ledger_path.read_bytes())==NATIVE_LEDGER_SHA, 'native ledger identity'
    ledger=read(ledger_path)
    assert ledger['target']=='archive/dos-original/YT.EXE' and ledger['target_sha256']==sha(binary), 'native ledger target'
    header=struct.unpack_from('<H',binary,8)[0]*16
    assert ledger['header_bytes']==header and ledger['module_bytes']==len(image) and ledger['relocations']==struct.unpack_from('<H',binary,6)[0] and ledger['load_segment']=='0x1000', 'native ledger geometry'
    count=0
    for filename,ranges in NATIVE_RANGES.items():
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

def verify_control(directory,decl,case,baseline,worlds,auxiliaries):
    name=case['name'];d=directory/name
    assert re.fullmatch(r'[a-z0-9-]+',name), 'scenario path'
    assert case==read(d/'result.json') and all(case[k]==v for k,v in decl.items()), 'manifest/declaration mismatch'
    assert case['recipe']==RECIPE and case['baseline_sha256']==BASE_SHA and case['binaries']==BINS, 'binary/session identity'
    assert case['date']==decl.get('date','10/24/2026') and case['time']==decl.get('time','00:00:00'), 'declared clock identity'
    assert case['timeout_seconds']==decl.get('timeout',120), 'capture timeout declaration'
    assert case['complete'] and case['program_returned'] and not case['timed_out'], 'incomplete DOS control'
    assert set(case['files'])==KEEP and {p.name for p in d.iterdir()}==KEEP|{'result.json.gz'}, 'retained file set'
    for file,digest in case['files'].items():assert sha((d/file).read_bytes())==digest, ('file hash',name,file)
    clock(d,case)
    assert (d/'RETURN.LOG').read_bytes()==b'MERCENARY_ACQUISITION_RETURNED\r\n', 'DOS return marker'
    before,after=zipped(d/'before.dat.gz'),zipped(d/'after.dat.gz');assert len(before)==len(after)==568687, 'world size'
    if case.get('parent'):
        assert case['parent'] in worlds, 'parent ordering'
        expected=bytearray(worlds[case['parent']]);patches=decl['patches']
        for r,o,v in patches:put(expected,r,o,v)
        initial=auxiliaries[case['parent']]
    else:
        expected,patches=setup(decl,baseline)
        initial={p.name:p.read_bytes() for p in SOURCE.iterdir() if p.suffix.upper() in ('.DAT','.ASC','.DEF','.TMP') and p.name!='YTDATA.DAT'}
    assert case['applied_patches']==patches, 'declared patch list'
    assert before==expected, 'undeclared setup or broken world chain'
    assert {n:bytes.fromhex(v) for n,v in read(d/'side-before.json').items()}==initial, 'auxiliary input chain'
    auxiliary=read(d/'sidefiles.json');final={n:bytes.fromhex(v['hex']) for n,v in auxiliary.items()}
    assert all(v['after_sha256']==sha(final[n]) and v['before_sha256']==(sha(initial[n]) if n in initial else None) for n,v in auxiliary.items()), 'auxiliary identity'
    assert (d/'KEYS.TXT').read_bytes()==('\r~~~~~\r~'+decl['command']+'\r~~~~'+'Q;Y\r~~~~'*12).encode(), 'exact input stream'
    text=(d/'transcript.txt').read_text()
    assert zipped(d/'game.log.gz').decode('cp437').replace('\r\n','\n')==text, 'raw transcript identity'
    semantics(case,before,after,text)
    assert sha(after)==WITNESSES[name]['world'], 'frozen complete world witness'
    assert sha(text.encode())==WITNESSES[name]['transcript'], 'frozen complete transcript witness'
    assert witness_aux(final)==WITNESSES[name]['aux'], 'frozen complete auxiliary witness'
    return after,final

def verify_history(changes,manual):
    assert sha(changes)=='dc4357ab4882a81fc671bd3024d003c36b5cf96c9564204e69d22374a207e420', 'change-log source identity'
    assert sha(manual)=='918f9d746c14cda8025397f47e8616263187f9f810d10b2dae21b190759dae5f', 'manual source identity'
    text=changes.decode('cp437').replace('\r\n','\n')
    part33=text.split('*** Version 3.3 of Yankee Trader',1)[1].split('*** Version 3.4',1)[0]
    part34=text.split('*** Version 3.4 of Yankee Trader',1)[1].split('*** Version 3.5',1)[0]
    part36=text.split('*** Version 3.6 of Yankee Trader',1)[1]
    assert 'Added a MOTHER SHIP for the Mercenaries.' in part33 and '5,000,000 credits each.' in part33, 'historical addition and price'
    assert 'REMOVED the mercenary mother ship.' in part34 and 'ADDED plasma bolt production to planets.' in part34, 'historical replacement chronology'
    assert 'Added a MERCENARY HOME PLANET to the game.' in part36, 'distinct3.6 home planet'
    assert 'You cannot buy them at Earth.' in manual.decode('cp437'), 'final manual acquisition boundary'

def verify(root):
    assert RECIPE_SHA and WITNESSES and BINS and FOOTPRINT, 'unfrozen acquisition declarations'
    verify_history((ROOT/'archive/dos-original/CHANGES.TXT').read_bytes(),(ROOT/'archive/dos-original/YTINSTR.DOC').read_bytes())
    directory=root/'dos';baseline=(SOURCE/'YTDATA.DAT').read_bytes()
    assert sha(baseline)==BASE_SHA and zipped(directory/'baseline.dat.gz')==baseline, 'baseline identity'
    recipe_bytes=(directory/'recipe.json').read_bytes();assert sha(recipe_bytes)==RECIPE_SHA, 'frozen declarations'
    recipe=json.loads(recipe_bytes);manifest=read(directory/'results.json')
    assert recipe['recipe']==manifest['recipe']==RECIPE and recipe['source']==str(SOURCE.relative_to(ROOT)), 'recipe identity'
    declarations={c['name']:c for c in recipe['scenarios']};rows={c['name']:c for c in manifest['scenarios']}
    assert len(rows)==len(manifest['scenarios'])==len(declarations)==len(WITNESSES), 'scenario count'
    assert set(rows)==set(declarations)==set(WITNESSES)==set(FOOTPRINT), 'scenario identity'
    binaries={n:(ROOT/('archive/analysis/yt-combat' if n=='KEYFEED.COM' else 'archive/dos-original')/n).read_bytes() for n in BINS}
    assert {n:sha(b) for n,b in binaries.items()}==BINS, 'archived binary identity'
    worlds={};auxiliaries={}
    for name,decl in declarations.items():
        try:worlds[name],auxiliaries[name]=verify_control(directory,decl,rows[name],baseline,worlds,auxiliaries)
        except AssertionError as error:raise AssertionError(f'{name}: {error}') from error
    reads=verify_native(root)
    chains=sum(bool(c.get('parent')) for c in declarations.values())
    print(f'Verified {len(rows)} returned acquisition controls, {chains} exact world/auxiliary reload chains and {reads} native byte observations.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--research',type=Path,default=ROOT/'research/yt-mercenary-plasma');verify(p.parse_args().research)
