package qbmbf

import (
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"os"
	"testing"
)

// Inline /a5 composes the qualified resolver and direct comparison. Address-only
// traces deliberately do not claim a memory read or comparison flag result.
func TestInlineSingleComparisonNative(t *testing.T) {
	raw, err := os.ReadFile("testdata/native_inline_single_compare.json")
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
	if d.Format != "qb-native-inline-single-compare-v1" || d.FlagsMask != 0x8c5 || len(d.Cases) != 296 {
		t.Fatal("fixture coverage")
	}
	full, address := 0, 0
	for _, c := range d.Cases {
		t.Run(c.Name, func(t *testing.T) {
			trace, e := hex.DecodeString(c.Trace)
			if e != nil {
				t.Fatal(e)
			}
			size := 93
			if c.Kind == "full" {
				size = 101
				full++
			} else if c.Kind == "address" {
				address++
			} else {
				t.Fatal("unsupported kind")
			}
			if len(trace) != size || string(trace[:4]) != "I5CF" || string(trace[size-4:]) != "END!" || c.Op != 165 {
				t.Fatal("complete /a5 protocol")
			}
			sum := sha256.Sum256(trace)
			if hex.EncodeToString(sum[:]) != c.Hash {
				t.Fatal("trace digest")
			}
			selected := SingleAddInlineOffset(c.Selector, c.Magic, c.Base10, c.Base12)
			if selected != c.Resolved || binary.LittleEndian.Uint16(trace[66:68]) != selected {
				t.Fatal("resolved SI")
			}
			fac, e := hex.DecodeString(c.FAC)
			if e != nil || len(fac) != 8 {
				t.Fatal("FAC")
			}
			left, e := hex.DecodeString(c.Left)
			if e != nil || len(left) != 4 {
				t.Fatal("left")
			}
			if string(trace[8:16]) != string(fac) || string(trace[76:84]) != string(fac) {
				t.Fatal("whole FAC changed")
			}
			if c.Kind == "address" {
				if c.Flags != nil || len(c.Branches) != 0 || binary.LittleEndian.Uint16(trace[68:70]) != selected {
					t.Fatal("resolver-only control claims comparison")
				}
				return
			}
			if selected > 65532 || c.Flags == nil || len(c.Branches) != 16 || string(trace[89:93]) != string(left) || hex.EncodeToString(trace[93:97]) != "0123c5fe" {
				t.Fatal("safe readonly operands")
			}
			if binary.LittleEndian.Uint16(trace[68:70]) != 0x1a {
				t.Fatal("right FAC mapping")
			}
			f := CompareSingle([4]byte(left), [4]byte(fac[4:]))
			if f.Bits() != *c.Flags || f.Bits() != binary.LittleEndian.Uint16(trace[40:42])&0x8c5 {
				t.Fatal("native comparison flags")
			}
			for i, b := range f.Jumps() {
				if b != (c.Branches[i] == 1) || b != (trace[42+i] == 1) {
					t.Fatalf("actual Jcc %02x", 112+i)
				}
			}
		})
	}
	if full != 275 || address != 21 {
		t.Fatalf("coverage full=%d address=%d", full, address)
	}
}
