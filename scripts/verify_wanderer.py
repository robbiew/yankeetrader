"""Independently verify original-DOS Wanderer lifecycle and transport evidence."""
import argparse
import gzip
import hashlib
import json
import math
import re
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'archive/analysis/yt-combat/experiments/fixture-planet-transfer'
RECIPE='wanderer-lifecycle-v1'
BASE_SHA='2a63d12af095a59227840946be57fd4b7e4dafb5724d4019de694da7c4194b19'
# Filled only after completed original controls have been independently inspected.
RECIPE_SHA='2ce14e37f63203654435f123855fa58d62f14769718621cb881c3135b4136b2a'
WORLD_SHA={'maint-linked': '50184b82b34f421a0bcf7c842e38995acea336a45b6698527155a3974aa7936d',
 'maint-missing-link': '76e9add13986e49e9fecbc2dcfdc415e468b2a60caa85e0d3b503a3169f55c22',
 'maint-inactive-linked': 'e778e4e4be29060898b4871030e3860488143f8bbb4f64b8820c43da997568e9',
 'maint-inactive-missing': 'daa52d5e8823b9deb7c2bae38377ee57b324252667a372125ce684485e4931fd',
 'maint-duplicate-links': '68aadfbf09b61c8d491ea7718540e007b3d8411942fccc2dea0bd8bdd6982c11',
 'maint-owned': '50184b82b34f421a0bcf7c842e38995acea336a45b6698527155a3974aa7936d',
 'maint-foreign': '50184b82b34f421a0bcf7c842e38995acea336a45b6698527155a3974aa7936d',
 'maint-zero-bank': 'ef6c3d1173a3bd99220ee54cc1916f31b6b786526757d9d30368cb5f91502e3f',
 'maint-one-bank': 'a030c52a81ae68f654d189e7741000ab35a2c93b7730a6c278afcf6aabd21d23',
 'maint-missing-zero-bank': '76e9add13986e49e9fecbc2dcfdc415e468b2a60caa85e0d3b503a3169f55c22',
 'maint-renamed': '8ce171af52a8de6a55bb6f67f7b39e0360a654e47f2ffddc3e044807c6eb73d2',
 'maint-missing-stale-tail': '271a4678f9135383248017f68636076d3f87b70508448bf1da2e026ea5ca59eb',
 'maint-source-only-empty': '2edab649a73457c0230c37ae707fafeff2cec67f32f4ac0594e88576bf367b1f',
 'maint-only-earth': '1d03cb4008f59d672aa1c4521f78a44590a6a9f2ae84e46ab999f2a0a2faa431',
 'maint-only-mines': 'ae138c74a9ecdc5cc80db84655747c52b7718a1b412df5aa4896f616a81805cc',
 'maint-only-fighters': '34d7a6bfeffc06960da55de479c11832f432e7c9c77b55b9a87f7207a9478809',
 'maint-only-disconnected': '75994337615eab2ac9d34c4e150e2daf1c5fa985049b3d8e55c97e33f8c5739e',
 'maint-next-day': '2c775323366ecd3b309140d4392c3d418c6c2a014ee5ff82757fca526ca92da9',
 'maint-same-day': 'e2227d9e2b69a0ad2d04911d56e579fa8c78ea6f7ac713052f9ae6a396262748',
 'maint-regenerated-next-day': 'cdfacdf23b978a003c0eb7bb073d655a0f30c356419ad23932f86a27c48b5ce1',
 'reset-defaults': '21e8501ffa8a894e4fa7137c9b45982285bd0489ee1edd28feeeb7ffd6f26688',
 'reset-first-maintenance': 'b6f93141d4e7072b7cd945fdf5bdfd854b831efbd3147539e94713fd518ee1fa',
 'init-defaults': '16f6e969d50d4ef8bbea250966267c00160a1302422e4c531129c570e1f5eeb0',
 'init-same-day': 'cd079dd073200a0b608ba4428e6701c5556564226b117e47dd50653edbae043d',
 'init-next-day': '25a80b546612aeb37cda894aa1692159909bc055c10581adfcc761e43c1292f4',
 'maint-clock-backward': '3f761ae8658170e115c4222a90c24c4633a84fd36fee80627b3ade335a55c654',
 'land-neutral': 'd62ed01a5db56c2e9890fa35b68186d4c0cfc637c7a902b0963eee1f33aad0bc',
 'land-owned': '9a4f47da270b25e871c6793e6947568257938b90193b0cf8ca4cd08134da0ced',
 'land-foreign-unguarded': 'fd50202fe97550453603a4c87807e0c837e7afd0370ba4da89da213c45af1d37',
 'land-foreign-guarded': '3e3a80664659d7e80f7a41436336bb3298df7c6728774d0b317f716f36ef82a0',
 'land-neutral-guarded': 'd62ed01a5db56c2e9890fa35b68186d4c0cfc637c7a902b0963eee1f33aad0bc',
 'land-team': '7a50f0331650034e59a522cd5977acd7c61ddbe577c675938a6f1a8cbccfaceb',
 'rename-reserved': '9a4f47da270b25e871c6793e6947568257938b90193b0cf8ca4cd08134da0ced',
 'rename-renamed-slot': '32127103c2a16fc5f55b38822dc488dfa4089cf486361ded51b864a856f911fc',
 'bank-owned': '3dbe4a06eb21c05df06b2e1244b71b5661af1f11d36723f56d5eb3f3f0a23c15',
 'transfer-owned': 'b9abc8d2875dc20b3640540c4962e48c5f598e015c601ddf6d5fbfe05b641dad',
 'transport-two': '7273a6878772f1c05bd1bdae196f6cb52c071449fb0db3ba8c0c5b94644e3aac',
 'transport-one': '7273a6878772f1c05bd1bdae196f6cb52c071449fb0db3ba8c0c5b94644e3aac',
 'transport-three': '7273a6878772f1c05bd1bdae196f6cb52c071449fb0db3ba8c0c5b94644e3aac',
 'transport-cancel': 'c8a963f87c5a10ca11197d1cf047d0ce0631ccef62b4819c1017231da0c5f82a',
 'transport-blank': '4347ec082e56f1104871a3787083c416566a44682aae465688d5645fa8143d05',
 'transport-nine': '9343bbfea6a40d49a1ad0c87686e4c98bb4fafc3f0bd952a2124583394f91ae5',
 'transport-ten': 'e41b7f1a9297ef5459bd0c66f95eb027355f35df67def4bc832c7ee64f25a254',
 'transport-nineteen': 'faae2a4a4e520ab53a5b01985b61d92d3eaa17f489069fa84f1032260efc88d0',
 'transport-twenty': '7009349a8a20d65e90ffe403ad634a93f3f33a614bab2d98d73e260afb42f31c',
 'transport-owned': '7273a6878772f1c05bd1bdae196f6cb52c071449fb0db3ba8c0c5b94644e3aac',
 'transport-teammate': '3b3ba65c27a5717871c5da0e5aabc4636da193ec0b801ad68ceb0d270072dbad',
 'transport-unguarded': 'a54d3b7575c6ede6a67d16baba4e5458c1957e821c7d1b10bf6cc87da820c7cd',
 'transport-renamed': '55bd3fb2d07265687ea54af73d12ece3648a009295227a365124094d5aceff0c',
 'transport-occupied-planned': '9abc51d82c04ec06fa303737125ef0c1917934468ec75a410452e8795f0c52d5',
 'transport-zero-fighters': 'a0bc401dd57c4f7b7aa4e06aa78371797dd0690ed4d309f07a15b12cb18f8e4b',
 'transport-planned-mines': '452eb752d2aeece1d6d5a18cdab022b0a1b64e9905eb294deeb2d6a5f880367e',
 'transport-planned-fighters': 'e9f7a5b8c17df42209765bc406d8cc7d74cf8dae6c81665693e559f2f228493a',
 'transport-planet-mines': '11e09ed391d790b0a2890ae0fcaedec741d9a50e79dae1f3b4c7ae768c9f7c4f',
 'transport-planet-fighters': 'b1d9fee6eae7ab86f87c2572c00fa9c741783d11bdd0dcd23ed8a3718375001a',
 'transport-reentry': '7273a6878772f1c05bd1bdae196f6cb52c071449fb0db3ba8c0c5b94644e3aac',
 'transport-maintenance': 'ac2a0ef9e06c8fda46fe69d8998570564013588956550a0fde5747653b07086e'}
