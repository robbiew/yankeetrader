package qbmbf

import (
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"os"
	"testing"
)

func TestNativeSingleAdditionEntryState(t *testing.T) {
	data, err := os.ReadFile("testdata/native_add_entries.json")
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
	if doc.Format != "qb-native-add-entry-state-v1" || len(doc.Cases) != 184 {
		t.Fatal("fixed entry-state fixture coverage")
	}
	overflows := 0
	for _, c := range doc.Cases {
		t.Run(c.Name, func(t *testing.T) {
			left, right, fac := addRaw(t, c.Left), addRaw(t, c.Right), addRaw(t, c.FAC)
			if c.Op != 0x7f && c.Op != 0x83 {
				t.Fatal("qualified direct entry")
			}
			if c.Op == 0x83 && fac != right {
				t.Fatal("entry83 right operand must be the initial FAC")
			}
			trace, err := hex.DecodeString(c.Trace)
			if err != nil {
				t.Fatal(err)
			}
			digest := sha256.Sum256(trace)
			if hex.EncodeToString(digest[:]) != c.SHA || len(trace) < 21 || string(trace[:4]) != "ASE1" || binary.LittleEndian.Uint32(trace[4:8]) != c.Initial || string(trace[8:12]) != string(fac[:]) || string(trace[12:16]) != string(left[:]) || string(trace[16:20]) != string(right[:]) || trace[20] != 0 {
				t.Fatal("entry-specific initial FAC and operand provenance")
			}
			got, ok := AddSingleWithFAC(left, right, fac)
			if c.Output == nil {
				overflows++
				address := "00F6"
				if c.Op == 0x83 {
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
				t.Fatalf("op%x FAC%x: %x + %x got (%x,%v), native %x", c.Op, fac, left, right, got, ok, want)
			}
		})
	}
	if overflows != 8 {
		t.Fatal("native entry-specific overflow coverage")
	}
}

func TestMemoryAdditionKeepsIndependentFACOnCancellation(t *testing.T) {
	left, right := [4]byte{0, 0, 64, 129}, [4]byte{0, 0, 192, 129}
	for _, fac := range [][4]byte{{90, 165, 213, 146}, {0, 0, 0, 0}, {18, 52, 86, 0}, {1, 0, 128, 1}, {255, 255, 255, 255}} {
		want := fac
		want[3] = 0
		if got, ok := AddSingleWithFAC(left, right, fac); !ok || got != want {
			t.Fatalf("prior FAC %x: got (%x,%v), want %x", fac, got, ok, want)
		}
	}
}

func TestMemoryPlusFACMustNotSwapZeroOperands(t *testing.T) {
	left, fac := [4]byte{18, 52, 86, 0}, [4]byte{255, 255, 255, 0}
	got, ok := AddSingleWithFAC(left, fac, fac)
	if !ok || got != fac {
		t.Fatal("entry83 selects the right FAC zero encoding")
	}
	wrong, wrongOK := AddSingle(fac, left)
	if !wrongOK || wrong == got {
		t.Fatal("countercontrol must distinguish naive commutative mapping")
	}
}

func TestZeroOperandsDoNotSelectIndependentPriorFAC(t *testing.T) {
	left, right, prior := [4]byte{18, 52, 86, 0}, [4]byte{255, 255, 255, 0}, [4]byte{90, 165, 213, 146}
	if got, ok := AddSingleWithFAC(left, right, prior); !ok || got != right {
		t.Fatal("zero-operand fast path selects right, not prior FAC residue")
	}
}
