"""Independent inline-resolver/frame and successful addition-entry audit."""
import hashlib, json, re, shlex, struct
from pathlib import Path
from verify_rng_trace import INIT_SHA, RUNTIME_SHA
from verify_rng_clock import read_date, read_time
from verify_maintenance_clock_neutral import HOST_SHA
ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'research/yt-mbf-inline-add/native'
CALLER_DEFAULT=ROOT/'research/yt-mbf-inline-add/caller-native'
CALLER_PINS_SHA='f843f17d60be18369d6542175216ea7a24f840e7ed611ea18d1243f25411f2c6'
CALLER_CASES={f'caller-{label}-{selector:02x}':dict(kind='address',magic=magic,base10=0x7e00,base12=0x08c3,selector=selector,left='00000000',fac='a55a3288',initial=16777215) for label,magic in (('bm',0x6d62),('bz',0x7a62)) for selector in range(0x80,0x8a)}
FIXTURE=ROOT/'internal/qbmbf/testdata/native_inline_add.json'
SHA=lambda b:hashlib.sha256(b).hexdigest()
PINS_SHA='8b0985ebea92d196d2a20522f162a8ccc27c76b3849e387e173402c7e4d9ddb8'
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
  "address-bm-01": {
    "kind": "address",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 1,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bm-02": {
    "kind": "address",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 2,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bm-3f": {
    "kind": "address",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 63,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bm-40": {
    "kind": "address",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 64,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bm-7e": {
    "kind": "address",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 126,
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
  "address-bm-81": {
    "kind": "address",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 129,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bm-82": {
    "kind": "address",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 130,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bm-bf": {
    "kind": "address",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 191,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bm-c0": {
    "kind": "address",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 192,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bm-fe": {
    "kind": "address",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 254,
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
  "address-bz-01": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 1,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bz-02": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 2,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bz-3f": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 63,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bz-40": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 64,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bz-7e": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 126,
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
  "address-bz-81": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 129,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bz-82": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 130,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bz-bf": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 191,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bz-c0": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 192,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bz-fe": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 254,
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
  "address-bm-wrap-02": {
    "kind": "address",
    "magic": 28002,
    "base10": 65528,
    "base12": 26624,
    "selector": 2,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bm-wrap-3f": {
    "kind": "address",
    "magic": 28002,
    "base10": 65528,
    "base12": 26624,
    "selector": 63,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bm-wrap-40": {
    "kind": "address",
    "magic": 28002,
    "base10": 65528,
    "base12": 26624,
    "selector": 64,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bm-wrap-7e": {
    "kind": "address",
    "magic": 28002,
    "base10": 65528,
    "base12": 26624,
    "selector": 126,
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
  "address-bm-wrap-80": {
    "kind": "address",
    "magic": 28002,
    "base10": 65528,
    "base12": 26624,
    "selector": 128,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bm-wrap-81": {
    "kind": "address",
    "magic": 28002,
    "base10": 65528,
    "base12": 26624,
    "selector": 129,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bm-wrap-82": {
    "kind": "address",
    "magic": 28002,
    "base10": 65528,
    "base12": 26624,
    "selector": 130,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bm-wrap-bf": {
    "kind": "address",
    "magic": 28002,
    "base10": 65528,
    "base12": 26624,
    "selector": 191,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bm-wrap-c0": {
    "kind": "address",
    "magic": 28002,
    "base10": 65528,
    "base12": 26624,
    "selector": 192,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bm-wrap-fe": {
    "kind": "address",
    "magic": 28002,
    "base10": 65528,
    "base12": 26624,
    "selector": 254,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bm-wrap-ff": {
    "kind": "address",
    "magic": 28002,
    "base10": 65528,
    "base12": 26624,
    "selector": 255,
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
  "address-bz-wrap-02": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 65528,
    "selector": 2,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bz-wrap-3f": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 65528,
    "selector": 63,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bz-wrap-40": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 65528,
    "selector": 64,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bz-wrap-7e": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 65528,
    "selector": 126,
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
  "address-bz-wrap-80": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 65528,
    "selector": 128,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bz-wrap-81": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 65528,
    "selector": 129,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bz-wrap-82": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 65528,
    "selector": 130,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bz-wrap-bf": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 65528,
    "selector": 191,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bz-wrap-c0": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 65528,
    "selector": 192,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bz-wrap-fe": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 65528,
    "selector": 254,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-bz-wrap-ff": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 65528,
    "selector": 255,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-non-bz-00": {
    "kind": "address",
    "magic": 0,
    "base10": 24576,
    "base12": 26624,
    "selector": 0,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-non-bz-01": {
    "kind": "address",
    "magic": 0,
    "base10": 24576,
    "base12": 26624,
    "selector": 1,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-non-bz-02": {
    "kind": "address",
    "magic": 0,
    "base10": 24576,
    "base12": 26624,
    "selector": 2,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-non-bz-3f": {
    "kind": "address",
    "magic": 0,
    "base10": 24576,
    "base12": 26624,
    "selector": 63,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-non-bz-40": {
    "kind": "address",
    "magic": 0,
    "base10": 24576,
    "base12": 26624,
    "selector": 64,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-non-bz-7e": {
    "kind": "address",
    "magic": 0,
    "base10": 24576,
    "base12": 26624,
    "selector": 126,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-non-bz-7f": {
    "kind": "address",
    "magic": 0,
    "base10": 24576,
    "base12": 26624,
    "selector": 127,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-non-bz-80": {
    "kind": "address",
    "magic": 0,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-non-bz-81": {
    "kind": "address",
    "magic": 0,
    "base10": 24576,
    "base12": 26624,
    "selector": 129,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-non-bz-82": {
    "kind": "address",
    "magic": 0,
    "base10": 24576,
    "base12": 26624,
    "selector": 130,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-non-bz-bf": {
    "kind": "address",
    "magic": 0,
    "base10": 24576,
    "base12": 26624,
    "selector": 191,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-non-bz-c0": {
    "kind": "address",
    "magic": 0,
    "base10": 24576,
    "base12": 26624,
    "selector": 192,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-non-bz-fe": {
    "kind": "address",
    "magic": 0,
    "base10": 24576,
    "base12": 26624,
    "selector": 254,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 5
  },
  "address-non-bz-ff": {
    "kind": "address",
    "magic": 0,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
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
  "full-bm-aliases-81": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 129,
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
  "full-bm-cancel-80": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "00004081",
    "fac": "0000c081",
    "initial": 5
  },
  "full-bm-cancel-81": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 129,
    "left": "00004081",
    "fac": "0000c081",
    "initial": 5
  },
  "full-bm-cancel-ff": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "00004081",
    "fac": "0000c081",
    "initial": 5
  },
  "full-bm-reverse-cancel-80": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "0000c081",
    "fac": "00004081",
    "initial": 5
  },
  "full-bm-reverse-cancel-81": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 129,
    "left": "0000c081",
    "fac": "00004081",
    "initial": 5
  },
  "full-bm-reverse-cancel-ff": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "0000c081",
    "fac": "00004081",
    "initial": 5
  },
  "full-bm-underflow-80": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "01000001",
    "fac": "00008001",
    "initial": 5
  },
  "full-bm-underflow-81": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 129,
    "left": "01000001",
    "fac": "00008001",
    "initial": 5
  },
  "full-bm-underflow-ff": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "01000001",
    "fac": "00008001",
    "initial": 5
  },
  "full-bm-even-tie-80": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "00000081",
    "fac": "00000069",
    "initial": 5
  },
  "full-bm-even-tie-81": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 129,
    "left": "00000081",
    "fac": "00000069",
    "initial": 5
  },
  "full-bm-even-tie-ff": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "00000081",
    "fac": "00000069",
    "initial": 5
  },
  "full-bm-gap-cutoff-80": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "00000081",
    "fac": "0000c068",
    "initial": 16777215
  },
  "full-bm-gap-cutoff-81": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 129,
    "left": "00000081",
    "fac": "0000c068",
    "initial": 16777215
  },
  "full-bm-gap-cutoff-ff": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "00000081",
    "fac": "0000c068",
    "initial": 16777215
  },
  "full-bm-sign-cross-80": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "00004081",
    "fac": "00008082",
    "initial": 5
  },
  "full-bm-sign-cross-81": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 129,
    "left": "00004081",
    "fac": "00008082",
    "initial": 5
  },
  "full-bm-sign-cross-ff": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "00004081",
    "fac": "00008082",
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
  "full-bm-align-81": {
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 129,
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
  "full-bz-aliases-81": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 129,
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
  "full-bz-cancel-80": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "00004081",
    "fac": "0000c081",
    "initial": 5
  },
  "full-bz-cancel-81": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 129,
    "left": "00004081",
    "fac": "0000c081",
    "initial": 5
  },
  "full-bz-cancel-ff": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "00004081",
    "fac": "0000c081",
    "initial": 5
  },
  "full-bz-reverse-cancel-80": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "0000c081",
    "fac": "00004081",
    "initial": 5
  },
  "full-bz-reverse-cancel-81": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 129,
    "left": "0000c081",
    "fac": "00004081",
    "initial": 5
  },
  "full-bz-reverse-cancel-ff": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "0000c081",
    "fac": "00004081",
    "initial": 5
  },
  "full-bz-underflow-80": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "01000001",
    "fac": "00008001",
    "initial": 5
  },
  "full-bz-underflow-81": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 129,
    "left": "01000001",
    "fac": "00008001",
    "initial": 5
  },
  "full-bz-underflow-ff": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "01000001",
    "fac": "00008001",
    "initial": 5
  },
  "full-bz-even-tie-80": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "00000081",
    "fac": "00000069",
    "initial": 5
  },
  "full-bz-even-tie-81": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 129,
    "left": "00000081",
    "fac": "00000069",
    "initial": 5
  },
  "full-bz-even-tie-ff": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "00000081",
    "fac": "00000069",
    "initial": 5
  },
  "full-bz-gap-cutoff-80": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "00000081",
    "fac": "0000c068",
    "initial": 16777215
  },
  "full-bz-gap-cutoff-81": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 129,
    "left": "00000081",
    "fac": "0000c068",
    "initial": 16777215
  },
  "full-bz-gap-cutoff-ff": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "00000081",
    "fac": "0000c068",
    "initial": 16777215
  },
  "full-bz-sign-cross-80": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "00004081",
    "fac": "00008082",
    "initial": 5
  },
  "full-bz-sign-cross-81": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 129,
    "left": "00004081",
    "fac": "00008082",
    "initial": 5
  },
  "full-bz-sign-cross-ff": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "00004081",
    "fac": "00008082",
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
  "full-bz-align-81": {
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 129,
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
FILES={'COMMANDS.TXT','launch.json','dosbox.stdout','dosbox.stderr','TRACE.BIN','DOSDATE.LOG','DOSTIME.LOG','ERROR.LOG','OK.LOG','RETURN.LOG'}


def expected_offset(case,alternate=False):
    use12=(case['magic']==0x7a62)^alternate
    return ((case['base12'] if use12 else case['base10'])+8*(case['selector']&127))&65535


def expected_payload(case,operation="add"):
    assert operation in ("add","subtract","multiply","divide"),"qualified inline operation"
    if operation=="divide":assert case['kind']=='address',"division requires the separate full execution/error protocol"
    opcode,marker={"add":(0x85,b"IA85"),"subtract":(0x9d,b"IS9D"),"multiply":(0x95,b"IM95"),"divide":(0x8d,b"ID8D")}[operation]
    def word(at,value,cs=False):return (b'\x2e' if cs else b'')+bytes.fromhex('c706')+struct.pack('<HH',at,value)
    def assign(at,raw):return b''.join(word(at+2*i,w) for i,w in enumerate(struct.unpack('<HH',raw)))
    def output(at,size):return bytes.fromhex('bb0100b9')+struct.pack('<H',size)+b'\xba'+struct.pack('<H',at)+bytes.fromhex('b440cd21')
    setup=bytes.fromhex('5589e583ec021e07')+word(0x5000,case['magic'])+bytes.fromhex('8cd80500058946fe')
    setup+=word(0x10,case['base10'],True)+word(0x12,case['base12'],True)+assign(0x1a,bytes.fromhex(case['fac']))+assign(0x1860,bytes.fromhex(case['left']))+word(0x1870,case['selector'])
    if case['kind']=='full':
        poison='00000082' if case['left']=='00000081' else '00000081'
        setup+=assign(expected_offset(case),bytes.fromhex(case['left']))+assign(expected_offset(case,True),bytes.fromhex(poison))
    context=bytes.fromhex('a10050a380182ea11000a382182ea11200a384188c1e86188c0688188b46fea38a18892e8c18')
    prefix=assign(0x1856,marker)+output(0x1856,4)+output(0x234,4)+output(0x1a,4)+output(0x1860,4)+output(0x1f,1)+output(0x1870,1)+output(0x1880,14)
    call=bytes.fromhex('b8efbecd3f')+bytes([opcode,0x90,0x90,case['selector']])
    saved=bytes.fromhex('89369018893e9218a394188c1e96188c069818892e9a18')
    suffix=output(0x1890,12)+output(0x1a,4)+output(0x234,4)+output(0x1f,1)
    if case['kind']=='full':suffix+=output(expected_offset(case),4)+output(expected_offset(case,True),4)
    return setup+context+prefix+call+saved+suffix+assign(0x1856,b'END!')+output(0x1856,4)+bytes.fromhex('89ec5db8004ccd21')


def verify_trace(trace,case,operation="add"):
    assert operation in ("add","subtract","multiply","divide"),"qualified inline operation"
    if operation=="divide":assert case['kind']=='address',"division requires the separate full execution/error protocol"
    marker={"add":b"IA85","subtract":b"IS9D","multiply":b"IM95","divide":b"ID8D"}[operation]
    assert case['kind'] in ('address','full'),'only declared resolver-only/full-success protocols'
    size=57 if case['kind']=='address' else 65
    assert len(trace)==size and trace[:4]==marker and trace[-4:]==b'END!','complete protocol-specific inline frame'
    assert trace[4:8]==struct.pack('<I',case['initial']) and trace[8:12].hex()==case['fac'] and trace[12:16].hex()==case['left'],'exact original RNG and inputs'
    assert trace[16]==0 and trace[17]==case['selector'],'default mode and actual selector'
    magic,b10,b12,ds,es,descriptor,bp=struct.unpack('<7H',trace[18:32])
    assert (magic,b10,b12)==(case['magic'],case['base10'],case['base12']),'actual descriptor word and opcode-caller CS fields'
    assert ds==es and ds!=0 and descriptor==(ds+0x500)&65535 and bp>=2,'declared ES=data DS and SS:BP-2 descriptor context'
    si,di,ax,after_ds,after_es,after_bp=struct.unpack('<6H',trace[32:44]);offset=expected_offset(case)
    assert si==offset and di==(offset if case['kind']=='address' else 0x1a),'actual resolved offset and protocol-specific DI'
    assert ax==0xbeef and (after_ds,after_es,after_bp)==(ds,es,bp),'AX, data segment, ES and BP survive the resolver protocol'
    assert trace[48:52]==struct.pack('<I',case['initial']) and trace[52]==0,'unrelated RNG and mode preserved'
    if case['kind']=='address':
        assert trace[44:48].hex()==case['fac'],'resolver-only controls must not claim arithmetic or read operand memory'
    else:
        assert offset<=65532 and expected_offset(case,True)<=65532,'full controls use safe complete operand spans'
        if operation=="add":from verify_single_add_entries import expected_entry
        elif operation=="subtract":from verify_single_sub import expected_entry
        else:from verify_single_multiply import expected_entry
        want=expected_entry(bytes.fromhex(case['left']),bytes.fromhex(case['fac']),bytes.fromhex(case['fac']))
        assert want is not None and trace[44:48]==want,'qualified shared arithmetic after actual inline address resolution'
        poison='00000082' if case['left']=='00000081' else '00000081'
        assert trace[53:57].hex()==case['left'] and trace[57:61].hex()==poison,'selected operand and alternate-base poison remain unchanged'
    return dict(resolved=si,fac_after=trace[44:48].hex())


def verify_static(runtime):
    from verify_rng_native import image
    from verify_single_add_entries import verify_static as verify_shared
    verify_shared(runtime)
    path=ROOT/'research/yt-xannor-revenge/rea/target-paths.json';raw=path.read_bytes()
    assert SHA(raw)=='30975a98d8e5f88c589defdc47f48cbc06b3f3ef8eb4eb717a98ad5d63c8eb15','immutable earlier resolver/frame packet'
    rows=json.loads(raw)['records'];assert len(rows)==23
    for address,size in [('0x11ec3',49),('0x11f6b',101),('0x1038d',396)]:
        found=[e for e in rows if e['subject']['name']=='BRUN30.EXE' and e['normalized_result'].get('address')==address];assert len(found)==1
        e=found[0];n=e['normalized_result'];assert e['subject']['digest']['sha256']==RUNTIME_SHA and e['operation']=='read_bytes' and n['complete'] is True and n['requested_bytes']==n['returned_bytes']==size
        at=int(address,16)-0x10000;assert bytes.fromhex(n['bytes_hex'])==image(runtime)[at:at+size]
    contracts=[('frame-helper.json','12096e37c141970e09d1092bb33ef422ee92d3df507189ddcf828a82d1dff17b','BRUN30.EXE','0x106b2',14),('resolver-tail.json','d0c39726b6f6996ebe8ac746e8af2b31489e2bbc969ea0a38cf7918b4660626d','BRUN30.EXE','0x11ef3',4),('maintenance-caller.json','3567ffd5a186f50c93012fcbb9264ee58eead55457f2c80012a896c7be02cb7a','YTMAINT.EXE','0x1095e',24)]
    for name,pin,binary,address,size in contracts:
        raw=(ROOT/'research/yt-mbf-inline-add/rea'/name).read_bytes();assert SHA(raw)==pin,'immutable missing-range observation'
        packet=json.loads(raw);assert packet['ok'] is True;e=packet['data'];n=e['normalized_result'];original=(ROOT/'archive/dos-original'/binary).read_bytes()
        assert e['operation']=='read_bytes' and e['parameters']==dict(address=address,length=size) and e['subject']['digest']['sha256']==SHA(original)
        assert n['address']==address and n['complete'] is True and n['requested_bytes']==n['returned_bytes']==size
        at=int(address,16)-0x10000;assert bytes.fromhex(n['bytes_hex'])==image(original)[at:at+size]
    assert runtime[0x697:0x699]==bytes.fromhex('6eb3') and runtime[0xb56e:0xb574]==bytes.fromhex('e8526bbf1a00'),'actual entry85 resolver then right-FAC mapping'
    maint=(ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes();assert maint[0xb6b:0xb71]==bytes.fromhex('cd3f85909080'),'real maintenance caller consumes one selector byte after five-byte opcode'
    assert maint[0x200:0x202]==b'bm' and struct.unpack_from('<HH',maint,0x210)==(0x7e00,0x08c3),'original maintenance module metadata, not the synthetic safe bases'


def verify_corpus(directory,cases,pins_sha,recipe_id,source_name,operation="add"):
    assert operation in ("add","subtract","multiply","divide"),"qualified inline operation"
    if operation=="divide":assert all(c['kind']=='address' for c in cases.values()),"division requires the separate full execution/error protocol"
    root=Path(directory); manifest=(root/'pins.json').read_bytes(); assert SHA(manifest)==pins_sha,'fixed native manifest'
    pins=json.loads(manifest)['files']
    assert {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.name!='pins.json'}==set(pins),'complete artifact inventory'
    for name,digest in pins.items(): assert SHA((root/name).read_bytes())==digest,'immutable observed artifact '+name
    original=(ROOT/'archive/dos-original/YT-INIT.EXE').read_bytes(); runtime=(ROOT/'archive/dos-original/BRUN30.EXE').read_bytes()
    assert (SHA(original),SHA(runtime))==(INIT_SHA,RUNTIME_SHA),'original executable identity'
    verify_static(runtime)
    source=root/'sources'/source_name; recipe=json.loads((root/'recipe.json').read_text())
    assert recipe==dict(recipe=recipe_id,cases=cases,initializer=INIT_SHA,runtime=RUNTIME_SHA,host_sha256=HOST_SHA,source_sha256=SHA(source.read_bytes())),'frozen prelaunch acquisition source and recipe'
    assert {p.name for p in root.iterdir()}==set(cases)|{'pins.json','recipe.json','sources'} and {p.name for p in source.parent.iterdir()}=={source.name},'fixed case/source coverage'
    portable=[]
    for name,case in cases.items():
        folder=root/name; meta=json.loads((folder/'result.json').read_text()); stub=expected_payload(case,operation)
        patched=bytearray(original); assert patched[0x23a:0x23f]==bytes.fromhex('cd3d439090'); patched[0x23a:0x23f]=bytes.fromhex('e930009090'); patched[0x26d:0x26d+len(stub)]=stub
        table=struct.unpack_from('<H',original,24)[0]
        for index in range(struct.unpack_from('<H',original,6)[0]):
            offset,segment=struct.unpack_from('<HH',original,table+4*index);at=16*segment+offset
            assert all(not(at<end and at+2>start) for start,end in ((0x3a,0x3f),(0x6d,0x6d+len(stub)))),'no loader relocation overlaps the diagnostic'
        copied=bytearray(runtime); struct.pack_into('<I',copied,0x10234,case['initial'])
        if case['kind']=='address':
            at={'add':0xb571,'subtract':0xb55c,'multiply':0xb6a8,'divide':0xb728}[operation]
            assert copied[at:at+3]==bytes.fromhex('bf1a00'),'original post-resolver FAC selection'
            copied[at:at+3]=bytes.fromhex('cb9090')
        assert set(meta)=={'recipe','case','kind','magic','base10','base12','selector','left','fac','initial','exit_code','timeout','missing','payload_hex','copied_initializer_sha256','copied_runtime_sha256','files'},'fixed result schema'
        assert {k:meta[k] for k in case}==case and meta['recipe']==recipe['recipe'] and meta['case']==name,'declared actual case'
        assert meta['exit_code']==0 and meta['timeout'] is False and meta['missing']==[],'normal emulator completion with all outcomes retained'
        assert meta['payload_hex']==stub.hex() and meta['copied_initializer_sha256']==SHA(patched) and meta['copied_runtime_sha256']==SHA(copied),'full copied image reconstruction'
        assert set(meta['files'])==FILES and {p.name for p in folder.iterdir()}==FILES|{'result.json'},'exact case inventory'
        for file,digest in meta['files'].items(): assert SHA((folder/file).read_bytes())==digest,'captured case digest'
        commands=(folder/'COMMANDS.TXT').read_text().splitlines()
        assert len(commands)==11 and commands[0].startswith(('mount c /tmp/','mount c /private/tmp/')) and Path(commands[0][8:]).name==name,'disposable case mount'
        assert commands[1:]==['c:','date 11/02/2026','time 00:00:00','date > DOSDATE.LOG','time > DOSTIME.LOG','yt-init > TRACE.BIN','if errorlevel 1 echo PROGRAM_ERROR > ERROR.LOG','if not errorlevel 1 echo PROGRAM_OK > OK.LOG','echo PROBE_RETURNED > RETURN.LOG','exit'],'complete actual commands'
        argv=['/opt/homebrew/bin/dosbox-staging','--noprimaryconf','--nolocalconf','--set','cpu_cycles=200000','--set','nosound=true']+[v for c in commands for v in ('-c',c)]
        assert json.loads((folder/'launch.json').read_text())==argv,'pinned actual launch'
        messages=[line.split(' | ',1)[1] for line in (folder/'dosbox.stderr').read_text().splitlines() if ' | ' in line]
        assert [shlex.split(m[11:]) for m in messages if m.startswith('arguments: ')]==[argv] and messages.count('dosbox-staging version 0.83.0 ()')==1,'actual host/version'
        assert 'SDL: dummy video initialised' in messages and "MIXER: Sound output disabled ('nosound' mode)" in messages and any(m.startswith('CPU: Setting fixed 200000 cycles.') for m in messages),'fixed headless host controls'
        assert (folder/'dosbox.stdout').read_bytes()==b'' and (folder/'ERROR.LOG').read_bytes()==b'' and (folder/'OK.LOG').read_bytes()==b'PROGRAM_OK\r\n' and (folder/'RETURN.LOG').read_bytes()==b'PROBE_RETURNED\r\n','native shell return; ERRORLEVEL alone does not prove conversion success'
        assert read_date((folder/'DOSDATE.LOG').read_bytes()).isoformat()=='2026-11-02' and abs(read_time((folder/'DOSTIME.LOG').read_bytes()))<=.1,'raw date/time controls'
        trace=(folder/'TRACE.BIN').read_bytes(); want=verify_trace(trace,case,operation)
        portable.append(dict(name=name,**case,**want,trace_hex=trace.hex(),source_trace_sha256=SHA(trace)))
    return portable


def verify_inventory():
    raw=(ROOT/'research/yt-mbf-inline-add/maintenance-calls.json').read_bytes()
    assert SHA(raw)=='4843809417352696bb12fa5bc9699b382546815bc74693c09d55446c0ccdd780','fixed ordinary caller inventory'
    data=json.loads(raw);original=(ROOT/'archive/dos-original/YTMAINT.EXE').read_bytes();listing=(ROOT/'archive/analysis/yt-maint/qb-annotated.txt').read_bytes()
    assert SHA(original)==data['original_sha256']=='8fdb4d0a13a8a1f5dae9d41c22cfe5f55fb58f2de58a62fe163165a774ec26a6'
    assert SHA(listing)==data['listing_sha256']=='097f46fd3f0e70743b9b89b56c8f5efd13f2bc2b6faf081aae4bb1b0583004c2'
    assert data['format']=='ordinary-maintenance-inline85-inventory-v1' and data['authority']=='Archived original bytes and annotated listing; static call-site inventory, not observed execution or an exhaustive indirect-call graph.'
    assert data['header_magic']=='626d' and data['base10']==0x7e00 and data['base12']==0x08c3
    calls=[]
    for address,selector in re.findall(r'1000:([0-9a-f]+)\s+QB_3f_85[^\n]*\n\s+INLINE ([0-9a-fA-F]{2})\s*\n',listing.decode()):
        offset=int(address,16);value=int(selector,16);assert original[512+offset:512+offset+6]==bytes.fromhex('cd3f859090')+bytes([value])
        calls.append(dict(code_offset=offset,file_offset=512+offset,selector=value,base10_candidate=(0x7e00+8*(value&127))&65535,base12_candidate=(0x08c3+8*(value&127))&65535))
    assert calls==data['calls'] and len(calls)==35 and {r['selector'] for r in calls}==set(range(0x80,0x8a)),'all listing-matched direct callers and observed selector set'
    return calls


def verify(directory=DEFAULT,fixture=FIXTURE,caller_directory=CALLER_DEFAULT):
    portable=verify_corpus(directory,CASES,PINS_SHA,'brun30-inline-add-v1','recover_inline_add.py')
    portable+=verify_corpus(caller_directory,CALLER_CASES,CALLER_PINS_SHA,'brun30-inline-add-callers-v1','recover_inline_add_callers.py')
    verify_inventory()
    document=dict(format='qb-native-inline-add-v1',cases=portable)
    if fixture is not None:assert json.loads(Path(fixture).read_text())==document,'portable fixture equals both complete native corpora'
    return document

if __name__=='__main__':
    doc=verify();print('Verified',len(doc['cases']),'inline controls:',sum(c['kind']=='address' for c in doc['cases']),'resolver-only and',sum(c['kind']=='full' for c in doc['cases']),'full successful additions; 35 static maintenance callers')