AUX_SHA={'maint-linked': 'ae8538268b02553290bba3c750dd2e7bdc710b92c04a43a2a961f061029522ee',
 'maint-missing-link': 'c63aaab0e0fe9ab911687590db415054daa0c47a81fd4028ff3318e53b702f3b',
 'maint-inactive-linked': '39718bed5ab541e2d71b2fdb6fed9fac8d5e58d1cf5fdc66f2d655df01f86d0f',
 'maint-inactive-missing': '0da95b28931b32fb3fd035fb7d57dff0c713a751315a4b327e18206abc2143b2',
 'maint-duplicate-links': 'ae8538268b02553290bba3c750dd2e7bdc710b92c04a43a2a961f061029522ee',
 'maint-owned': 'ae8538268b02553290bba3c750dd2e7bdc710b92c04a43a2a961f061029522ee',
 'maint-foreign': 'ae8538268b02553290bba3c750dd2e7bdc710b92c04a43a2a961f061029522ee',
 'maint-zero-bank': 'ae8538268b02553290bba3c750dd2e7bdc710b92c04a43a2a961f061029522ee',
 'maint-one-bank': 'ae8538268b02553290bba3c750dd2e7bdc710b92c04a43a2a961f061029522ee',
 'maint-missing-zero-bank': 'c63aaab0e0fe9ab911687590db415054daa0c47a81fd4028ff3318e53b702f3b',
 'maint-renamed': 'ae8538268b02553290bba3c750dd2e7bdc710b92c04a43a2a961f061029522ee',
 'maint-missing-stale-tail': 'c63aaab0e0fe9ab911687590db415054daa0c47a81fd4028ff3318e53b702f3b',
 'maint-source-only-empty': '6eb3f6f931520be95a7a336f2849ee3c827cb0cb8d59f13994071ff28ae1b411',
 'maint-only-earth': 'abcf85b239787424ccd28c4f8fcb8c854afa94c60d9c43ed630b352ce778d68f',
 'maint-only-mines': '14ffa400ad8d2c33c3c715012d041286839c481ff41a1c89b9e2a40b42838a0b',
 'maint-only-fighters': 'a47e672d81fb3a2f6bde89928796b16f63b22902baf63bb565727cfc6329b624',
 'maint-only-disconnected': '14ffa400ad8d2c33c3c715012d041286839c481ff41a1c89b9e2a40b42838a0b',
 'maint-next-day': '97b863fd4e6ccf6a7dbe6f127650978ddd6d3f4cd9dadc2882392c94ec3c44f8',
 'maint-same-day': 'e869f1ecbb3bf3f8d4823bfccd7a5037e7075858cbf5e1a6d03df38286a5bdf6',
 'maint-regenerated-next-day': '07708a53eaa3e068aced8f04a3f590ffcf7a0781bc53c5a73d56da6a843d7efd',
 'reset-defaults': '48d9ccd595113eacea9b02e47a9371055f5c65aae8ef66784b5811509e00db0c',
 'reset-first-maintenance': '24c21b606ba9ee1d0fa28c5039469a6b0a04151717b1f26c349781efcb28191b',
 'init-defaults': '580b5c5aa2052f6672dc8f1ed933bbd39cf8bcf7f0e1227fc45a68c180dbc81a',
 'init-same-day': '7dc2c93f184416f2cb9c8a4190c7e80098db495d82936a515454f15faa44c0af',
 'init-next-day': '444d022ab90854e4549ec242fdd1328d44cb1099ffc124b830000f01f6344711',
 'maint-clock-backward': 'ce9703c6808b932dd01ceda28ad590060aae2314a2fbde2dc57c915dd6b581e5',
 'land-neutral': 'cc8d74ed17829afb79b73a27e51a6a4348e30d211003c907b63d6e4bc723fbf5',
 'land-owned': 'cc8d74ed17829afb79b73a27e51a6a4348e30d211003c907b63d6e4bc723fbf5',
 'land-foreign-unguarded': 'cc8d74ed17829afb79b73a27e51a6a4348e30d211003c907b63d6e4bc723fbf5',
 'land-foreign-guarded': '4478a5cbe6642fa8ca41765f83011c7270a9039f75b808032125a2e680f9753a',
 'land-neutral-guarded': 'cc8d74ed17829afb79b73a27e51a6a4348e30d211003c907b63d6e4bc723fbf5',
 'land-team': '0cc7ea0a3a8e90a9ea1536320baea0ab884724bdda7fc9a805f315865f094754',
 'rename-reserved': 'cc8d74ed17829afb79b73a27e51a6a4348e30d211003c907b63d6e4bc723fbf5',
 'rename-renamed-slot': 'cc8d74ed17829afb79b73a27e51a6a4348e30d211003c907b63d6e4bc723fbf5',
 'bank-owned': 'a41b7e8e78c81f38835509387fd3c7f846b3c6658b61594cf7fdf1735f323a88',
 'transfer-owned': '45c567eb6e958a2cf234913b922d31469c229a1e3ffe2c349ef2f721f43c78ed',
 'transport-two': 'a04db039a1ef8dca911ede1ef54e2b3a86446113597bbb4767bbbb77224f4f6a',
 'transport-one': 'a04db039a1ef8dca911ede1ef54e2b3a86446113597bbb4767bbbb77224f4f6a',
 'transport-three': 'a04db039a1ef8dca911ede1ef54e2b3a86446113597bbb4767bbbb77224f4f6a',
 'transport-cancel': 'a04db039a1ef8dca911ede1ef54e2b3a86446113597bbb4767bbbb77224f4f6a',
 'transport-blank': 'a04db039a1ef8dca911ede1ef54e2b3a86446113597bbb4767bbbb77224f4f6a',
 'transport-nine': 'a04db039a1ef8dca911ede1ef54e2b3a86446113597bbb4767bbbb77224f4f6a',
 'transport-ten': 'a04db039a1ef8dca911ede1ef54e2b3a86446113597bbb4767bbbb77224f4f6a',
 'transport-nineteen': 'a04db039a1ef8dca911ede1ef54e2b3a86446113597bbb4767bbbb77224f4f6a',
 'transport-twenty': 'a04db039a1ef8dca911ede1ef54e2b3a86446113597bbb4767bbbb77224f4f6a',
 'transport-owned': 'a04db039a1ef8dca911ede1ef54e2b3a86446113597bbb4767bbbb77224f4f6a',
 'transport-teammate': 'b854ea4311bc3d181ad3c379a2f6f2a8498ec13674d01f5be25ce128d5ed651a',
 'transport-unguarded': 'a04db039a1ef8dca911ede1ef54e2b3a86446113597bbb4767bbbb77224f4f6a',
 'transport-renamed': 'a04db039a1ef8dca911ede1ef54e2b3a86446113597bbb4767bbbb77224f4f6a',
 'transport-occupied-planned': 'a2af7ad7a07f84e0d9caf42864cea42f53fce8c928c6d1b548ce17e2ddc7065f',
 'transport-zero-fighters': 'c21d04d4e15cf8a0d5fc63b1a3bc5c9950698d12b5f1e960d686ca9a7d846a03',
 'transport-planned-mines': 'c982eb40c014b1ffb108ed3c42fda89c0bfa4ab4c021fc57d50c4a8f921c74db',
 'transport-planned-fighters': 'dd0da69847ac55bd2ec2bbc71e8d7bc6fa01257eb04e3714b8dabd27de064ebf',
 'transport-planet-mines': 'a04db039a1ef8dca911ede1ef54e2b3a86446113597bbb4767bbbb77224f4f6a',
 'transport-planet-fighters': '6ff016b7e52eb84f9ba18146c4f4637e4788078fd5472c8d14a0e7931a61a27f',
 'transport-reentry': 'f224f5a46c9da80b15ff0765c55b136a4b4a240d13cbb9b5e4ec3a77de7c8318',
 'transport-maintenance': '8d68303a3ef1a9ff3c3bb10e33156b6b5144a1b998bbb283648ff1047293fc8e'}
