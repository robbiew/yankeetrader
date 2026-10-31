"""Independently verify isolated DOS planetary movement and forced-landing evidence."""
import argparse
import gzip
import hashlib
import json
import math
import re
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'archive/analysis/yt-combat/experiments/fixture-planet-transfer'
RECIPE = 'planet-mobility-v1'
BASE_SHA = '2a63d12af095a59227840946be57fd4b7e4dafb5724d4019de694da7c4194b19'
# Final declarations and witnesses are frozen only after returned controls have
# been independently inspected. Unfrozen research must fail rather than self-pass.
RECIPE_SHA = 'f58b289354f0727c07492dd3977e5fc26f0a606f47972b98dfad75e306efc740'
WORLD_SHA = {'control-owned': 'faad3b0cd918fc12d3fbc897b9be5d0978675fb2c042eac5d7165465c0a04d32',
 'move-one': 'f4d32e259d8f3b966526c5897a70512a922076859e5b25ba3ac26de0d9978412',
 'move-two': 'efdee8d70676901ef7162197c6d43f81fff33d35e0434e7550e1a11594c18719',
 'move-four': '9c3846138c6dc9701cf2507694533e67efa352ea1c6aa51fe1a6fff7d2193b04',
 'move-cancel': '0b00ab9d23fe00ec0a592f500ad6878f6e1fc221f834f6c678b30abb2468986c',
 'move-blank': '923c32dd2d0f30f32bb5907254b92819469000badd89d091ea23bbfe93e92a4b',
 'move-current': '0b00ab9d23fe00ec0a592f500ad6878f6e1fc221f834f6c678b30abb2468986c',
 'move-zero': 'd1350d9fb35ada217ad5a4da5409a39235ecb8606c4a7358f409caaa8a63333a',
 'move-negative': 'f0dd4d5dad81014b2d1a18bf390f3475fa7692eac00b72d300ff2b8852564e4f',
 'move-outside': '584bcb27e6192b77ebc078dee845bd0b7839fdb672f43322146370b7c2d6398e',
 'move-unreachable': '584bcb27e6192b77ebc078dee845bd0b7839fdb672f43322146370b7c2d6398e',
 'turns-one-below': '98652fbb158e8c57c963c3e700e69225473d5000ad33c35fcb14a5b2d8ec7657',
 'turns-one-exact': 'db3cc4da8d627420c0e92c9fc67fa5ab0e505995a14bf8a4e643680d5502a826',
 'turns-two-below': '62bbb0a7bd5e62cc2f7cb62e17b5da747b052356dbed6dae0be218533e051908',
 'turns-two-exact': 'd7e1047c5aa6362f28c2c25fbc4f714982c66a687e95b8d832b1b049f68be55c',
 'turns-two-above': '47294080b1c3a14271eccc686cbed95e1dcaaef166d26cac46ee02c6bde739e2',
 'collision-first': '5e01010522148e9f9c836d7fd98210e1cba374ac84de06549d2b2e971c3ee8f6',
 'collision-later': 'a0106b6b97bc43f6b7b63d8c0f9c4e82d7933214885c02eb31eb87c89236d82b',
 'collision-one-fighter': '41bbd55abbad3f22948ab3d460aabb1c193ba18761f1c5155c970b749c76482f',
 'collision-zero-fighters': '44a7d999d62fc51c611afda0948227ae1a29b80858e82e3c0080e9f00909318b',
 'move-unguarded': 'dea7f40824db20360f496a29f250eea71031f006d54e0793d7112718768bf435',
 'move-teammate': 'f44ca3e3ea750bc3cd95bf1dd4ee2dad96e7ebb7c6ab9906b2047099c92e13b1',
 'move-neutral': '02c43590a4307232dd516655e00b00e51ca598719e24eeecd0b75e50ba2e7cd0',
 'move-captured-xannoron': '061963e56566c62211877fa849bad1286196e3358458c09973cfbacb81bdee7a',
 'move-wanderer': 'f9ca8862af30c7dc685fb708b38c398f9a4c28b4a59acb81ea364fa529707fee',
 'move-mines': '0d8be8c62213aa6ac2e06831e873e955153c882b75060d9eb953c4bad0ee2bd0',
 'move-hostile-fighters': '39cc9df2960f7843a8cd005cf24221f1cd3624c0bb8ccffaad4ce0c0b57b5b76',
 'move-own-fighters': 'ebb9f3b9407878b6e3028e22dedad7a2bbdf7eacde808f2df904b1eaaefb6937',
 'move-later-hostile': 'dec1afdc502845d019beb73786a0a303578b8d0ff9156188565db9180dc9548d',
 'move-anomaly-first': '7f9e7544741dfba6acfdaf9ee953ac5f4b707f9b41cfdc006016a6b97a1a38a0',
 'move-anomaly-later': 'daa77bc1532c9d73ea6d71778611ac178649fa57ed007544ef2eb672f474590e',
 'move-earth': '82566391f5e62f9a881adb3d8ee217d57847af2e6ce974023f09d0de1da6405f',
 'move-cloak-boundary': 'd80bd45e33074ed967bf086cfba59c992a736d8a33d774be8c0259083a13aea4',
 'force-decline': '9d5effae545187b35c098a166380c99c9d82e45675f63f46d7b475a5b993fdcc',
 'force-blank': '19f852bcdd479eaae5828dc3d951df634392becea79b388ad859b74d49b66ef2',
 'force-no-troops': 'e65503cb9ee6177efa27c674fa7c7bf634292dbf816d53a9d9a07b41cf38de1b',
 'force-zero': '5b4bac02318bb42a16aac2bba0951957bf0be7a08da2696eeba3c88a6cfe9308',
 'force-negative': '78ed916b5dca871fa1ee7431fa9ed897fe3fd62d609b673aeb2d834fb3ba488c',
 'force-over': '2b1769332299166221d35780961972f9aa07567316792e175ae7a72174ed1b23',
 'force-invalid': '2b1769332299166221d35780961972f9aa07567316792e175ae7a72174ed1b23',
 'force-full': 'd27a8f0bb2541d24a0ea4ab53e4c8eef61287042999bb4bb48d7a706d711316b',
 'force-partial': 'af29985426fef1ea10e1ab3edcbda675e7eaa1d8663f349ec85114601de07906',
 'force-loss': '0bc02ac0dd75da1b8fe65488ce0a34ec1e7346c8be1506f34f7d5d07fd223b7b',
 'force-one': '74a209301ce0769641e52afb9806c6c09303b002c1a72640e8313abdf621b8d9',
 'force-fraction': 'e88a72328c69e83a7ac5e5819e79fa110f2ab27d89338806e528232954e0b3a0',
 'land-fractional-defender': 'd171356536075447b003537844ec7ba74f7e06ac176cbe4d00f50c14adc6641d',
 'land-unguarded': 'd171356536075447b003537844ec7ba74f7e06ac176cbe4d00f50c14adc6641d',
 'land-neutral-defended': '17c10aae0cab0aca0ca40c33936faf9de87db38adbb32f7d69ebbd64fd2bb995',
 'land-teammate': 'f24c422e390b3b9bd9382b80c135426343c1ca584fedfb0f4b6bc99ffd108cbd',
 'land-dead-governor': '64af5be239181a7859ff2ac971f9e61aa88db7f94b106269a5ace6771a922074',
 'force-mercenary': 'd27a8f0bb2541d24a0ea4ab53e4c8eef61287042999bb4bb48d7a706d711316b',
 'force-xannor': 'd27a8f0bb2541d24a0ea4ab53e4c8eef61287042999bb4bb48d7a706d711316b',
 'force-no-ship-defenses': '4dc0567c00195de9a5c86d225691015a3b31760846ff332c601435d191fb9bc6',
 'captured-reentry': 'e004572da3e06be7ac566e62a124223c02d76da4b9e5bedecaa63f9531ffc7b2',
 'failed-retry': 'e5d6b23b51e6e7c8f3e73543de287566da2990e5feb74e439c325dceb4869ccd'}
