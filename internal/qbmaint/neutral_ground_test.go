package qbmaint

import (
	"bytes"
	"encoding/json"
	"os"
	"reflect"
	"testing"
)

type neutralGroundCase struct {
	Name                 string
	Before               string `json:"before_sha256"`
	Group, Sector, Force int
	State                uint32 `json:"initial_state"`
	Expected             string `json:"expected_sha256"`
	Event                struct {
		Group, Sector, Force, Ground int
		InitialForce                 int    `json:"initial_force"`
		RawForce                     int    `json:"raw_force"`
		InitialGround                int    `json:"initial_ground"`
		InitialState                 uint32 `json:"initial_rng_state"`
		FinalState                   uint32 `json:"final_rng_state"`
		Draws                        int    `json:"rng_draws"`
	}
}
type neutralGroundFixture struct {
	Format           string
	Worlds           map[string]string
	Cases, Synthetic []neutralGroundCase
	Comparisons      int `json:"native_six_file_comparisons"`
	Witnesses        int `json:"native_rng_witnesses"`
}

func neutralGroundLoad(t *testing.T) neutralGroundFixture {
	t.Helper()
	b, e := os.ReadFile("testdata/neutral_ground.json")
	if e != nil {
		t.Fatal(e)
	}
	var d neutralGroundFixture
	if e = json.Unmarshal(b, &d); e != nil {
		t.Fatal(e)
	}
	if d.Format != "qb-neutral-ground-v1" || len(d.Cases) != 57 || len(d.Synthetic) != 36 || d.Comparisons != 180 || d.Witnesses != 1872 {
		t.Fatal("qualified inventory")
	}
	return d
}
func neutralGroundInputs(c neutralGroundCase) NeutralGroundInputs {
	return NeutralGroundInputs{Group: c.Group, Sector: c.Sector, Force: c.Force, State: c.State}
}
func TestNeutralGroundQualifiedEncountersAndSyntheticBoundaries(t *testing.T) {
	d := neutralGroundLoad(t)
	for _, set := range [][]neutralGroundCase{d.Cases, d.Synthetic} {
		for _, c := range set {
			t.Run(c.Name, func(t *testing.T) {
				before := unpack(t, d.Worlds[c.Before])
				if digest(before) != c.Before {
					t.Fatal("before identity")
				}
				saved := bytes.Clone(before)
				world, stats, e := ReplayNeutralGroundAssault(before, neutralGroundInputs(c))
				if e != nil {
					t.Fatal(e)
				}
				v := c.Event
				want := NeutralGroundStats{InitialForce: v.InitialForce, RawForce: v.RawForce, Force: v.Force, InitialGround: v.InitialGround, Ground: v.Ground, Draws: v.Draws, InitialState: v.InitialState, FinalState: v.FinalState}
				if digest(world) != c.Expected || !reflect.DeepEqual(stats, want) {
					t.Fatalf("complete modeled world/receipt mismatch: %+v want %+v", stats, want)
				}
				if stats.Force != 0 || stats.RawForce > 0 || stats.RawForce < -999 || stats.InitialGround-stats.Ground != stats.Draws {
					t.Fatal("ground/damage/death accounting")
				}
				at := 4052*RecordSize + 77
				for i, b := range world {
					if (i < at || i >= at+4) && b != before[i] {
						t.Fatal("write outside ground field", i)
					}
				}
				if !bytes.Equal(before, saved) {
					t.Fatal("input mutation")
				}
				world[0] ^= 255
				if !bytes.Equal(before, saved) {
					t.Fatal("output aliases input")
				}
			})
		}
	}
	// Successive native-qualified attacks retain the preceding Go ground value;
	// other modeled route writes are intentionally outside this primitive.
	for _, ob := range []string{"observed-a", "observed-b", "observed-c"} {
		count := 0
		ground := 505000
		for _, c := range d.Cases {
			if !bytes.Contains([]byte(c.Name), []byte("/"+ob+"/")) {
				continue
			}
			before := unpack(t, d.Worlds[c.Before])
			planetPut(before, 4053, 77, float64(ground))
			world, stats, e := ReplayNeutralGroundAssault(before, neutralGroundInputs(c))
			if e != nil || digest(world) != c.Expected {
				t.Fatal("calculated prior-ground handoff", e)
			}
			ground = stats.Ground
			count++
		}
		if count != 19 || ground != 504975 {
			t.Fatal("retained nineteen-attack ground chain", count, ground)
		}
	}
	zero, maxDraw := 0, 0
	for _, c := range d.Synthetic {
		if c.Force != 1 {
			continue
		}
		if c.Event.FinalState == 0 {
			zero++
			if c.Event.Draws != 1 || c.Event.RawForce != 0 {
				t.Fatal("minimum real LCG damage")
			}
		}
		if c.Event.FinalState == 0xffffff {
			maxDraw++
			if c.Event.Draws != 1 || c.Event.RawForce != -999 {
				t.Fatal("maximum real LCG damage")
			}
		}
	}
	if zero != 3 || maxDraw != 3 {
		t.Fatal("real LCG extrema controls")
	}
}
func TestNeutralGroundAtomicRefusalsAndRawZeros(t *testing.T) {
	d := neutralGroundLoad(t)
	c := d.Cases[0]
	changes := map[string]func([]byte, *NeutralGroundInputs){
		"group":       func(w []byte, in *NeutralGroundInputs) { in.Group = 1 },
		"large group": func(w []byte, in *NeutralGroundInputs) { in.Group = 21 },
		"sector":      func(w []byte, in *NeutralGroundInputs) { in.Sector = 853 },
		"state":       func(w []byte, in *NeutralGroundInputs) { in.State = 1 << 24 },
		"force":       func(w []byte, in *NeutralGroundInputs) { in.Force = 0 },
		"large force": func(w []byte, in *NeutralGroundInputs) { in.Force = 10001 },
		"geometry":    func(w []byte, in *NeutralGroundInputs) { planetPut(w, 1, 53, 52) },
		"slot":        func(w []byte, in *NeutralGroundInputs) { planetPut(w, 905, 93, 3) },
		"defense":     func(w []byte, in *NeutralGroundInputs) { planetPut(w, 905, 81, 1) },
		"mine":        func(w []byte, in *NeutralGroundInputs) { planetPut(w, 905, 129, 1) },
		"name":        func(w []byte, in *NeutralGroundInputs) { w[4052*RecordSize] = 'X' },
		"padding":     func(w []byte, in *NeutralGroundInputs) { w[4052*RecordSize+40] = 'X' },
		"length":      func(w []byte, in *NeutralGroundInputs) { planetPut(w, 4053, 85, 10) },
		"owner":       func(w []byte, in *NeutralGroundInputs) { planetPut(w, 4053, 73, -1) },
		"weak ground": func(w []byte, in *NeutralGroundInputs) { planetPut(w, 4053, 77, 500000) },
		"high ground": func(w []byte, in *NeutralGroundInputs) { planetPut(w, 4053, 77, 505001) },
	}
	for name, change := range changes {
		t.Run(name, func(t *testing.T) {
			before := unpack(t, d.Worlds[c.Before])
			in := neutralGroundInputs(c)
			change(before, &in)
			saved := bytes.Clone(before)
			out, stats, e := ReplayNeutralGroundAssault(before, in)
			if e == nil || out != nil || !reflect.DeepEqual(stats, NeutralGroundStats{}) {
				t.Fatal("unsupported output")
			}
			if !bytes.Equal(before, saved) {
				t.Fatal("failed replay changed input")
			}
		})
	}
	if out, _, e := ReplayNeutralGroundAssault(nil, neutralGroundInputs(c)); e == nil || out != nil {
		t.Fatal("short world")
	}
	before := unpack(t, d.Worlds[c.Before])
	alias := [4]byte{1, 2, 0x80, 0}
	for _, field := range [][2]int{{905, 81}, {905, 129}, {4053, 73}} {
		a := (field[0]-1)*RecordSize + field[1]
		copy(before[a:a+4], alias[:])
	}
	world, _, e := ReplayNeutralGroundAssault(before, neutralGroundInputs(c))
	if e != nil {
		t.Fatal(e)
	}
	for _, field := range [][2]int{{905, 81}, {905, 129}, {4053, 73}} {
		a := (field[0]-1)*RecordSize + field[1]
		if !bytes.Equal(world[a:a+4], alias[:]) {
			t.Fatal("raw zero alias normalized")
		}
	}
}
