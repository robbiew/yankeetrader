package qbmbf

import (
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"math"
	"os"
	"testing"
)

func TestNativeInt16Double(t *testing.T) {
	data, err := os.ReadFile("testdata/native_int16_double.json")
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
	if doc.Format != "qb-native-int16-double-v1" || len(doc.Cases) != 104 {
		t.Fatal("native fixture coverage")
	}
	overflows := 0
	for _, c := range doc.Cases {
		t.Run(c.Name, func(t *testing.T) {
			raw, err := hex.DecodeString(c.Raw)
			if err != nil || len(raw) != 8 {
				t.Fatal("raw DOUBLE input")
			}
			trace, err := hex.DecodeString(c.Trace)
			if err != nil {
				t.Fatal(err)
			}
			digest := sha256.Sum256(trace)
			if hex.EncodeToString(digest[:]) != c.SHA || len(trace) < 17 || string(trace[:4]) != "D16!" || binary.LittleEndian.Uint32(trace[4:8]) != c.Initial || string(trace[8:16]) != string(raw) || trace[16] != 0 {
				t.Fatal("native input/mode provenance")
			}
			if c.Op != 0x76 && c.Op != 0x78 {
				t.Fatal("native entry")
			}
			got, ok := Int16Double([8]byte(raw))
			if c.Value == nil {
				overflows++
				address := "00CD"
				if c.Op == 0x78 {
					address = "00CA"
				}
				want := "\r\nOverflow in module YT-INIT  at address 01A3:" + address + "\r\n\r\nHit any key to return to system"
				if string(trace[17:]) != want || ok || got != 0 {
					t.Fatalf("overflow got (%d,%v)", got, ok)
				}
				return
			}
			if len(trace) != 36 || string(trace[32:]) != "END!" {
				t.Fatal("successful native framing")
			}
			native := int16(binary.LittleEndian.Uint16(trace[17:19]))
			if native != *c.Value || !ok || got != native {
				t.Fatalf("raw %x: got (%d,%v), native %d", raw, got, ok, native)
			}
			if string(trace[19:23]) != string(raw[:4]) || string(trace[23:25]) != string(trace[17:19]) || string(trace[25:27]) != string(raw[6:]) || binary.LittleEndian.Uint32(trace[27:31]) != c.Initial || trace[31] != 0 {
				t.Fatal("native FAC residue/RNG/mode")
			}
		})
	}
	if overflows != 30 {
		t.Fatal("native overflow coverage")
	}
}

func TestInt16DoubleRetainsPrecisionBeforeRounding(t *testing.T) {
	// These exact MBF encodings lie one native ULP below a rounding tie.
	// float64 demotion first rounds them to the tie and changes the result.
	for _, c := range []struct {
		hex  string
		want int16
	}{
		{"ffffffffffff1f82", 2},
		{"ffffffffffff9f82", -2},
		{"fffffffffffe7f8f", 32767},
		{"ffffffff7f008090", -32768},
	} {
		bytes, err := hex.DecodeString(c.hex)
		if err != nil {
			t.Fatal(err)
		}
		raw := [8]byte(bytes)
		got, ok := Int16Double(raw)
		if !ok || got != c.want {
			t.Fatalf("%x: got (%d,%v), want %d", raw, got, ok, c.want)
		}
		significand := doubleBits(raw)&((uint64(1)<<55)-1) | uint64(1)<<55
		lossy := math.Ldexp(float64(significand), int(raw[7])-184)
		if raw[6]&128 != 0 {
			lossy = -lossy
		}
		if math.Round(lossy) == float64(c.want) {
			t.Fatal("countercontrol does not distinguish float64 demotion")
		}
	}
}

func TestInt16DoubleZeroAliasesAndBoundaries(t *testing.T) {
	for exponent := 0; exponent < 128; exponent++ {
		for _, sign := range []byte{0, 128} {
			raw := [8]byte{255, 255, 255, 255, 255, 255, 127 | sign, byte(exponent)}
			if got, ok := Int16Double(raw); !ok || got != 0 {
				t.Fatalf("%x: %d %v", raw, got, ok)
			}
		}
	}
	for _, c := range []struct {
		raw  [8]byte
		want int16
		ok   bool
	}{
		{[8]byte{0, 0, 0, 0, 0, 0, 32, 130}, 3, true},
		{[8]byte{0, 0, 0, 0, 0, 0, 160, 130}, -3, true},
		{[8]byte{0, 0, 0, 0, 0, 0, 128, 144}, -32768, true},
		{[8]byte{0, 0, 0, 0, 128, 0, 128, 144}, 0, false},
		{[8]byte{0, 0, 0, 0, 0, 255, 127, 143}, 0, false},
		{[8]byte{255, 255, 255, 255, 255, 255, 255, 255}, 0, false},
	} {
		if got, ok := Int16Double(c.raw); got != c.want || ok != c.ok {
			t.Fatalf("%x: got (%d,%v), want (%d,%v)", c.raw, got, ok, c.want, c.ok)
		}
	}
}