AUX_SHA = {'control-owned': '0f8bf6ed4770fd3a61e9a3326712c591b0c8f07f56e202275969c843147a5259',
 'move-one': '8df760d4d730586a33e1030e8d4442e406bd3a91fbe43bdd2c9e6523aa9f62fd',
 'move-two': '8df760d4d730586a33e1030e8d4442e406bd3a91fbe43bdd2c9e6523aa9f62fd',
 'move-four': '8df760d4d730586a33e1030e8d4442e406bd3a91fbe43bdd2c9e6523aa9f62fd',
 'move-cancel': '8df760d4d730586a33e1030e8d4442e406bd3a91fbe43bdd2c9e6523aa9f62fd',
 'move-blank': '8df760d4d730586a33e1030e8d4442e406bd3a91fbe43bdd2c9e6523aa9f62fd',
 'move-current': '8df760d4d730586a33e1030e8d4442e406bd3a91fbe43bdd2c9e6523aa9f62fd',
 'move-zero': '8df760d4d730586a33e1030e8d4442e406bd3a91fbe43bdd2c9e6523aa9f62fd',
 'move-negative': '8df760d4d730586a33e1030e8d4442e406bd3a91fbe43bdd2c9e6523aa9f62fd',
 'move-outside': '76763c283a0f70c4818646727715c833c62e5eefd75b97a61a6c1415a03a12ce',
 'move-unreachable': '76763c283a0f70c4818646727715c833c62e5eefd75b97a61a6c1415a03a12ce',
 'turns-one-below': '8df760d4d730586a33e1030e8d4442e406bd3a91fbe43bdd2c9e6523aa9f62fd',
 'turns-one-exact': '8df760d4d730586a33e1030e8d4442e406bd3a91fbe43bdd2c9e6523aa9f62fd',
 'turns-two-below': '8df760d4d730586a33e1030e8d4442e406bd3a91fbe43bdd2c9e6523aa9f62fd',
 'turns-two-exact': '8df760d4d730586a33e1030e8d4442e406bd3a91fbe43bdd2c9e6523aa9f62fd',
 'turns-two-above': '8df760d4d730586a33e1030e8d4442e406bd3a91fbe43bdd2c9e6523aa9f62fd',
 'collision-first': 'a7f577bceb78ccedd5c72223910baf2b01c86ac0ce5cb00f56c697dc09d42318',
 'collision-later': '698a6165c0f13157205ecca44966067a230e67bd3a208ea75711993f03772d7f',
 'collision-one-fighter': 'feca6d659bcbe041cfe65fd021a6f63cd38b346ce17b8ac24854509428ea2dbc',
 'collision-zero-fighters': '3103c7c270013969eb86b97940da3325c21f10bc1b179c75f959c292b3ba229b',
 'move-unguarded': '8df760d4d730586a33e1030e8d4442e406bd3a91fbe43bdd2c9e6523aa9f62fd',
 'move-teammate': '2bca4dfe509b773399b4e778d2f972247ec00ce5cbe9d2e2b30aa55acfcde19b',
 'move-neutral': '8df760d4d730586a33e1030e8d4442e406bd3a91fbe43bdd2c9e6523aa9f62fd',
 'move-captured-xannoron': '8df760d4d730586a33e1030e8d4442e406bd3a91fbe43bdd2c9e6523aa9f62fd',
 'move-wanderer': '8df760d4d730586a33e1030e8d4442e406bd3a91fbe43bdd2c9e6523aa9f62fd',
 'move-mines': '144dbd97ac030fc13a8d8a5cc12e189736b4bc9d212b3a195c51158d3fbea765',
 'move-hostile-fighters': '809f79c89103aab146eb623db9a207eddf09bdee554b460c69c4e382a371018e',
 'move-own-fighters': '3e6b0658d320b86bc3d8183fe9f2b0918d70f2f4e5dc50bc60ff076a8ae3472c',
 'move-later-hostile': '809f79c89103aab146eb623db9a207eddf09bdee554b460c69c4e382a371018e',
 'move-anomaly-first': '8df760d4d730586a33e1030e8d4442e406bd3a91fbe43bdd2c9e6523aa9f62fd',
 'move-anomaly-later': '8df760d4d730586a33e1030e8d4442e406bd3a91fbe43bdd2c9e6523aa9f62fd',
 'move-earth': '8df760d4d730586a33e1030e8d4442e406bd3a91fbe43bdd2c9e6523aa9f62fd',
 'move-cloak-boundary': '8df760d4d730586a33e1030e8d4442e406bd3a91fbe43bdd2c9e6523aa9f62fd',
 'force-decline': 'b535ecc88e93c5423800eb34a9e8ea3399997d37934b90e82b5378677380d321',
 'force-blank': 'b535ecc88e93c5423800eb34a9e8ea3399997d37934b90e82b5378677380d321',
 'force-no-troops': '500f4a27c9f157c0ad68a66d2717734fc747a4e68f1c75119161dd8ed4bb1574',
 'force-zero': '8df760d4d730586a33e1030e8d4442e406bd3a91fbe43bdd2c9e6523aa9f62fd',
 'force-negative': '8df760d4d730586a33e1030e8d4442e406bd3a91fbe43bdd2c9e6523aa9f62fd',
 'force-over': '8df760d4d730586a33e1030e8d4442e406bd3a91fbe43bdd2c9e6523aa9f62fd',
 'force-invalid': '8df760d4d730586a33e1030e8d4442e406bd3a91fbe43bdd2c9e6523aa9f62fd',
 'force-full': '59c866d5f09b5f9ffebcdb7021f73b003025c50d0842b2d27e1c7839d14e6aa1',
 'force-partial': '36cdd062479dbcd2d18ccf0a63c7d520af18601abc78f55a5272980067fba3e0',
 'force-loss': '6ce024bc802212669a0cd87148d7676a75591bb5804511c7143e8abe75e9c301',
 'force-one': 'a46253a0ff9348e742f97d09d325b44aefd38d681f3d1046e781ce48b7527efa',
 'force-fraction': 'b43d4166aef739a1ea8124586fad5a1affb969bd70013740c4b2e9287348e73a',
 'land-fractional-defender': '0f8bf6ed4770fd3a61e9a3326712c591b0c8f07f56e202275969c843147a5259',
 'land-unguarded': '0f8bf6ed4770fd3a61e9a3326712c591b0c8f07f56e202275969c843147a5259',
 'land-neutral-defended': '0f8bf6ed4770fd3a61e9a3326712c591b0c8f07f56e202275969c843147a5259',
 'land-teammate': 'fecb81fa975ca575f74892207cb852346369490627ba0231556dda3a42b7589b',
 'land-dead-governor': 'f57d8bdff16def7cfd30d8f70d2a93f8ff86e96532d017afdba20786848fd879',
 'force-mercenary': '59c866d5f09b5f9ffebcdb7021f73b003025c50d0842b2d27e1c7839d14e6aa1',
 'force-xannor': '59c866d5f09b5f9ffebcdb7021f73b003025c50d0842b2d27e1c7839d14e6aa1',
 'force-no-ship-defenses': '19802046e90ec20b0729acbac373d14cc4d53a75e6fffc3b9a4221731938216e',
 'captured-reentry': 'd26f84434d0fadadaf3d469b63af2452c47177d4446d13662434d46bf6b6ce43',
 'failed-retry': '854624dc0a71142b89723c8be0b186e270287c41fce3d254c75c27984b33f4b6'}
