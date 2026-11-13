package qbmbf

import (
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"os"
	"testing"
)

func TestSignZeroNative(t *testing.T) {
	raw, err := os.ReadFile("testdata/native_sign_zero.json")
	if err != nil {
		t.Fatal(err)
	}
	var d struct {
		Format    string
		FlagsMask uint16 `json:"flags_mask"`
		Cases     []struct {
			Name, Left, FAC string
			Op              byte
			Flags           uint16
			Branches        []int
			Trace           string `json:"trace_hex"`
			Hash            string `json:"source_trace_sha256"`
		}
	}
	if err = json.Unmarshal(raw, &d); err != nil {
		t.Fatal(err)
	}
	if d.Format != "qb-native-sign-zero-flags-v1" || d.FlagsMask != 0x8c5 || len(d.Cases) != 248 {
		t.Fatal("fixture coverage")
	}
	counts := map[byte]int{}
	for _, c := range d.Cases {
		t.Run(c.Name, func(t *testing.T) {
			counts[c.Op]++
			trace, e := hex.DecodeString(c.Trace)
			if e != nil || len(trace) != 113 {
				t.Fatal("trace")
			}
			h := sha256.Sum256(trace)
			if hex.EncodeToString(h[:]) != c.Hash {
				t.Fatal("native trace digest")
			}
			left, e := hex.DecodeString(c.Left)
			if e != nil || len(left) != 8 {
				t.Fatal("memory input")
			}
			fac, e := hex.DecodeString(c.FAC)
			if e != nil || len(fac) != 8 {
				t.Fatal("FAC input")
			}
			var f ComparisonFlags
			switch c.Op {
			case 0xa7:
				f = SignZeroSingle([4]byte(left[:4]))
			case 0xa8:
				f = SignZeroDouble([8]byte(left))
			case 0xa9:
				f = SignZeroSingle([4]byte(fac[4:]))
			case 0xaa:
				f = SignZeroDouble([8]byte(fac))
			default:
				t.Fatal("unadmitted opcode")
			}
			if f.Bits() != c.Flags || f.Bits() != binary.LittleEndian.Uint16(trace[44:46])&0x8c5 {
				t.Fatal("native flags")
			}
			if len(c.Branches) != 16 {
				t.Fatal("branch coverage")
			}
			for i, b := range f.Jumps() {
				if b != (c.Branches[i] == 1) || b != (trace[46+i] == 1) {
					t.Fatalf("Jcc %02x", 112+i)
				}
			}
			if string(trace[8:16]) != string(trace[80:88]) || string(trace[16:24]) != string(trace[88:96]) || string(trace[24:32]) != string(trace[96:104]) {
				t.Fatal("readonly FAC/operands")
			}
		})
	}
	for _, op := range []byte{167, 168, 169, 170} {
		if counts[op] != 62 {
			t.Fatal("per-entry coverage")
		}
	}
}

func TestSignZeroFlagsAreNotSGN(t *testing.T) {
	f := SignZeroSingle([4]byte{255, 255, 255, 0})
	if !f.Zero || f.Carry {
		t.Fatal("negative zero alias")
	}
	f = SignZeroSingle([4]byte{0, 0, 0, 129})
	if f.Zero || f.Carry || !f.Sign {
		t.Fatal("SF records exponent logical flags, not numeric sign")
	}
	f = SignZeroDouble([8]byte{1, 2, 3, 4, 5, 6, 192, 1})
	if !f.Carry || f.Overflow || f.Sign {
		t.Fatal("RCL flags")
	}
}
