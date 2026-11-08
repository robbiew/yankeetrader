package qbmbf

import (
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"os"
	"testing"
)

func TestNativeSINGLEIntPairs(t *testing.T) {
	data, err := os.ReadFile("testdata/native_int_single.json")
	if err != nil {
		t.Fatal(err)
	}
	var fixture struct {
		Format  string
		Samples int `json:"samples_per_case"`
		Cases   []struct {
			Name      string
			Initial   uint32
			Arguments []string
			Trace     string `json:"trace_hex"`
			SHA       string `json:"source_trace_sha256"`
		}
	}
	if err = json.Unmarshal(data, &fixture); err != nil {
		t.Fatal(err)
	}
	if fixture.Format != "qb-native-int-single-v1" || fixture.Samples != 64 || len(fixture.Cases) != 16 {
		t.Fatal("fixed native fixture coverage")
	}
	for _, c := range fixture.Cases {
		t.Run(c.Name, func(t *testing.T) {
			trace, err := hex.DecodeString(c.Trace)
			if err != nil {
				t.Fatal(err)
			}
			digest := sha256.Sum256(trace)
			if len(trace) != 780 || string(trace[:4]) != "INT2" || string(trace[776:]) != "END!" || hex.EncodeToString(digest[:]) != c.SHA {
				t.Fatal("native trace identity")
			}
			if binary.LittleEndian.Uint32(trace[4:8]) != c.Initial {
				t.Fatal("initial RNG state")
			}
			for i := 0; i < 64; i++ {
				at := 8 + 12*i
				var raw, want [4]byte
				copy(raw[:], trace[at:at+4])
				copy(want[:], trace[at+8:at+12])
				if hex.EncodeToString(raw[:]) != c.Arguments[i%len(c.Arguments)] || binary.LittleEndian.Uint32(trace[at+4:at+8]) != c.Initial {
					t.Fatal("native operation/RNG provenance")
				}
				if got := IntSingle(raw); got != want {
					t.Fatalf("operation%d raw%x: got%x native%x", i, raw, got, want)
				}
			}
		})
	}
}

func TestIntSingleRawZerosAndResidues(t *testing.T) {
	for _, raw := range [][4]byte{{}, {255, 255, 127, 0}, {255, 255, 255, 0}, {18, 52, 86, 0}} {
		if IntSingle(raw) != raw {
			t.Fatal("zero alias normalized")
		}
	}
	raw := [4]byte{255, 255, 127, 128}
	if got := IntSingle(raw); got != [4]byte{255, 255, 127, 0} {
		t.Fatalf("positive subunit residue %x", got)
	}
	raw = [4]byte{0, 0, 128, 128}
	if got := IntSingle(raw); got != [4]byte{0, 0, 128, 129} {
		t.Fatalf("negative half must floor to -1: %x", got)
	}
}

func TestIntSingleNegativeCarryAndIntegralExtremes(t *testing.T) {
	for _, c := range []struct{ raw, want [4]byte }{
		{[4]byte{0, 128, 255, 136}, [4]byte{0, 0, 128, 137}},
		{[4]byte{255, 255, 255, 151}, [4]byte{0, 0, 128, 152}},
	} {
		if got := IntSingle(c.raw); got != c.want {
			t.Fatalf("negative floor carry %x: %x != %x", c.raw, got, c.want)
		}
	}
	for _, raw := range [][4]byte{{255, 255, 127, 152}, {255, 255, 255, 152}, {255, 255, 255, 255}, {1, 0, 0, 255}} {
		if IntSingle(raw) != raw {
			t.Fatal("integral large SINGLE changed")
		}
	}
}