NATIVE_RANGES = {'0x12fb4':980,'0x28b6f':192,'0x2b0df':264,'0x37f86':4,
 '0x13d14':380,'0x2809f':689,'0x274e2':1191,'0x13515':395,'0x32450':4,
 '0x3758e':4,'0x275e2':1191,'0x2b1e7':69,'0x2b45f':160,'0x37e7c':4,
 '0x28355':1012,'0x23efb':135,'0x20436':951,'0x10833':87,'0x1a41c':350}
KEEP = {'before.dat.gz', 'after.dat.gz', 'side-before.json.gz', 'sidefiles.json.gz',
        'transcript.txt', 'game.log.gz', 'DOSDATE.LOG', 'DOSTIME.LOG', 'RETURN.LOG',
        'KEYS.TXT', 'dosbox.log'}
BINS = {
 'YT.EXE':'c74093a488fdb44808f0a61908596fc04c4f3adbb1bbf63ccc9e1fc84296f037',
 'BRUN30.EXE':'3ce1a61e2184c96c8ab9dcd4cbb7e5a9121ac289a469364730f3de1c21db4fe8',
 'LOCAL.EXE':'bb970c43eb29fb80e7252f3968884f1c43543a5e39c6714b209ffca7dbf2d93a',
 'KEYFEED.COM':'06dd2b9fcb91502185f6f4a2123ad7fdac144f47f5170df203760b86db127596',
}


