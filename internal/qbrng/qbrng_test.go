package qbrng

import (
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"math"
	"os"
	"testing"
)

func mbfValue(raw []byte) float32 {
	if raw[3] == 0 {
		return 0
	}
	mantissa := uint32(raw[0]) | uint32(raw[1])<<8 | uint32(raw[2])<<16
	value := math.Ldexp(1+float64(mantissa&0x7fffff)/(1<<23), int(raw[3])-129)
	if mantissa&0x800000 != 0 {
		value = -value
	}
	return float32(value)
}

func TestAllNativeRawSeedAndRNDTraces(t *testing.T) {
	data, err := os.ReadFile("testdata/native_rng.json")
	if err != nil {
		t.Fatal(err)
	}
	var fixture struct {
		Format string
		Cases  []struct {
			Name, Mode string
			Initial    uint32
			TraceHex   string `json:"trace_hex"`
			SourceSHA  string `json:"source_trace_sha256"`
		}
	}
	if err = json.Unmarshal(data, &fixture); err != nil {
		t.Fatal(err)
	}
	if fixture.Format != "qb-native-rng-v1" || len(fixture.Cases) != 16 {
		t.Fatal("native fixture coverage")
	}
	for _, c := range fixture.Cases {
		t.Run(c.Name, func(t *testing.T) {
			trace, err := hex.DecodeString(c.TraceHex)
			if err != nil {
				t.Fatal(err)
			}
			if len(trace) != 2072 || string(trace[:4]) != "RNG1" || string(trace[len(trace)-4:]) != "END!" {
				t.Fatal("native trace frame")
			}
			digest := sha256.Sum256(trace)
			if hex.EncodeToString(digest[:]) != c.SourceSHA {
				t.Fatal("native trace identity")
			}
			g := New(c.Initial)
			if g.State() != binary.LittleEndian.Uint32(trace[4:8]) {
				t.Fatal("initial state")
			}
			if c.Mode != "unseeded" {
				var raw [4]byte
				copy(raw[:], trace[12:16])
				g.RandomizeMBF(raw)
			}
			if g.State() != binary.LittleEndian.Uint32(trace[16:20]) {
				t.Fatal("RANDOMIZE differs from native raw bytes")
			}
			for i := 0; i < 256; i++ {
				at := 20 + i*8
				got := g.Float32()
				want := mbfValue(trace[at+4 : at+8])
				if got != want || g.State() != binary.LittleEndian.Uint32(trace[at:at+4]) || got < 0 || got >= 1 {
					t.Fatalf("draw%d: state%06x value%.10g, native state%06x value%.10g", i, g.State(), got, binary.LittleEndian.Uint32(trace[at:at+4]), want)
				}
			}
		})
	}
}

func TestRawZeroResidueAndPreservedLowByte(t *testing.T) {
	g := New(5)
	g.RandomizeMBF([4]byte{0, 0, 0x80, 0})
	if g.State() != 0x8005 {
		t.Fatal("canonical negative zero", g.State())
	}
	g = New(5)
	g.RandomizeMBF([4]byte{0, 0, 0xc8, 0})
	if g.State() != 0xc805 {
		t.Fatal("measured midnight residue", g.State())
	}
	g = New(0x1234ab)
	g.RandomizeMBF([4]byte{0, 0, 0xc9, 0x87})
	if g.State() != 0x87c9ab {
		t.Fatal("low byte not preserved", g.State())
	}
	before := g.State()
	g.RandomizeMBF([4]byte{0, 0, 0xc9, 0x87})
	if g.State() != before {
		t.Fatal("RANDOMIZE advanced state")
	}
}
