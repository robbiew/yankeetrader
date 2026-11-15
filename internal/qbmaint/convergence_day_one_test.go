package qbmaint

import (
	"bytes"
	"encoding/json"
	"os"
	"reflect"
	"slices"
	"strings"
	"testing"

	"github.com/robbiew/yankeetrader/internal/qbrng"
)

type dayOneCase struct {
	continuationCase
	WandererDay     int    `json:"wanderer_day"`
	XannoronDay     int    `json:"xannoron_day"`
	BaseDay         int    `json:"base_day"`
	Timer           string `json:"xannoron_timer"`
	Timestamp, Bank string
	Ground          int
	Created         []string
	BaseAttempts    []int `json:"base_attempts"`
}
type dayOneFixture struct {
	Format      string
	Worlds      map[string]string
	Cases       []dayOneCase
	Comparisons int `json:"native_six_file_comparisons"`
	Witnesses   int `json:"native_rng_witnesses"`
	Fields      int `json:"native_cache_fields"`
}

func dayOneLoad(t *testing.T) dayOneFixture {
	t.Helper()
	b, e := os.ReadFile("testdata/convergence_day_one.json")
	if e != nil {
		t.Fatal(e)
	}
	var d dayOneFixture
	if e = json.Unmarshal(b, &d); e != nil {
		t.Fatal(e)
	}
	if d.Format != "qb-convergence-day-one-v1" || len(d.Cases) != 3 || d.Comparisons != 54 || d.Witnesses != 501 || d.Fields != 1440 {
		t.Fatal("qualified inventory")
	}
	return d
}
func dayOneInputs(t *testing.T, c dayOneCase) ConvergenceDayOneInputs {
	t.Helper()
	return ConvergenceDayOneInputs{State: c.State, WandererDay: c.WandererDay, XannoronDay: c.XannoronDay, BaseDay: c.BaseDay, XannoronTimer: planetRaw(t, c.Timer), Helpers: continuationInputs(t, c.continuationCase).Helpers}
}
func TestQualifiedConvergenceDayOneHomes(t *testing.T) {
	d := dayOneLoad(t)
	for _, c := range d.Cases {
		t.Run(c.Name, func(t *testing.T) {
			before := unpack(t, d.Worlds[c.BeforeSHA])
			if digest(before) != c.BeforeSHA {
				t.Fatal("modeled before identity")
			}
			saved := bytes.Clone(before)
			in := dayOneInputs(t, c)
			helpers := append([]ContinuationClock(nil), in.Helpers...)
			out, s, e := ReplayConvergenceDayOneHomes(before, in)
			if e != nil {
				t.Fatal(e)
			}
			if digest(out) != c.SHA {
				t.Fatal("complete Python-qualified day-one world mismatch")
			}
			if s.Births == nil || s.Draws != c.Draws || s.FinalState != c.Final || s.InitialState != c.State || s.Groups != c.Groups || s.Cache != c.Cache || s.Allocations != 19 || s.WandererSector != c.Wanderer || s.BaseSector != c.Base || !slices.Equal(s.WandererAttempts, c.Attempts) || !slices.Equal(s.Births.BaseAttempts, c.BaseAttempts) || !slices.Equal(s.Births.Created[:], c.Created) || s.Births.Timestamp != planetRaw(t, c.Timestamp) || s.Births.Bank != planetRaw(t, c.Bank) || s.Births.InitialGround+s.XannoronIncrement != c.Ground {
				t.Fatalf("day-one phase statistics: %+v", s)
			}
			if len(s.Seeds) != len(c.Seeds) || len(s.Routes) != len(c.Routes) {
				t.Fatal("source activity inventory")
			}
			for i, v := range s.Seeds {
				w := c.Seeds[i]
				if v.Clock.Family != w.Family || v.Clock.Caller != w.Caller || v.Clock.Timer != planetRaw(t, w.Timer) || v.OldState != w.Old || v.SeededState != w.Seed {
					t.Fatal("helper chronology/seed")
				}
			}
			for i, v := range s.Routes {
				w := c.Routes[i]
				want := ContinuationRoute{Group: w.Group, Origin: w.Origin, Target: w.Target, Fallback: w.Fallback, Candidate: w.Candidate, Preferred: w.Preferred, Strength: w.Strength, CandidateDraws: w.CandidateDraws, InterceptionDraws: w.InterceptionDraws, Route: w.Route}
				if !reflect.DeepEqual(v, want) {
					t.Fatal("route activity")
				}
			}
			a := (4053 - 1) * RecordSize
			if !bytes.Equal(out[a:a+RecordSize], before[a:a+RecordSize]) {
				t.Fatal("Convergence Haven was masked or rewritten")
			}
			for _, r := range []int{4052, 4150, 4151} {
				for _, o := range []int{81, 93, 97, 101, 105, 109, 113, 121, 129, 133} {
					a := (r-1)*RecordSize + o
					if !bytes.Equal(out[a:a+4], before[a:a+4]) {
						t.Fatal("unassigned birth field reset")
					}
				}
			}
			if !bytes.Equal(saved, before) || !slices.Equal(in.Helpers, helpers) {
				t.Fatal("input mutated")
			}
			out[0] ^= 255
			if !bytes.Equal(saved, before) {
				t.Fatal("output alias")
			}
			if _, _, e := ReplayExistingHomeContinuation(before, ContinuationInputs{State: in.State, Helpers: in.Helpers}); e == nil {
				t.Fatal("existing-home API broadened")
			}
			if _, _, e := ReplayWandererBirth(before, WandererInputs{Day: 306, State: in.State, HelperTimer: in.Helpers[0].Timer}); e == nil {
				t.Fatal("historical birth API broadened")
			}
		})
	}
}
func TestGoConvergenceDayOnePortEconomyHomesAndTail(t *testing.T) {
	d := dayOneLoad(t)
	ports := evolvedLoad(t)
	planets := planetLoad(t)
	tails := evolvedTailLoad(t)
	count := 0
	for _, c := range d.Cases {
		var world []byte
		for _, p := range ports.Cases {
			if p.Name != c.Name {
				continue
			}
			s := EvolvedPortSchedule{Days: p.Days}
			for _, v := range p.Timers {
				s.TimerMinutes = append(s.TimerMinutes, planetRaw(t, v))
			}
			world = unpack(t, ports.Initial)
			block, _, e := ReplayEvolvedPorts(world, s)
			if e != nil {
				t.Fatal(e)
			}
			copy(world[PortStart:], block)
		}
		if world == nil {
			t.Fatal("source port schedule")
		}
		for _, p := range planets.Cases {
			if p.Name != c.Name {
				continue
			}
			if digest(world) != p.BeforeSHA {
				t.Fatal("Go port handoff")
			}
			var e error
			var stats EvolvedPlanetStats
			world, stats, e = ReplayEvolvedPlanets(world, planetInputs(t, p))
			if e != nil {
				t.Fatal(e)
			}
			in := dayOneInputs(t, c)
			in.State = stats.FinalState
			if digest(world) != c.BeforeSHA || in.State != c.State {
				t.Fatal("Go economy handoff")
			}
			var home ContinuationStats
			world, home, e = ReplayConvergenceDayOneHomes(world, in)
			if e != nil {
				t.Fatal(e)
			}
			for _, tail := range tails.Cases {
				if tail.Name != "convergence/"+c.Name {
					continue
				}
				if digest(world) != tail.BeforeSHA || home.FinalState != tail.State {
					t.Fatal("Go home/mobile handoff")
				}
				ti := evolvedTailInputs(t, tail)
				ti.State = home.FinalState
				out, ts, e := ReplayEvolvedNPCTail(world, ti)
				if e != nil || digest(out) != tail.SHA || ts.FinalState != tail.Final {
					t.Fatal("Go day-one pipeline", e)
				}
				count++
			}
		}
	}
	if count != 3 {
		t.Fatal("day-one composition coverage")
	}
}
func TestConvergenceDayOneAtomicRefusals(t *testing.T) {
	d := dayOneLoad(t)
	c := d.Cases[0]
	cases := map[string]func([]byte, *ConvergenceDayOneInputs){
		"missing date":          func(w []byte, i *ConvergenceDayOneInputs) { i.WandererDay = 0 },
		"different date":        func(w []byte, i *ConvergenceDayOneInputs) { i.BaseDay = 307 },
		"state":                 func(w []byte, i *ConvergenceDayOneInputs) { i.State = 1 << 24 },
		"day":                   func(w []byte, i *ConvergenceDayOneInputs) { planetPut(w, 1, 81, 306) },
		"existing home":         func(w []byte, i *ConvergenceDayOneInputs) { planetPut(w, 4052, 85, 12) },
		"unknown planet":        func(w []byte, i *ConvergenceDayOneInputs) { planetPut(w, 4054, 85, 1) },
		"Haven owner":           func(w []byte, i *ConvergenceDayOneInputs) { planetPut(w, 4053, 73, 0) },
		"pre-economy Haven":     func(w []byte, i *ConvergenceDayOneInputs) { planetPut(w, 4053, 41, 305) },
		"creation timer":        func(w []byte, i *ConvergenceDayOneInputs) { i.XannoronTimer = encode(86400) },
		"sub-centisecond timer": func(w []byte, i *ConvergenceDayOneInputs) { i.XannoronTimer = portSingleBytes(.001) },
		"wrong helper":          func(w []byte, i *ConvergenceDayOneInputs) { i.Helpers[0].Caller = 0x437a },
		"missing Base clock":    func(w []byte, i *ConvergenceDayOneInputs) { i.Helpers = i.Helpers[:len(i.Helpers)-1] },
		"tail clock": func(w []byte, i *ConvergenceDayOneInputs) {
			i.Helpers = append(i.Helpers, ContinuationClock{Family: 1, Caller: 0x53b4})
		},
		"initial mines": func(w []byte, i *ConvergenceDayOneInputs) { planetPut(w, 52, 129, 1) },
	}
	for name, change := range cases {
		t.Run(name, func(t *testing.T) {
			w := unpack(t, d.Worlds[c.BeforeSHA])
			in := dayOneInputs(t, c)
			change(w, &in)
			saved := bytes.Clone(w)
			helpers := append([]ContinuationClock(nil), in.Helpers...)
			out, s, e := ReplayConvergenceDayOneHomes(w, in)
			if e == nil || out != nil || !reflect.DeepEqual(s, ContinuationStats{}) {
				t.Fatal("non-atomic refusal")
			}
			if !bytes.Equal(saved, w) || !slices.Equal(helpers, in.Helpers) {
				t.Fatal("mutated source on refusal")
			}
			if name == "missing Base clock" && !strings.Contains(e.Error(), "helper exhaustion") {
				t.Fatal("wrong late boundary", e)
			}
		})
	}
	if out, _, e := ReplayConvergenceDayOneHomes(nil, dayOneInputs(t, c)); e == nil || out != nil {
		t.Fatal("world extent")
	}
}
func TestConvergenceDayOneRawZeroCreationTimer(t *testing.T) {
	d := dayOneLoad(t)
	c := d.Cases[0]
	for _, raw := range [][4]byte{{}, {0, 0, 0x48, 0}} {
		w := unpack(t, d.Worlds[c.BeforeSHA])
		in := dayOneInputs(t, c)
		in.XannoronTimer = raw
		out, s, e := ReplayConvergenceDayOneHomes(w, in)
		if e != nil {
			t.Fatal(e)
		}
		a := (4151-1)*RecordSize + 89
		if [4]byte(out[a:a+4]) != raw || s.Births.Timestamp != raw || s.FinalState != c.Final || s.Draws != c.Draws {
			t.Fatal("zero FAC residue or RNG chronology changed")
		}
	}
}

