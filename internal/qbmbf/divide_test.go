package qbmbf

import (
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"os"
	"testing"
)

func TestNativeSingleDivisionEntryState(t *testing.T) {
	data, err := os.ReadFile("testdata/native_divide_single.json")
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
			Error                  *string
			Trace                  string `json:"trace_hex"`
			SHA                    string `json:"source_trace_sha256"`
		}
	}
	if err = json.Unmarshal(data, &doc); err != nil {
		t.Fatal(err)
	}
	if doc.Format != "qb-native-divide-single-v1" || len(doc.Cases) != 105 {
		t.Fatal("fixed entry-state fixture coverage")
	}
	failures := map[string]int{}
	for _, c := range doc.Cases {
		t.Run(c.Name, func(t *testing.T) {
			left, right, fac := addRaw(t, c.Left), addRaw(t, c.Right), addRaw(t, c.FAC)
			if c.Op != 0x87 && c.Op != 0x89 && c.Op != 0x8b {
				t.Fatal("qualified direct entry")
			}
			if c.Op == 0x8b && fac != right {
				t.Fatal("entry8b right operand must be the initial FAC")
			}
			trace, err := hex.DecodeString(c.Trace)
			if err != nil {
				t.Fatal(err)
			}
			digest := sha256.Sum256(trace)
			if hex.EncodeToString(digest[:]) != c.SHA || len(trace) < 21 || string(trace[:4]) != "DIV1" || binary.LittleEndian.Uint32(trace[4:8]) != c.Initial || string(trace[8:12]) != string(fac[:]) || string(trace[12:16]) != string(left[:]) || string(trace[16:20]) != string(right[:]) || trace[20] != 0 {
				t.Fatal("entry-specific initial FAC and operand provenance")
			}
			if c.Op == 0x89 && fac != left {
				t.Fatal("entry89 left operand must be initial FAC")
			}
			got, err := DivideSingleWithFAC(left, right, fac)
			if c.Op == 0x89 {
				direct, directErr := DivideSingle(left, right)
				if direct != got || directErr != err {
					t.Fatal("FAC-divided-by-memory adapter")
				}
			}
			if c.Output == nil {
				if c.Error == nil {
					t.Fatal("missing native error classification")
				}
				failures[*c.Error]++
				wantErr := ErrSingleDivisionOverflow
				label := "Overflow"
				if *c.Error == "division_by_zero" {
					wantErr = ErrSingleDivisionByZero
					label = "Division by zero"
				} else if *c.Error != "overflow" {
					t.Fatal("unknown native error")
				}
				address := "00F6"
				if c.Op == 0x8b {
					address = "00F3"
				}
				message := "\r\n" + label + " in module YT-INIT  at address 01A3:" + address + "\r\n\r\nHit any key to return to system"
				if string(trace[21:]) != message || err != wantErr || got != [4]byte{} {
					t.Fatalf("division error got (%x,%v)", got, err)
				}
				return
			}
			want := addRaw(t, *c.Output)
			if len(trace) != 42 || string(trace[38:]) != "END!" || string(trace[21:25]) != string(want[:]) || string(trace[25:29]) != string(left[:]) || string(trace[29:33]) != string(right[:]) || binary.LittleEndian.Uint32(trace[33:37]) != c.Initial || trace[37] != 0 {
				t.Fatal("complete result, readonly memory blocks, RNG and mode")
			}
			if c.Error != nil || err != nil || got != want {
				t.Fatalf("op%x FAC%x: %x / %x got (%x,%v), native %x", c.Op, fac, left, right, got, err, want)
			}
		})
	}
	if failures["division_by_zero"] != 16 || failures["overflow"] != 14 {
		t.Fatal("native entry-specific error coverage")
	}
}
