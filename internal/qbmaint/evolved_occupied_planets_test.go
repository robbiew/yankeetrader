package qbmaint

import (
	"bytes"
	"encoding/json"
	"github.com/robbiew/yankeetrader/internal/qbrng"
	"os"
	"reflect"
	"strings"
	"testing"
)

func evolvedOccupiedLoad(t *testing.T) planetFixture {
	t.Helper()
	b, e := os.ReadFile("testdata/evolved_occupied_planets.json")
	if e != nil {
		t.Fatal(e)
	}
	var d planetFixture
	if e = json.Unmarshal(b, &d); e != nil {
		t.Fatal(e)
	}
	if d.Format != "qb-evolved-occupied-planet-v1" || len(d.Cases) != 24 || d.Comparisons != 144 || d.Witnesses != 1242 {
		t.Fatal("coverage")
	}
	return d
}
func TestEvolvedOccupiedPlanetQualifiedPhases(t *testing.T) {
	d := evolvedOccupiedLoad(t)
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
			got, stats, e := ReplayEvolvedOccupiedPlanets(before, in)
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
	if count != 78 {
		t.Fatal("active planet inventory")
	}
}

func TestEvolvedOccupiedPlanetAtomicRefusals(t *testing.T) {
	d := evolvedOccupiedLoad(t)
	c := d.Cases[0]
	tests := map[string]func([]byte, *EvolvedPlanetInputs){
		"geometry":        func(w []byte, in *EvolvedPlanetInputs) { planetPut(w, 1, 53, 52) },
		"human":           func(w []byte, in *EvolvedPlanetInputs) { planetPut(w, 2, 85, 1) },
		"before day":      func(w []byte, in *EvolvedPlanetInputs) { planetPut(w, 1, 81, 308) },
		"missing clocks":  func(w []byte, in *EvolvedPlanetInputs) { in.Clocks = in.Clocks[:len(in.Clocks)-1] },
		"extra clock":     func(w []byte, in *EvolvedPlanetInputs) { in.Clocks = append(in.Clocks, in.Clocks[0]) },
		"clock order":     func(w []byte, in *EvolvedPlanetInputs) { in.Clocks[0], in.Clocks[1] = in.Clocks[1], in.Clocks[0] },
		"clock day":       func(w []byte, in *EvolvedPlanetInputs) { in.Clocks[0].Day++ },
		"late clock":      func(w []byte, in *EvolvedPlanetInputs) { in.Clocks[len(in.Clocks)-1].TimerMinutes = encode(1) },
		"negative clock":  func(w []byte, in *EvolvedPlanetInputs) { in.Clocks[0].TimerMinutes = encode(-1) },
		"state":           func(w []byte, in *EvolvedPlanetInputs) { in.State = 1 << 24 },
		"name":            func(w []byte, in *EvolvedPlanetInputs) { w[4051*137] ^= 1 },
		"home owner":      func(w []byte, in *EvolvedPlanetInputs) { planetPut(w, 4052, 73, -1) },
		"old date":        func(w []byte, in *EvolvedPlanetInputs) { planetPut(w, 4052, 41, 306) },
		"prior minute":    func(w []byte, in *EvolvedPlanetInputs) { planetPut(w, 4052, 89, 1) },
		"reserved":        func(w []byte, in *EvolvedPlanetInputs) { planetPut(w, 4151, 121, 1001) },
		"bank":            func(w []byte, in *EvolvedPlanetInputs) { planetPut(w, 4151, 117, 30000004) },
		"ground":          func(w []byte, in *EvolvedPlanetInputs) { planetPut(w, 4151, 77, 600001) },
		"rates":           func(w []byte, in *EvolvedPlanetInputs) { planetPut(w, 4151, 45, 0) },
		"stock":           func(w []byte, in *EvolvedPlanetInputs) { planetPut(w, 4151, 129, -1) },
		"tiny stock":      func(w []byte, in *EvolvedPlanetInputs) { planetPut(w, 4151, 129, 1.0/(1<<25)) },
		"additional slot": func(w []byte, in *EvolvedPlanetInputs) { planetPut(w, 4055, 85, 1) },
		"missing link": func(w []byte, in *EvolvedPlanetInputs) {
			for r := 52; r <= 3051; r++ {
				if portSingleValue([4]byte(w[(r-1)*137+93:(r-1)*137+97])) == 100 {
					planetPut(w, r, 93, 0)
				}
			}
		},
		"duplicate link": func(w []byte, in *EvolvedPlanetInputs) { planetPut(w, 52, 93, 100) },
	}
	for name, change := range tests {
		t.Run(name, func(t *testing.T) {
			w := unpack(t, d.Worlds[c.BeforeSHA])
			in := planetInputs(t, c)
			change(w, &in)
			saved := bytes.Clone(w)
			recipe, _ := json.Marshal(in)
			out, s, e := ReplayEvolvedOccupiedPlanets(w, in)
			after, _ := json.Marshal(in)
			if e == nil || out != nil || !reflect.DeepEqual(s, EvolvedPlanetStats{}) || !bytes.Equal(w, saved) || !bytes.Equal(recipe, after) {
				t.Fatal("non-atomic refusal", e)
			}
		})
	}
	w := unpack(t, d.Worlds[c.BeforeSHA])
	in := planetInputs(t, c)
	if _, _, e := ReplayEvolvedPlanets(w, in); e == nil {
		t.Fatal("convergence admission widened")
	}
	if _, _, e := ReplayOccupiedPlanets(w, OccupiedPlanetInputs{State: in.State, Clocks: in.Clocks}); e == nil {
		t.Fatal("initial occupied admission widened")
	}
	if _, s, e := ReplayEvolvedOccupiedPlanets(w[:100], in); e == nil || !reflect.DeepEqual(s, EvolvedPlanetStats{}) {
		t.Fatal("short world")
	}
}