DIAGNOSTIC_SHA={'no-vacancy': {'recipe': '6031baf9e2924e72f2e5ebac274a6a7b6fd14b114b6e6f78b3f3eb69a6d56b8c',
                'world': '7d39c7e9c17421d0d174865e705819522348685919610801307f2f10b5a12a6c',
                'aux': '2e44f6c6a0c368392bef9082c9c522e1fa91da53c1020c7d119087460abbd62a',
                'transcript': '72154c3d7d3089e53a4fd478f76d5d9435978f00dc608b4fe9fdb63ae913d103'},
 'later-npc-interference': {'recipe': '799675cd923ed55b12235d24d0bc742179ce70a51310c01452db166c0d109d5b',
                            'world': '6cc6ce453b397230e1e910afc3938af9f4cea9e6498da2c24f34007f5b15399e',
                            'aux': '17527766f91bd4976aeece8672a75036d70e34548b1467e0f7d89e5c6d6e7bce',
                            'transcript': '4bd1dfe78fa83f66e26515700a39aa9f009026def3241506fa0f4d66bb9a14cc'}}
NATIVE_RANGES={
 'yt-init.json':('YT-INIT.EXE',{'0x11efa':207,'0x103c9':415,'0x123c2':34}),
 'yt.json':('YT.EXE',{'0x15464':428,'0x2b0df':264,'0x2809f':689,'0x274e2':1191,'0x13515':395,'0x132a3':230,'0x20ef9':39}),
 'ytmaint.json':('YTMAINT.EXE',{'0x19078':80,'0x11cf5':884,'0x178f3':240,'0x10096':426}),
}
KEEP={'before.dat.gz','after.dat.gz','side-before.json.gz','sidefiles.json.gz','transcript.txt','game.log.gz','DOSDATE.LOG','DOSTIME.LOG','RETURN.LOG','KEYS.TXT','dosbox.log'}
BINS={
 'RMT-INIT.EXE':'05f639fe5249ac6ae8e28d8656f4c5e668e40ff08bf66524b109ad31a2217dac',
 'YT-INIT.EXE':'601e42bbe1ce91cb776d5a0fa6b4860b269a3d8c3e214df4ddd4d89d8b2aa7a2',
 'YT.EXE':'c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037',
 'YTMAINT.EXE':'8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6',
 'BRUN30.EXE':'3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8',
 'LOCAL.EXE':'bb970c43eb29fb80e7252f3968884f1c43543a5e39c6714b209ffca7dbf2d93a',
 'KEYFEED.COM':'06dd2b9fcb91502185f6f4a2123ad7fdac144f47f5170df203760b86db127596',
}


def sha(value):
    return hashlib.sha256(value).hexdigest()


def read(path):
    if path.exists():return json.loads(path.read_text())
    return json.loads(gzip.decompress(path.with_suffix(path.suffix+'.gz').read_bytes()))


