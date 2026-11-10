"""Authenticate bounded inline9d resolution and complete successful subtraction frames."""
import json,re,struct
from pathlib import Path
import verify_inline_add as shared
import verify_single_sub as subtract
ROOT=shared.ROOT
DEFAULT=ROOT/'research/yt-mbf-inline-sub/native'
CALLER_DEFAULT=ROOT/'research/yt-mbf-inline-sub/caller-native'
FIXTURE=ROOT/'internal/qbmbf/testdata/native_inline_sub.json'
PINS_SHA='d5311615c31f800486ea078734b09bca9e4d36f66725d7a12f626c0714b6f0a3'
CALLER_PINS_SHA='140f552184227e14a2a39f0468b6f3e48c0f5588c0f048706ff1a9cffd48704d'
CASES={
  "address-bm-00": {
    "kind": "address",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 0,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bm-80": {
    "kind": "address",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bm-7f": {
    "kind": "address",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 127,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bm-ff": {
    "kind": "address",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bz-00": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 0,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bz-80": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bz-7f": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 127,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bz-ff": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bm-wrap-00": {
    "kind": "address",
    "magic": 28002,
    "base10": 65528,
    "base12": 26624,
    "selector": 0,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bm-wrap-01": {
    "kind": "address",
    "magic": 28002,
    "base10": 65528,
    "base12": 26624,
    "selector": 1,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bm-wrap-7f": {
    "kind": "address",
    "magic": 28002,
    "base10": 65528,
    "base12": 26624,
    "selector": 127,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bz-wrap-00": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 65528,
    "selector": 0,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bz-wrap-01": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 65528,
    "selector": 1,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bz-wrap-7f": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 65528,
    "selector": 127,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-fallback-83": {
    "kind": "address",
    "magic": 0,
    "base10": 24576,
    "base12": 26624,
    "selector": 131,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-caller-bm-83": {
    "kind": "address",
    "magic": 28002,
    "base10": 32256,
    "base12": 2243,
    "selector": 131,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-caller-bz-83": {
    "kind": "address",
    "magic": 31330,
    "base10": 32256,
    "base12": 2243,
    "selector": 131,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "full-bm-aliases-80": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "12345600",
    "fac": "ffffff00",
    "initial": 5
  },
  "full-bm-aliases-83": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 131,
    "left": "12345600",
    "fac": "ffffff00",
    "initial": 5
  },
  "full-bm-aliases-ff": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "12345600",
    "fac": "ffffff00",
    "initial": 5
  },
  "full-bm-left-zero-80": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "12345600",
    "fac": "00000081",
    "initial": 5
  },
  "full-bm-left-zero-83": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 131,
    "left": "12345600",
    "fac": "00000081",
    "initial": 5
  },
  "full-bm-left-zero-ff": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "12345600",
    "fac": "00000081",
    "initial": 5
  },
  "full-bm-right-zero-80": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "00000081",
    "fac": "ffffff00",
    "initial": 5
  },
  "full-bm-right-zero-83": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 131,
    "left": "00000081",
    "fac": "ffffff00",
    "initial": 5
  },
  "full-bm-right-zero-ff": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "00000081",
    "fac": "ffffff00",
    "initial": 5
  },
  "full-bm-cancel-80": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "00004081",
    "fac": "00004081",
    "initial": 5
  },
  "full-bm-cancel-83": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 131,
    "left": "00004081",
    "fac": "00004081",
    "initial": 5
  },
  "full-bm-cancel-ff": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "00004081",
    "fac": "00004081",
    "initial": 5
  },
  "full-bm-negative-cancel-80": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "0000c081",
    "fac": "0000c081",
    "initial": 5
  },
  "full-bm-negative-cancel-83": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 131,
    "left": "0000c081",
    "fac": "0000c081",
    "initial": 5
  },
  "full-bm-negative-cancel-ff": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "0000c081",
    "fac": "0000c081",
    "initial": 5
  },
  "full-bm-underflow-80": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "01000001",
    "fac": "00000001",
    "initial": 5
  },
  "full-bm-underflow-83": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 131,
    "left": "01000001",
    "fac": "00000001",
    "initial": 5
  },
  "full-bm-underflow-ff": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "01000001",
    "fac": "00000001",
    "initial": 5
  },
  "full-bm-reverse-underflow-80": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "00000001",
    "fac": "01000001",
    "initial": 5
  },
  "full-bm-reverse-underflow-83": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 131,
    "left": "00000001",
    "fac": "01000001",
    "initial": 5
  },
  "full-bm-reverse-underflow-ff": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "00000001",
    "fac": "01000001",
    "initial": 5
  },
  "full-bm-even-tie-80": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "00000081",
    "fac": "00008069",
    "initial": 5
  },
  "full-bm-even-tie-83": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 131,
    "left": "00000081",
    "fac": "00008069",
    "initial": 5
  },
  "full-bm-even-tie-ff": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "00000081",
    "fac": "00008069",
    "initial": 5
  },
  "full-bm-gap-cutoff-80": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "00000081",
    "fac": "00004068",
    "initial": 16777215
  },
  "full-bm-gap-cutoff-83": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 131,
    "left": "00000081",
    "fac": "00004068",
    "initial": 16777215
  },
  "full-bm-gap-cutoff-ff": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "00000081",
    "fac": "00004068",
    "initial": 16777215
  },
  "full-bm-sign-cross-80": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "00004081",
    "fac": "00000082",
    "initial": 5
  },
  "full-bm-sign-cross-83": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 131,
    "left": "00004081",
    "fac": "00000082",
    "initial": 5
  },
  "full-bm-sign-cross-ff": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "00004081",
    "fac": "00000082",
    "initial": 5
  },
  "full-bm-align-80": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "56341291",
    "fac": "ac681380",
    "initial": 5
  },
  "full-bm-align-83": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 131,
    "left": "56341291",
    "fac": "ac681380",
    "initial": 5
  },
  "full-bm-align-ff": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "56341291",
    "fac": "ac681380",
    "initial": 5
  },
  "full-bz-aliases-80": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "12345600",
    "fac": "ffffff00",
    "initial": 5
  },
  "full-bz-aliases-83": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 131,
    "left": "12345600",
    "fac": "ffffff00",
    "initial": 5
  },
  "full-bz-aliases-ff": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "12345600",
    "fac": "ffffff00",
    "initial": 5
  },
  "full-bz-left-zero-80": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "12345600",
    "fac": "00000081",
    "initial": 5
  },
  "full-bz-left-zero-83": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 131,
    "left": "12345600",
    "fac": "00000081",
    "initial": 5
  },
  "full-bz-left-zero-ff": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "12345600",
    "fac": "00000081",
    "initial": 5
  },
  "full-bz-right-zero-80": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "00000081",
    "fac": "ffffff00",
    "initial": 5
  },
  "full-bz-right-zero-83": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 131,
    "left": "00000081",
    "fac": "ffffff00",
    "initial": 5
  },
  "full-bz-right-zero-ff": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "00000081",
    "fac": "ffffff00",
    "initial": 5
  },
  "full-bz-cancel-80": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "00004081",
    "fac": "00004081",
    "initial": 5
  },
  "full-bz-cancel-83": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 131,
    "left": "00004081",
    "fac": "00004081",
    "initial": 5
  },
  "full-bz-cancel-ff": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "00004081",
    "fac": "00004081",
    "initial": 5
  },
  "full-bz-negative-cancel-80": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "0000c081",
    "fac": "0000c081",
    "initial": 5
  },
  "full-bz-negative-cancel-83": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 131,
    "left": "0000c081",
    "fac": "0000c081",
    "initial": 5
  },
  "full-bz-negative-cancel-ff": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "0000c081",
    "fac": "0000c081",
    "initial": 5
  },
  "full-bz-underflow-80": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "01000001",
    "fac": "00000001",
    "initial": 5
  },
  "full-bz-underflow-83": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 131,
    "left": "01000001",
    "fac": "00000001",
    "initial": 5
  },
  "full-bz-underflow-ff": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "01000001",
    "fac": "00000001",
    "initial": 5
  },
  "full-bz-reverse-underflow-80": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "00000001",
    "fac": "01000001",
    "initial": 5
  },
  "full-bz-reverse-underflow-83": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 131,
    "left": "00000001",
    "fac": "01000001",
    "initial": 5
  },
  "full-bz-reverse-underflow-ff": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "00000001",
    "fac": "01000001",
    "initial": 5
  },
  "full-bz-even-tie-80": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "00000081",
    "fac": "00008069",
    "initial": 5
  },
  "full-bz-even-tie-83": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 131,
    "left": "00000081",
    "fac": "00008069",
    "initial": 5
  },
  "full-bz-even-tie-ff": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "00000081",
    "fac": "00008069",
    "initial": 5
  },
  "full-bz-gap-cutoff-80": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "00000081",
    "fac": "00004068",
    "initial": 16777215
  },
  "full-bz-gap-cutoff-83": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 131,
    "left": "00000081",
    "fac": "00004068",
    "initial": 16777215
  },
  "full-bz-gap-cutoff-ff": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "00000081",
    "fac": "00004068",
    "initial": 16777215
  },
  "full-bz-sign-cross-80": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "00004081",
    "fac": "00000082",
    "initial": 5
  },
  "full-bz-sign-cross-83": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 131,
    "left": "00004081",
    "fac": "00000082",
    "initial": 5
  },
  "full-bz-sign-cross-ff": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "00004081",
    "fac": "00000082",
    "initial": 5
  },
  "full-bz-align-80": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "56341291",
    "fac": "ac681380",
    "initial": 5
  },
  "full-bz-align-83": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 131,
    "left": "56341291",
    "fac": "ac681380",
    "initial": 5
  },
  "full-bz-align-ff": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "56341291",
    "fac": "ac681380",
    "initial": 5
  }
}
CALLER_CASES={f'caller-{label}-{selector:02x}':dict(kind='address',magic=magic,base10=0x7e00,base12=0x08c3,selector=selector,left='00000000',fac='a55a3288',initial=16777215) for label,magic in (('bm',0x6d62),('bz',0x7a62)) for selector in (0x80,0x81,0x82)}


