package qbmaint

import (
	"bytes"
	"encoding/json"
	"os"
	"reflect"
	"strings"
	"testing"
)

type occupiedRouteCase struct {
	continuationCase
	WandererDay    int    `json:"wanderer_day"`
	XannoronDay    int    `json:"xannoron_day"`
	BaseDay        int    `json:"base_day"`
	Timer          string `json:"xannoron_timer"`
	BaseAttempts   []int  `json:"base_attempts"`
	BirthGround    int    `json:"birth_ground"`
	BirthBank      string `json:"birth_bank"`
	BirthTimestamp string `json:"birth_timestamp"`
	Paths          []struct {
		Group, Origin, Target, Fallback, Candidate, Preferred, Strength int
		CandidateDraws                                                  int `json:"candidate_draws"`
		InterceptionDraws                                               int `json:"interception_draws"`
		Route, Entered                                                  []int
	} `json:"routes"`
	Events []struct {
		Kind                                    string
		Group, Sector, Force, Ground, Defenders int
		InitialForce                            int    `json:"initial_force"`
		RawForce                                int    `json:"raw_force"`
		InitialGround                           int    `json:"initial_ground"`
		InitialDefenders                        int    `json:"initial_defenders"`
		XDamage                                 int    `json:"x_damage"`
		DefenderDamage                          int    `json:"defender_damage"`
		InitialState                            uint32 `json:"initial_rng_state"`
		FinalState                              uint32 `json:"final_rng_state"`
		Draws                                   int    `json:"rng_draws"`
	}
}
type occupiedRouteFixture struct {
	Format      string
	Worlds      map[string]string
	Cases       []occupiedRouteCase
	Comparisons int `json:"native_six_file_comparisons"`
	Witnesses   int `json:"native_rng_witnesses"`
}