def sha(value):
    return hashlib.sha256(value).hexdigest()


def read(path):
    return json.loads(path.read_text())


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
    assert 1 <= record <= 4151 and offset in range(41, 134, 4), 'patch bounds'
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


def verify_native(root):
    assert NATIVE_RANGES, 'unfrozen native declarations'
    binary = (ROOT/'archive/dos-original/YT.EXE').read_bytes()
    assert sha(binary)==BINS['YT.EXE'], 'native binary identity'
    image, seen = loaded(binary), set()
    observations = read(root/'rea/yt.json')['records']
    assert len(observations) == len(NATIVE_RANGES)+1, 'native observation count'
    images=[e for e in observations if e['operation']=='inspect_native_load_image']
    assert len(images)==1, 'native load image count'
    verify_load_image(images[0],binary,image)
    for e in observations:
        if e['operation']=='inspect_native_load_image':
            continue
        value = e['normalized_result']
        address = value['address']
        assert address in NATIVE_RANGES and address not in seen, 'native address set'
        seen.add(address)
        count = NATIVE_RANGES[address]
        assert e['operation'] == 'read_bytes', 'native operation'
        assert e['subject']['digest']['sha256'] == sha(binary), 'native target identity'
        assert value['complete'] and value['requested_bytes'] == value['returned_bytes'] == count, 'incomplete native bytes'
        at = int(address, 16)-0x10000
        assert bytes.fromhex(value['bytes_hex']) == image[at:at+count], 'native bytes'
    assert seen == set(NATIVE_RANGES), 'native address set'



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


def verify_clock(directory, case):
    assert case['date'] == '10/24/2026' and re.search(r'Current date: Sat 10/24/2026(?:\r?\n|$)', (directory/'DOSDATE.LOG').read_text()), 'DOS date'
    assert case['time'] in {'00:00:00', '00:01:00'}, 'declared clock'
    m = re.search(r'Current time: (\d+):(\d+):(\d+)\.(\d+)(am|pm)', (directory/'DOSTIME.LOG').read_text())
    assert m, 'DOS clock'
    h, minute, second, frac, ampm = m.groups()
    actual = (int(h) % 12+(12 if ampm == 'pm' else 0))*3600+int(minute)*60+int(second)+int(frac)/10**len(frac)
    h,m,sec=map(int,case['time'].split(':'))
    assert abs(actual-(3600*h+60*m+sec)) <= .06, 'DOS clock mismatch'



def public_score(data, player):
    """Public native ship score; planetary bank/production are not ship assets."""
    terms=((53,50),(61,100),(65,2500),(69,20),(73,30),(77,40),(81,1),
           (97,1000),(113,1000000),(117,50000),(121,750),(129,2500))
    if get(data,player,45)!=0:
        return 0
    total=sum(get(data,player,offset)*weight for offset,weight in terms)
    total+=sum(get(data,51+sector,81)*100 for sector in range(1,3001) if get(data,51+sector,85)==player)
    # These controls never install the scanner (its flag contributes 250000).
    if get(data,player,93)>0:
        total+=250000
    return total


def shortest_path(data, start, target):
    if not 1<=target<=3000:
        return None
    pending=[(start,[start])];seen={start}
    for current,path in pending:
        if current==target:
            return path
        for offset in range(41,65,4):
            destination=int(get(data,51+current,offset))
            if destination and destination not in seen:
                assert 1<=destination<=3000, 'route graph bounds'
                seen.add(destination);pending.append((destination,path+[destination]))
    return None


