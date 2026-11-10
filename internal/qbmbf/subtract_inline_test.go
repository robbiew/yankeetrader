package qbmbf

import (
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"os"
	"testing"
)

func TestNativeInlineSubtraction(t *testing.T) {
	data, err := os.ReadFile("testdata/native_inline_sub.json")
	if err != nil {
		t.Fatal(err)
	}
	var doc struct {
		Format string
		Cases  []struct {
			Name, Kind, Left, FAC string
			Magic, Base10, Base12 uint16
			Selector              byte
			Initial               uint32
			Resolved              uint16
			After                 string `json:"fac_after"`
			Trace                 string `json:"trace_hex"`
			SHA                   string `json:"source_trace_sha256"`
		}
	}
	if err = json.Unmarshal(data, &doc); err != nil {
		t.Fatal(err)
	}
	if doc.Format != "qb-native-inline-sub-v1" || len(doc.Cases) != 89 {
		t.Fatal("fixed native coverage")
	}
	counts := map[string]int{}
	for _, c := range doc.Cases {
		t.Run(c.Name, func(t *testing.T) {
			counts[c.Kind]++
			raw, e := hex.DecodeString(c.Trace)
			if e != nil {
				t.Fatal(e)
			}
			sum := sha256.Sum256(raw)
			size := 57
			if c.Kind == "full" {
				size = 65
			} else if c.Kind != "address" {
				t.Fatal("unknown protocol")
			}
			if hex.EncodeToString(sum[:]) != c.SHA || len(raw) != size || string(raw[:4]) != "IS9D" || string(raw[size-4:]) != "END!" {
				t.Fatal("native framing and digest")
			}
			word := func(i int) uint16 { return binary.LittleEndian.Uint16(raw[i : i+2]) }
			offset := SingleAddInlineOffset(c.Selector, c.Magic, c.Base10, c.Base12)
			if offset != c.Resolved || offset != word(32) || raw[17] != c.Selector || word(18) != c.Magic || word(20) != c.Base10 || word(22) != c.Base12 {
				t.Fatal("native selector, descriptor and resolved offset")
			}
			di := offset
			if c.Kind == "full" {
				di = 0x1a
			}
			if word(34) != di || word(36) != 0xbeef || word(24) == 0 || word(24) != word(26) || word(28) != word(24)+0x500 || word(30) < 2 || word(38) != word(24) || word(40) != word(26) || word(42) != word(30) {
				t.Fatal("resolver register/frame state")
			}
			fac, left, want := addRaw(t, c.FAC), addRaw(t, c.Left), addRaw(t, c.After)
			if string(raw[8:12]) != string(fac[:]) || string(raw[12:16]) != string(left[:]) || string(raw[44:48]) != string(want[:]) || binary.LittleEndian.Uint32(raw[4:8]) != c.Initial || binary.LittleEndian.Uint32(raw[48:52]) != c.Initial || raw[16] != 0 || raw[52] != 0 {
				t.Fatal("inputs, FAC, RNG and mode")
			}
			if c.Kind == "address" {
				if want != fac {
					t.Fatal("resolver-only FAC changed")
				}
				return
			}
			got, ok := SubtractSingleWithFAC(left, fac, fac)
			if !ok || got != want {
				t.Fatalf("shared subtraction got %x,%v; native %x", got, ok, want)
			}
			poison := "00000081"
			if c.Left == poison {
				poison = "00000082"
			}
			p := addRaw(t, poison)
			if string(raw[53:57]) != string(left[:]) || string(raw[57:61]) != string(p[:]) {
				t.Fatal("selected and alternate-base memory")
			}
		})
	}
	if counts["address"] != 23 || counts["full"] != 66 {
		t.Fatal("resolver and arithmetic coverage")
	}
}
