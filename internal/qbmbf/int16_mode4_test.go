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

func TestNativeMode4Conversions(t *testing.T) {
	data, err := os.ReadFile("testdata/native_int16_mode4.json")
	if err != nil {
		t.Fatal(err)
	}
	var doc struct {
		Format string
		Cases  []struct {
			Name, Kind, Raw string
			Op              int
			Initial         uint32
			Value           *int16
			Trace           string `json:"trace_hex"`
			SHA             string `json:"source_trace_sha256"`
		}
	}
	if err = json.Unmarshal(data, &doc); err != nil {
		t.Fatal(err)
	}
	if doc.Format != "qb-native-int16-mode4-v1" || len(doc.Cases) != 224 {
		t.Fatal("fixed mode-4 corpus coverage")
	}
	errors := 0
	for _, c := range doc.Cases {
		t.Run(c.Name, func(t *testing.T) {
			raw, err := hex.DecodeString(c.Raw)
			if err != nil {
				t.Fatal(err)
			}
			trace, err := hex.DecodeString(c.Trace)
			if err != nil {
				t.Fatal(err)
			}
			single := c.Kind == "single"
			size := 8
			magic := "M4D!"
			if single {
				size = 4
				magic = "M4S!"
			} else if c.Kind != "double" {
				t.Fatal("native input kind")
			}
			if len(raw) != size || len(trace) < size+10 {
				t.Fatal("native raw input/frame length")
			}
			digest := sha256.Sum256(trace)
			if hex.EncodeToString(digest[:]) != c.SHA || string(trace[:4]) != magic || binary.LittleEndian.Uint32(trace[4:8]) != c.Initial || string(trace[8:8+size]) != string(raw) || trace[8+size] != 0 || trace[9+size] != 4 {
				t.Fatal("native input and explicit mode-setting provenance")
			}
			var got int16
			var ok bool
			if single {
				if c.Op != 0x75 && c.Op != 0x77 {
					t.Fatal("native SINGLE entry")
				}
				got, ok = Int16SingleMode4([4]byte(raw))
			} else {
				if c.Op != 0x76 && c.Op != 0x78 {
					t.Fatal("native DOUBLE entry")
				}
				got, ok = Int16DoubleMode4([8]byte(raw))
			}
			at := size + 10
			if c.Value == nil {
				errors++
				address := map[int]string{0x75: "00D3", 0x77: "00D0", 0x76: "00DF", 0x78: "00DC"}[c.Op]
				message := "\r\nOverflow in module YT-INIT  at address 01A3:" + address + "\r\n\r\nHit any key to return to system"
				if string(trace[at:]) != message || ok || got != 0 {
					t.Fatalf("overflow got (%d,%v)", got, ok)
				}
				return
			}
			if len(trace) != 2*size+21 || string(trace[len(trace)-4:]) != "END!" {
				t.Fatal("complete native return frame")
			}
			native := int16(binary.LittleEndian.Uint16(trace[at : at+2]))
			if native != *c.Value || !ok || got != native {
				t.Fatalf("raw %x: got (%d,%v), native %d", raw, got, ok, native)
			}
			fac := append([]byte(nil), raw...)
			word := 0
			if !single {
				word = 4
			}
			binary.LittleEndian.PutUint16(fac[word:word+2], uint16(native))
			if string(trace[at+2:at+2+size]) != string(fac) || binary.LittleEndian.Uint32(trace[at+2+size:at+6+size]) != c.Initial || trace[at+6+size] != 4 {
				t.Fatal("FAC residue/RNG/applied mode preserved")
			}
		})
	}
	if errors != 56 {
		t.Fatal("fixed native overflow coverage")
	}
}

func TestMode4DiffersFromDefaultRounding(t *testing.T) {
	for _, c := range []struct {
		raw            [4]byte
		floor, nearest int16
	}{
		{[4]byte{0, 0, 32, 130}, 2, 3},   // +2.5
		{[4]byte{0, 0, 128, 127}, -1, 0}, // -0.25
	} {
		got, ok := Int16SingleMode4(c.raw)
		near, nearOK := Int16Single(c.raw)
		if !ok || got != c.floor || !nearOK || near != c.nearest {
			t.Fatalf("mode separation for %x", c.raw)
		}
	}
	// +32767.5 floors within range, while the default rounded cast overflows.
	raw := [4]byte{0, 255, 127, 143}
	if got, ok := Int16SingleMode4(raw); !ok || got != 32767 {
		t.Fatal("mode-4 upper bound")
	}
	if _, ok := Int16Single(raw); ok {
		t.Fatal("default-mode upper bound changed")
	}
}

func TestMode4DoubleRejectsFloat64Demotion(t *testing.T) {
	for _, c := range []struct {
		hex  string
		want int16
		ok   bool
	}{
		{"ffffffffffff7f80", 0, true},     // 1 - 2^-56
		{"0100000000008081", -2, true},    // -1 - 2^-55
		{"ffffffffffff7f8f", 32767, true}, // 32768 - 2^-41
		{"0100000000008090", 0, false},    // -32768 - 2^-40
	} {
		data, err := hex.DecodeString(c.hex)
		if err != nil {
			t.Fatal(err)
		}
		raw := [8]byte(data)
		got, ok := Int16DoubleMode4(raw)
		if got != c.want || ok != c.ok {
			t.Fatalf("%x: (%d,%v)", raw, got, ok)
		}
		bits := doubleBits(raw)&((uint64(1)<<55)-1) | uint64(1)<<55
		lossy := math.Ldexp(float64(bits), int(raw[7])-184)
		if raw[6]&128 != 0 {
			lossy = -lossy
		}
		wrong := math.Floor(lossy)
		wrongOK := wrong >= -32768 && wrong <= 32767
		if wrongOK == c.ok && (!wrongOK || int16(wrong) == c.want) {
			t.Fatal("countercontrol must distinguish float64 demotion")
		}
	}
}

func TestMode4ZeroAliasesAndIntegralExtremes(t *testing.T) {
	for _, raw := range [][4]byte{{255, 255, 255, 0}, {18, 52, 86, 0}} {
		if got, ok := Int16SingleMode4(raw); !ok || got != 0 {
			t.Fatal("zero alias")
		}
	}
	for _, raw := range [][8]byte{{255, 255, 255, 255, 255, 255, 255, 0}, {18, 52, 86, 120, 154, 188, 222, 0}} {
		if got, ok := Int16DoubleMode4(raw); !ok || got != 0 {
			t.Fatal("DOUBLE zero alias")
		}
	}
	if got, ok := Int16SingleMode4([4]byte{0, 0, 128, 144}); !ok || got != -32768 {
		t.Fatal("exact lower bound")
	}
	if _, ok := Int16SingleMode4([4]byte{64, 0, 128, 144}); ok {
		t.Fatal("negative fraction below lower bound")
	}
	if _, ok := Int16DoubleMode4([8]byte{255, 255, 255, 255, 255, 255, 255, 255}); ok {
		t.Fatal("finite extreme overflow")
	}
}