def verify_ground_trace(before, after, record, committed, text):
    """Check every observed exchange without inventing the original RNG stream."""
    a,d=int(committed),int(get(before,record,77))
    assert 'Forces engaging!' in text, 'ground engagement notice'
    assert get(after,2,121)==get(before,2,121)-a, 'committed ground debit'
    matches=list(re.finditer(r'(Your forces remaining|Ground forces remaining) *: *([0-9,]+)!',text))
    for m in matches:
        assert a>0 and d>0, 'ground trace after termination'
        value=int(m.group(2).replace(',',''))
        if m.group(1).startswith('Your'):
            assert max(0,a-d)<=value<=a, 'attacker casualty bound'
            a=value
        else:
            assert max(0,d-a)<=value<=d, 'defender casualty bound'
            d=value
    assert a==0 or d==0, 'unterminated ground trace'
    if d==0 and a>0:
        assert "You've captured the planet!" in text and 'Planetary defenses destroyed!' in text, 'capture notice'
        assert get(after,record,73)==2 and get(after,record,77)==a, 'captured ownership/garrison'
    else:
        assert a==0 and "You've captured the planet!" not in text, 'failed assault capture'
        assert get(after,record,73)==get(before,record,73) and get(after,record,77)==d, 'failed assault preservation'
        assert f'Attack Failed! Ground Forces remaining: {d}!' in text, 'failed assault notice'
    return a,d


def verify_lazy_growth(case,before,after,record):
    """Bound observed elapsed production, not bit-exact QuickBASIC arithmetic."""
    assert get(after,record,41)==297, 'planet production day'
    minutes=get(after,record,89)
    h,m,sec=map(int,case['time'].split(':'));start=60*h+m+sec/60
    assert max(start,get(before,record,89))<=minutes<=start+3, 'planet production clock'
    elapsed=max(0,minutes-get(before,record,89))/1440
    for offset in (45,49,53):
        old,new=get(before,record,offset),get(after,record,offset)
        assert old<=new<=old*(1+elapsed)+.0001, 'planet production growth bound'
    for stock,rate in ((57,45),(61,49),(65,53),(129,53)):
        old,new=get(before,record,stock),get(after,record,stock)
        factor=10 if stock==129 else 1
        assert old<=new<=old+max(get(after,record,rate)*factor,1)*elapsed+1, 'planet stock growth bound'
    assert get(after,record,117)==get(before,record,117), 'planet bank preservation'
    for offset in (69,113,125):
        old,new=get(before,record,offset),get(after,record,offset)
        assert old<=new<=old+max(old,1)*elapsed+.0001, 'planet weapon preservation'


def assert_unchanged_except(before,after,fields=(),names=()):
    masked=bytearray(after)
    for record,offset in fields:
        at=(record-1)*137+offset;masked[at:at+4]=before[at:at+4]
    for record in names:
        at=(record-1)*137;masked[at:at+41]=before[at:at+41]
    assert masked==before, 'unrelated world mutation'


