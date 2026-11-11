"""Authenticate inline95 addressing, finite multiplication and bounded errors."""
import json,struct
from pathlib import Path
import verify_inline_add as address
import verify_inline_overflow as context
import verify_single_multiply as product
ROOT=address.ROOT
DEFAULT=ROOT/'research/yt-mbf-inline-multiply/native'
ADDRESS_DEFAULT=ROOT/'research/yt-mbf-inline-multiply/address-native'
FIXTURE=ROOT/'internal/qbmbf/testdata/native_inline_multiply.json'
PINS_SHA='14f19574ac5d975ed23f09094a097ae103525a6073230cdfd5e3526f33cc2057'
ADDRESS_PINS_SHA='8a0cff8bb3b40c72151cbda133099a1d33b07d52f5f6daea8fbdf072a546b028'
CASES={
  "bm-aliases-80": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "12345600",
    "fac": "ffffff00",
    "initial": 5
  },
  "bm-aliases-85": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 133,
    "left": "12345600",
    "fac": "ffffff00",
    "initial": 5
  },
  "bm-left-zero-80": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "12345600",
    "fac": "00004081",
    "initial": 5
  },
  "bm-left-zero-85": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 133,
    "left": "12345600",
    "fac": "00004081",
    "initial": 5
  },
  "bm-right-zero-80": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "00004081",
    "fac": "12345600",
    "initial": 5
  },
  "bm-right-zero-85": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 133,
    "left": "00004081",
    "fac": "12345600",
    "initial": 5
  },
  "bm-fraction-80": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "00004081",
    "fac": "00004081",
    "initial": 5
  },
  "bm-fraction-85": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 133,
    "left": "00004081",
    "fac": "00004081",
    "initial": 5
  },
  "bm-negative-80": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "0000c081",
    "fac": "00004081",
    "initial": 5
  },
  "bm-negative-85": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 133,
    "left": "0000c081",
    "fac": "00004081",
    "initial": 5
  },
  "bm-both-negative-80": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "0000c081",
    "fac": "0000c081",
    "initial": 5
  },
  "bm-both-negative-85": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 133,
    "left": "0000c081",
    "fac": "0000c081",
    "initial": 5
  },
  "bm-underflow-80": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "01000040",
    "fac": "feff7f41",
    "initial": 5
  },
  "bm-underflow-85": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 133,
    "left": "01000040",
    "fac": "feff7f41",
    "initial": 5
  },
  "bm-align-80": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "56341291",
    "fac": "ac681380",
    "initial": 5
  },
  "bm-align-85": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 133,
    "left": "56341291",
    "fac": "ac681380",
    "initial": 5
  },
  "bm-tie48-even-80": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "00004081",
    "fac": "06004081",
    "initial": 5
  },
  "bm-tie48-even-85": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 133,
    "left": "00004081",
    "fac": "06004081",
    "initial": 5
  },
  "bm-sticky48-above-80": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "3d0c0081",
    "fac": "15eb7f81",
    "initial": 16777215
  },
  "bm-sticky48-above-85": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 133,
    "left": "3d0c0081",
    "fac": "15eb7f81",
    "initial": 16777215
  },
  "bm-positive-overflow-80": {
    "op": 149,
    "expect": "overflow",
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "ffff7fff",
    "fac": "00000082",
    "initial": 5
  },
  "bm-positive-overflow-85": {
    "op": 149,
    "expect": "overflow",
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 133,
    "left": "ffff7fff",
    "fac": "00000082",
    "initial": 5
  },
  "bm-negative-overflow-80": {
    "op": 149,
    "expect": "overflow",
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "ffffffff",
    "fac": "00000082",
    "initial": 16777215
  },
  "bm-negative-overflow-85": {
    "op": 149,
    "expect": "overflow",
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 133,
    "left": "ffffffff",
    "fac": "00000082",
    "initial": 16777215
  },
  "bm-round-overflow-80": {
    "op": 149,
    "expect": "overflow",
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "010000c0",
    "fac": "feff7fc0",
    "initial": 5
  },
  "bm-round-overflow-85": {
    "op": 149,
    "expect": "overflow",
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 133,
    "left": "010000c0",
    "fac": "feff7fc0",
    "initial": 5
  },
  "bz-aliases-80": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "12345600",
    "fac": "ffffff00",
    "initial": 5
  },
  "bz-aliases-85": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 133,
    "left": "12345600",
    "fac": "ffffff00",
    "initial": 5
  },
  "bz-left-zero-80": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "12345600",
    "fac": "00004081",
    "initial": 5
  },
  "bz-left-zero-85": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 133,
    "left": "12345600",
    "fac": "00004081",
    "initial": 5
  },
  "bz-right-zero-80": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "00004081",
    "fac": "12345600",
    "initial": 5
  },
  "bz-right-zero-85": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 133,
    "left": "00004081",
    "fac": "12345600",
    "initial": 5
  },
  "bz-fraction-80": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "00004081",
    "fac": "00004081",
    "initial": 5
  },
  "bz-fraction-85": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 133,
    "left": "00004081",
    "fac": "00004081",
    "initial": 5
  },
  "bz-negative-80": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "0000c081",
    "fac": "00004081",
    "initial": 5
  },
  "bz-negative-85": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 133,
    "left": "0000c081",
    "fac": "00004081",
    "initial": 5
  },
  "bz-both-negative-80": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "0000c081",
    "fac": "0000c081",
    "initial": 5
  },
  "bz-both-negative-85": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 133,
    "left": "0000c081",
    "fac": "0000c081",
    "initial": 5
  },
  "bz-underflow-80": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "01000040",
    "fac": "feff7f41",
    "initial": 5
  },
  "bz-underflow-85": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 133,
    "left": "01000040",
    "fac": "feff7f41",
    "initial": 5
  },
  "bz-align-80": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "56341291",
    "fac": "ac681380",
    "initial": 5
  },
  "bz-align-85": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 133,
    "left": "56341291",
    "fac": "ac681380",
    "initial": 5
  },
  "bz-tie48-even-80": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "00004081",
    "fac": "06004081",
    "initial": 5
  },
  "bz-tie48-even-85": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 133,
    "left": "00004081",
    "fac": "06004081",
    "initial": 5
  },
  "bz-sticky48-above-80": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "3d0c0081",
    "fac": "15eb7f81",
    "initial": 16777215
  },
  "bz-sticky48-above-85": {
    "op": 149,
    "expect": "return",
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 133,
    "left": "3d0c0081",
    "fac": "15eb7f81",
    "initial": 16777215
  },
  "bz-positive-overflow-80": {
    "op": 149,
    "expect": "overflow",
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "ffff7fff",
    "fac": "00000082",
    "initial": 5
  },
  "bz-positive-overflow-85": {
    "op": 149,
    "expect": "overflow",
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 133,
    "left": "ffff7fff",
    "fac": "00000082",
    "initial": 5
  },
  "bz-negative-overflow-80": {
    "op": 149,
    "expect": "overflow",
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "ffffffff",
    "fac": "00000082",
    "initial": 16777215
  },
  "bz-negative-overflow-85": {
    "op": 149,
    "expect": "overflow",
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 133,
    "left": "ffffffff",
    "fac": "00000082",
    "initial": 16777215
  },
  "bz-round-overflow-80": {
    "op": 149,
    "expect": "overflow",
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "010000c0",
    "fac": "feff7fc0",
    "initial": 5
  },
  "bz-round-overflow-85": {
    "op": 149,
    "expect": "overflow",
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 133,
    "left": "010000c0",
    "fac": "feff7fc0",
    "initial": 5
  },
  "pad16-positive-overflow": {
    "op": 149,
    "expect": "overflow",
    "pad": 16,
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 132,
    "left": "ffff7fff",
    "fac": "00000082",
    "initial": 16777215
  },
  "pad16-underflow": {
    "op": 149,
    "expect": "return",
    "pad": 16,
    "kind": "full",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 132,
    "left": "01000040",
    "fac": "feff7f41",
    "initial": 16777215
  },
  "pad32-positive-overflow": {
    "op": 149,
    "expect": "overflow",
    "pad": 32,
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 132,
    "left": "ffff7fff",
    "fac": "00000082",
    "initial": 16777215
  },
  "pad32-underflow": {
    "op": 149,
    "expect": "return",
    "pad": 32,
    "kind": "full",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 132,
    "left": "01000040",
    "fac": "feff7f41",
    "initial": 16777215
  }
}
ADDRESS_CASES={
  "address-bm-00": {
    "kind": "address",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 0,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 16777215
  },
  "address-bm-80": {
    "kind": "address",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 16777215
  },
  "address-bm-7f": {
    "kind": "address",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 127,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 16777215
  },
  "address-bm-ff": {
    "kind": "address",
    "magic": 28002,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 16777215
  },
  "address-bz-00": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 0,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 16777215
  },
  "address-bz-80": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 128,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 16777215
  },
  "address-bz-7f": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 127,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 16777215
  },
  "address-bz-ff": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 26624,
    "selector": 255,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 16777215
  },
  "address-bm-wrap-00": {
    "kind": "address",
    "magic": 28002,
    "base10": 65528,
    "base12": 26624,
    "selector": 0,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 16777215
  },
  "address-bm-wrap-01": {
    "kind": "address",
    "magic": 28002,
    "base10": 65528,
    "base12": 26624,
    "selector": 1,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 16777215
  },
  "address-bm-wrap-7f": {
    "kind": "address",
    "magic": 28002,
    "base10": 65528,
    "base12": 26624,
    "selector": 127,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 16777215
  },
  "address-bz-wrap-00": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 65528,
    "selector": 0,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 16777215
  },
  "address-bz-wrap-01": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 65528,
    "selector": 1,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 16777215
  },
  "address-bz-wrap-7f": {
    "kind": "address",
    "magic": 31330,
    "base10": 24576,
    "base12": 65528,
    "selector": 127,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 16777215
  },
  "address-fallback-84": {
    "kind": "address",
    "magic": 0,
    "base10": 24576,
    "base12": 26624,
    "selector": 132,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 16777215
  },
  "address-caller-bm-80": {
    "kind": "address",
    "magic": 28002,
    "base10": 32256,
    "base12": 2243,
    "selector": 128,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 16777215
  },
  "address-caller-bm-81": {
    "kind": "address",
    "magic": 28002,
    "base10": 32256,
    "base12": 2243,
    "selector": 129,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 16777215
  },
  "address-caller-bm-82": {
    "kind": "address",
    "magic": 28002,
    "base10": 32256,
    "base12": 2243,
    "selector": 130,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 16777215
  },
  "address-caller-bm-84": {
    "kind": "address",
    "magic": 28002,
    "base10": 32256,
    "base12": 2243,
    "selector": 132,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 16777215
  },
  "address-caller-bm-85": {
    "kind": "address",
    "magic": 28002,
    "base10": 32256,
    "base12": 2243,
    "selector": 133,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 16777215
  },
  "address-caller-bz-80": {
    "kind": "address",
    "magic": 31330,
    "base10": 32256,
    "base12": 2243,
    "selector": 128,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 16777215
  },
  "address-caller-bz-81": {
    "kind": "address",
    "magic": 31330,
    "base10": 32256,
    "base12": 2243,
    "selector": 129,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 16777215
  },
  "address-caller-bz-82": {
    "kind": "address",
    "magic": 31330,
    "base10": 32256,
    "base12": 2243,
    "selector": 130,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 16777215
  },
  "address-caller-bz-84": {
    "kind": "address",
    "magic": 31330,
    "base10": 32256,
    "base12": 2243,
    "selector": 132,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 16777215
  },
  "address-caller-bz-85": {
    "kind": "address",
    "magic": 31330,
    "base10": 32256,
    "base12": 2243,
    "selector": 133,
    "left": "00000000",
    "fac": "a55a3288",
    "initial": 16777215
  }
}