func TestConvergenceDayOneRejectsUnqualifiedZeroGround(t *testing.T) {
	d := dayOneLoad(t)
	c := d.Cases[0]
	w := unpack(t, d.Worlds[c.BeforeSHA])
	in := dayOneInputs(t, c)
	found := false
	for seconds := 0; seconds < 86400; seconds++ {
		timer := encode(seconds)
		g := qbrng.New(in.State)
		g.RandomizeMBF(timer)
		sector := int(float32(g.Float32()*3000)) + 1
		a := (50+sector)*RecordSize + 93
		if portSingleValue([4]byte(w[a:a+4])) > 0 {
			continue
		}
		ground := int(float32(g.Float32() * 250))
		g.Float32()
		extra := int(float32(g.Float32() * 25))
		if ground+extra == 0 {
			in.Helpers[0].Timer = timer
			found = true
			break
		}
	}
	if !found {
		t.Fatal("synthetic zero-ground inputs")
	}
	saved := bytes.Clone(w)
	out, s, e := ReplayConvergenceDayOneHomes(w, in)
	if e == nil || !strings.Contains(e.Error(), "zero/out-of-range birth ground") || out != nil || !reflect.DeepEqual(s, ContinuationStats{}) || !bytes.Equal(w, saved) {
		t.Fatal("zero-ground qualification boundary", e)
	}
}
