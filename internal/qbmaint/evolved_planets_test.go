package qbmaint

import (
	"bytes"
	"encoding/hex"
	"encoding/json"
	"os"
	"reflect"
	"testing"

	"github.com/robbiew/yankeetrader/internal/qbrng"
)

type planetCase struct {
	Name      string
	BeforeSHA string `json:"before_sha256"`
	State     uint32 `json:"initial_state"`
	Clocks    []struct {
		Record, Day int
		Timer       string `json:"timer_minutes"`
	}
	SHA   string `json:"expected_sha256"`
	Final uint32 `json:"final_state"`
	Draws int
	Rows  []struct {
		Record, Day, Ground int
		Elapsed             string
		Draws               [3]string `json:"event_draws"`
		Rates               [3]string `json:"cargo_rates"`
	}
}
type planetFixture struct {
	Format      string
	Worlds      map[string]string
	Cases       []planetCase
	Comparisons int `json:"native_six_file_comparisons"`
	Witnesses   int `json:"native_rng_witnesses"`
}

func planetLoad(t *testing.T) planetFixture {
	t.Helper()
	b, e := os.ReadFile("testdata/evolved_planets.json")
	if e != nil {
		t.Fatal(e)
	}
	var d planetFixture
	if e = json.Unmarshal(b, &d); e != nil {
		t.Fatal(e)
	}
	if d.Format != "qb-evolved-planet-replay-v1" || len(d.Cases) != 9 || d.Comparisons != 54 || d.Witnesses != 501 {
		t.Fatal("coverage")
	}
	return d
}
func planetRaw(t *testing.T, v string) [4]byte {
	t.Helper()
	b, e := hex.DecodeString(v)
	if e != nil || len(b) != 4 {
		t.Fatal("raw SINGLE")
	}
	return [4]byte(b)
}
func planetInputs(t *testing.T, c planetCase) EvolvedPlanetInputs {
	t.Helper()
	in := EvolvedPlanetInputs{State: c.State}
	for _, r := range c.Clocks {
		in.Clocks = append(in.Clocks, PlanetClock{Record: r.Record, Day: r.Day, TimerMinutes: planetRaw(t, r.Timer)})
	}
	return in
}
func TestEvolvedPlanetQualifiedPhases(t *testing.T) {
	d := planetLoad(t)
	count := 0
	for _, c := range d.Cases {
		t.Run(c.Name, func(t *testing.T) {
			before := unpack(t, d.Worlds[c.BeforeSHA])
			if digest(before) != c.BeforeSHA {
				t.Fatal("modeled before fingerprint")
			}
			saved := bytes.Clone(before)
			in := planetInputs(t, c)
			clocks := append([]PlanetClock(nil), in.Clocks...)
			got, stats, e := ReplayEvolvedPlanets(before, in)
			if e != nil {
				t.Fatal(e)
			}
			if digest(got) != c.SHA {
				t.Fatal("complete Python-qualified economy-phase world mismatch")
			}
			if stats.InitialState != c.State || stats.FinalState != c.Final || stats.Draws != c.Draws || stats.Draws != 3*len(c.Clocks) || len(stats.Rows) != len(c.Rows) {
				t.Fatal("RNG phase summary")
			}
			rng := qbrng.New(c.State)
			for i, r := range stats.Rows {
				want := c.Rows[i]
				if r.Record != want.Record || r.Day != want.Day || r.Ground != want.Ground || r.Elapsed != planetRaw(t, want.Elapsed) {
					t.Fatal("phase row")
				}
				for j := 0; j < 3; j++ {
					if r.EventDraws[j] != planetRaw(t, want.Draws[j]) || r.EventDraws[j] != portSingleBytes(rng.Float32()) || r.CargoRates[j] != planetRaw(t, want.Rates[j]) {
						t.Fatal("raw row arithmetic/draw")
					}
				}
				count++
			}
			if rng.State() != stats.FinalState {
				t.Fatal("eager draws continuation")
			}
			if !bytes.Equal(before, saved) || !reflect.DeepEqual(in.Clocks, clocks) || in.State != c.State {
				t.Fatal("input mutation")
			}
			written := map[int]bool{}
			for _, r := range in.Clocks {
				for _, o := range []int{41, 45, 49, 53, 57, 61, 65, 69, 77, 89, 113, 117, 125, 129} {
					for j := 0; j < 4; j++ {
						written[(r.Record-1)*RecordSize+o+j] = true
					}
				}
			}
			for i, b := range got {
				if !written[i] && b != before[i] {
					t.Fatal("unwritten byte changed")
				}
			}
			for _, r := range in.Clocks {
				a := (r.Record-1)*RecordSize + 89
				if [4]byte(got[a:a+4]) != r.TimerMinutes {
					t.Fatal("raw TIMER residue changed")
				}
			}
			got[0] ^= 255
			if !bytes.Equal(before, saved) {
				t.Fatal("output aliases before")
			}
		})
	}
	if count != 27 {
		t.Fatal("active planet inventory")
	}
}
func planetPut(w []byte, r, o int, v float64) {
	b := portSingleBytes(float32(v))
	a := (r-1)*RecordSize + o
	copy(w[a:a+4], b[:])
}
func TestEvolvedPlanetInterestRoundBeforeFloor(t *testing.T) {
	d := planetLoad(t)
	c := d.Cases[0]
	w := unpack(t, d.Worlds[c.BeforeSHA])
	in := planetInputs(t, c)
	// Synthetic source-order boundary: .01 SINGLE lies slightly below .01, but
	// the complete interest expression rounds to SINGLE before INT floors it.
	planetPut(w, 4053, 117, 1000000)
	planetPut(w, 4053, 77, 0)
	planetPut(w, 4053, 89, 0)
	planetPut(w, 4053, 41, 296)
	got, _, e := ReplayEvolvedPlanets(w, in)
	if e != nil {
		t.Fatal(e)
	}
	a := (4053 - 1) * RecordSize
	if v := portSingleValue([4]byte(got[a+117 : a+121])); v != 1100000 {
		t.Fatalf("bank = %v", v)
	}
	if v := portSingleValue([4]byte(got[a+77 : a+81])); v != 1000 {
		t.Fatalf("old-bank ground bonus = %v", v)
	}
}
func TestEvolvedPlanetAtomicRefusals(t *testing.T) {
	d := planetLoad(t)
	c := d.Cases[1]
	cases := map[string]func([]byte, *EvolvedPlanetInputs){
		"state":              func(w []byte, i *EvolvedPlanetInputs) { i.State = 1 << 24 },
		"clock inventory":    func(w []byte, i *EvolvedPlanetInputs) { i.Clocks = i.Clocks[:3] },
		"record attribution": func(w []byte, i *EvolvedPlanetInputs) { i.Clocks[1].Record = 4052 },
		"calendar":           func(w []byte, i *EvolvedPlanetInputs) { i.Clocks[0].Day-- },
		"midnight bound":     func(w []byte, i *EvolvedPlanetInputs) { i.Clocks[0].TimerMinutes = encode(1) },
		"geometry":           func(w []byte, i *EvolvedPlanetInputs) { planetPut(w, 1, 53, 50) },
		"human":              func(w []byte, i *EvolvedPlanetInputs) { planetPut(w, 2, 85, 1) },
		"unknown planet":     func(w []byte, i *EvolvedPlanetInputs) { planetPut(w, 4054, 85, 1) },
		"name":               func(w []byte, i *EvolvedPlanetInputs) { w[(4053-1)*RecordSize] = 'X' },
		"owner":              func(w []byte, i *EvolvedPlanetInputs) { planetPut(w, 4053, 73, 1) },
		"bank":               func(w []byte, i *EvolvedPlanetInputs) { planetPut(w, 4053, 117, 30000004) },
		"underflow-scale stock": func(w []byte, i *EvolvedPlanetInputs) {
			a := (4053-1)*RecordSize + 113
			copy(w[a:a+4], []byte{1, 0, 0, 1})
		},
		"zero elapsed": func(w []byte, i *EvolvedPlanetInputs) { planetPut(w, 4052, 41, 307); planetPut(w, 4052, 89, 0) },
		"stock":        func(w []byte, i *EvolvedPlanetInputs) { planetPut(w, 4053, 57, -1) },
		"reserved":     func(w []byte, i *EvolvedPlanetInputs) { planetPut(w, 4151, 133, 1) },
		"missing link": func(w []byte, i *EvolvedPlanetInputs) {
			for s := 1; s <= 3000; s++ {
				a := (50+s)*RecordSize + 93
				if portSingleValue([4]byte(w[a:a+4])) == 2 {
					planetPut(w, 51+s, 93, 0)
				}
			}
		},
		"late phase selected plague": func(w []byte, i *EvolvedPlanetInputs) {
			for j := 0; j < 3; j++ {
				planetPut(w, 4052, 45+4*j, 1000)
				planetPut(w, 4052, 57+4*j, 0)
				planetPut(w, 4053, 45+4*j, 200000)
				planetPut(w, 4053, 57+4*j, 0)
			}
			for state := uint32(0); state < 10000; state++ {
				g := qbrng.New(state)
				for j := 0; j < 3; j++ {
					g.Float32()
				}
				a, b := g.Float32(), g.Float32()
				if a > .8 && b < .1 {
					i.State = state
					return
				}
			}
			t.Fatal("synthetic seed")
		},
	}
	for name, change := range cases {
		t.Run(name, func(t *testing.T) {
			w := unpack(t, d.Worlds[c.BeforeSHA])
			in := planetInputs(t, c)
			change(w, &in)
			saved := bytes.Clone(w)
			clocks := append([]PlanetClock(nil), in.Clocks...)
			got, stats, e := ReplayEvolvedPlanets(w, in)
			if e == nil || got != nil || !reflect.DeepEqual(stats, EvolvedPlanetStats{}) {
				t.Fatal("non-atomic refusal")
			}
			if !bytes.Equal(w, saved) || !reflect.DeepEqual(clocks, in.Clocks) {
				t.Fatal("mutated source on refusal")
			}
		})
	}
	for _, w := range [][]byte{nil, make([]byte, WorldRecords*RecordSize-1)} {
		if got, _, e := ReplayEvolvedPlanets(w, planetInputs(t, c)); e == nil || got != nil {
			t.Fatal("world extent")
		}
	}
}

func TestEvolvedPlanetRollbackCatchupAndZeroState(t *testing.T) {
	d := planetLoad(t)
	c := d.Cases[0]
	w := unpack(t, d.Worlds[c.BeforeSHA])
	in := planetInputs(t, c)
	in.State = 0
	planetPut(w, 4053, 41, 307)
	planetPut(w, 4053, 89, 0)
	_, stats, e := ReplayEvolvedPlanets(w, in)
	if e != nil {
		t.Fatal(e)
	}
	if stats.InitialState != 0 || stats.Rows[0].Elapsed != encode(10) || stats.Draws != 3 {
		t.Fatal("rollback cap / explicit zero RNG state")
	}
}
