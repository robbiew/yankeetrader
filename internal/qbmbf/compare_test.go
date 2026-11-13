package qbmbf

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"
	"testing"
)

func TestCompareSingleNative(t *testing.T) {
	raw, err := os.ReadFile("testdata/native_compare_single.json")
	if err != nil {
		t.Fatal(err)
	}
	var d struct {
		Format    string
		FlagsMask int `json:"flags_mask"`
		Cases     []struct {
			Name, Left, Right string
			Flags             uint16
			Branches          []int
			Trace             string `json:"trace_hex"`
			Hash              string `json:"source_trace_sha256"`
		}
	}
	if err = json.Unmarshal(raw, &d); err != nil {
		t.Fatal(err)
	}
	if d.Format != "qb-native-single-compare-flags-v1" || d.FlagsMask != 0x8c5 || len(d.Cases) != 216 {
		t.Fatal("fixture coverage")
	}
	for _, c := range d.Cases {
		t.Run(c.Name, func(t *testing.T) {
			l, e := hex.DecodeString(c.Left)
			if e != nil || len(l) != 4 {
				t.Fatal("left")
			}
			r, e := hex.DecodeString(c.Right)
			if e != nil || len(r) != 4 {
				t.Fatal("right")
			}
			trace, e := hex.DecodeString(c.Trace)
			if e != nil || len(trace) != 97 {
				t.Fatal("trace")
			}
			sum := sha256.Sum256(trace)
			if hex.EncodeToString(sum[:]) != c.Hash {
				t.Fatal("trace hash")
			}
			f := CompareSingle([4]byte(l), [4]byte(r))
			if f.Bits() != c.Flags || f.Bits() != (uint16(trace[36])|uint16(trace[37])<<8)&0x8c5 {
				t.Fatalf("flags %04x want %04x", f.Bits(), c.Flags)
			}
			if len(c.Branches) != 16 {
				t.Fatal("branch coverage")
			}
			for i, b := range f.Jumps() {
				if b != (c.Branches[i] == 1) || b != (trace[38+i] == 1) {
					t.Fatalf("Jcc %02x", 0x70+i)
				}
			}
		})
	}
}

func TestCompareSingleDoesNotSynthesizeSignedOrder(t *testing.T) {
	f := CompareSingle([4]byte{0, 0, 0, 129}, [4]byte{0, 0, 128, 129})
	if !f.Jumps()[7] || !f.Jumps()[12] {
		t.Fatal("positive vs negative has both JA and JL")
	}
	f = CompareSingle([4]byte{255, 127, 0, 129}, [4]byte{0, 128, 0, 129})
	if !f.Carry || !f.Sign || !f.Overflow || f.Jumps()[12] {
		t.Fatal("low-word subtraction overflow must survive")
	}
}