func TestEvolvedOccupiedPlanetLateEventAtomic(t *testing.T) {
	d := evolvedOccupiedLoad(t)
	c := d.Cases[0]
	w := unpack(t, d.Worlds[c.BeforeSHA])
	in := planetInputs(t, c)
	for _, row := range in.Clocks {
		for _, o := range []int{45, 49, 53} {
			planetPut(w, row.Record, o, 1)
		}
		for _, o := range []int{57, 61, 65, 69, 113, 117, 125, 129} {
			planetPut(w, row.Record, o, 0)
		}
	}
	last := in.Clocks[len(in.Clocks)-1].Record
	for _, o := range []int{45, 49, 53} {
		planetPut(w, last, o, 200000)
	}
	found := false
	for seed := uint32(0); seed < 100000; seed++ {
		r := qbrng.New(seed)
		for i := 0; i < 3*(len(in.Clocks)-1); i++ {
			r.Float32()
		}
		a, b := r.Float32(), r.Float32()
		if float32(a*606000) > float32(float32(b*1000000)+100000) {
			in.State = seed
			found = true
			break
		}
	}
	if !found {
		t.Fatal("real LCG event control")
	}
	saved := bytes.Clone(w)
	out, s, e := ReplayEvolvedOccupiedPlanets(w, in)
	if e == nil || !strings.Contains(e.Error(), "selected event") || out != nil || !reflect.DeepEqual(s, EvolvedPlanetStats{}) || !bytes.Equal(w, saved) {
		t.Fatal("late event must refuse whole phase", e)
	}
}

func TestEvolvedOccupiedPlanetFractionalAndInterestBoundaries(t *testing.T) {
	d := evolvedOccupiedLoad(t)
	c := d.Cases[0]
	for _, fractional := range []bool{false, true} {
		w := unpack(t, d.Worlds[c.BeforeSHA])
		in := planetInputs(t, c)
		// Use the ordinary one-day Xannoron interval, keeping the inherited home
		// timestamp and all other active planets' source contexts intact.
		planetPut(w, 4151, 117, 1000000)
		planetPut(w, 4151, 77, 0)
		planetPut(w, 4151, 89, 0)
		for i := range in.Clocks {
			if in.Clocks[i].Record == 4151 {
				in.Clocks[i].TimerMinutes = [4]byte{}
				if fractional {
					in.Clocks[i].TimerMinutes = portSingleBytes(.5)
				}
			}
		}
		got, s, e := ReplayEvolvedOccupiedPlanets(w, in)
		if e != nil {
			t.Fatal(e)
		}
		row := s.Rows[len(s.Rows)-1]
		if !fractional {
			at := 4150 * 137
			if portSingleValue([4]byte(got[at+117:at+121])) != 1010000 || portSingleValue([4]byte(got[at+77:at+81])) != 100 {
				t.Fatal("round complete SINGLE expression before INT; old-bank ground bonus")
			}
		} else if portSingleValue(row.Elapsed) <= 1 || row.Elapsed != portSingleBytes(1.0003472566604614) {
			t.Fatal("fractional TIMER minutes must not truncate to whole minute")
		}
	}
}
