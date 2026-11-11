package qbmbf

import (
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"os"
	"testing"
)

func TestNativeSingleMultiplicationEntryState(t *testing.T) {
	data, err := os.ReadFile("testdata/native_multiply_single.json")
	if err != nil {
		t.Fatal(err)
	}
	var doc struct {
		Format string
		Cases  []struct {
			Name, Left, Right, FAC string
			Op                     int
			Initial                uint32
			Output                 *string
			Trace                  string `json:"trace_hex"`
			SHA                    string `json:"source_trace_sha256"`
		}
	}
	if err = json.Unmarshal(data, &doc); err != nil {
		t.Fatal(err)
	}
	if doc.Format != "qb-native-multiply-single-v1" || len(doc.Cases) != 115 {
		t.Fatal("fixed entry-state fixture coverage")
	}
	overflows := 0
	for _, c := range doc.Cases {
		t.Run(c.Name, func(t *testing.T) {
			left, right, fac := addRaw(t, c.Left), addRaw(t, c.Right), addRaw(t, c.FAC)
			if c.Op != 0x8f && c.Op != 0x91 && c.Op != 0x93 {
				t.Fatal("qualified direct entry")
			}
			if c.Op == 0x93 && fac != right {
				t.Fatal("entry93 right operand must be the initial FAC")
			}
			trace, err := hex.DecodeString(c.Trace)
			if err != nil {
				t.Fatal(err)
			}
			digest := sha256.Sum256(trace)
			if hex.EncodeToString(digest[:]) != c.SHA || len(trace) < 21 || string(trace[:4]) != "MUL1" || binary.LittleEndian.Uint32(trace[4:8]) != c.Initial || string(trace[8:12]) != string(fac[:]) || string(trace[12:16]) != string(left[:]) || string(trace[16:20]) != string(right[:]) || trace[20] != 0 {
				t.Fatal("entry-specific initial FAC and operand provenance")
			}
			if c.Op == 0x91 && fac != left {
				t.Fatal("entry91 left operand must be initial FAC")
			}
			got, ok := MultiplySingleWithFAC(left, right, fac)
			if c.Op == 0x91 {
				direct, directOK := MultiplySingle(left, right)
				if direct != got || directOK != ok {
					t.Fatal("FAC-times-memory adapter")
				}
			}
			if c.Output == nil {
				overflows++
				address := "00F6"
				if c.Op == 0x93 {
					address = "00F3"
				}
				message := "\r\nOverflow in module YT-INIT  at address 01A3:" + address + "\r\n\r\nHit any key to return to system"
				if string(trace[21:]) != message || ok || got != [4]byte{} {
					t.Fatalf("overflow got (%x,%v)", got, ok)
				}
				return
			}
			want := addRaw(t, *c.Output)
			if len(trace) != 42 || string(trace[38:]) != "END!" || string(trace[21:25]) != string(want[:]) || string(trace[25:29]) != string(left[:]) || string(trace[29:33]) != string(right[:]) || binary.LittleEndian.Uint32(trace[33:37]) != c.Initial || trace[37] != 0 {
				t.Fatal("complete result, readonly memory blocks, RNG and mode")
			}
			if !ok || got != want {
				t.Fatalf("op%x FAC%x: %x * %x got (%x,%v), native %x", c.Op, fac, left, right, got, ok, want)
			}
		})
	}
	if overflows != 9 {
		t.Fatal("native entry-specific overflow coverage")
	}
}

// The native zero exit precedes rounding: this product is just below the MBF
// minimum normal and would round up into range if rounding were performed first.
func TestMultiplySingleFlushesBeforeRounding(t *testing.T) {
	left, right := addRaw(t, "01000040"), addRaw(t, "feff7f41")
	want := addRaw(t, "01000000")
	if got, ok := MultiplySingle(left, right); !ok || got != want {
		t.Fatalf("got %x,%v; native %x", got, ok, want)
	}
	fac := addRaw(t, "5aa5d592")
	want = addRaw(t, "5aa5d500")
	if got, ok := MultiplySingleWithFAC(left, right, fac); !ok || got != want {
		t.Fatalf("independent FAC got %x,%v; native %x", got, ok, want)
	}
}
