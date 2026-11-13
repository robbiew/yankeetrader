package qbmbf

import (
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"os"
	"testing"
)

func TestNativeDoubleDivisionEntries(t *testing.T) {
	data, err := os.ReadFile("testdata/native_divide_double.json")
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
			Error                  string
			Trace                  string `json:"trace_hex"`
			SHA                    string `json:"source_trace_sha256"`
		}
	}
	if err = json.Unmarshal(data, &doc); err != nil {
		t.Fatal(err)
	}
	if doc.Format != "qb-native-divide-double-v1" || len(doc.Cases) != 178 {
		t.Fatal("fixed native coverage")
	}
	errors, zeroErrors := 0, 0
	entries := map[byte]int{}
	for _, c := range doc.Cases {
		t.Run(c.Name, func(t *testing.T) {
			left, right, fac := addDoubleRaw(t, c.Left), addDoubleRaw(t, c.Right), addDoubleRaw(t, c.FAC)
			if c.Op != 0x88 && c.Op != 0x8a && c.Op != 0x8c {
				t.Fatal("qualified direct DOUBLE entry")
			}
			entries[c.Op]++
			if c.Op == 0x8a && fac != left || c.Op == 0x8c && fac != right {
				t.Fatal("entry-specific FAC operand binding")
			}
			raw, err := hex.DecodeString(c.Trace)
			if err != nil {
				t.Fatal(err)
			}
			digest := sha256.Sum256(raw)
			if hex.EncodeToString(digest[:]) != c.SHA || len(raw) < 33 || string(raw[:4]) != "DDP1" || binary.LittleEndian.Uint32(raw[4:8]) != c.Initial || string(raw[8:16]) != string(fac[:]) || string(raw[16:24]) != string(left[:]) || string(raw[24:32]) != string(right[:]) || raw[32] != 0 {
				t.Fatal("full raw input/FAC, RNG and default-mode provenance")
			}
			got, divideErr := DivideDoubleWithFAC(left, right, fac)
			if c.Op == 0x8a {
				direct, directErr := DivideDouble(left, right)
				if got != direct || divideErr != directErr {
					t.Fatal("FAC-divided-by-memory adapter")
				}
			}
			if c.Output == nil {
				errors++
				at := "011A"
				if c.Op == 0x8c {
					at = "0117"
				}
				label, wantErr := "Overflow", ErrDoubleDivisionOverflow
				if c.Error == "division_by_zero" {
					label, wantErr = "Division by zero", ErrDoubleDivisionByZero
					zeroErrors++
				} else if c.Error != "overflow" {
					t.Fatal("distinct error classification")
				}
				message := "\r\n" + label + " in module YT-INIT  at address 01A3:" + at + "\r\n\r\nHit any key to return to system"
				if string(raw[33:]) != message || divideErr != wantErr || got != [8]byte{} {
					t.Fatal("exact native error and API rejection, no post-error FAC claim")
				}
				return
			}
			want := addDoubleRaw(t, *c.Output)
			if len(raw) != 66 || string(raw[62:]) != "END!" || string(raw[33:41]) != string(want[:]) || string(raw[41:49]) != string(left[:]) || string(raw[49:57]) != string(right[:]) || binary.LittleEndian.Uint32(raw[57:61]) != c.Initial || raw[61] != 0 {
				t.Fatal("complete result, readonly memory blocks, RNG and mode")
			}
			if divideErr != nil || c.Error != "" || got != want {
				t.Fatalf("op%x FAC%x: %x/%x got(%x,%v), native %x", c.Op, fac, left, right, got, divideErr, want)
			}
		})
	}
	if errors != 28 || zeroErrors != 16 || entries[0x88] != 49 || entries[0x8a] != 100 || entries[0x8c] != 29 {
		t.Fatal("native entry/error coverage")
	}
}

func TestDoubleDivisionZeroDivisorPrecedence(t *testing.T) {
	for _, left := range [][8]byte{{}, addDoubleRaw(t, "123456789abcde00"), addDoubleRaw(t, "ffffffffffff7fff")} {
		got, err := DivideDouble(left, addDoubleRaw(t, "ffffffffffffff00"))
		if err != ErrDoubleDivisionByZero || got != [8]byte{} {
			t.Fatalf("zero divisor priority got %x,%v", got, err)
		}
	}
}

func TestDoubleDivisionLateUnderflowResidue(t *testing.T) {
	left := addDoubleRaw(t, "0000000000000001")
	right := addDoubleRaw(t, "cdab896745230181")
	fac := addDoubleRaw(t, "5aa5d5c33c918092")
	want := addDoubleRaw(t, "00cdab8967452300")
	if got, err := DivideDoubleWithFAC(left, right, fac); err != nil || got != want {
		t.Fatalf("late underflow got %x,%v, native %x", got, err, want)
	}
	right[7]++
	want = fac
	want[7] = 0
	if got, err := DivideDoubleWithFAC(left, right, fac); err != nil || got != want {
		t.Fatalf("early underflow got %x,%v, native %x", got, err, want)
	}
}
