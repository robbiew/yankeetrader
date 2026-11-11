package qbmbf

import (
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"os"
	"testing"
)

type inline8dAddress struct {
	Name, Left, FAC                 string
	Magic, Base10, Base12, Resolved uint16
	Selector                        byte
	Initial                         uint32
	After                           string `json:"fac_after"`
	Trace                           string `json:"trace_hex"`
	SHA                             string `json:"source_trace_sha256"`
}
type inline8dExecution struct {
	Name, Left, FAC, Expect        string
	Op, Pad, Magic, Base10, Base12 uint16
	Selector                       byte
	Initial                        uint32
	Output                         *string
	Error                          *string
	Address                        *string `json:"error_address"`
	Trace                          string  `json:"trace_hex"`
	SHA                            string  `json:"source_trace_sha256"`
}

func inline8dTrace(t *testing.T, encoded, digest string) []byte {
	t.Helper()
	raw, err := hex.DecodeString(encoded)
	if err != nil {
		t.Fatal(err)
	}
	sum := sha256.Sum256(raw)
	if hex.EncodeToString(sum[:]) != digest {
		t.Fatal("raw native digest")
	}
	return raw
}
func TestNativeInlineDivision(t *testing.T) {
	data, err := os.ReadFile("testdata/native_inline_divide.json")
	if err != nil {
		t.Fatal(err)
	}
	var doc struct {
		Format     string
		Addresses  []inline8dAddress   `json:"address_cases"`
		Executions []inline8dExecution `json:"execution_cases"`
	}
	if err = json.Unmarshal(data, &doc); err != nil {
		t.Fatal(err)
	}
	if doc.Format != "qb-native-inline-divide-v1" || len(doc.Addresses) != 15 || len(doc.Executions) != 78 {
		t.Fatal("fixed profile coverage")
	}
	for _, c := range doc.Addresses {
		t.Run(c.Name, func(t *testing.T) {
			raw := inline8dTrace(t, c.Trace, c.SHA)
			if len(raw) != 57 || string(raw[:4]) != "ID8D" || string(raw[53:]) != "END!" {
				t.Fatal("complete resolver-only frame")
			}
			word := func(i int) uint16 { return binary.LittleEndian.Uint16(raw[i : i+2]) }
			offset := SingleAddInlineOffset(c.Selector, c.Magic, c.Base10, c.Base12)
			fac, left, after := addRaw(t, c.FAC), addRaw(t, c.Left), addRaw(t, c.After)
			if raw[17] != c.Selector || word(18) != c.Magic || word(20) != c.Base10 || word(22) != c.Base12 || offset != c.Resolved || word(32) != offset || word(34) != offset || word(36) != 0xbeef {
				t.Fatal("actual resolver fields and returned offsets")
			}
			if word(24) == 0 || word(24) != word(26) || word(28) != word(24)+0x500 || word(38) != word(24) || word(40) != word(26) || word(42) != word(30) {
				t.Fatal("declared synthetic frame and registers")
			}
			if fac != after || string(raw[8:12]) != string(fac[:]) || string(raw[12:16]) != string(left[:]) || string(raw[44:48]) != string(fac[:]) || binary.LittleEndian.Uint32(raw[4:8]) != c.Initial || binary.LittleEndian.Uint32(raw[48:52]) != c.Initial || raw[16] != 0 || raw[52] != 0 {
				t.Fatal("resolver-only FAC, RNG, mode and inputs")
			}
			// No division or unsafe operand dereference is attributed to this protocol.
		})
	}
	failures, returns := map[string]int{}, 0
	for _, c := range doc.Executions {
		t.Run(c.Name, func(t *testing.T) {
			raw := inline8dTrace(t, c.Trace, c.SHA)
			if len(raw) < 46 || string(raw[:4]) != "IOF1" {
				t.Fatal("complete pre-entry context")
			}
			word := func(i int) uint16 { return binary.LittleEndian.Uint16(raw[i : i+2]) }
			left, fac := addRaw(t, c.Left), addRaw(t, c.FAC)
			if c.Op != 0x8d || word(32) != c.Op || raw[17] != c.Selector || word(18) != c.Magic || word(20) != c.Base10 || word(22) != c.Base12 || binary.LittleEndian.Uint32(raw[4:8]) != c.Initial || string(raw[8:12]) != string(fac[:]) || string(raw[12:16]) != string(left[:]) || raw[16] != 0 {
				t.Fatal("actual inline8d operands and header context")
			}
			if word(24) == 0 || word(24) != word(26) || word(28) != word(24)+0x500 || word(34) != 0xa68 || word(36) != 0 || word(40) != 0 || word(44) < 40 || word(38) != word(44) || word(42)+6 != word(44) || word(30)+8+c.Pad != word(44) {
				t.Fatal("admitted bootstrap error context and padding")
			}
			got, err := DivideSingleWithFAC(left, fac, fac)
			if c.Output == nil {
				if c.Error == nil {
					t.Fatal("missing distinct native error")
				}
				failures[*c.Error]++
				wantErr, label := ErrSingleDivisionOverflow, "Overflow"
				if *c.Error == "division_by_zero" {
					wantErr, label = ErrSingleDivisionByZero, "Division by zero"
				} else if *c.Error != "overflow" {
					t.Fatal("unknown error")
				}
				address := "0194"
				if c.Pad != 0 {
					address = "0197"
				}
				message := "\r\n" + label + " in module YT-INIT  at address 01A3:" + address + "\r\n\r\nHit any key to return to system"
				if c.Expect != *c.Error || c.Address == nil || *c.Address != address || string(raw[46:]) != message || err != wantErr || got != [4]byte{} {
					t.Fatal("exact distinct fatal diagnostic and API rejection")
				}
				return
			}
			returns++
			want := addRaw(t, *c.Output)
			poison := addRaw(t, "00000081")
			if c.Expect != "return" || c.Address != nil || c.Error != nil || err != nil || got != want || len(raw) != 79 || string(raw[75:]) != "END!" {
				t.Fatal("finite raw quotient and framing")
			}
			if word(46) != SingleAddInlineOffset(c.Selector, c.Magic, c.Base10, c.Base12) || word(48) != 0x1a || word(50) != 0xbeef || word(52) != word(24) || word(54) != word(26) || word(56) != word(30) {
				t.Fatal("finite resolver/ABI registers")
			}
			if string(raw[58:62]) != string(want[:]) || binary.LittleEndian.Uint32(raw[62:66]) != c.Initial || raw[66] != 0 || string(raw[67:71]) != string(left[:]) || string(raw[71:75]) != string(poison[:]) {
				t.Fatal("finite FAC, memory, RNG and mode")
			}
		})
	}
	if failures["overflow"] != 10 || failures["division_by_zero"] != 14 || returns != 54 {
		t.Fatal("native finite/fatal matrix")
	}
}