def verify_semantics(case, before, after, text):
    name,kind=case['name'],case['expect']
    slot=int(case.get('source_slot',2));record=4051+slot
    source=int(get(before,2,57));expected_sector=source;spent=0
    assert '<Land/Create planet>' in text, 'landing entry notice'
    assert '<Take all>' not in text, 'unrelated default withdrawal'
    verify_lazy_growth(case,before,after,record)
    fields={(2,109),(3,109)} | {(record,o)for o in(41,45,49,53,57,61,65,69,89,113,117,125,129)}
    names=set()
    pointers={s:int(get(before,51+s,93))for s in range(1,3001)}
    expected_pointers=dict(pointers)
    expected_owner=get(before,record,73);expected_ground=int(get(before,record,77))
    expected_ship_ground=get(before,2,121)
    if get(before,record,77)==0:
        fields.add((record,77))  # DOS normalizes otherwise noncanonical MBF zero bytes.
    if get(before,2,89)==1 and get(before,3,89)==1:
        assert get(after,52,77)==2, 'team member recount'
        fields.add((52,77))
    if 'destination' in case:
        destination=case['destination'];path=shortest_path(before,source,destination)
        assert 'Moving planets costs 10 turns per sector.' in text, 'thruster cost notice'
        assert f'Move planet to what sector? {destination}' in text, 'thruster destination input'
        if kind=='invalid-route':
            assert 'Move the planet? (Y/[N])' not in text and 'Planet thrusters engaged.' not in text, 'invalid route confirmation'
            if destination==source:assert 'Hey, look out the window dummy!' in text, 'current-sector refusal'
            elif not 1<=destination<=3000:assert 'Valid sector numbers are from 1 to 3000!' in text, 'sector bounds refusal'
            else:assert path is None and "You can't get there" in text, 'unreachable route refusal'
        else:
            assert path and len(path)-1==case['hops'], 'shortest route length'
            assert f"Distance is {case['hops']} and will take {case['hops']*10} turns." in text, 'route quote'
            if kind=='insufficient':
                assert get(before,2,49)<10*case['hops'] and 'Not enough turns left to move the planet that far!' in text and 'Move the planet? (Y/[N])'not in text, 'turn admission refusal'
            else:
                assert get(before,2,49)>=10*case['hops'] and 'Move the planet? (Y/[N])' in text, 'turn admission/confirmation'
                if kind=='cancel':
                    assert 'Planet thrusters engaged.' not in text, 'cancelled thrusters'
                else:
                    assert 'Planet thrusters engaged.' in text, 'thruster engagement'
                    if kind=='reserved-home':
                        assert slot==100 and "We don't want no trouble from no Xannor" in text, 'reserved-home refusal'
                    elif kind=='collision':
                        collision=case['collision_sector'];index=path.index(collision);hops=index-1
                        expected_sector=path[hops];spent=10*hops
                        expected_pointers[source]=0
                        assert 'There is already a planet in that sector!' in text and 'PLANET Test Planet EXPLODED!' in text, 'collision destruction notice'
                        assert get(after,record,85)==0 and after[(record-1)*137:(record-1)*137+41]==bytes(4)+b' '*37, 'moving planet deletion'
                        target=pointers[collision];assert target>0 and target!=slot, 'collision target setup'
                        assert after[(4050+target)*137:(4051+target)*137]==before[(4050+target)*137:(4051+target)*137], 'collision target preservation'
                        old_fighters=get(before,2,61);loss=old_fighters-get(after,2,61)
                        assert loss==int(loss) and 0<=loss<=old_fighters and (loss>=1 if old_fighters else loss==0), 'explosion fighter bounds'
                        assert (f'You lost {int(loss)} fighters in the explosion!' in text)==bool(old_fighters), 'explosion loss receipt'
                        fields|={(record,85),(2,61)};names.add(record)
                    elif kind=='wanderer':
                        assert slot==1 and 'The Wanderer vanishes from your sensors!' in text, 'Wanderer stop notice'
                        expected_sector=path[1];spent=10;expected_pointers[source]=0
                        links=[s for s in range(1,3001)if get(after,51+s,93)==slot]
                        assert len(links)==1 and links[0]!=expected_sector and pointers[links[0]]==0, 'Wanderer separate relocation'
                        expected_pointers[links[0]]=slot
                    else:
                        assert kind in {'route','anomaly'}, 'unknown route outcome'
                        stop={'move-mines':101,'move-hostile-fighters':101,'move-later-hostile':102}.get(name,destination)
                        expected_sector=stop;spent=10*path.index(stop)
                        expected_pointers[source]=0;expected_pointers[stop]=slot
                        assert get(after,record,85)==get(before,record,85), 'moved planet activity'
                        if stop==destination:
                            assert 'Test Planet moved! (Xannoron Movers, we move anyTHING, anyWHERE!)' in text, 'move completion notice'
                        else:
                            assert 'Test Planet moved!' not in text, 'early-stop completion receipt'
                        if name=='move-mines':
                            assert get(after,51+stop,129)==0, 'arrival mines consumed'
                            remaining=int(get(before,51+stop,129));shield=get(before,2,53)
                            bursts=[(int(a),int(b))for a,b in re.findall(r'There are (\d+) mines here! (\d+) EXPLODE!',text)]
                            shields=[int(s)for s in re.findall(r'Shields down to (\d+) units!',text)]
                            assert bursts and len(bursts)==len(shields), 'mine burst trace'
                            for (stock,burst),next_shield in zip(bursts,shields):
                                assert stock==remaining and 1<=burst<=remaining, 'mine burst conservation'
                                assert max(0,shield-1000*burst)<=next_shield<=shield, 'mine shield damage bound'
                                remaining-=burst;shield=next_shield
                            assert remaining==0 and get(after,2,53)==shield, 'mine aftermath settlement'
                            fields|={(51+stop,129),(2,53)}
                        if name in {'move-hostile-fighters','move-later-hostile'}:
                            assert 'You have to defeat the fighters before you can enter this sector.' in text and 'Option? (A,B,D,I,Q,S,T,W,?=Help):?' in text, 'hostile fighter admission stop'
        # Thrusters debit in ten-turn chunks rather than running the ordinary
        # per-turn cloak-decrement helper, even across a 35->25 boundary.
        assert get(after,2,125)==get(before,2,125), 'thruster cloak preservation'
    else:
        assert 'Planet thrusters engaged.' not in text, 'unrequested thruster action'
        if kind=='assault':
            committed=int(case['committed'])
            assert 1<=committed<=get(before,2,121), 'assault commitment admission'
            assert 'Permission to land is DENIED!' in text and 'Do you wish to try to force a landing? [y/N]' in text and 'Use how many ground forces?' in text, 'assault admission prompts'
            a,d=verify_ground_trace(before,after,record,committed,text)
            expected_ship_ground-=committed;expected_ground=a if d==0 and a>0 else d
            expected_owner=2 if d==0 and a>0 else get(before,record,73)
            fields|={(2,121),(record,73),(record,77)}
        else:
            assert 'Forces engaging!'not in text and "You've captured the planet!"not in text, 'unrequested ground battle'
            if kind in {'decline','invalid-force'}:
                assert 'Permission to land is DENIED!' in text and 'Do you wish to try to force a landing? [y/N]' in text, 'refused landing admission'
                assert ('Use how many ground forces?'in text)==(kind=='invalid-force'), 'cancelled/invalid quantity branch'
            elif kind=='no-troops':
                assert get(before,2,121)==0 and 'Permission to land is DENIED!' in text and 'Do you wish to try to force a landing?'not in text, 'no-ground admission'
            elif kind=='permission':
                assert name in {'land-neutral-defended','land-dead-governor'} and 'This planet has no governor! Hail to the new planetary governor!!'in text, 'governor adoption notice'
                expected_owner=2;expected_ground=get(after,record,77)
                assert 0<=expected_ground<=get(before,record,77), 'unrest defense bound'
                assert f'ground forces have been reduced to {int(expected_ground)} from {int(get(before,record,77))}!'in text, 'unrest receipt'
                fields|={(record,73),(record,77)}
            else:
                assert kind in {'landing','reentry'}, 'unknown noncombat outcome'
                assert 'Permission to land is DENIED!'not in text and 'Do you wish to try to force a landing?'not in text and 'Planet: Test Planet'in text, 'ordinary landing admission'
                if name=='land-fractional-defender':
                    assert get(before,record,77)==.25 and get(after,record,77)==0, 'fractional defender floor'
                    fields.add((record,77))
    assert get(after,2,57)==expected_sector, 'final ship sector'
    assert get(after,2,49)==get(before,2,49)-spent, 'turn debit'
    assert get(after,2,45)==get(before,2,45), 'ship death preservation'
    assert get(after,2,121)==expected_ship_ground, 'ship ground conservation'
    assert get(after,record,73)==expected_owner and get(after,record,77)==expected_ground, 'planet ownership/ground settlement'
    after_pointers={s:int(get(after,51+s,93))for s in range(1,3001)}
    assert after_pointers==expected_pointers, 'planet sector links'
    if expected_sector!=source:fields|={(2,57),(2,49)}
    for sector,value in expected_pointers.items():
        if value!=pointers[sector]:fields.add((51+sector,93))
    for player in(2,3):
        assert rawfield(after,player,109)==enc(public_score(after,player)), 'public score arithmetic'
    assert_unchanged_except(before,after,fields,names)