def zipped(path):
    return gzip.decompress(path.read_bytes())


def side(path):
    return json.loads(zipped(path))


def rawfield(data, record, offset):
    at = (record-1)*137+offset
    return data[at:at+4]


def get(data, record, offset):
    raw = rawfield(data, record, offset)
    mantissa = int.from_bytes(raw[:3], 'little')
    if raw[3] == 0:
        return 0.0
    value = math.ldexp(1+(mantissa & 0x7fffff)/(1 << 23), raw[3]-129)
    return -value if mantissa & 0x800000 else value


def enc(value):
    if value == 0:
        return bytes(4)
    fraction, exponent = math.frexp(abs(value))
    mantissa = round((2*fraction-1)*(1 << 23))
    if mantissa == 1 << 23:
        mantissa = 0
        exponent += 1
    return (mantissa | (0x800000 if value < 0 else 0)).to_bytes(3, 'little')+bytes([exponent+128])


def put(data, record, offset, value):
    assert 1 <= record <= len(data)//137 and offset in range(41, 134, 4), 'patch bounds'
    at = (record-1)*137+offset
    data[at:at+4] = enc(value)


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


def public_score(data, player):
    """Public native ship score; planetary bank/production are not ship assets."""
    terms=((53,50),(61,100),(65,2500),(69,20),(73,30),(77,40),(81,1),
           (97,1000),(113,1000000),(117,50000),(121,750),(129,2500))
    if get(data,player,45)!=0:
        return 0
    total=sum(get(data,player,offset)*weight for offset,weight in terms)
    total+=sum(get(data,51+sector,81)*100 for sector in range(1,int(get(data,1,57)-get(data,1,53))+1) if get(data,51+sector,85)==player)
    # These controls never install the scanner (its flag contributes 250000).
    if get(data,player,93)>0:
        total+=250000
    return total


def assert_unchanged_except(before,after,fields=(),names=()):
    masked=bytearray(after)
    for record,offset in fields:
        at=(record-1)*137+offset;masked[at:at+4]=before[at:at+4]
    for record in names:
        at=(record-1)*137;masked[at:at+41]=before[at:at+41]
    assert masked==before, 'unrelated world mutation'


def auxiliary_witness(files):
    return sha(b''.join(name.encode()+b'\0'+data+b'\0' for name,data in sorted(files.items())))


def verify_native(root):
    assert NATIVE_RANGES, 'unfrozen native declarations'
    reads=0
    for filename,(executable,ranges)in NATIVE_RANGES.items():
        binary=(ROOT/'archive/dos-original'/executable).read_bytes()
        assert sha(binary)==BINS[executable], 'native binary identity'
        image=loaded(binary)
        records=read(root/'rea'/filename)['records']
        assert len(records)==len(ranges)+1, 'native observation count'
        images=[r for r in records if r['operation']=='inspect_native_load_image']
        assert len(images)==1, 'native load image count'
        verify_load_image(images[0],binary,image)
        seen=set()
        for record in records:
            if record['operation']=='inspect_native_load_image':continue
            assert record['operation']=='read_bytes', 'native operation'
            value=record['normalized_result'];address=value['address']
            assert address in ranges and address not in seen, 'native address set'
            seen.add(address);count=ranges[address]
            assert record['subject']['digest']['sha256']==sha(binary), 'native target identity'
            assert value['complete']and value['requested_bytes']==value['returned_bytes']==count, 'incomplete native bytes'
            at=int(address,16)-0x10000
            assert 0<=at<at+count<=len(image), 'native read bounds'
            assert bytes.fromhex(value['bytes_hex'])==image[at:at+count], 'native bytes'
        assert seen==set(ranges), 'native address set'
        reads+=len(seen)
    return reads


def verify_clock(directory,case):
    date=case['date'];clock=case['time']
    assert re.fullmatch(r'10/2[3-9]/2026',date), 'declared DOS date'
    line=(directory/'DOSDATE.LOG').read_text()
    assert re.search(r'Current date: [A-Za-z]{3} '+re.escape(date)+r'(?:\n|$)',line), 'DOS date'
    match=re.search(r'Current time: (\d+):(\d+):(\d+)\.(\d+)(am|pm)',(directory/'DOSTIME.LOG').read_text())
    assert match, 'DOS clock'
    h,m,s,f,ampm=match.groups()
    actual=(int(h)%12+(12 if ampm=='pm'else 0))*3600+int(m)*60+int(s)+int(f)/10**len(f)
    h,m,s=map(int,clock.split(':'));expected=3600*h+60*m+s
    assert abs(actual-expected)<=.06, 'DOS clock mismatch'


def planet_name(data):
    return data[4051*137:4051*137+41].decode('cp437').rstrip()


def links(data):
    return {s for s in range(1,3001)if get(data,51+s,93)==1}


def verify_growth(case,before,after,record=4052,transferred_fighters=0,ground_growth=True):
    """Conservative elapsed-time bounds; frozen witnesses retain exact MBF bytes."""
    days=get(after,record,41)-get(before,record,41)
    if days<0:days+=365
    elapsed=min(10,days+max(0,get(after,record,89)-get(before,record,89))/1440)
    assert 0<=elapsed<=12, 'planet elapsed production bound'
    for offset in(45,49,53):
        old,new=get(before,record,offset),get(after,record,offset)
        assert old<=new<=old*(1+elapsed)+.001, 'planet production growth bound'
    for stock,rate,multiplier in((57,45,1),(61,49,1),(65,53,1),(77,53,1),(69,53,1),(113,53,1),(125,53,1),(129,53,10)):
        if stock==77 and not ground_growth:continue
        old,new=get(before,record,stock),get(after,record,stock)
        if stock==129:old+=transferred_fighters
        assert old<=new<=old+max(get(after,record,rate),1)*multiplier*elapsed+1, 'planet stock growth bound'


