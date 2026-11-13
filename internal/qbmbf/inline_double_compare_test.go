package qbmbf

import (
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"os"
	"testing"
)

// Inline /a6 composes the qualified resolver and direct comparison. Address-only
// traces deliberately do not claim a memory read or comparison flag result.
func TestInlineDoubleComparisonNative(t *testing.T) {
	raw, err := os.ReadFile("testdata/native_inline_double_compare.json")
	if err != nil {
		t.Fatal(err)
	}
	var d struct {
		Format    string
		FlagsMask uint16 `json:"flags_mask"`
		Cases     []struct {
			Name, Kind, Left, FAC               string
			Op, Magic, Base10, Base12, Resolved uint16
			Selector                            byte
			Flags                               *uint16
			Branches                            []int
			Trace                               string `json:"trace_hex"`
			Hash                                string `json:"source_trace_sha256"`
		}
	}
	if err = json.Unmarshal(raw, &d); err != nil {
		t.Fatal(err)
	}
	if d.Format != "qb-native-inline-double-compare-v1" || d.FlagsMask != 0x8c5 || len(d.Cases) != 348 {
		t.Fatal("fixture coverage")
	}
	full, address := 0, 0
	for _, c := range d.Cases {
		t.Run(c.Name, func(t *testing.T) {
			trace, e := hex.DecodeString(c.Trace)
			if e != nil {
				t.Fatal(e)
			}
			size := 97
			if c.Kind == "full" {
				size = 113
				full++
			} else if c.Kind == "address" {
				address++
			} else {
				t.Fatal("unsupported kind")
			}
			if len(trace) != size || string(trace[:4]) != "I6CF" || string(trace[size-4:]) != "END!" || c.Op != 166 {
				t.Fatal("complete /a6 protocol")
			}
			sum := sha256.Sum256(trace)
			if hex.EncodeToString(sum[:]) != c.Hash {
				t.Fatal("trace digest")
			}
			selected := SingleAddInlineOffset(c.Selector, c.Magic, c.Base10, c.Base12)
			if selected != c.Resolved || binary.LittleEndian.Uint16(trace[70:72]) != selected {
				t.Fatal("resolved SI")
			}
			fac, e := hex.DecodeString(c.FAC)
			if e != nil || len(fac) != 8 {
				t.Fatal("FAC")
			}
			left, e := hex.DecodeString(c.Left)
			if e != nil || len(left) != 8 {
				t.Fatal("left")
			}
			if string(trace[8:16]) != string(fac) || string(trace[80:88]) != string(fac) {
				t.Fatal("whole FAC changed")
			}
			if c.Kind == "address" {
				if c.Flags != nil || len(c.Branches) != 0 || binary.LittleEndian.Uint16(trace[72:74]) != selected {
					t.Fatal("resolver-only control claims comparison")
				}
				return
			}
			if selected > 65528 || c.Flags == nil || len(c.Branches) != 16 || string(trace[93:101]) != string(left) || hex.EncodeToString(trace[101:109]) != "0123456789abc5fe" {
				t.Fatal("safe readonly operands")
			}
			if binary.LittleEndian.Uint16(trace[72:74]) != 0x16 {
				t.Fatal("right FAC mapping")
			}
			f := CompareDouble([8]byte(left), [8]byte(fac))
			if f.Bits() != *c.Flags || f.Bits() != binary.LittleEndian.Uint16(trace[44:46])&0x8c5 {
				t.Fatal("native comparison flags")
			}
			for i, b := range f.Jumps() {
				if b != (c.Branches[i] == 1) || b != (trace[46+i] == 1) {
					t.Fatalf("actual Jcc %02x", 112+i)
				}
			}
		})
	}
	if full != 329 || address != 19 {
		t.Fatalf("coverage full=%d address=%d", full, address)
	}
}
