package qbmaint

import (
	"bytes"
	"encoding/json"
	"os"
	"reflect"
	"testing"
)

type defenseCase struct {
	Name                 string
	Before               string `json:"before_sha256"`
	Group, Sector, Force int
	State                uint32 `json:"initial_state"`
	Expected             string `json:"expected_sha256"`
	Event                struct {
		Group, Sector, Force, Defenders int
		Owner                           float64
		InitialForce                    int    `json:"initial_force"`
		InitialDefenders                int    `json:"initial_defenders"`
		XDamage                         int    `json:"x_damage"`
		DefenderDamage                  int    `json:"defender_damage"`
		InitialState                    uint32 `json:"initial_rng_state"`
		FinalState                      uint32 `json:"final_rng_state"`
		Draws                           int    `json:"rng_draws"`
	}
}
type defenseFixture struct {
	Format           string
	Worlds           map[string]string
	Cases, Synthetic []defenseCase
	Comparisons      int `json:"native_six_file_comparisons"`
	Witnesses        int `json:"native_rng_witnesses"`
}

func defenseLoad(t *testing.T) defenseFixture {
	t.Helper()
	b, e := os.ReadFile("testdata/foreign_defense.json")
	if e != nil {
		t.Fatal(e)
	}
	var d defenseFixture
	if e = json.Unmarshal(b, &d); e != nil {
		t.Fatal(e)
	}
	if d.Format != "qb-foreign-defense-v1" || len(d.Cases) != 63 || len(d.Synthetic) != 24 || d.Comparisons != 180 || d.Witnesses != 1872 {
		t.Fatal("qualified inventory")
	}
	return d
}
func defenseInputs(c defenseCase) ForeignDefenseInputs {
	return ForeignDefenseInputs{Group: c.Group, Sector: c.Sector, Force: c.Force, State: c.State}
}
func TestForeignDefenseQualifiedEncountersAndSyntheticBoundaries(t *testing.T) {
	d := defenseLoad(t)
	nativeWins, nativeLosses := 0, 0
	for _, set := range [][]defenseCase{d.Cases, d.Synthetic} {
		for _, c := range set {
			t.Run(c.Name, func(t *testing.T) {
				before := unpack(t, d.Worlds[c.Before])
				if digest(before) != c.Before {
					t.Fatal("phase before identity")
				}
				saved := bytes.Clone(before)
				world, stats, e := ReplayForeignDefense(before, defenseInputs(c))
				if e != nil {
					t.Fatal(e)
				}
				v := c.Event
				want := ForeignDefenseStats{InitialForce: v.InitialForce, Force: v.Force, InitialDefenders: v.InitialDefenders, Defenders: v.Defenders, XDamage: v.XDamage, DefenderDamage: v.DefenderDamage, Draws: v.Draws, InitialState: v.InitialState, FinalState: v.FinalState, PreferredCleared: v.Defenders == 0}
				if digest(world) != c.Expected || !reflect.DeepEqual(stats, want) {
					t.Fatalf("complete modeled world/receipt mismatch: %+v want %+v", stats, want)
				}
				if (stats.Force == 0) == (stats.Defenders == 0) || stats.XDamage < stats.InitialForce-stats.Force || stats.DefenderDamage < stats.InitialDefenders-stats.Defenders {
					t.Fatal("raw counters/capped survivor conservation")
				}
				at := (905 - 1) * RecordSize
				for i, b := range world {
					if (i < at+81 || i >= at+89) && b != before[i] {
						t.Fatal("unrelated byte changed", i)
					}
				}
				if !bytes.Equal(saved, before) {
					t.Fatal("input mutation")
				}
				if stats.PreferredCleared {
					if !bytes.Equal(world[at+81:at+89], make([]byte, 8)) {
						t.Fatal("defense clear not canonical")
					}
				} else if !bytes.Equal(world[at+85:at+89], before[at+85:at+89]) {
					t.Fatal("surviving owner changed")
				}
				world[0] ^= 255
				if !bytes.Equal(saved, before) {
					t.Fatal("output aliases input")
				}
			})
		}
	}
	for _, c := range d.Cases {
		if c.Event.Defenders == 0 {
			nativeWins++
		} else {
			nativeLosses++
		}
	}
	if nativeWins == 0 || nativeLosses == 0 {
		t.Fatal("both native-qualified outcomes required")
	}
	// The exact-half and adjacent fraction controls use real generator states,
	// not injected draws. One round at 500 selects the equality side unambiguously.
	ties, above := 0, 0
	for _, c := range d.Synthetic {
		if c.Force != 500 || c.Event.InitialDefenders != 500 {
			continue
		}
		if c.Event.FinalState == 0x800000 {
			ties++
			if c.Event.Draws != 1 || c.Event.Force != 500 || c.Event.Defenders != 0 {
				t.Fatal("exact tie must damage defenders")
			}
		}
		if c.Event.FinalState == 0x800001 {
			above++
			if c.Event.Draws != 1 || c.Event.Force != 0 || c.Event.Defenders != 500 {
				t.Fatal("above half must damage attackers")
			}
		}
	}
	if ties != 1 || above != 1 {
		t.Fatal("real LCG boundary controls")
	}
}
func TestForeignDefenseAtomicRefusalsAndRawHazardZeros(t *testing.T) {
	d := defenseLoad(t)
	c := d.Cases[0]
	changes := map[string]func([]byte, *ForeignDefenseInputs){
		"group":              func(w []byte, in *ForeignDefenseInputs) { in.Group = 1 },
		"sector":             func(w []byte, in *ForeignDefenseInputs) { in.Sector = 853 },
		"state":              func(w []byte, in *ForeignDefenseInputs) { in.State = 1 << 24 },
		"empty attack":       func(w []byte, in *ForeignDefenseInputs) { in.Force = 0 },
		"large attack":       func(w []byte, in *ForeignDefenseInputs) { in.Force = 10001 },
		"geometry":           func(w []byte, in *ForeignDefenseInputs) { planetPut(w, 1, 53, 52) },
		"neutral":            func(w []byte, in *ForeignDefenseInputs) { planetPut(w, 905, 85, 0) },
		"human":              func(w []byte, in *ForeignDefenseInputs) { planetPut(w, 905, 85, 2) },
		"friendly":           func(w []byte, in *ForeignDefenseInputs) { planetPut(w, 905, 85, -1) },
		"fractional defense": func(w []byte, in *ForeignDefenseInputs) { planetPut(w, 905, 81, .5) },
		"large defense":      func(w []byte, in *ForeignDefenseInputs) { planetPut(w, 905, 81, 100001) },
		"empty defense":      func(w []byte, in *ForeignDefenseInputs) { planetPut(w, 905, 81, 0) },
		"mine":               func(w []byte, in *ForeignDefenseInputs) { planetPut(w, 905, 129, 1) },
		"planet":             func(w []byte, in *ForeignDefenseInputs) { planetPut(w, 905, 93, 2) },
	}
	for name, change := range changes {
		t.Run(name, func(t *testing.T) {
			before := unpack(t, d.Worlds[c.Before])
			in := defenseInputs(c)
			change(before, &in)
			saved := bytes.Clone(before)
			out, stats, e := ReplayForeignDefense(before, in)
			if e == nil || out != nil || !reflect.DeepEqual(stats, ForeignDefenseStats{}) {
				t.Fatal("unsupported result published")
			}
			if !bytes.Equal(before, saved) {
				t.Fatal("refusal mutated input")
			}
		})
	}
	if out, _, e := ReplayForeignDefense(nil, defenseInputs(c)); e == nil || out != nil {
		t.Fatal("short world")
	}
	before := unpack(t, d.Worlds[c.Before])
	alias := [4]byte{1, 2, 0x80, 0}
	for _, o := range []int{93, 129} {
		a := 904*RecordSize + o
		copy(before[a:a+4], alias[:])
	}
	out, _, e := ReplayForeignDefense(before, defenseInputs(c))
	if e != nil {
		t.Fatal(e)
	}
	for _, o := range []int{93, 129} {
		a := 904*RecordSize + o
		if !bytes.Equal(out[a:a+4], alias[:]) {
			t.Fatal("raw hazard zero normalized")
		}
	}
}