def verify_semantics(case,before,after,text):
    from datetime import datetime
    mode=case['mode'];kind=case['expect'];name=case['name'];day=datetime.strptime(case['date'],'%m/%d/%Y').timetuple().tm_yday
    before_links=links(before);after_links=links(after);record=4052
    if mode=='initializer':
        assert 'Initializing planets...'in text and 'Daily Maintenance Completed OK'in text, 'initializer maintenance handoff'
        assert len(after_links)==1 and get(after,1,81)==day, 'initializer Wanderer bootstrap'
        expected={41:day-10,45:5000,49:5000,53:5000,57:0,61:0,65:0,69:0,73:0,77:0,85:12,113:0,117:250000,125:0,129:0}
        assert planet_name(after)=='The Wanderer'and all(get(after,record,o)==value for o,value in expected.items()), 'initializer Wanderer fields'
        return
    if mode=='reset':
        assert 'Initialization completed sucessfully!'in text, 'initializer completion'
        assert not after_links and all(get(after,4051+p,85)==0 for p in range(1,101)), 'reset Wanderer remains inactive'
        assert 'Moving The Wanderer'not in text and 'P.H.O.E.N.I.X.'not in text, 'reset does not run maintenance'
        assert get(after,1,81)==get(before,1,81), 'reset maintenance day preservation'
        return
    if mode=='maintenance':
        assert 'Yankee Trader Maintenance program'in text, 'maintenance entry'
        assert 'Daily Maintenance Completed OK'in text and get(after,1,81)==day, 'maintenance completion/day'
        assert 'Moving The Wanderer (Planet #1)'in text and 'Wanderer has successfully warped!'in text, 'maintenance relocation notices'
        first=min(before_links)if before_links else None
        survivors=before_links-({first}if first else set())
        candidates=after_links-survivors
        assert len(candidates)==1 and survivors<=after_links, 'first-link-only relocation'
        candidate=next(iter(candidates))
        assert get(before,51+candidate,93)==0 or candidate==first, 'candidate planet admission'
        assert after_links==survivors|{candidate}, 'Wanderer link conservation'
        assert get(after,4052,73)==0, 'maintenance governor reset'
        regenerated=not before_links
        assert ('The Wanderer is missing or has been destroyed!'in text)==regenerated, 'regeneration missing notice'
        assert ('The Wanderer regenerated with P.H.O.E.N.I.X. device!'in text)==regenerated, 'regeneration device notice'
        if regenerated:
            assert planet_name(after)=='The Wanderer'and get(after,record,85)==12, 'regenerated name/activity'
            expected={41:day-10,45:5000,49:5000,53:5000,57:0,61:0,65:0,69:0,73:0,77:0,117:250000,125:0}
            assert all(get(after,record,o)==value for o,value in expected.items()), 'regenerated Wanderer fields'
            # These cells lie outside the PHOENIX reset assignments. Active
            # pre-maintenance stock growth can precede recreation.
            for o in(81,93,97,101,105,109,121,133):assert rawfield(after,record,o)==rawfield(before,record,o), 'regeneration stale tail preservation'
            for o in(113,129):
                assert get(after,record,o)>=get(before,record,o), 'regeneration retained weapon stock'
                if get(before,record,85)==0:assert rawfield(after,record,o)==rawfield(before,record,o), 'inactive regeneration weapon preservation'
            if get(before,record,85)==0:assert rawfield(after,record,89)==rawfield(before,record,89), 'inactive regeneration clock preservation'
        else:
            assert planet_name(after)==planet_name(before)and get(after,record,85)==get(before,record,85), 'linked name/activity preservation'
            elapsed=day-get(before,record,41)
            if elapsed<0:elapsed+=365
            old_bank=get(before,record,117)
            expected_bank=250000 if old_bank<=0 else old_bank+math.floor(old_bank*.01*min(10,elapsed))
            assert get(after,record,117)==expected_bank, 'linked bank settlement'
            if get(before,record,85)==0:
                expected=bytearray(before[(record-1)*137:record*137]);at=73;expected[at:at+4]=rawfield(after,record,73)
                assert after[(record-1)*137:record*137]==expected, 'inactive linked record preservation'
            else:verify_growth(case,before,after)
        if 'candidate'in case:assert candidate==case['candidate'], 'single-candidate placement'
        if kind=='source-only':assert candidate==first==100, 'source sector reuse'
        # Background maintenance changes ports/factions/messages as well; exact
        # complete-world and auxiliary witnesses bind those non-Wanderer effects.
        for player in(2,3):
            if get(before,player,85)>0:
                for offset in(45,49,53,57,61,65,69,73,77,81,97,113,117,121,129):assert rawfield(before,player,offset)==rawfield(after,player,offset), 'maintenance player asset preservation'
        return
    assert mode=='game'and 'Returning to Yankee Trader Local Logon Program...'in text, 'normal quit'
    assert '<Land/Create planet>'in text, 'planet entry command'
    assert '<Take all>'not in text, 'unrequested default withdrawal'
    owner=get(before,record,73);ground=int(get(before,record,77));bank=get(before,record,117)
    ship_sector=int(get(before,2,57));turns=get(before,2,49)
    fields={(2,109),(3,109)}|{(record,o)for o in(41,45,49,53,57,61,65,69,77,89,113,125,129)}
    names=set();expected_links=set(before_links);expected_name=planet_name(before)
    if get(before,2,89)==1 and get(before,3,89)==1:
        assert get(after,52,77)==2, 'team member recount';fields.add((52,77))
    if kind=='no-planet':
        assert 'Planet: '+expected_name not in text, 'reentry has no transported planet'
        assert after_links==before_links, 'reentry planet link preservation'
    else:
        verify_growth(case,before,after,transferred_fighters=123 if kind=='transfer'else 0,ground_growth=False)
        assert 'Planet: '+expected_name in text or kind=='denied', 'planet display identity'
    if 'This planet has no governor! Hail to the new planetary governor!!'in text:
        owner=2;ground=get(after,record,77)
        assert 0<=ground<=get(before,record,77), 'adoption unrest bound'
        assert f'ground forces have been reduced to {int(ground)} from {int(get(before,record,77))}!'in text, 'adoption unrest receipt'
        fields.add((record,73))
    if kind=='denied':
        assert 'Permission to land is DENIED!'in text and 'Do you wish to try to force a landing?'in text and 'Forces engaging!'not in text, 'guarded landing denial'
    elif kind=='rename-refused':assert "You can't re-name this planet!"in text, 'reserved rename refusal'
    elif kind=='bank':
        bank=case['bank_target'];deposit=bank-get(before,record,117)
        assert get(after,2,81)==get(before,2,81)-deposit, 'bank transfer conservation';fields.add((2,81))
    elif kind=='transfer':
        quantity=123
        assert get(after,2,61)==get(before,2,61)-quantity and get(after,record,129)>=get(before,record,129)+quantity, 'fighter transfer conservation';fields.add((2,61))
    if 'destination'in case:
        assert 'Moving planets costs 10 turns per sector.'in text, 'thruster cost notice'
        path=shortest_path(before,ship_sector,case['destination']);assert path and len(path)>1, 'transport route'
        hops=len(path)-1
        assert f'Distance is {hops} and will take {10*hops} turns.'in text, 'transport route quote'
        if kind=='insufficient':
            assert turns<10*hops and 'Not enough turns left to move the planet that far!'in text and 'Planet thrusters engaged.'not in text, 'transport turn admission'
        elif kind=='cancel':
            assert 'Move the planet? (Y/[N])'in text and 'Planet thrusters engaged.'not in text, 'transport cancellation'
        elif kind=='collision':
            assert 'There is already a planet in that sector!'in text and 'EXPLODED!'in text, 'occupied planned destination collision'
            assert get(after,record,85)==0 and after[(record-1)*137:(record-1)*137+41]==bytes(4)+b' '*37, 'collision Wanderer deletion'
            loss=get(before,2,61)-get(after,2,61)
            assert loss==int(loss)and 0<=loss<=get(before,2,61)and(loss>=1 if get(before,2,61)else loss==0), 'collision fighter bounds'
            assert(f'You lost {int(loss)} fighters in the explosion!'in text)==bool(get(before,2,61)), 'collision fighter receipt'
            expected_links.discard(ship_sector);fields|={(record,85),(2,61)};names.add(record)
        else:
            assert turns>=10*hops and 'Planet thrusters engaged.'in text and 'The Wanderer vanishes from your sensors!'in text, 'Wanderer transport notices'
            turns-=10;ship_sector=path[1]
            assert len(after_links)==1, 'single transported Wanderer link';candidate=next(iter(after_links))
            assert get(before,51+candidate,93)==0 or candidate==int(get(before,2,57)), 'transport candidate planet admission'
            expected_links={candidate}
            if candidate not in path:
                assert not re.search(r'(?<![0-9])'+str(candidate)+r'(?![0-9])',text), 'hidden transport destination'
            assert get(after,record,85)==get(before,record,85), 'transport activity preservation'
            assert 'Test Planet moved!'not in text and expected_name+' moved!'not in text, 'no ordinary transport completion'
            if case.get('all_mines'):assert get(before,51+candidate,129)==3, 'planet mine candidate admission'
            if case.get('all_fighters'):assert get(before,51+candidate,81)==100 and get(before,51+candidate,85)==3, 'planet fighter candidate admission'
            if kind=='planned-mines':
                assert get(after,51+ship_sector,129)==0, 'planned arrival mines consumed'
                shield=get(before,2,53);remaining=int(get(before,51+ship_sector,129))
                bursts=re.findall(r'There are (\d+) mines here! (\d+) EXPLODE!',text);shield_rows=re.findall(r'Shields down to (\d+) units!',text)
                assert bursts and len(bursts)==len(shield_rows), 'planned mine trace'
                for (stock,burst),next_shield in zip(bursts,shield_rows):
                    stock,burst,next_shield=int(stock),int(burst),int(next_shield)
                    assert stock==remaining and 1<=burst<=remaining and max(0,shield-1000*burst)<=next_shield<=shield, 'planned mine damage bound'
                    remaining-=burst;shield=next_shield
                assert remaining==0 and get(after,2,53)==shield, 'planned mine settlement'
                fields|={(51+ship_sector,129),(2,53)}
            if kind=='planned-fighters':assert 'You have to defeat the fighters before you can enter this sector.'in text, 'planned fighter encounter'
        assert get(after,2,125)==get(before,2,125), 'transport cloak preservation'
    assert get(after,record,73)==owner and get(after,record,77)==ground, 'game governor/ground preservation'
    assert get(after,record,117)==bank, 'game bank preservation'
    assert get(after,2,49)==turns and get(after,2,57)==ship_sector, 'game ship turn/location settlement'
    assert after_links==expected_links, 'game Wanderer link settlement'
    for sector in before_links|after_links:
        if get(before,51+sector,93)!=get(after,51+sector,93):fields.add((51+sector,93))
    if ship_sector!=get(before,2,57):fields|={(2,49),(2,57)}
    fields.add((record,117))
    if record not in names:assert planet_name(after)==expected_name, 'game planet name preservation'
    for player in(2,3):assert rawfield(after,player,109)==enc(public_score(after,player)), 'public score arithmetic'
    assert_unchanged_except(before,after,fields,names)