def auxiliary_witness(files):
    return sha(b''.join(name.encode()+b'\0'+data+b'\0' for name,data in sorted(files.items())))


def verify_aux(case, before, after, text, initial, final):
    assert set(final) == set(initial), 'auxiliary file set'
    for name, data in initial.items():
        if name not in {'YTNEWS.DAT', 'YTSCORE.ASC'}:
            assert final[name] == data, ('unrelated auxiliary effect', case['name'], name)
    prefix=initial['YTNEWS.DAT'].rstrip(b'\x1a')
    news=final['YTNEWS.DAT']
    assert news.startswith(prefix), 'public news prefix preservation'
    tail=news[len(prefix):].decode('cp437')
    match=re.match(r'-=\*=-( [0-9]{2}:[0-9]{2}:[0-9]{2}) Q  Logged on -=\*=-\r\n',tail)
    assert match, 'public login news'
    h,m,sec=map(int,match[1].split(':'));actual=3600*h+60*m+sec
    h,m,sec=map(int,case['time'].split(':'));assert 0<=actual-(3600*h+60*m+sec)<=30, 'public login news clock'
    expected=''
    slot=case.get('source_slot',2);record=4051+slot
    if case['expect']=='assault':
        expected+=f" +++ Q  attacked planet Test Planet with {int(case['committed'])} ground forces!\r\n"
        if get(after,record,73)==2:
            expected+=' +++ Planetary defenses destroyed!\r\n +++ Q  captured planet Test Planet!\r\n'
        else:
            expected+=f" +++ Attack Failed! Ground Forces remaining: {int(get(after,record,77))}!\r\n"
    elif case['expect']=='collision':
        expected+=' *** Planet Test Planet EXPLODED while being moved by Q !!!\r\n'
        loss=int(get(before,2,61)-get(after,2,61))
        if get(before,2,61):expected+=f'Q  lost {loss} fighters in the explosion!\r\n'
    if case['name']=='move-mines':
        expected+=f"Q  hit sector mines in sector {int(get(after,2,57))}!\r\nShields reduced to {int(get(after,2,53))} units!\r\n"
    assert tail[match.end():]==expected+'\x1a', 'exact public event settlement'
    score=final['YTSCORE.ASC'].decode('cp437')
    rows=re.findall(r'^ *([12]) +([0-9.]+)% +([0-9,]+) +(None|1) +([0-9]+) +(Q|Enemy) *\r?$',score,re.M)
    assert len(rows)==2, 'public scoreboard player rows'
    high=max(public_score(after,p)for p in(2,3))
    for rank,percent,points,team,ports,alias in rows:
        player=2 if alias=='Q'else 3;value=public_score(after,player)
        assert int(points.replace(',',''))==int(value), 'public scoreboard points'
        assert abs(float(percent)-100*value/high)<=.006, 'public scoreboard rank percent'
        assert int(ports)==get(after,player,117), 'public scoreboard ports'
        assert team==('1'if get(after,player,89)==1 else'None'), 'public scoreboard team'
    assert auxiliary_witness(final)==AUX_SHA[case['name']], 'frozen complete auxiliary witness'


