package qbmbf

import (
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"os"
	"testing"
)

func TestNativeInlineOverflowContext(t *testing.T) {
	data, err := os.ReadFile("testdata/native_inline_overflow.json")
	if err != nil {
		t.Fatal(err)
	}
	var doc struct {
		Format string
		Cases  []struct {
			Name, Left, FAC, Expect        string
			Op, Pad, Magic, Base10, Base12 uint16
			Selector                       byte
			Initial                        uint32
			Output                         *string
			Address                        *string `json:"error_address"`
			Trace                          string  `json:"trace_hex"`
			SHA                            string  `json:"source_trace_sha256"`
		}
	}
	if err = json.Unmarshal(data, &doc); err != nil {
		t.Fatal(err)
	}
	if doc.Format != "qb-native-inline-overflow-v1" || len(doc.Cases) != 20 {
		t.Fatal("fixed native context coverage")
	}
	errors, returns := 0, 0
	for _, c := range doc.Cases {
		t.Run(c.Name, func(t *testing.T) {
			raw, e := hex.DecodeString(c.Trace)
			if e != nil {
				t.Fatal(e)
			}
			digest := sha256.Sum256(raw)
			if hex.EncodeToString(digest[:]) != c.SHA || len(raw) < 46 || string(raw[:4]) != "IOF1" {
				t.Fatal("complete pre-entry frame and raw digest")
			}
			word := func(i int) uint16 { return binary.LittleEndian.Uint16(raw[i : i+2]) }
			left, fac := addRaw(t, c.Left), addRaw(t, c.FAC)
			if string(raw[8:12]) != string(fac[:]) || string(raw[12:16]) != string(left[:]) || binary.LittleEndian.Uint32(raw[4:8]) != c.Initial || raw[16] != 0 || raw[17] != c.Selector || word(18) != c.Magic || word(20) != c.Base10 || word(22) != c.Base12 {
				t.Fatal("actual operation inputs and metadata")
			}
			if word(24) == 0 || word(24) != word(26) || word(28) != word(24)+0x500 || word(32) != c.Op || word(34) != 0xa68 || word(36) != 0 || word(40) != 0 || word(44) < 40 || word(38) != word(44) || word(42)+6 != word(44) || word(30)+8+c.Pad != word(44) {
				t.Fatal("admitted bootstrap error route and frame depth")
			}
			var got [4]byte
			var ok bool
			switch c.Op {
			case 0x85:
				got, ok = AddSingleWithFAC(left, fac, fac)
			case 0x9d:
				got, ok = SubtractSingleWithFAC(left, fac, fac)
			default:
				t.Fatal("qualified inline operation")
			}
			if c.Output == nil {
				errors++
				address := "0194"
				if c.Pad != 0 {
					address = "0197"
				}
				message := "\r\nOverflow in module YT-INIT  at address 01A3:" + address + "\r\n\r\nHit any key to return to system"
				if c.Expect != "overflow" || c.Address == nil || *c.Address != address || string(raw[46:]) != message || ok {
					t.Fatal("exact fatal result and API overflow rejection")
				}
				// No result register or operand/RNG preservation is inferred after a fatal exit.
				return
			}
			returns++
			want := addRaw(t, *c.Output)
			poison := addRaw(t, "00000081")
			if c.Expect != "return" || c.Address != nil || !ok || got != want || len(raw) != 79 || string(raw[75:]) != "END!" {
				t.Fatal("complete finite control and arithmetic")
			}
			if word(46) != SingleAddInlineOffset(c.Selector, c.Magic, c.Base10, c.Base12) || word(48) != 0x1a || word(50) != 0xbeef || word(52) != word(24) || word(54) != word(26) || word(56) != word(30) {
				t.Fatal("finite return registers")
			}
			if string(raw[58:62]) != string(want[:]) || binary.LittleEndian.Uint32(raw[62:66]) != c.Initial || raw[66] != 0 || string(raw[67:71]) != string(left[:]) || string(raw[71:75]) != string(poison[:]) {
				t.Fatal("finite FAC, RNG, mode and readonly operands")
			}
		})
	}
	if errors != 12 || returns != 8 {
		t.Fatal("fatal and finite native coverage")
	}
}