def shortest_path(data,start,target):
    queue=[(start,[start])];seen={start}
    for current,path in queue:
        if current==target:return path
        for offset in range(41,65,4):
            sector=int(get(data,51+current,offset))
            if sector and sector not in seen:
                assert 1<=sector<=3000, 'warp bounds'
                seen.add(sector);queue.append((sector,path+[sector]))
    return None


def verify_aux(case,before,after,text,initial,final):
    from datetime import datetime
    assert set(initial)==set(final), 'auxiliary file set'
    mode=case['mode'];day=datetime.strptime(case['date'],'%m/%d/%Y').timetuple().tm_yday
    if mode=='game':
        allowed={'YTNEWS.DAT','YTSCORE.ASC'}
        prefix=initial['YTNEWS.DAT'].rstrip(b'\x1a');news=final['YTNEWS.DAT']
        assert news.startswith(prefix), 'public news prefix preservation'
        tail=news[len(prefix):].decode('cp437')
        match=re.match(r'-=\*=- ([0-9]{2}:[0-9]{2}:[0-9]{2}) Q  Logged on -=\*=-\r\n',tail)
        assert match, 'public login news'
        h,m,s=map(int,match[1].split(':'));actual=3600*h+60*m+s
        h,m,s=map(int,case['time'].split(':'));assert 0<=actual-(3600*h+60*m+s)<=30, 'public login clock'
        expected=''
        if case['expect']=='collision':
            expected+=f' *** Planet {planet_name(before)} EXPLODED while being moved by Q !!!\r\n'
            loss=int(get(before,2,61)-get(after,2,61))
            if get(before,2,61):expected+=f'Q  lost {loss} fighters in the explosion!\r\n'
        if case['expect']=='planned-mines':expected+=f'Q  hit sector mines in sector {int(get(after,2,57))}!\r\nShields reduced to {int(get(after,2,53))} units!\r\n'
        assert tail[match.end():]==expected+'\x1a', 'exact public game event settlement'
    elif mode in {'maintenance','initializer'}:
        allowed={'YTNEWS.DAT','YTYNEWS.DAT','YTSCORE.ASC'}
        if mode=='initializer':allowed.add('YTNAME.DAT')
        else:assert final['YTYNEWS.DAT']==initial['YTNEWS.DAT'], 'maintenance newspaper rotation'
        news=final['YTNEWS.DAT'].decode('cp437')
        regenerated=mode=='initializer'or not links(before)
        for line in ['  -  The Wanderer is missing or has been destroyed!\r\n','  -  The Wanderer regenerated with P.H.O.E.N.I.X. device!\r\n']:
            assert news.count(line)==int(regenerated), 'public regeneration event'
        assert 'successfully warped'not in news and 'vanishes from your sensors'not in news, 'private transport notice separation'
    else:
        assert mode=='reset', 'auxiliary mode'
        allowed={'YTNEWS.DAT','YTYNEWS.DAT','YTNAME.DAT','YTRMSG.DAT'}
        assert final['YTSCORE.ASC']==initial['YTSCORE.ASC'], 'reset preserves old scoreboard'
        assert b'P.H.O.E.N.I.X.'not in final['YTNEWS.DAT'], 'reset has no regeneration event'
    for name,data in initial.items():
        if name not in allowed:assert final[name]==data, ('unrelated auxiliary effect',case['name'],name)
    if mode in {'game','maintenance','initializer'}:
        for player in(2,3):
            if get(after,player,85)<=0:continue
            alias='Q'if player==2 else'Enemy';score=final['YTSCORE.ASC'].decode('cp437')
            match=re.search(r'^ *\d+ +[0-9.]+% +([0-9,]+) +(None|1) +(\d+) +'+alias+r' *\r?$',score,re.M)
            assert match and int(match[1].replace(',',''))==int(public_score(after,player)), 'public scoreboard points'
            assert int(match[3])==get(after,player,117), 'public scoreboard ports'
    assert auxiliary_witness(final)==AUX_SHA[case['name']], 'frozen complete auxiliary witness'


