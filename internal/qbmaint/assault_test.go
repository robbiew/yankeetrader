package qbmaint

import (
	"bytes"
	"encoding/hex"
	"encoding/json"
	"os"
	"testing"
)

type assaultEvent struct {
	Group, Sector, Force int
	State                uint32
	Draws, Rounds        int
	Damage               int    `json:"damage_rounds"`
	RawForce             int    `json:"raw_force"`
	Final                uint32 `json:"final_state"`
	Record               string `json:"record_hex"`
}
type assaultCase struct {
	Name   string
	Before string `json:"before_sha256"`
	Events []assaultEvent
	Native string `json:"native_record_hex"`
}
type assaultFixture struct {
	Format string
	Worlds map[string]string
	Cases  []assaultCase
}

func assaultData(t *testing.T) assaultFixture {
	t.Helper()
	raw, e := os.ReadFile("testdata/wanderer_assault.json")
	if e != nil {
		t.Fatal(e)
	}
	var d assaultFixture
	if e = json.Unmarshal(raw, &d); e != nil || d.Format != "qb-wanderer-assault-v1" || len(d.Cases) != 3 {
		t.Fatal("assault fixture", e)
	}
	return d
}
func TestWandererAssaultNativeChains(t *testing.T) {
	d := assaultData(t)
	for _, c := range d.Cases {
		t.Run(c.Name, func(t *testing.T) {
			before := unpack(t, d.Worlds[c.Before])
			if digest(before) != c.Before || len(c.Events) != 18 {
				t.Fatal("modeled prefix/step inventory")
			}
			for _, v := range c.Events {
				saved := append([]byte(nil), before...)
				out, s, e := ReplayWandererAssault(before, AssaultInputs{Group: v.Group, Sector: v.Sector, Force: v.Force, State: v.State})
				if e != nil {
					t.Fatal(e)
				}
				record, e := hex.DecodeString(v.Record)
				if e != nil || len(record) != 137 {
					t.Fatal("modeled step record")
				}
				if !bytes.Equal(out[4051*137:4052*137], record) {
					t.Fatal("step rates/raw inherited record", v.Group)
				}
				var rates [3][4]byte
				for i, o := range []int{45, 49, 53} {
					rates[i] = [4]byte(record[o : o+4])
				}
				if s != (AssaultStats{InitialForce: v.Force, RawForce: v.RawForce, Rounds: v.Rounds, DamageRounds: v.Damage, Draws: v.Draws, FinalRates: rates, FinalState: v.Final}) {
					t.Fatal("step model stats", v.Group, s)
				}
				for i, b := range out {
					r := i - 4051*137
					changed := (r >= 45 && r < 57) || (r >= 73 && r < 77)
					if !changed && b != before[i] {
						t.Fatal("unrelated byte", i)
					}
				}
				if !bytes.Equal(before, saved) {
					t.Fatal("mutated input")
				}
				out[0] ^= 255
				if !bytes.Equal(before, saved) {
					t.Fatal("output alias")
				}
				out[0] ^= 255
				before = out
			}
			native, e := hex.DecodeString(c.Native)
			if e != nil || !bytes.Equal(before[4051*137:4052*137], native) {
				t.Fatal("whole final native Wanderer record")
			}
		})
	}
}
func TestWandererAssaultAdmission(t *testing.T) {
	d := assaultData(t)
	c := d.Cases[0]
	v := c.Events[0]
	before := unpack(t, d.Worlds[c.Before])
	in := AssaultInputs{Group: v.Group, Sector: v.Sector, Force: v.Force, State: v.State}
	changes := map[string]func([]byte, *AssaultInputs){"group20": func(_ []byte, i *AssaultInputs) { i.Group = 20 }, "protected": func(_ []byte, i *AssaultInputs) { i.Sector = 7 }, "zero force": func(_ []byte, i *AssaultInputs) { i.Force = 0 }, "state": func(_ []byte, i *AssaultInputs) { i.State = 1 << 24 }, "name": func(b []byte, _ *AssaultInputs) { b[4051*137] = 'X' }, "ground": func(b []byte, _ *AssaultInputs) { r := encode(1); copy(b[4051*137+77:], r[:]) }, "owner": func(b []byte, _ *AssaultInputs) { r := encode(-1); copy(b[4051*137+73:], r[:]) }, "stock": func(b []byte, _ *AssaultInputs) { r := encode(1); copy(b[4051*137+57:], r[:]) }, "rate500": func(b []byte, _ *AssaultInputs) { r := encode(500); copy(b[4051*137+45:], r[:]) }, "rate5001": func(b []byte, _ *AssaultInputs) { r := encode(5001); copy(b[4051*137+45:], r[:]) }, "mines": func(b []byte, i *AssaultInputs) { r := encode(1); copy(b[(50+i.Sector)*137+129:], r[:]) }}
	for name, f := range changes {
		t.Run(name, func(t *testing.T) {
			b := append([]byte(nil), before...)
			i := in
			f(b, &i)
			saved := append([]byte(nil), b...)
			out, s, e := ReplayWandererAssault(b, i)
			if e == nil || out != nil || s != (AssaultStats{}) || !bytes.Equal(b, saved) {
				t.Fatal("invalid assault admitted/partial mutation")
			}
		})
	}
	if out, s, e := ReplayWandererAssault(before[:2], in); e == nil || out != nil || s != (AssaultStats{}) {
		t.Fatal("short world")
	}
}

func TestWandererAssaultHalfGateAnd450Batch(t *testing.T) {
	d := assaultData(t)
	c := d.Cases[0]
	before := unpack(t, d.Worlds[c.Before])
	v := c.Events[0]
	out, s, e := ReplayWandererAssault(before, AssaultInputs{Group: 2, Sector: v.Sector, Force: 1, State: 0xecf641})
	if e != nil {
		t.Fatal(e)
	}
	if s.Draws != 1 || s.Rounds != 1 || s.DamageRounds != 0 || s.RawForce != -449 {
		t.Fatal("exact half gate must lose full 450 despite force 1", s)
	}
	for _, o := range []int{45, 49, 53, 57, 61, 65, 77} {
		a := 4051*137 + o
		if !bytes.Equal(out[a:a+4], before[a:a+4]) {
			t.Fatal("unrelated/raw zero field changed", o)
		}
	}
	if [4]byte(out[4051*137+73:4051*137+77]) != ([4]byte{0, 0, 0x20, 0}) {
		t.Fatal("original owner zero residue")
	}
}