def expected_payload(c):return context.expected_payload(c)
def verify_trace(raw,c):
    assert c['op']==0x95,'only qualified inline multiplication operation'
    return context.verify_trace(raw,c)
def expected_address_payload(c):return address.expected_payload(c,'multiply')
def verify_address_trace(raw,c):
    assert c['kind']=='address','resolver-only profile'
    return address.verify_trace(raw,c,'multiply')


def verify_static(runtime):
    product.verify_static(runtime) # retained product, direct entry mappings and 12 inline95 sites
    context.verify_static(runtime) # retained shared resolver, compiled-frame helper and default error dispatch
    assert struct.unpack_from('<H',runtime,0x58d+2*0x95)[0]==0xb4a5,'original inline95 dispatch'
    assert runtime[0xb6a5:0xb6ae]==bytes.fromhex('e81b6abf1a00e8bd6a'),'same resolver, right FAC, then multiplication ABI'
    _,calls=product.verify_inventory()
    admitted={c['selector'] for c in ADDRESS_CASES.values() if (c['base10'],c['base12'])==(0x7e00,0x08c3)}
    assert {r['selector'] for r in calls}==admitted=={0x80,0x81,0x82,0x84,0x85},'existing source inventory and actual-header selector coverage'
    return calls


def verify(directory=DEFAULT,fixture=FIXTURE,address_directory=ADDRESS_DEFAULT):
    assert all(c['op']==0x95 and c['kind']=='full' for c in CASES.values()) and all(c['kind']=='address' for c in ADDRESS_CASES.values())
    verify_static((ROOT/'archive/dos-original/BRUN30.EXE').read_bytes())
    execution=context.verify_corpus(directory,CASES,PINS_SHA,'brun30-inline-multiply-v1','recover_inline_multiply.py')
    addresses=address.verify_corpus(address_directory,ADDRESS_CASES,ADDRESS_PINS_SHA,'brun30-inline-multiply-address-v1','recover_inline_multiply_address.py','multiply')
    doc=dict(format='qb-native-inline-multiply-v1',address_cases=addresses,execution_cases=execution)
    if fixture is not None:assert json.loads(Path(fixture).read_text())==doc,'portable fixture equals both complete inline95 corpora'
    return doc

if __name__=='__main__':
    d=verify();print('Verified',len(d['address_cases']),'resolver-only controls and',len(d['execution_cases']),'full inline95 outcomes:',sum(c['output']is None for c in d['execution_cases']),'Overflow diagnostics; 12 static source callers')