def verify_diagnostics(root,worlds,auxiliaries):
    """Incomplete/phase-interference evidence never counts as isolated success."""
    paths={
        'no-vacancy':('exploratory/no-vacancy/maint-no-vacancy','exploratory/no-vacancy/recipe.json'),
        'later-npc-interference':('exploratory/later-npc-interference/transport-maintenance','exploratory/later-npc-interference/source-recipe.json'),
    }
    baseline=(SOURCE/'YTDATA.DAT').read_bytes()
    for label,(relative,recipe_path)in paths.items():
        d=root/relative;case=read(d/'result.json');recipe_bytes=(root/recipe_path).read_bytes()
        assert sha(recipe_bytes)==DIAGNOSTIC_SHA[label]['recipe'], 'frozen diagnostic declarations'
        recipe=json.loads(recipe_bytes);decl=next(c for c in recipe['scenarios']if c['name']==case['name'])
        assert all(case[k]==value for k,value in decl.items()), 'diagnostic declaration mismatch'
        metadata='result.json'if(d/'result.json').exists()else'result.json.gz'
        assert {p.name for p in d.iterdir()}==KEEP|{metadata}and set(case['files'])==KEEP, 'diagnostic retained files'
        assert case['recipe']==RECIPE and case['baseline_sha256']==BASE_SHA and case['binaries']==BINS, 'diagnostic source identity'
        for file,digest in case['files'].items():assert sha((d/file).read_bytes())==digest, 'diagnostic file hash'
        verify_clock(d,case)
        assert(d/'KEYS.TXT').read_bytes()==b'~~~~\r', 'diagnostic exact input'
        before,after=zipped(d/'before.dat.gz'),zipped(d/'after.dat.gz')
        assert len(before)==len(after)==568687, 'diagnostic world size'
        if label=='no-vacancy':
            assert case==read(d.parent/'results.json')['scenarios'][0], 'diagnostic manifest mismatch'
            assert zipped(d.parent/'baseline.dat.gz')==baseline, 'diagnostic baseline identity'
            expected=bytearray(baseline)
            for name,record in [('Mercenary Base',4150),('Xannoron',4151)]:expected[(record-1)*137:(record-1)*137+41]=name.encode().ljust(41,b' ')
            patches=recipe['common_patches']+[[51+s,93,2]for s in range(1,3001)]+[[151,93,1],[1165,93,100],[2051,93,99]]+decl['patches']
            initial={p.name:p.read_bytes()for p in SOURCE.iterdir()if p.suffix.upper()in('.DAT','.ASC','.DEF','.TMP')and p.name!='YTDATA.DAT'}
        else:
            assert case['parent']=='transport-owned', 'diagnostic exact parent'
            expected=bytearray(worlds[case['parent']]);patches=decl['patches'];initial=auxiliaries[case['parent']]
        assert case['applied_patches']==patches, 'diagnostic declared patches'
        for record,offset,value in patches:put(expected,record,offset,value)
        assert before==expected, 'diagnostic before-world reconstruction'
        assert {n:bytes.fromhex(value)for n,value in side(d/'side-before.json.gz').items()}==initial, 'diagnostic auxiliary input chain'
        auxiliary=side(d/'sidefiles.json.gz');final={n:bytes.fromhex(row['hex'])for n,row in auxiliary.items()}
        assert all(row['after_sha256']==sha(final[n])and row['before_sha256']==(sha(initial[n])if n in initial else None)for n,row in auxiliary.items()), 'diagnostic auxiliary identity'
        text=(d/'transcript.txt').read_text()
        assert zipped(d/'game.log.gz').decode('cp437').replace('\r\n','\n')==text, 'diagnostic raw transcript identity'
        if label=='no-vacancy':
            assert case['timed_out']and not case['program_returned']and not case['complete']and case['timeout_seconds']==8 and(d/'RETURN.LOG').read_bytes()==b'', 'bounded diagnostic timeout/nonreturn'
            assert not links(before)and not links(after)and all(get(before,51+s,93)>0 for s in range(1,3001)), 'no-vacancy diagnostic setup/outcome'
            assert text.count('Wanderer has successfully warped!')>1 and 'Daily Maintenance Completed OK'not in text, 'optimistic timeout notice/noncompletion'
            assert get(after,4052,85)==12 and get(after,4052,117)==250000, 'partial regeneration before search'
        else:
            assert not case['timed_out']and case['program_returned']and case['complete']and(d/'RETURN.LOG').read_bytes()==b'WANDERER_PROGRAM_RETURNED\r\n', 'interference normal return'
            notices=['Wanderer has successfully warped!','attacked the planet "The Wanderer"','Planet "The Wanderer" destroyed!']
            assert all(n in text for n in notices)and text.index(notices[0])<text.index(notices[1])<text.index(notices[2]), 'later NPC destruction phase order'
            assert not links(after)and get(after,4052,85)==0, 'later NPC destruction outcome'
        witness=DIAGNOSTIC_SHA[label]
        assert sha(after)==witness['world']and auxiliary_witness(final)==witness['aux']and sha(text.encode())==witness['transcript'], 'frozen complete diagnostic witness'


