package qbmbf

import (
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"os"
	"testing"
)

func TestNativeDoubleIntFixPairs(t *testing.T) {
	data, err := os.ReadFile("testdata/native_int_fix_double.json")
	if err != nil {
		t.Fatal(err)
	}
	var fixture struct {
		Format  string
		Samples int `json:"samples_per_case"`
		Cases   []struct {
			Name, Operation string
			Initial         uint32
			Arguments       []string
			Trace           string `json:"trace_hex"`
			SHA             string `json:"source_trace_sha256"`
		}
	}
	if err = json.Unmarshal(data, &fixture); err != nil {
		t.Fatal(err)
	}
	if fixture.Format != "qb-native-int-fix-double-v1" || fixture.Samples != 64 || len(fixture.Cases) != 24 {
		t.Fatal("fixed native DOUBLE coverage")
	}
	for _, c := range fixture.Cases {
		t.Run(c.Name, func(t *testing.T) {
			trace, err := hex.DecodeString(c.Trace)
			if err != nil {
				t.Fatal(err)
			}
			digest := sha256.Sum256(trace)
			header := "DINT"
			operation := IntDouble
			if c.Operation == "fix" {
				header = "DFIX"
				operation = FixDouble
			} else if c.Operation != "int" {
				t.Fatal("unknown operation")
			}
			if len(trace) != 1292 || string(trace[:4]) != header || string(trace[1288:]) != "END!" || hex.EncodeToString(digest[:]) != c.SHA {
				t.Fatal("native identity/frame")
			}
			if binary.LittleEndian.Uint32(trace[4:8]) != c.Initial {
				t.Fatal("initial RNG state")
			}
			for i := 0; i < 64; i++ {
				at := 8 + 20*i
				var raw, want [8]byte
				copy(raw[:], trace[at:at+8])
				copy(want[:], trace[at+12:at+20])
				if hex.EncodeToString(raw[:]) != c.Arguments[i%len(c.Arguments)] || binary.LittleEndian.Uint32(trace[at+8:at+12]) != c.Initial {
					t.Fatal("input/RNG provenance")
				}
				if got := operation(raw); got != want {
					t.Fatalf("operation%d raw%x: %x != native%x", i, raw, got, want)
				}
			}
		})
	}
}

func TestDoublePrecisionBeyondFloat64(t *testing.T) {
	// 2^53 - .5 is exactly representable in MBF DOUBLE, but not IEEE float64.
	raw := [8]byte{252, 255, 255, 255, 255, 255, 127, 181}
	want := [8]byte{248, 255, 255, 255, 255, 255, 127, 181} // 2^53 - 1
	if IntDouble(raw) != want || FixDouble(raw) != want {
		t.Fatal("lost low significand bits")
	}
	raw[6] |= 128
	if FixDouble(raw) != [8]byte{248, 255, 255, 255, 255, 255, 255, 181} {
		t.Fatal("negative truncation precision")
	}
	if IntDouble(raw) != [8]byte{0, 0, 0, 0, 0, 0, 128, 182} {
		t.Fatal("negative floor carry")
	}
}

func TestDoubleZerosSubunitsAndIntegralExtremes(t *testing.T) {
	for _, raw := range [][8]byte{{}, {255, 255, 255, 255, 255, 255, 255, 0}, {18, 52, 86, 120, 154, 188, 222, 0}, {255, 255, 255, 255, 255, 255, 255, 255}, {1, 0, 0, 0, 0, 0, 0, 184}} {
		if IntDouble(raw) != raw || FixDouble(raw) != raw {
			t.Fatal("raw zero or integral extreme normalized")
		}
	}
	raw := [8]byte{0, 0, 0, 0, 0, 0, 192, 128}
	if FixDouble(raw) != [8]byte{0, 0, 0, 0, 0, 0, 192, 0} {
		t.Fatal("negative zero residue")
	}
	if IntDouble(raw) != [8]byte{0, 0, 0, 0, 0, 0, 128, 129} {
		t.Fatal("negative subunit floor")
	}
}
