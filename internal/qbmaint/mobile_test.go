package qbmaint

import (
	"bytes"
	"encoding/json"
	"os"
	"testing"
)

type mobileCase struct {
	Name   string
	State  uint32
	One    []string `json:"helper_one"`
	Two    []string `json:"helper_two"`
	Groups []MobileGroup
	Top    int `json:"top_fallback"`
	Draws  int
	Final  uint32 `json:"final_state"`
	Native string `json:"native_sha256"`
}

func mobileFixture(t *testing.T) (fixture, []xannoronCase, []mobileCase) {
	t.Helper()
	p, x := xannoronFixture(t)
	b, e := os.ReadFile("testdata/mobile_groups.json")
	if e != nil {
		t.Fatal(e)
	}
	var d struct {
		Format string
		Cases  []mobileCase
	}
	if e = json.Unmarshal(b, &d); e != nil || d.Format != "qb-mobile-groups-v1" || len(d.Cases) != 29 {
		t.Fatal("mobile fixture", e)
	}
	return p, x, d.Cases
}
func mobilePrefix(t *testing.T, p fixture, x []xannoronCase, c mobileCase) ([]byte, MobileInputs) {
	t.Helper()
	for _, v := range x {
		if v.Name != c.Name {
			continue
		}
		b := xannoronPrefix(t, p, v)
		out, s, e := ReplayXannoronBirth(b, XannoronInputs{Day: v.Day, State: v.State, TimerSeconds: raw4(t, v.Timer)})
		if e != nil || s.FinalState != c.State {
			t.Fatal("Xannoron handoff", e)
		}
		in := MobileInputs{State: s.FinalState}
		if len(c.One) != 39 || len(c.Two) != 19 {
			t.Fatal("helper inventory")
		}
		for i, v := range c.One {
			in.HelperOne[i] = raw4(t, v)
		}
		for i, v := range c.Two {
			in.HelperTwo[i] = raw4(t, v)
		}
		return out, in
	}
	t.Fatal("missing predecessor")
	return nil, MobileInputs{}
}
func mobileProjection(b []byte) []byte {
	var out []byte
	for s := 1; s <= 3000; s++ {
		for _, o := range []int{81, 85, 129} {
			a := (50+s)*RecordSize + o
			out = append(out, b[a:a+4]...)
		}
	}
	for g := 0; g < 20; g++ {
		a := (51+g)*RecordSize + 105
		out = append(out, b[a:a+4]...)
	}
	return out
}
func TestMobileNativeAndContinuation(t *testing.T) {
	p, x, cases := mobileFixture(t)
	for _, c := range cases {
		t.Run(c.Name, func(t *testing.T) {
			b, in := mobilePrefix(t, p, x, c)
			saved := append([]byte(nil), b...)
			out, s, e := ReplayInitialMobileGroups(b, in)
			if e != nil {
				t.Fatal(e)
			}
			if digest(mobileProjection(out)) != c.Native {
				t.Fatal("complete native force/owner/mine/pointer inventory")
			}
			if s.Draws != c.Draws || s.FinalState != c.Final || s.TopFallback != c.Top {
				t.Fatalf("continuation: %+v want draws %d state %x", s, c.Draws, c.Final)
			}
			total := 0
			for i, g := range s.Groups {
				if g != c.Groups[i] {
					t.Fatal("group", i, g, c.Groups[i])
				}
				total += g.Strength
			}
			if total != 10000 {
				t.Fatal("force conservation")
			}
			allowed := map[int]bool{}
			for i, g := range s.Groups {
				for _, o := range []int{81, 85} {
					for j := 0; j < 4; j++ {
						allowed[(50+g.Sector)*RecordSize+o+j] = true
					}
				}
				for j := 0; j < 4; j++ {
					allowed[(51+i)*RecordSize+105+j] = true
				}
			}
			for j := 0; j < 4; j++ {
				allowed[(50+s.Groups[19].Sector)*RecordSize+129+j] = true
			}
			for i, v := range out {
				if !allowed[i] && v != b[i] {
					t.Fatal("unrelated byte", i)
				}
			}
			if !bytes.Equal(b, saved) {
				t.Fatal("mutated input")
			}
			out[0] ^= 255
			if !bytes.Equal(b, saved) {
				t.Fatal("alias")
			}
		})
	}
}
func TestMobileAdmission(t *testing.T) {
	p, x, cases := mobileFixture(t)
	b, in := mobilePrefix(t, p, x, cases[0])
	tests := map[string]func([]byte, *MobileInputs){"active player": func(b []byte, _ *MobileInputs) { v := encode(1); copy(b[137+85:], v[:]) },
		"state": func(_ []byte, i *MobileInputs) { i.State = 1 << 24 }, "timer": func(_ []byte, i *MobileInputs) { i.HelperTwo[18] = encode(-1) }, "geometry": func(b []byte, _ *MobileInputs) { b[56] = 0 }, "group": func(b []byte, _ *MobileInputs) { v := encode(1); copy(b[52*137+105:], v[:]) }, "force": func(b []byte, _ *MobileInputs) { v := encode(1); copy(b[51*137+81:], v[:]) }, "warp": func(b []byte, _ *MobileInputs) { v := encode(3001); copy(b[51*137+41:], v[:]) }, "hazard": func(b []byte, _ *MobileInputs) { v := encode(1); copy(b[51*137+129:], v[:]) }, "no routes": func(b []byte, _ *MobileInputs) {
			for s := 1; s <= 3000; s++ {
				clear(b[(50+s)*137+41 : (50+s)*137+65])
			}
		}}
	for n, f := range tests {
		t.Run(n, func(t *testing.T) {
			v := append([]byte(nil), b...)
			i := in
			f(v, &i)
			saved := append([]byte(nil), v...)
			out, s, e := ReplayInitialMobileGroups(v, i)
			if e == nil || out != nil || s != (MobileStats{}) || !bytes.Equal(v, saved) {
				t.Fatal("invalid input admitted/partial mutation")
			}
		})
	}
	if out, s, e := ReplayInitialMobileGroups(b[:2], in); e == nil || out != nil || s != (MobileStats{}) {
		t.Fatal("short world")
	}
}

func TestMobileEnteredPlanetRejected(t *testing.T) {
	p, x, cases := mobileFixture(t)
	b, in := mobilePrefix(t, p, x, cases[0])
	_, stats, e := ReplayInitialMobileGroups(b, in)
	if e != nil {
		t.Fatal(e)
	}
	for s := 1; s <= 3000; s++ {
		at := (50+s)*137 + 93
		if [4]byte(b[at:at+4]) == encode(1) {
			clear(b[at : at+4])
		}
	}
	at := (50+stats.Groups[1].Sector)*137 + 93
	v := encode(1)
	copy(b[at:at+4], v[:])
	saved := append([]byte(nil), b...)
	out, st, e := ReplayInitialMobileGroups(b, in)
	if e == nil || out != nil || st != (MobileStats{}) || !bytes.Equal(b, saved) {
		t.Fatal("entered planet accepted or partially mutated")
	}
}
