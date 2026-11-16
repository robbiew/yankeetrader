package qbmaint

import (
	"bytes"
	"encoding/json"
	"os"
	"reflect"
	"testing"
)

type occupiedPlanetCase struct {
	planetCase
	Initial string `json:"initial_before_sha256"`
	Ports   struct {
		Days   []int
		Timers []string `json:"timer_minutes"`
	}
}
type occupiedPlanetFixture struct {
	Format      string
	Worlds      map[string]string
	Cases       []occupiedPlanetCase
	Comparisons int `json:"native_six_file_comparisons"`
	Witnesses   int `json:"native_rng_witnesses"`
}

func occupiedPlanetLoad(t *testing.T) occupiedPlanetFixture {
	t.Helper()
	b, e := os.ReadFile("testdata/occupied_planets.json")
	if e != nil {
		t.Fatal(e)
	}
	var d occupiedPlanetFixture
	if e = json.Unmarshal(b, &d); e != nil {
		t.Fatal(e)
	}
	if d.Format != "qb-occupied-planets-v1" || len(d.Cases) != 30 || d.Comparisons != 180 || d.Witnesses != 1872 {
		t.Fatal("qualified inventory")
	}
	return d
}
func occupiedPlanetInputs(t *testing.T, c occupiedPlanetCase) OccupiedPlanetInputs {
	v := planetInputs(t, c.planetCase)
	return OccupiedPlanetInputs{State: v.State, Clocks: v.Clocks}
}
func TestOccupiedPlanetQualifiedPhasesAndGoPortHandoff(t *testing.T) {
	d := occupiedPlanetLoad(t)
	updates := 0
	empty := 0
	for _, c := range d.Cases {
		t.Run(c.Name, func(t *testing.T) {
			before := unpack(t, d.Worlds[c.BeforeSHA])
			if digest(before) != c.BeforeSHA {
				t.Fatal("before hash")
			}
			saved := bytes.Clone(before)
			in := occupiedPlanetInputs(t, c)
			clocks := append([]PlanetClock(nil), in.Clocks...)
			world, stats, e := ReplayOccupiedPlanets(before, in)
			if e != nil {
				t.Fatal(e)
			}
			if digest(world) != c.SHA || stats.InitialState != c.State || stats.FinalState != c.Final || stats.Draws != c.Draws || stats.Draws != 3*len(in.Clocks) || len(stats.Rows) != len(c.Rows) {
				t.Fatal("complete modeled phase/state mismatch")
			}
			if len(c.Rows) == 0 {
				empty++
				if !bytes.Equal(world, before) || stats.FinalState != in.State {
					t.Fatal("no-planet phase changed world/state")
				}
			}
			allowed := map[int]bool{}
			for i, row := range stats.Rows {
				want := c.Rows[i]
				updates++
				if row.Record != want.Record || row.Day != want.Day || row.Elapsed != planetRaw(t, want.Elapsed) || row.Ground != want.Ground {
					t.Fatal("economy receipt")
				}
				for j := 0; j < 3; j++ {
					if row.EventDraws[j] != planetRaw(t, want.Draws[j]) || row.CargoRates[j] != planetRaw(t, want.Rates[j]) {
						t.Fatal("draw/rate receipt")
					}
				}
				for _, o := range []int{41, 45, 49, 53, 57, 61, 65, 69, 77, 89, 113, 117, 125, 129} {
					for k := 0; k < 4; k++ {
						allowed[(row.Record-1)*RecordSize+o+k] = true
					}
				}
				a := (row.Record-1)*RecordSize + 89
				if !bytes.Equal(world[a:a+4], in.Clocks[i].TimerMinutes[:]) {
					t.Fatal("raw timestamp")
				}
			}
			for i, b := range world {
				if !allowed[i] && b != before[i] {
					t.Fatal("write outside qualified fields", i)
				}
			}
			if !bytes.Equal(before, saved) || !reflect.DeepEqual(in.Clocks, clocks) {
				t.Fatal("input mutation")
			}
			// Build the phase input from actual Go ports, not the Python phase world.
			initial := unpack(t, d.Worlds[c.Initial])
			if digest(initial) != c.Initial {
				t.Fatal("initial hash")
			}
			schedule := PortSchedule{Days: c.Ports.Days, Capped: true}
			for _, s := range c.Ports.Timers {
				schedule.TimerMinutes = append(schedule.TimerMinutes, planetRaw(t, s))
			}
			block, _, e := ReplayCleanPorts(initial, schedule)
			if e != nil {
				t.Fatal(e)
			}
			composed := bytes.Clone(initial)
			copy(composed[PortStart:PortStart+PortCount*RecordSize], block)
			if digest(composed) != c.BeforeSHA {
				t.Fatal("actual Go port handoff")
			}
			result, actual, e := ReplayOccupiedPlanets(composed, in)
			if e != nil || digest(result) != c.SHA || !reflect.DeepEqual(actual, stats) {
				t.Fatal("composed economy", e)
			}
			world[0] ^= 255
			if !bytes.Equal(before, saved) {
				t.Fatal("output aliases input")
			}
		})
	}
	if updates != 24 || empty != 9 {
		t.Fatal("complete update/no-planet inventory", updates, empty)
	}
}
func TestOccupiedPlanetAtomicRefusals(t *testing.T) {
	d := occupiedPlanetLoad(t)
	var c occupiedPlanetCase
	for _, v := range d.Cases {
		if len(v.Clocks) == 2 {
			c = v
			break
		}
	}
	cases := map[string]func([]byte, *OccupiedPlanetInputs){
		"state":         func(w []byte, in *OccupiedPlanetInputs) { in.State = 1 << 24 },
		"geometry":      func(w []byte, in *OccupiedPlanetInputs) { planetPut(w, 1, 61, 4052) },
		"watermark":     func(w []byte, in *OccupiedPlanetInputs) { planetPut(w, 1, 81, 306) },
		"human":         func(w []byte, in *OccupiedPlanetInputs) { planetPut(w, 2, 85, 1) },
		"third slot":    func(w []byte, in *OccupiedPlanetInputs) { planetPut(w, 4055, 85, 1) },
		"missing clock": func(w []byte, in *OccupiedPlanetInputs) { in.Clocks = in.Clocks[:1] },
		"order":         func(w []byte, in *OccupiedPlanetInputs) { in.Clocks[0], in.Clocks[1] = in.Clocks[1], in.Clocks[0] },
		"late date":     func(w []byte, in *OccupiedPlanetInputs) { in.Clocks[1].Day = 307 },
		"late TIMER":    func(w []byte, in *OccupiedPlanetInputs) { in.Clocks[1].TimerMinutes = encode(1) },
		"owner":         func(w []byte, in *OccupiedPlanetInputs) { planetPut(w, 4054, 73, 1) },
		"bank":          func(w []byte, in *OccupiedPlanetInputs) { planetPut(w, 4054, 117, 1) },
		"stock":         func(w []byte, in *OccupiedPlanetInputs) { planetPut(w, 4054, 57, 1) },
		"ground":        func(w []byte, in *OccupiedPlanetInputs) { planetPut(w, 4054, 77, 499999) },
		"rate":          func(w []byte, in *OccupiedPlanetInputs) { planetPut(w, 4054, 45, 1001) },
		"old date":      func(w []byte, in *OccupiedPlanetInputs) { planetPut(w, 4054, 41, 304) },
		"reserved":      func(w []byte, in *OccupiedPlanetInputs) { planetPut(w, 4054, 133, 1) },
		"name":          func(w []byte, in *OccupiedPlanetInputs) { w[4053*RecordSize] = 1 },
		"padding":       func(w []byte, in *OccupiedPlanetInputs) { w[4053*RecordSize+40] = 'X' },
		"length":        func(w []byte, in *OccupiedPlanetInputs) { planetPut(w, 4054, 85, 42) },
		"link":          func(w []byte, in *OccupiedPlanetInputs) { planetPut(w, 52, 93, 3) },
	}
	for name, change := range cases {
		t.Run(name, func(t *testing.T) {
			before := unpack(t, d.Worlds[c.BeforeSHA])
			in := occupiedPlanetInputs(t, c)
			change(before, &in)
			saved := bytes.Clone(before)
			clocks := append([]PlanetClock(nil), in.Clocks...)
			out, stats, e := ReplayOccupiedPlanets(before, in)
			if e == nil || out != nil || !reflect.DeepEqual(stats, EvolvedPlanetStats{}) {
				t.Fatal("partial/unsupported output")
			}
			if !bytes.Equal(saved, before) || !reflect.DeepEqual(clocks, in.Clocks) {
				t.Fatal("failed replay mutated input")
			}
		})
	}
	if out, _, e := ReplayOccupiedPlanets(nil, OccupiedPlanetInputs{}); e == nil || out != nil {
		t.Fatal("short world")
	}
	before := unpack(t, d.Worlds[c.BeforeSHA])
	if _, _, e := ReplayEvolvedPlanets(before, planetInputs(t, c.planetCase)); e == nil {
		t.Fatal("older named convergence gate broadened")
	}
}
func TestOccupiedPlanetZeroAliasesAndWiderGroundFloor(t *testing.T) {
	d := occupiedPlanetLoad(t)
	var c occupiedPlanetCase
	for _, v := range d.Cases {
		if len(v.Clocks) == 1 {
			c = v
			break
		}
	}
	before := unpack(t, d.Worlds[c.BeforeSHA])
	in := occupiedPlanetInputs(t, c)
	r := in.Clocks[0].Record
	alias := [4]byte{0xde, 0xad, 0x80, 0}
	in.Clocks[0].TimerMinutes = alias
	// Numeric zero admission does not normalize untouched reserved bytes.
	a := (r-1)*RecordSize + 133
	copy(before[a:a+4], alias[:])
	world, stats, e := ReplayOccupiedPlanets(before, in)
	if e != nil {
		t.Fatal(e)
	}
	if stats.Rows[0].Ground != 504999 || stats.Rows[0].Elapsed != encode(1) {
		t.Fatal("wider INT floor was replaced by evolved SINGLE rounding")
	}
	at := (r-1)*RecordSize + 89
	if !bytes.Equal(world[at:at+4], alias[:]) || !bytes.Equal(world[a:a+4], alias[:]) {
		t.Fatal("zero residues normalized")
	}
}