def verify(root):
    assert RECIPE_SHA and WORLD_SHA and AUX_SHA, 'unfrozen Wanderer capture declarations'
    directory=root/'dos';baseline=(SOURCE/'YTDATA.DAT').read_bytes()
    assert sha(baseline)==BASE_SHA and zipped(directory/'baseline.dat.gz')==baseline, 'baseline identity'
    recipe_bytes=(directory/'recipe.json').read_bytes()
    assert sha(recipe_bytes)==RECIPE_SHA, 'frozen declarations'
    recipe=json.loads(recipe_bytes);manifest=read(directory/'results.json')
    assert recipe['recipe']==manifest['recipe']==RECIPE, 'recipe identity'
    declarations={c['name']:c for c in recipe['scenarios']};rows=manifest['scenarios']
    assert len(declarations)==len(rows)==len(WORLD_SHA), 'scenario count'
    assert len({r['name']for r in rows})==len(rows)and set(declarations)==set(WORLD_SHA)==set(AUX_SHA)=={r['name']for r in rows}, 'scenario identity'
    binaries={n:(ROOT/'archive/dos-original'/n).read_bytes()for n in BINS if n!='KEYFEED.COM'}
    binaries['KEYFEED.COM']=(ROOT/'archive/analysis/yt-combat/KEYFEED.COM').read_bytes()
    assert {n:sha(b)for n,b in binaries.items()}==BINS, 'archived binary identity'
    worlds={};auxiliaries={}
    for case in rows:
        name=case['name'];assert re.fullmatch(r'[a-z0-9-]+',name), 'scenario path'
        d=directory/name;decl=declarations[name]
        assert case==read(d/'result.json')and all(case[k]==v for k,v in decl.items()), 'manifest/declaration mismatch'
        assert case['recipe']==RECIPE and case['baseline_sha256']==BASE_SHA, 'session identity'
        assert case['complete']and case['program_returned']and not case['timed_out']and case['timeout_seconds']==case.get('timeout',120), 'incomplete DOS control'
        assert case['binaries']==BINS, 'binary identity'
        metadata='result.json'if(d/'result.json').exists()else'result.json.gz'
        assert set(case['files'])==KEEP and {p.name for p in d.iterdir()}==KEEP|{metadata}, 'retained file set'
        for file,digest in case['files'].items():assert sha((d/file).read_bytes())==digest, ('file hash',name,file)
        verify_clock(d,case)
        assert (d/'RETURN.LOG').read_bytes()==b'WANDERER_PROGRAM_RETURNED\r\n', 'DOS return marker'
        before,after=zipped(d/'before.dat.gz'),zipped(d/'after.dat.gz')
        assert len(before)==len(after)==568687, 'world size'
        if case.get('parent'):
            assert case['parent']in worlds, 'parent ordering'
            expected=bytearray(worlds[case['parent']]);initial=auxiliaries[case['parent']];patches=decl['patches']
        else:
            expected=bytearray(baseline)
            initial={p.name:p.read_bytes()for p in SOURCE.iterdir()if p.suffix.upper()in('.DAT','.ASC','.DEF','.TMP')and p.name!='YTDATA.DAT'}
            for label,record in [('Mercenary Base',4150),('Xannoron',4151)]:expected[(record-1)*137:(record-1)*137+41]=label.encode().ljust(41,b' ')
            patches=list(recipe['common_patches'])
            if decl.get('fill_planets'):patches +=[(51+s,93,2)for s in range(1,3001)]+[(151,93,1),(1165,93,100),(2051,93,99)]
            if decl.get('all_mines'):patches +=[(51+s,129,3)for s in range(1,3001)if s not in(1,100,101)]
            if decl.get('all_fighters'):patches +=[(51+s,o,v)for s in range(1,3001)if s not in(1,100,101)for o,v in((81,100),(85,3))]
            patches+=decl['patches']
        assert case['applied_patches']==[list(p)for p in patches], 'declared patch list'
        for record,offset,value in patches:put(expected,record,offset,value)
        if decl.get('name_patch'):expected[4051*137:4051*137+41]=decl['name_patch'].encode().ljust(41,b' ')
        assert before==expected, 'undeclared setup or broken world chain'
        assert {n:bytes.fromhex(v)for n,v in side(d/'side-before.json.gz').items()}==initial, 'auxiliary input chain'
        auxiliary=side(d/'sidefiles.json.gz');final={n:bytes.fromhex(v['hex'])for n,v in auxiliary.items()}
        assert all(v['after_sha256']==sha(final[n])and v['before_sha256']==(sha(initial[n])if n in initial else None)for n,v in auxiliary.items()), 'auxiliary identity'
        if decl['mode']=='game':keys=('\r~~~~~\r~'+decl['command']+'\r~~~~'+'Q;Y\r~~~~'*12).encode()
        elif decl['mode']=='initializer':keys=b'Y\r\n\r\n'
        elif decl['mode']=='reset':keys=('~~~~Y\r'+'~~\r'*12).encode()
        else:assert decl['mode']=='maintenance', 'capture mode';keys=b'~~~~\r'
        assert (d/'KEYS.TXT').read_bytes()==keys, 'exact input stream'
        text=(d/'transcript.txt').read_text()
        assert zipped(d/'game.log.gz').decode('cp437').replace('\r\n','\n')==text, 'raw transcript identity'
        verify_semantics(case,before,after,text)
        verify_aux(case,before,after,text,initial,final)
        assert sha(after)==WORLD_SHA[name], 'frozen complete world witness'
        worlds[name],auxiliaries[name]=after,final
    verify_diagnostics(root,worlds,auxiliaries)
    reads=verify_native(root)
    print(f'Verified {len(rows)} normally returned Wanderer controls, exact world/auxiliary chains, bounded semantics,2 separate diagnostics and {reads} native byte observations.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--research',type=Path,default=ROOT/'research/yt-wanderer')
    verify(parser.parse_args().research)
