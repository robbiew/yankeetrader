package qbmbf

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"
	"testing"
)

func TestCompareDoubleNative(t *testing.T) {
	raw, err := os.ReadFile("testdata/native_compare_double.json")
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
	if d.Format != "qb-native-double-compare-flags-v1" || d.FlagsMask != 0x8c5 || len(d.Cases) != 486 {
		t.Fatal("fixture coverage")
	}
	for _, c := range d.Cases {
		t.Run(c.Name, func(t *testing.T) {
			l, e := hex.DecodeString(c.Left)
			if e != nil || len(l) != 8 {
				t.Fatal("left")
			}
			r, e := hex.DecodeString(c.Right)
			if e != nil || len(r) != 8 {
				t.Fatal("right")
			}
			trace, e := hex.DecodeString(c.Trace)
			if e != nil || len(trace) != 113 {
				t.Fatal("trace")
			}
			sum := sha256.Sum256(trace)
			if hex.EncodeToString(sum[:]) != c.Hash {
				t.Fatal("trace hash")
			}
			f := CompareDouble([8]byte(l), [8]byte(r))
			if f.Bits() != c.Flags || f.Bits() != (uint16(trace[44])|uint16(trace[45])<<8)&0x8c5 {
				t.Fatalf("flags %04x want %04x", f.Bits(), c.Flags)
			}
			if len(c.Branches) != 16 {
				t.Fatal("branch coverage")
			}
			for i, b := range f.Jumps() {
				if b != (c.Branches[i] == 1) || b != (trace[46+i] == 1) {
					t.Fatalf("Jcc %02x", 0x70+i)
				}
			}
		})
	}
}

func TestCompareDoubleRetainsLowerWords(t *testing.T) {
	for offset := 0; offset < 6; offset += 2 {
		l := [8]byte{0, 0, 0, 0, 0, 0, 0, 129}
		r := l
		l[offset], l[offset+1] = 255, 127
		r[offset], r[offset+1] = 0, 128
		f := CompareDouble(l, r)
		if !f.Carry || !f.Sign || !f.Overflow || f.Jumps()[12] {
			t.Fatalf("word %d subtraction flags lost", offset/2)
		}
		// The high SINGLE-sized portion alone cannot distinguish these operands.
		if offset < 4 && !CompareSingle([4]byte(l[4:]), [4]byte(r[4:])).Zero {
			t.Fatal("test does not expose truncation")
		}
	}
	f := CompareDouble([8]byte{0, 0, 0, 0, 0, 0, 0, 129}, [8]byte{0, 0, 0, 0, 0, 0, 128, 129})
	if !f.Jumps()[7] || !f.Jumps()[12] {
		t.Fatal("JA and JL native sign exit")
	}
}