func occupiedRouteLoad(t *testing.T) occupiedRouteFixture {
	t.Helper()
	b, e := os.ReadFile("testdata/occupied_routing.json")
	if e != nil {
		t.Fatal(e)
	}
	var d occupiedRouteFixture
	if e = json.Unmarshal(b, &d); e != nil {
		t.Fatal(e)
	}
	if d.Format != "qb-occupied-routing-v1" || len(d.Cases) != 30 || d.Comparisons != 180 || d.Witnesses != 1872 {
		t.Fatal("qualified inventory")
	}
	return d
}
func occupiedRouteInputs(t *testing.T, c occupiedRouteCase) OccupiedRoutingInputs {
	return OccupiedRoutingInputs{State: c.State, Helpers: continuationInputs(t, c.continuationCase).Helpers, Creation: ConvergenceCreationClocks{WandererDay: c.WandererDay, XannoronDay: c.XannoronDay, BaseDay: c.BaseDay, XannoronTimer: planetRaw(t, c.Timer)}}
}
func TestOccupiedRoutingQualifiedPhasesAndEconomyHandoff(t *testing.T) {
	d := occupiedRouteLoad(t)
	economy := occupiedPlanetLoad(t)
	events := 0
	for _, c := range d.Cases {
		t.Run(c.Name, func(t *testing.T) {
			before := unpack(t, d.Worlds[c.BeforeSHA])
			if digest(before) != c.BeforeSHA {
				t.Fatal("before identity")
			}
			saved := bytes.Clone(before)
			in := occupiedRouteInputs(t, c)
			recipe, _ := json.Marshal(in)
			world, stats, e := ReplayOccupiedHomeMobile(before, in)
			if e != nil {
				t.Fatal(e)
			}
			if digest(world) != c.SHA || stats.InitialState != c.State || stats.FinalState != c.Final || stats.Draws != c.Draws || stats.Groups != c.Groups || stats.WandererSector != c.Wanderer || stats.BaseSector != c.Base || stats.Allocations != 19 {
				t.Fatalf("complete phase/receipt mismatch: state %x/%x draws %d/%d", stats.FinalState, c.Final, stats.Draws, c.Draws)
			}
			if !reflect.DeepEqual(stats.WandererAttempts, c.Attempts) || stats.Births == nil || !reflect.DeepEqual(stats.Births.BaseAttempts, c.BaseAttempts) || stats.Births.InitialGround+stats.XannoronIncrement != c.BirthGround || stats.Births.Bank != planetRaw(t, c.BirthBank) || stats.Births.Timestamp != planetRaw(t, c.BirthTimestamp) {
				t.Fatal("birth/rejection receipts")
			}
			if len(stats.Seeds) != len(c.Seeds) || len(stats.Routes) != len(c.Paths) || len(stats.Entered) != len(c.Paths) || len(stats.Events) != len(c.Events) {
				t.Fatal("receipt inventories")
			}
			for i, s := range stats.Seeds {
				v := c.Seeds[i]
				if s.Clock.Family != v.Family || s.Clock.Caller != v.Caller || s.Clock.Timer != planetRaw(t, v.Timer) || s.OldState != v.Old || s.SeededState != v.Seed {
					t.Fatal("computed helper reseed", i)
				}
			}
			for i, r := range stats.Routes {
				v := c.Paths[i]
				want := ContinuationRoute{Group: v.Group, Origin: v.Origin, Target: v.Target, Fallback: v.Fallback, Candidate: v.Candidate, Preferred: v.Preferred, Strength: v.Strength, CandidateDraws: v.CandidateDraws, InterceptionDraws: v.InterceptionDraws, Route: v.Route}
				if !reflect.DeepEqual(r, want) || !reflect.DeepEqual(stats.Entered[i], v.Entered) {
					t.Fatal("source traversal/pursuit/scans", i)
				}
			}
			for i, event := range stats.Events {
				v := c.Events[i]
				events++
				if event.Kind != v.Kind || event.Group != v.Group || event.Sector != v.Sector {
					t.Fatal("event order/context")
				}
				if event.Kind == "defense" {
					want := ForeignDefenseStats{InitialForce: v.InitialForce, Force: v.Force, InitialDefenders: v.InitialDefenders, Defenders: v.Defenders, XDamage: v.XDamage, DefenderDamage: v.DefenderDamage, Draws: v.Draws, InitialState: v.InitialState, FinalState: v.FinalState, PreferredCleared: v.Defenders == 0}
					if event.Defense == nil || event.Ground != nil || !reflect.DeepEqual(*event.Defense, want) {
						t.Fatal("defense handoff")
					}
				} else {
					want := NeutralGroundStats{InitialForce: v.InitialForce, RawForce: v.RawForce, Force: v.Force, InitialGround: v.InitialGround, Ground: v.Ground, Draws: v.Draws, InitialState: v.InitialState, FinalState: v.FinalState}
					if event.Ground == nil || event.Defense != nil || !reflect.DeepEqual(*event.Ground, want) {
						t.Fatal("ground handoff")
					}
				}
			}
			after, _ := json.Marshal(in)
			if !bytes.Equal(recipe, after) || !bytes.Equal(saved, before) {
				t.Fatal("source mutation")
			}
			found := false
			for _, p := range economy.Cases {
				if p.Name != c.Name {
					continue
				}
				found = true
				initial := unpack(t, economy.Worlds[p.Initial])
				schedule := PortSchedule{Days: p.Ports.Days, Capped: true}
				for _, s := range p.Ports.Timers {
					schedule.TimerMinutes = append(schedule.TimerMinutes, planetRaw(t, s))
				}
				block, _, e := ReplayCleanPorts(initial, schedule)
				if e != nil {
					t.Fatal(e)
				}
				work := bytes.Clone(initial)
				copy(work[PortStart:PortStart+PortCount*RecordSize], block)
				work, ps, e := ReplayOccupiedPlanets(work, occupiedPlanetInputs(t, p))
				if e != nil || digest(work) != c.BeforeSHA {
					t.Fatal("actual Go economy handoff", e)
				}
				derived := in
				derived.State = ps.FinalState
				out, actual, e := ReplayOccupiedHomeMobile(work, derived)
				if e != nil || digest(out) != c.SHA || !reflect.DeepEqual(actual, stats) {
					t.Fatal("full Go port/economy/routing composition", e)
				}
			}
			if !found {
				t.Fatal("economy inputs")
			}
			world[0] ^= 255
			if !bytes.Equal(before, saved) {
				t.Fatal("output alias")
			}
			if strings.HasPrefix(c.Name, "route-mercenary-37/") {
				var fourth *ContinuationRoute
				for i := range stats.Routes {
					if stats.Routes[i].Group == 4 {
						fourth = &stats.Routes[i]
						break
					}
				}
				if fourth == nil || fourth.Preferred != 0 || fourth.CandidateDraws != 50 || fourth.Target != fourth.Fallback {
					t.Fatal("defender victory did not clear pursuit before next candidate scan")
				}
			}
		})
	}
	if events != 120 {
		t.Fatal("combat inventory", events)
	}
}

