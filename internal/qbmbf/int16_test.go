package qbmbf

import (
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"os"
	"testing"
)

func TestNativeInt16Single(t *testing.T) {
	data, err := os.ReadFile("testdata/native_int16_single.json")
	if err != nil {
		t.Fatal(err)
	}
	var doc struct {
		Format string
		Cases  []struct {
			Name, Raw string
			Op        int
			Initial   uint32
			Value     *int16
			Trace     string `json:"trace_hex"`
			SHA       string `json:"source_trace_sha256"`
		}
	}
	if err := json.Unmarshal(data, &doc); err != nil {
		t.Fatal(err)
	}
	if doc.Format != "qb-native-int16-single-v1" || len(doc.Cases) != 96 {
		t.Fatal("native fixture coverage")
	}
	overflows := 0
	for _, c := range doc.Cases {
		t.Run(c.Name, func(t *testing.T) {
			raw, err := hex.DecodeString(c.Raw)
			if err != nil || len(raw) != 4 {
				t.Fatal("raw SINGLE input")
			}
			trace, err := hex.DecodeString(c.Trace)
			if err != nil {
				t.Fatal(err)
			}
			digest := sha256.Sum256(trace)
			if hex.EncodeToString(digest[:]) != c.SHA || len(trace) < 13 || string(trace[:4]) != "C16!" || binary.LittleEndian.Uint32(trace[4:8]) != c.Initial || string(trace[8:12]) != string(raw) || trace[12] != 0 {
				t.Fatal("native input/mode provenance")
			}
			if c.Op != 0x75 && c.Op != 0x77 {
				t.Fatal("native entry")
			}
			got, ok := Int16Single([4]byte(raw))
			if c.Value == nil {
				overflows++
				address := "00C1"
				if c.Op == 0x77 {
					address = "00BE"
				}
				want := "\r\nOverflow in module YT-INIT  at address 01A3:" + address + "\r\n\r\nHit any key to return to system"
				if string(trace[13:]) != want || ok || got != 0 {
					t.Fatalf("overflow got (%d,%v)", got, ok)
				}
				return
			}
			if len(trace) != 28 || string(trace[24:]) != "END!" {
				t.Fatal("successful native framing")
			}
			native := int16(binary.LittleEndian.Uint16(trace[13:15]))
			if native != *c.Value || !ok || got != native {
				t.Fatalf("raw %x: got (%d,%v), native %d", raw, got, ok, native)
			}
			if string(trace[15:17]) != string(trace[13:15]) || string(trace[17:19]) != string(raw[2:]) || binary.LittleEndian.Uint32(trace[19:23]) != c.Initial || trace[23] != 0 {
				t.Fatal("native FAC residue/RNG/mode")
			}
		})
	}
	if overflows != 26 {
		t.Fatal("native overflow coverage")
	}
}

func TestInt16SingleRangeAndZeroAliases(t *testing.T) {
	for exponent := 0; exponent < 128; exponent++ {
		for _, sign := range []byte{0, 128} {
			if got, ok := Int16Single([4]byte{255, 255, 127 | sign, byte(exponent)}); !ok || got != 0 {
				t.Fatalf("subunit/zero %d: %d %v", exponent, got, ok)
			}
		}
	}
	for _, c := range []struct {
		raw  [4]byte
		want int16
		ok   bool
	}{
		{[4]byte{0, 0, 32, 130}, 3, true},   // +2.5
		{[4]byte{0, 0, 160, 130}, -3, true}, // -2.5
		{[4]byte{0, 0, 128, 144}, -32768, true},
		{[4]byte{64, 0, 128, 144}, -32768, true}, // -32768.25, kernel boundary below the half
		{[4]byte{128, 0, 128, 144}, 0, false},
		{[4]byte{0, 255, 127, 143}, 0, false}, // +32767.5
		{[4]byte{0, 0, 0, 144}, 0, false},
		{[4]byte{255, 255, 255, 255}, 0, false},
	} {
		if got, ok := Int16Single(c.raw); got != c.want || ok != c.ok {
			t.Fatalf("%x: got (%d,%v) want (%d,%v)", c.raw, got, ok, c.want, c.ok)
		}
	}
}
