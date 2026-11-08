package qbrng

import (
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"os"
	"testing"
)

func TestNativeArgumentedRNDControls(t *testing.T) {
	data, err := os.ReadFile("testdata/native_rng_arguments.json")
	if err != nil {
		t.Fatal(err)
	}
	var fixture struct {
		Format  string
		Samples int `json:"samples_per_case"`
		Cases   []struct {
			Name           string
			Initial, Final uint32
			Arguments      []string
			Trace          string `json:"trace_hex"`
			SHA            string `json:"source_trace_sha256"`
		}
	}
	if err = json.Unmarshal(data, &fixture); err != nil {
		t.Fatal(err)
	}
	if fixture.Format != "qb-native-rnd-arguments-v1" || fixture.Samples != 64 || len(fixture.Cases) != 16 {
		t.Fatal("native fixture coverage")
	}
	for _, c := range fixture.Cases {
		t.Run(c.Name, func(t *testing.T) {
			trace, err := hex.DecodeString(c.Trace)
			if err != nil {
				t.Fatal(err)
			}
			digest := sha256.Sum256(trace)
			if hex.EncodeToString(digest[:]) != c.SHA || len(trace) != 780 || string(trace[:4]) != "RND2" || string(trace[776:]) != "END!" {
				t.Fatal("native identity/frame")
			}
			g := New(c.Initial)
			if g.State() != binary.LittleEndian.Uint32(trace[4:8]) {
				t.Fatal("initial state")
			}
			for i := 0; i < 64; i++ {
				at := 8 + 12*i
				var raw [4]byte
				copy(raw[:], trace[at:at+4])
				if hex.EncodeToString(raw[:]) != c.Arguments[i%len(c.Arguments)] {
					t.Fatal("input schedule")
				}
				got := g.Float32MBF(raw)
				if got != mbfValue(trace[at+8:at+12]) || g.State() != binary.LittleEndian.Uint32(trace[at+4:at+8]) {
					t.Fatalf("operation %d differs from original state/value", i)
				}
			}
			if g.State() != c.Final {
				t.Fatal("native final state")
			}
		})
	}
}

func TestArgumentedRNDZeroDoesNotAdvance(t *testing.T) {
	for _, raw := range [][4]byte{{}, {255, 255, 127, 0}, {255, 255, 255, 0}} {
		g := New(0x1234ab)
		if got := g.Float32MBF(raw); got != float32(0x1234ab)/(1<<24) || g.State() != 0x1234ab {
			t.Fatal("raw zero advanced or reseeded")
		}
	}
}

func TestNegativeRNDReplacesOldState(t *testing.T) {
	raw := [4]byte{255, 255, 128, 129}
	a, b := New(5), New(0xffffff)
	if a.Float32MBF(raw) != b.Float32MBF(raw) || a.State() != b.State() {
		t.Fatal("negative argument depends on old state")
	}
	a, b = New(5), New(5)
	a.RandomizeMBF(raw)
	a.Float32()
	b.Float32MBF(raw)
	if a.State() == b.State() {
		t.Fatal("negative RND conflated with RANDOMIZE")
	}
}

func TestPositiveArgumentMatchesArgumentlessRND(t *testing.T) {
	a, b := New(0x1234ab), New(0x1234ab)
	for i := 0; i < 256; i++ {
		raw := [4]byte{byte(i), byte(i >> 1), byte(i & 127), byte(i%255 + 1)}
		if a.Float32MBF(raw) != b.Float32() || a.State() != b.State() {
			t.Fatal("positive magnitude changes sequence")
		}
	}
}