func TestOccupiedRoutingAtomicRefusals(t *testing.T) {
	d := occupiedRouteLoad(t)
	c := d.Cases[0]
	changes := map[string]func([]byte, *OccupiedRoutingInputs){
		"state":                     func(w []byte, in *OccupiedRoutingInputs) { in.State = 1 << 24 },
		"creation day":              func(w []byte, in *OccupiedRoutingInputs) { in.Creation.BaseDay = 307 },
		"creation TIMER":            func(w []byte, in *OccupiedRoutingInputs) { in.Creation.XannoronTimer = encode(-1) },
		"geometry":                  func(w []byte, in *OccupiedRoutingInputs) { planetPut(w, 1, 53, 52) },
		"human":                     func(w []byte, in *OccupiedRoutingInputs) { planetPut(w, 2, 85, 1) },
		"tax":                       func(w []byte, in *OccupiedRoutingInputs) { planetPut(w, 3053, 89, 1) },
		"revenges":                  func(w []byte, in *OccupiedRoutingInputs) { planetPut(w, 72, 105, 1) },
		"pointer":                   func(w []byte, in *OccupiedRoutingInputs) { planetPut(w, 53, 105, 854) },
		"force":                     func(w []byte, in *OccupiedRoutingInputs) { planetPut(w, 51+849, 81, 9999) },
		"unqualified neutral force": func(w []byte, in *OccupiedRoutingInputs) { planetPut(w, 905, 81, 100000); planetPut(w, 905, 85, 0) },
		"foreign owner":             func(w []byte, in *OccupiedRoutingInputs) { planetPut(w, 905, 81, 37); planetPut(w, 905, 85, 2) },
		"mine":                      func(w []byte, in *OccupiedRoutingInputs) { planetPut(w, 905, 129, 1) },
		"link":                      func(w []byte, in *OccupiedRoutingInputs) { planetPut(w, 52, 93, 2) },
		"warp":                      func(w []byte, in *OccupiedRoutingInputs) { planetPut(w, 52, 41, 3001) },
		"unknown planet":            func(w []byte, in *OccupiedRoutingInputs) { planetPut(w, 4055, 85, 1) },
		"before economy":            func(w []byte, in *OccupiedRoutingInputs) { planetPut(w, 4053, 41, 305) },
		"bank":                      func(w []byte, in *OccupiedRoutingInputs) { planetPut(w, 4053, 117, 1) },
		"unconsumed clock": func(w []byte, in *OccupiedRoutingInputs) {
			in.Helpers = append(in.Helpers, in.Helpers[len(in.Helpers)-1])
		},
		"exhausted late clock": func(w []byte, in *OccupiedRoutingInputs) { in.Helpers = in.Helpers[:len(in.Helpers)-1] },
		"late caller":          func(w []byte, in *OccupiedRoutingInputs) { in.Helpers[len(in.Helpers)-1].Caller ^= 1 },
		"late TIMER":           func(w []byte, in *OccupiedRoutingInputs) { in.Helpers[len(in.Helpers)-1].Timer = encode(-1) },
	}
	for name, change := range changes {
		t.Run(name, func(t *testing.T) {
			before := unpack(t, d.Worlds[c.BeforeSHA])
			in := occupiedRouteInputs(t, c)
			change(before, &in)
			saved := bytes.Clone(before)
			recipe, _ := json.Marshal(in)
			out, stats, e := ReplayOccupiedHomeMobile(before, in)
			if e == nil || out != nil || !reflect.DeepEqual(stats, OccupiedRoutingStats{}) {
				t.Fatal("unsupported/partial output published")
			}
			after, _ := json.Marshal(in)
			if !bytes.Equal(recipe, after) || !bytes.Equal(saved, before) {
				t.Fatal("failed replay mutated caller data")
			}
		})
	}
	if out, _, e := ReplayOccupiedHomeMobile(nil, occupiedRouteInputs(t, c)); e == nil || out != nil {
		t.Fatal("short world")
	}
	before := unpack(t, d.Worlds[c.BeforeSHA])
	in := occupiedRouteInputs(t, c)
	if _, _, e := ReplayConvergenceDayOneHomes(before, ConvergenceDayOneInputs{State: in.State, WandererDay: 306, XannoronDay: 306, BaseDay: 306, XannoronTimer: in.Creation.XannoronTimer, Helpers: in.Helpers}); e == nil {
		t.Fatal("historical convergence admission broadened")
	}
}
