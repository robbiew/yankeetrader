package qbmbf

import (
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"os"
	"testing"
)

func TestNativeDoubleMultiplicationEntries(t *testing.T) {
	data, err := os.ReadFile("testdata/native_multiply_double.json")
	if err != nil {
		t.Fatal(err)
	}
	var doc struct {
		Format string
		Cases  []struct {
			Name, Left, Right, FAC string
			Op                     byte
			Initial                uint32
			Output                 *string
			Trace                  string `json:"trace_hex"`
			SHA                    string `json:"source_trace_sha256"`
		}
	}
	if err = json.Unmarshal(data, &doc); err != nil {
		t.Fatal(err)
	}
	if doc.Format != "qb-native-multiply-double-v1" || len(doc.Cases) != 118 {
		t.Fatal("fixed native coverage")
	}
	errors := 0
	entries := map[byte]int{}
	for _, c := range doc.Cases {
		t.Run(c.Name, func(t *testing.T) {
			left, right, fac := addDoubleRaw(t, c.Left), addDoubleRaw(t, c.Right), addDoubleRaw(t, c.FAC)
			if c.Op != 0x90 && c.Op != 0x92 && c.Op != 0x94 {
				t.Fatal("qualified direct DOUBLE entry")
			}
			entries[c.Op]++
			if c.Op == 0x92 && fac != left || c.Op == 0x94 && fac != right {
				t.Fatal("entry-specific FAC operand binding")
			}
			raw, err := hex.DecodeString(c.Trace)
			if err != nil {
				t.Fatal(err)
			}
			digest := sha256.Sum256(raw)
			if hex.EncodeToString(digest[:]) != c.SHA || len(raw) < 33 || string(raw[:4]) != "DMP1" || binary.LittleEndian.Uint32(raw[4:8]) != c.Initial || string(raw[8:16]) != string(fac[:]) || string(raw[16:24]) != string(left[:]) || string(raw[24:32]) != string(right[:]) || raw[32] != 0 {
				t.Fatal("full raw input/FAC, RNG and default-mode provenance")
			}
			got, ok := MultiplyDoubleWithFAC(left, right, fac)
			if c.Op == 0x92 {
				direct, directOK := MultiplyDouble(left, right)
				if got != direct || ok != directOK {
					t.Fatal("FAC-times-memory adapter")
				}
			}
			if c.Output == nil {
				errors++
				at := "011A"
				if c.Op == 0x94 {
					at = "0117"
				}
				message := "\r\nOverflow in module YT-INIT  at address 01A3:" + at + "\r\n\r\nHit any key to return to system"
				if string(raw[33:]) != message || ok || got != [8]byte{} {
					t.Fatal("exact native error and API rejection, no post-error FAC claim")
				}
				return
			}
			want := addDoubleRaw(t, *c.Output)
			if len(raw) != 66 || string(raw[62:]) != "END!" || string(raw[33:41]) != string(want[:]) || string(raw[41:49]) != string(left[:]) || string(raw[49:57]) != string(right[:]) || binary.LittleEndian.Uint32(raw[57:61]) != c.Initial || raw[61] != 0 {
				t.Fatal("complete result, readonly memory blocks, RNG and mode")
			}
			if !ok || got != want {
				t.Fatalf("op%x FAC%x: %x*%x got(%x,%v), native %x", c.Op, fac, left, right, got, ok, want)
			}
		})
	}
	if errors != 7 || entries[0x90] != 34 || entries[0x92] != 66 || entries[0x94] != 18 {
		t.Fatal("native entry/error coverage")
	}
}

func TestDoubleMultiplicationPreRoundUnderflow(t *testing.T) {
	left := addDoubleRaw(t, "0100000000000040")
	right := addDoubleRaw(t, "feffffffffff7f41")
	fac := addDoubleRaw(t, "5aa5d5c33c918092")
	want := fac
	want[7] = 0
	if got, ok := MultiplyDoubleWithFAC(left, right, fac); !ok || got != want {
		t.Fatalf("pre-round underflow got %x,%v, native %x", got, ok, want)
	}
}
func TestDoubleMultiplicationLowBitTie(t *testing.T) {
	left := addDoubleRaw(t, "0000000000004081")
	right := addDoubleRaw(t, "0100000000000081")
	want := addDoubleRaw(t, "0200000000004081")
	if got, ok := MultiplyDouble(left, right); !ok || got != want {
		t.Fatalf("full-width odd tie got %x,%v, native %x", got, ok, want)
	}
}
