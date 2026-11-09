package qbmbf

import (
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"math"
	"os"
	"testing"
)

type addFixture struct {
	Format string
	Cases  []struct {
		Name, Left, Right string
		Initial           uint32
		Output            *string
		Trace             string `json:"trace_hex"`
		SHA               string `json:"source_trace_sha256"`
	}
	Rewards []struct{ Name, Left, Right, Output string } `json:"reused_rewards"`
}

func additionFixture(t *testing.T) addFixture {
	t.Helper()
	data, err := os.ReadFile("testdata/native_add_single.json")
	if err != nil {
		t.Fatal(err)
	}
	var fixture addFixture
	if err = json.Unmarshal(data, &fixture); err != nil {
		t.Fatal(err)
	}
	if fixture.Format != "qb-native-add-single-v1" || len(fixture.Cases) != 82 || len(fixture.Rewards) != 9 {
		t.Fatal("fixed new and reused addition corpus coverage")
	}
	return fixture
}

func addRaw(t *testing.T, value string) [4]byte {
	t.Helper()
	data, err := hex.DecodeString(value)
	if err != nil || len(data) != 4 {
		t.Fatalf("invalid raw SINGLE %q", value)
	}
	return [4]byte(data)
}

func TestNativeAddSingle(t *testing.T) {
	fixture := additionFixture(t)
	overflows := 0
	for _, c := range fixture.Cases {
		t.Run(c.Name, func(t *testing.T) {
			left, right := addRaw(t, c.Left), addRaw(t, c.Right)
			trace, err := hex.DecodeString(c.Trace)
			if err != nil {
				t.Fatal(err)
			}
			hash := sha256.Sum256(trace)
			if hex.EncodeToString(hash[:]) != c.SHA || len(trace) < 17 || string(trace[:4]) != "ADD1" || binary.LittleEndian.Uint32(trace[4:8]) != c.Initial || string(trace[8:12]) != string(left[:]) || string(trace[12:16]) != string(right[:]) || trace[16] != 0 {
				t.Fatal("exact raw operand/RNG/mode provenance")
			}
			got, ok := AddSingle(left, right)
			if c.Output == nil {
				overflows++
				message := "\r\nOverflow in module YT-INIT  at address 01A3:00DA\r\n\r\nHit any key to return to system"
				if string(trace[17:]) != message || ok || got != [4]byte{} {
					t.Fatalf("overflow got (%x,%v)", got, ok)
				}
				return
			}
			want := addRaw(t, *c.Output)
			if len(trace) != 34 || string(trace[30:]) != "END!" || string(trace[17:21]) != string(want[:]) || string(trace[21:25]) != string(right[:]) || binary.LittleEndian.Uint32(trace[25:29]) != c.Initial || trace[29] != 0 {
				t.Fatal("complete native result, readonly operand and preserved RNG/mode")
			}
			if !ok || got != want {
				t.Fatalf("%x + %x: got (%x,%v), native %x", left, right, got, ok, want)
			}
		})
	}
	if overflows != 4 {
		t.Fatal("native overflow coverage")
	}
}

func TestAddSingleReusesNativeHQRewards(t *testing.T) {
	for _, c := range additionFixture(t).Rewards {
		t.Run(c.Name, func(t *testing.T) {
			added, ok := AddSingle(addRaw(t, c.Left), addRaw(t, c.Right))
			if !ok {
				t.Fatal("earlier bounded reward overflow")
			}
			if got, want := IntSingle(added), addRaw(t, c.Output); got != want {
				t.Fatalf("addition then INT: got %x, retained native credit %x", got, want)
			}
		})
	}
}

func TestAddSingleZeroResiduesAreDirectional(t *testing.T) {
	left, right := [4]byte{18, 52, 86, 0}, [4]byte{255, 255, 255, 0}
	if got, ok := AddSingle(left, right); !ok || got != right {
		t.Fatal("both zero aliases select right encoding")
	}
	if got, ok := AddSingle(right, left); !ok || got != left {
		t.Fatal("reversed zero aliases select right encoding")
	}
	for _, c := range []struct{ left, right, want [4]byte }{
		{[4]byte{0, 0, 64, 129}, [4]byte{0, 0, 192, 129}, [4]byte{0, 0, 64, 0}},
		{[4]byte{0, 0, 192, 129}, [4]byte{0, 0, 64, 129}, [4]byte{0, 0, 192, 0}},
		{[4]byte{1, 0, 0, 1}, [4]byte{0, 0, 128, 1}, [4]byte{1, 0, 0, 0}},
	} {
		if got, ok := AddSingle(c.left, c.right); !ok || got != c.want {
			t.Fatalf("zero residue: got (%x,%v), want %x", got, ok, c.want)
		}
	}
}

func TestAddSingleNativeGapShortcutDiffersFromIEEE(t *testing.T) {
	// Native ignores the smaller operand at exponent gap 25. IEEE arithmetic
	// would round the exact difference down by one representable step below 1.
	left, right := [4]byte{0, 0, 0, 129}, [4]byte{0, 0, 192, 104}
	if got, ok := AddSingle(left, right); !ok || got != left {
		t.Fatalf("native shortcut got (%x,%v)", got, ok)
	}
	ieee := float32(1.0 - 3.0/math.Pow(2, 26))
	if ieee == 1 {
		t.Fatal("IEEE countercontrol no longer distinguishes the native shortcut")
	}
	if got, ok := AddSingle(right, left); !ok || got != left {
		t.Fatal("dominant operand must be selected independent of position")
	}
}

func TestAddSingleEvenTiesAndOverflow(t *testing.T) {
	half := [4]byte{0, 0, 0, 105}
	for _, c := range []struct{ left, want [4]byte }{
		{[4]byte{0, 0, 0, 129}, [4]byte{0, 0, 0, 129}},
		{[4]byte{1, 0, 0, 129}, [4]byte{2, 0, 0, 129}},
	} {
		if got, ok := AddSingle(c.left, half); !ok || got != c.want {
			t.Fatalf("even tie got (%x,%v), want %x", got, ok, c.want)
		}
	}
	for _, sign := range []byte{0, 128} {
		max := [4]byte{255, 255, 127 | sign, 255}
		if got, ok := AddSingle(max, max); ok || got != [4]byte{} {
			t.Fatal("signed overflow must not clamp/wrap")
		}
	}
}