def expected_payload(case):return shared.expected_payload(case,'subtract')
def verify_trace(trace,case):return shared.verify_trace(trace,case,'subtract')


def verify_inventory():
    raw=(ROOT/'research/yt-mbf-inline-sub/maintenance-calls.json').read_bytes()
    assert shared.SHA(raw)=='c94a357ef02e5417086bfc651d91a1d84aedd3f5d68c651ea67e80d884b68d25','fixed inline9d caller inventory'
    d=json.loads(raw);original=(ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes();listing=(ROOT/'archive/analysis/yt-maint/qb-annotated.txt').read_bytes()
    assert d['format']=='maintenance-inline9d-callers-v1' and d['authority']=='Static annotated direct-call inventory matched to archived bytes; not observed execution or exhaustive indirect coverage.'
    assert shared.SHA(original)==d['original_sha256']=='8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6'
    assert shared.SHA(listing)==d['listing_sha256']=='097f46fd3f0e70743b9b89b56c8f5efd13f2bc2b6faf081aae4bb1b0583004c2'
    assert original[0x200:0x202]==b'bm' and struct.unpack_from('<HH',original,0x210)==(0x7e00,0x08c3),'archived caller metadata'
    calls=[]
    for address,selector in re.findall(r'1000:([0-9a-f]+)\s+QB_3f_9d[^\n]*\n\s+INLINE ([0-9a-fA-F]{2})\s*\n',listing.decode()):
        off=int(address,16);v=int(selector,16);assert original[512+off:512+off+6]==bytes.fromhex('cd3f9d9090')+bytes([v]);calls.append(dict(code_offset=off,file_offset=512+off,selector=v))
    assert calls==d['calls'] and len(calls)==5 and {r['selector'] for r in calls}==set(range(0x80,0x84)),'all matched direct inline9d callers'
    return calls


def verify(directory=DEFAULT,fixture=FIXTURE,caller_directory=CALLER_DEFAULT):
    runtime=(ROOT/'archive/dos-original/BRUN30.EXE').read_bytes()
    subtract.verify_static(runtime) # retained subtraction wrapper, addition kernel and ABI
    shared.verify_static(runtime) # retained shared inline resolver, frame helper and tail
    assert struct.unpack_from('<H',runtime,0x58d+2*0x9d)[0]==0xb359
    assert runtime[0xb559:0xb569]==bytes.fromhex('e8676bbf1a00e8096c8b45023480eb11'),'inline9d resolves then joins original subtraction wrapper'
    verify_inventory()
    portable=shared.verify_corpus(directory,CASES,PINS_SHA,'brun30-inline-sub-v1','recover_inline_sub.py','subtract')
    portable+=shared.verify_corpus(caller_directory,CALLER_CASES,CALLER_PINS_SHA,'brun30-inline-sub-callers-v1','recover_inline_sub_callers.py','subtract')
    doc=dict(format='qb-native-inline-sub-v1',cases=portable)
    if fixture is not None:assert json.loads(Path(fixture).read_text())==doc,'portable fixture equals both full inline9d corpora'
    return doc

if __name__=='__main__':
    doc=verify();print('Verified',len(doc['cases']),'inline9d controls:',sum(c['kind']=='address' for c in doc['cases']),'resolver-only and',sum(c['kind']=='full' for c in doc['cases']),'full successful subtractions; five static maintenance callers')
