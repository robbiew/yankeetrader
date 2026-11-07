"""Authenticate original Mercenary friendly-force/planet pickup precedence.

Reuses a single complete retained REA read; opens no native controls, target
saves, acquisition writers or replay models. Static contracts are conditional
on the physical force actually present when the arriving group reads a sector.
They do not establish that a local group held during an earlier activation.
"""
import hashlib
import json
from pathlib import Path

from verify_rng_native import image

ROOT = Path(__file__).resolve().parents[1]
SHA = lambda data: hashlib.sha256(data).hexdigest()
BINARY_SHA = '8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6'
PACKET = 'research/yt-maint/collision-replay-native/rea.json'
PACKET_SHA = 'be0f500c1a8b201970dcbb65bbe4b6c718f668fba5326d582af840289cccb202'
EVIDENCE = 'ev_c92656dd4a34f4605e434c81cbd3e9f730962d0373f2a3fecfce72256fbfcd2f'
ADDRESS, LENGTH = '0x14600', 3462

# These are independently declared original LOAD-image slices, not bytes read
# back out of a capture or selected observation at verification time.
SPANS = {
 'descending-scan': (0x47c9, 'bfa47ebedc18cd3f7f9090bf147ccd3f7d9090bf187cbea07ecd3f7b9090bee018cd3f6f9090e9310b'),
 'actor-double': (0x4804, 'bb9018cd3d199090cd3f749090bf207ccd3f7e9090'),
 'eager-linked-planet-hold': (0x4847, 'bb9c18cd3d199090cd3fa99090bb000076014bcd3d349090bfde87cd3fa19090ba000073014a23d323d27403e9a20a'),
 'depart-clear-before-route': (0x4876, 'bb9e858bd3cd3d1c90908bcaba9418cd3f5b90908bd9cd3d1c9090ba9018cd3f5b9090bb1c7ccd3e7b9090bb010033d2cd3e289090'),
 'entered-sector-caches': (0x49f1, 'bb9c18cd3d199090bf2c7ccd3f7d9090bb9018cd3d199090cd3f749090bf907bcd3f7e9090bbc418cd3d199090bf307ccd3f7d9090bb9418cd3d1990908bdfbfec18cd3f7d9090'),
 'owner-and-link-pickup-priority': (0x4c7f, 'bf0e80beec18cd3f9f9090bb000075014bcd3fa79090ba000075014a0bd3be2c7c8bde8bcbcd3f75909023da23db7503e91102'),
 'stock-INT-before-name-length': (0x4cd0, 'bbc418cd3d199090bb1a00cd3d0390908bdfbff87bcd3f7d9090bb9418cd3d199090cd3f779090'),
 'whole-stock-clear-and-save': (0x4d09, 'bb7284cd3d1c9090bac418cd3f5b90908bdfbfe418be2c7ccd3f7f90908bd3bb1a00cd3e7b90908bd833d2cd3e289090'),
 'stock-plus-actor-plus-entering': (0x4d68, 'bef87bcd3f7390908bdfbf207ccd3f8290908bd7bf907bcd3f829090cd3f7a9090bb1a00cd3d1c9090ba9018cd3f5b9090'),
 'sector-save-before-receipts': (0x4d99, 'bb007ecd3e7b90908bd833d2cd3e289090'),
 'capture-only-zero-entering-force': (0x4daa, '8bdfbf687bbe287ccd3f9f9090ba000074014a8bf3cd3fa89090b9000075014923ca23c97503e96100'),
 'positive-taking-combined-stamp': (0x4e34, 'bef87bcd3fa790907703e97f00bf207c8bdebe907bcd3f8090908bd3bb1600cd3d129090'),
 'pickup-skips-plain-merge': (0x4ec0, 'e95504'),
 'plain-friendly-merge-fallback': (0x4ec3, 'be907bcd3fa89090bb000076014b8bd6beec18cd3fa79090b9000074014923cb23c97503e92b04bf0e80cd3f9f90907403e96b008bfabe207ccd3f8090908bfecd3f7e9090'),
 'plain-merge-clears-and-continues': (0x4f2d, 'bb72848bc3cd3d1c9090ba9418cd3f5b90908bd8cd3d1c9090ba9018cd3f5b9090bb007ecd3e7b90908bd933d2cd3e289090e9d0f9'),
 'descending-next': (0x5318, 'bf187cbe1c7ccd3f7f9090bf1c7ccd3f7d9090be187ccd3fa790907203e912008bf7bf147ccd3f9f90907203e9abf4e91000'),
}
LITERALS = {0x800e: '00008082', 0x87de: 'c3f52880', 0x8472: '00008000', 0x859e: '00002800'}


def select_record(raw):
    assert type(raw) is bytes and SHA(raw) == PACKET_SHA, 'immutable complete Mercenary packet'
    rows = json.loads(raw)['records']
    assert type(rows) is list and all(type(row) is dict for row in rows), 'native observation inventory'
    selected = [row for row in rows if row.get('evidence_id') == EVIDENCE]
    assert len(selected) == 1, 'one exact Mercenary evidence ID'
    return selected[0]


def verify_record(record, binary):
    assert type(binary) is bytes and SHA(binary) == BINARY_SHA, 'immutable original maintenance binary'
    assert record['evidence_id'] == EVIDENCE and record['operation'] == 'read_bytes' and record['subject']['digest']['sha256'] == BINARY_SHA, 'exact evidence identity, operation and subject'
    assert record['parameters'] == dict(address=ADDRESS, length=LENGTH), 'exact native read parameters'
    value = record['normalized_result']
    data = bytes.fromhex(value['bytes_hex'])
    assert value['address'] == ADDRESS and value['complete'] is True and value['requested_bytes'] == value['returned_bytes'] == len(data) == LENGTH, 'complete untruncated native range'
    assert data == image(binary)[0x4600:0x4600+LENGTH], 'normalized bytes equal original relocated MZ LOAD image'


def verify_paths(binary):
    assert type(binary) is bytes and SHA(binary) == BINARY_SHA, 'immutable original maintenance binary'
    code = image(binary)
    for name, (at, expected) in SPANS.items():
        expected = bytes.fromhex(expected)
        assert code[at:at+len(expected)] == expected, 'original source contract: ' + name
    for at, expected in LITERALS.items():
        assert binary[at+0xfd0:at+0xfd0+4] == bytes.fromhex(expected), 'original source literal ' + hex(at)
    return {
        'entering_force_cache': '7b90',
        'actor_force_cache': '7c20',
        'pickup_precedes_plain_merge': True,
        'pickup_gate': 'cached sector owner is zero or -2, and planet link is nonzero',
        'planet_governor_is_pickup_gate': False,
        'saved_force': 'actor + entering physical force + converted whole planet stock',
        'taking_stamp': 'actor + entering physical force',
        'capture_gate': 'entering physical force equals zero and route sector differs from 7b68',
        'taking_gate': 'converted whole planet stock is positive',
        'stock_zero_path': 'unconditional full-stock clear and sector save; receipt gates still apply',
        'hold_gate': 'positive planet link and eager movement draw below source SINGLE .66',
        'scan': 'descending physical sector records; local 3000 activates before actor 2368',
    }


def verify():
    record = select_record((ROOT/PACKET).read_bytes())
    binary = (ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes()
    verify_record(record, binary)
    return dict(reused_native_packets=1, reused_native_reads=1, retained_read_bytes=LENGTH,
                evidence_id=EVIDENCE, **verify_paths(binary),
                scope='conditional static source order; no assertion that a local group held, no new DOS execution or general MBF claim')


if __name__ == '__main__':
    print('Friendly stock native evidence verified:', verify())
