package qbmbf

import (
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"os"
	"testing"
)

type inline8eAddress struct {
	Name, Left, FAC                 string
	Magic, Base10, Base12, Resolved uint16
	Selector                        byte
	Initial                         uint32
	After                           string `json:"fac_after"`
	Trace                           string `json:"trace_hex"`
	SHA                             string `json:"source_trace_sha256"`
}
type inline8eExecution struct {
	Name, Left, FAC, Expect        string
	Op, Pad, Magic, Base10, Base12 uint16
	Selector                       byte
	Initial                        uint32
	Output                         *string
	Address                        *string `json:"error_address"`
	Trace                          string  `json:"trace_hex"`
	SHA                            string  `json:"source_trace_sha256"`
}

func inline8eTrace(t *testing.T, encoded, digest string) []byte {
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
func TestNativeInlineDoubleDivision(t *testing.T) {
	data, err := os.ReadFile("testdata/native_inline_divide_double.json")
	if err != nil {
		t.Fatal(err)
	}
	var doc struct {
		Format     string
		Addresses  []inline8eAddress   `json:"address_cases"`
		Executions []inline8eExecution `json:"execution_cases"`
	}
	if err = json.Unmarshal(data, &doc); err != nil {
		t.Fatal(err)
	}
	if doc.Format != "qb-native-inline-divide-double-v1" || len(doc.Addresses) != 15 || len(doc.Executions) != 148 {
		t.Fatal("fixed profile coverage")
	}
	for _, c := range doc.Addresses {
		t.Run(c.Name, func(t *testing.T) {
			raw := inline8eTrace(t, c.Trace, c.SHA)
			if len(raw) != 69 || string(raw[:4]) != "DV8E" || string(raw[65:]) != "END!" {
				t.Fatal("complete eight-byte resolver-only frame")
			}
			word := func(i int) uint16 { return binary.LittleEndian.Uint16(raw[i : i+2]) }
			fac, left, after := addDoubleRaw(t, c.FAC), addDoubleRaw(t, c.Left), addDoubleRaw(t, c.After)
			off := SingleAddInlineOffset(c.Selector, c.Magic, c.Base10, c.Base12)
			if raw[25] != c.Selector || word(26) != c.Magic || word(28) != c.Base10 || word(30) != c.Base12 || off != c.Resolved || word(40) != off || word(42) != off || word(44) != 0xbeef {
				t.Fatal("actual eight-byte profile resolver fields")
			}
			if word(32) == 0 || word(32) != word(34) || word(36) != word(32)+0x500 || word(46) != word(32) || word(48) != word(34) || word(50) != word(38) {
				t.Fatal("declared resolver-only frame/register context")
			}
			if fac != after || string(raw[8:16]) != string(fac[:]) || string(raw[16:24]) != string(left[:]) || string(raw[52:60]) != string(fac[:]) || binary.LittleEndian.Uint32(raw[4:8]) != c.Initial || binary.LittleEndian.Uint32(raw[60:64]) != c.Initial || raw[24] != 0 || raw[64] != 0 {
				t.Fatal("all eight FAC bytes, inputs, RNG and mode preserved")
			}
			// This protocol computes offsets without operand reads or arithmetic.
		})
	}

	errors, zeroErrors, returns := 0, 0, 0
	for _, c := range doc.Executions {
		t.Run(c.Name, func(t *testing.T) {
			raw := inline8eTrace(t, c.Trace, c.SHA)
			if len(raw) < 54 || string(raw[:4]) != "DVF1" {
				t.Fatal("complete DOUBLE pre-entry protocol")
			}
			word := func(i int) uint16 { return binary.LittleEndian.Uint16(raw[i : i+2]) }
			left, fac := addDoubleRaw(t, c.Left), addDoubleRaw(t, c.FAC)
			if c.Op != 0x8e || word(40) != c.Op || raw[25] != c.Selector || word(26) != c.Magic || word(28) != c.Base10 || word(30) != c.Base12 || binary.LittleEndian.Uint32(raw[4:8]) != c.Initial || string(raw[8:16]) != string(fac[:]) || string(raw[16:24]) != string(left[:]) || raw[24] != 0 {
				t.Fatal("actual inline8e inputs and header context")
			}
			if word(32) == 0 || word(32) != word(34) || word(36) != word(32)+0x500 || word(42) != 0xa68 || word(44) != 0 || word(48) != 0 || word(52) < 40 || word(46) != word(52) || word(50)+6 != word(52) || word(38)+8+c.Pad != word(52) {
				t.Fatal("declared baseline/padded original error context")
			}
			got, divideErr := DivideDoubleWithFAC(left, fac, fac)
			if c.Output == nil {
				errors++
				at := "01C4"
				if c.Pad != 0 {
					at = "01C7"
				}
				label, wantErr := "Overflow", ErrDoubleDivisionOverflow
				if c.Expect == "division_by_zero" {
					label, wantErr = "Division by zero", ErrDoubleDivisionByZero
					zeroErrors++
				} else if c.Expect != "overflow" {
					t.Fatal("distinct error classification")
				}
				message := "\r\n" + label + " in module YT-INIT  at address 01A3:" + at + "\r\n\r\nHit any key to return to system"
				if c.Address == nil || *c.Address != at || string(raw[54:]) != message || divideErr != wantErr || got != [8]byte{} {
					t.Fatal("exact native error and API rejection; no post-error FAC claim")
				}
				return
			}
			returns++
			want := addDoubleRaw(t, *c.Output)
			if c.Expect != "return" || c.Address != nil || divideErr != nil || got != want || len(raw) != 99 || string(raw[95:]) != "END!" {
				t.Fatal("complete finite DOUBLE output")
			}
			off := SingleAddInlineOffset(c.Selector, c.Magic, c.Base10, c.Base12)
			altMagic := uint16(0x7a62)
			if c.Magic == 0x7a62 {
				altMagic = 0x6d62
			}
			if off > 65528 || SingleAddInlineOffset(c.Selector, altMagic, c.Base10, c.Base12) > 65528 {
				t.Fatal("safe full eight-byte spans")
			}
			if word(54) != off || word(56) != 0x16 || word(58) != 0xbeef || word(60) != word(32) || word(62) != word(34) || word(64) != word(38) {
				t.Fatal("resolved DOUBLE FAC and preserved registers")
			}
			poison := addDoubleRaw(t, "0000000000000081")
			if left == poison {
				poison = addDoubleRaw(t, "0000000000000082")
			}
			if string(raw[66:74]) != string(want[:]) || binary.LittleEndian.Uint32(raw[74:78]) != c.Initial || raw[78] != 0 || string(raw[79:87]) != string(left[:]) || string(raw[87:95]) != string(poison[:]) {
				t.Fatal("all raw result/readonly operand/RNG/mode bytes")
			}
		})
	}
	if errors != 28 || zeroErrors != 18 || returns != 120 {
		t.Fatal("fixed full execution outcomes")
	}
}
