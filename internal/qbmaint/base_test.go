package qbmaint

import (
	"bytes"
	"encoding/hex"
	"encoding/json"
	"os"
	"testing"
)

type baseCase struct {
	Name   string
	Day    int
	Timer  string `json:"timer_hex"`
	State  uint32
	Sector int
	Seeded uint32 `json:"seeded_state"`
	Final  uint32 `json:"final_state"`
	Record string `json:"record_hex"`
	Link   string `json:"link_hex"`
}

func baseFixture(t *testing.T) (fixture, []xannoronCase, []mobileCase, []baseCase) {
	t.Helper()
	p, x, m := mobileFixture(t)
	b, e := os.ReadFile("testdata/mercenary_base.json")
	if e != nil {
		t.Fatal(e)
	}
	var d struct {
		Format string
		Cases  []baseCase
	}
	if e = json.Unmarshal(b, &d); e != nil || d.Format != "qb-mercenary-base-v1" || len(d.Cases) != 29 {
		t.Fatal("base fixture", e)
	}
	return p, x, m, d.Cases
}
func basePrefix(t *testing.T, p fixture, x []xannoronCase, m []mobileCase, c baseCase) ([]byte, BaseInputs) {
	t.Helper()
	for _, mc := range m {
		if mc.Name != c.Name {
			continue
		}
		b, in := mobilePrefix(t, p, x, mc)
		out, s, e := ReplayInitialMobileGroups(b, in)
		if e != nil || s.FinalState != c.State {
			t.Fatal("mobile handoff", e)
		}
		return out, BaseInputs{Day: c.Day, State: s.FinalState, HelperTimer: raw4(t, c.Timer)}
	}
	t.Fatal("missing group predecessor")
	return nil, BaseInputs{}
}
func TestMercenaryBaseNativeWithGoPrefix(t *testing.T) {
	p, x, m, cases := baseFixture(t)
	for _, c := range cases {
		t.Run(c.Name, func(t *testing.T) {
			b, in := basePrefix(t, p, x, m, c)
			saved := append([]byte(nil), b...)
			out, s, e := ReplayMercenaryBaseBirth(b, in)
			if e != nil {
				t.Fatal(e)
			}
			record, e := hex.DecodeString(c.Record)
			if e != nil || len(record) != 137 {
				t.Fatal("native record")
			}
			link := raw4(t, c.Link)
			at := (50+c.Sector)*137 + 93
			if !bytes.Equal(out[4149*137:4150*137], record) || !bytes.Equal(out[at:at+4], link[:]) {
				t.Fatal("native whole record/link")
			}
			if s != (BaseStats{Sector: c.Sector, Draws: 1, SeededState: c.Seeded, FinalState: c.Final}) {
				t.Fatal("modeled continuation", s)
			}
			for i, v := range out {
				if !(i >= 4149*137 && i < 4150*137) && !(i >= at && i < at+4) && v != b[i] {
					t.Fatal("unrelated byte", i)
				}
			}
			if !bytes.Equal(b, saved) {
				t.Fatal("mutated input")
			}
			out[0] ^= 255
			if !bytes.Equal(b, saved) {
				t.Fatal("aliased output")
			}
		})
	}
}
func TestMercenaryBaseAdmission(t *testing.T) {
	p, x, m, cases := baseFixture(t)
	b, in := basePrefix(t, p, x, m, cases[0])
	tests := map[string]func([]byte, *BaseInputs){"day": func(_ []byte, i *BaseInputs) { i.Day = 0 }, "state": func(_ []byte, i *BaseInputs) { i.State = 1 << 24 }, "timer": func(_ []byte, i *BaseInputs) { i.HelperTimer = encode(86400) }, "geometry": func(b []byte, _ *BaseInputs) { b[56] = 0 }, "active": func(b []byte, _ *BaseInputs) { b[137+88] = 129 }, "existing base": func(b []byte, _ *BaseInputs) { b[4149*137+88] = 129 }, "revenge": func(b []byte, _ *BaseInputs) { v := encode(3); copy(b[71*137+105:], v[:]) }, "occupied placement": func(b []byte, _ *BaseInputs) {
		v := encode(1)
		for s := 1; s <= 3000; s++ {
			at := (50+s)*137 + 93
			if [4]byte(b[at:at+4]) == v {
				clear(b[at : at+4])
			}
		}
		copy(b[(50+cases[0].Sector)*137+93:], v[:])
	}, "force": func(b []byte, _ *BaseInputs) {
		v := encode(10001)
		hq, _ := integer([4]byte(b[117:121]))
		copy(b[(50+hq)*137+81:], v[:])
	}}
	for name, f := range tests {
		t.Run(name, func(t *testing.T) {
			v := append([]byte(nil), b...)
			i := in
			f(v, &i)
			saved := append([]byte(nil), v...)
			out, s, e := ReplayMercenaryBaseBirth(v, i)
			if e == nil || out != nil || s != (BaseStats{}) || !bytes.Equal(v, saved) {
				t.Fatal("admitted invalid input or partial mutation")
			}
		})
	}
	if out, s, e := ReplayMercenaryBaseBirth(b[:2], in); e == nil || out != nil || s != (BaseStats{}) {
		t.Fatal("short world")
	}
}
func TestMercenaryBaseInheritedFieldsAndRawZeros(t *testing.T) {
	p, x, m, cases := baseFixture(t)
	b, in := basePrefix(t, p, x, m, cases[0])
	sentinel := [4]byte{1, 2, 3, 4}
	copy(b[4149*137+133:], sentinel[:])
	out, _, e := ReplayMercenaryBaseBirth(b, in)
	if e != nil {
		t.Fatal(e)
	}
	for _, o := range []int{57, 61, 65, 69} {
		if [4]byte(out[4149*137+o:4149*137+o+4]) != ([4]byte{0, 0, 0xa0, 0}) {
			t.Fatal("stock zero residue")
		}
	}
	if [4]byte(out[4149*137+125:4149*137+129]) != ([4]byte{0, 0, 0x3e, 0}) || [4]byte(out[4149*137+133:4150*137]) != sentinel {
		t.Fatal("inherited/raw FAC bytes")
	}
}