def verify(root):
    directory = root/'dos'
    baseline = (SOURCE/'YTDATA.DAT').read_bytes()
    assert sha(baseline) == BASE_SHA and zipped(directory/'baseline.dat.gz') == baseline, 'baseline identity'
    declaration_bytes = (directory/'recipe.json').read_bytes()
    assert RECIPE_SHA and sha(declaration_bytes) == RECIPE_SHA, 'frozen declarations'
    declarations = json.loads(declaration_bytes)
    manifest = read(directory/'results.json')
    assert declarations['recipe'] == manifest['recipe'] == RECIPE, 'recipe identity'
    cases = {c['name']: c for c in declarations['scenarios']}
    rows = manifest['scenarios']
    assert len(cases) == len(rows) == len(WORLD_SHA), 'scenario count'
    assert len({c['name'] for c in rows}) == len(rows) and set(cases) == set(WORLD_SHA) == {c['name'] for c in rows}, 'scenario identity'
    binaries = {name: (ROOT/'archive/dos-original'/name).read_bytes() for name in BINS if name != 'KEYFEED.COM'}
    binaries['KEYFEED.COM'] = (ROOT/'archive/analysis/yt-combat/KEYFEED.COM').read_bytes()
    assert {name:sha(data)for name,data in binaries.items()}==BINS, 'archived binary identity'
    worlds, auxiliaries = {}, {}
    for case in rows:
        name = case['name']
        assert re.fullmatch(r'[a-z0-9-]+', name), 'scenario path'
        d, decl = directory/name, cases[name]
        assert case == read(d/'result.json') and all(case[k] == v for k, v in decl.items()), 'manifest/declaration mismatch'
        assert case['recipe'] == RECIPE and case['baseline_sha256'] == BASE_SHA, 'session identity'
        assert case['complete'] and case['program_returned'] and not case['timed_out'] and case['timeout_seconds'] == 120, 'incomplete DOS control'
        assert case['binaries'] == {n: sha(b) for n, b in binaries.items()}, 'binary identity'
        assert set(case['files']) == KEEP and {p.name for p in d.iterdir()} == KEEP | {'result.json'}, 'retained file set'
        for file, digest in case['files'].items():
            assert sha((d/file).read_bytes()) == digest, ('file hash', name, file)
        verify_clock(d, case)
        assert (d/'RETURN.LOG').read_bytes() == b'MOBILITY_PROGRAM_RETURNED\r\n', 'DOS return marker'
        before, after = zipped(d/'before.dat.gz'), zipped(d/'after.dat.gz')
        assert len(before) == len(after) == 568687, 'world size'
        if case.get('parent'):
            assert case['parent'] in worlds, 'parent ordering'
            expected = bytearray(worlds[case['parent']])
            initial = auxiliaries[case['parent']]
            patches = decl['patches']
        else:
            expected = bytearray(baseline)
            initial = {p.name: p.read_bytes() for p in SOURCE.iterdir() if p.suffix.upper() in ('.DAT', '.ASC', '.DEF', '.TMP') and p.name != 'YTDATA.DAT'}
            patches = declarations['common_patches']+decl['patches']
        if decl.get('planet_copies'):
            assert not case.get('parent'), 'copy/parent setup ambiguity'
            for record,offset,value in declarations['common_patches']:
                put(expected,record,offset,value)
            for source,target in decl['planet_copies']:
                assert source in range(1,101) and target in range(1,101), 'copy bounds'
                expected[(4050+target)*137:(4051+target)*137]=expected[(4050+source)*137:(4051+source)*137]
            patches=declarations['common_patches']+decl['patches']
            # Common fields were written before the copies. Reapplying them here
            # would clobber a copied source slot; apply only case mutations below.
            assert case['applied_patches']==patches, 'declared patch list'
            patches=decl['patches']
        else:
            assert case['applied_patches'] == patches, 'declared patch list'
        assert patches is not None, 'declared patch list'
        for record, offset, value in patches:
            put(expected, record, offset, value)
        assert before == expected, 'undeclared setup or broken world chain'
        assert {n: bytes.fromhex(v) for n, v in side(d/'side-before.json.gz').items()} == initial, 'auxiliary input chain'
        aux = side(d/'sidefiles.json.gz')
        final = {n: bytes.fromhex(v['hex']) for n, v in aux.items()}
        assert all(v['after_sha256'] == sha(final[n]) and v['before_sha256'] == (sha(initial[n]) if n in initial else None) for n, v in aux.items()), 'auxiliary identity'
        keys = ('\r~~~~~\r~'+decl['command']+'\r~~~~'+'Q;Y\r~~~~'*12).encode()
        assert (d/'KEYS.TXT').read_bytes() == keys, 'exact input stream'
        text = (d/'transcript.txt').read_text()
        assert zipped(d/'game.log.gz').decode('cp437').replace('\r\n', '\n') == text, 'raw transcript identity'
        assert 'Returning to Yankee Trader Local Logon Program...' in text, 'normal quit'
        verify_semantics(case, before, after, text)
        verify_aux(case, before, after, text, initial, final)
        assert sha(after) == WORLD_SHA[name], 'frozen complete world witness'
        worlds[name], auxiliaries[name] = after, final
    verify_native(root)
    print(f'Verified {len(rows)} normally returned planetary mobility/landing controls, exact world/auxiliary chains, bounded semantics and {len(NATIVE_RANGES)} native byte observations.')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--research', type=Path, default=ROOT/'research/yt-planet-mobility')
    verify(p.parse_args().research)
