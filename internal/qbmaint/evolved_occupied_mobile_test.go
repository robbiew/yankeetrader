package qbmaint

import (
	"bytes"
	"encoding/json"
	"os"
	"reflect"
	"testing"
)

func evolvedMobileLoad(t *testing.T) occupiedRouteFixture {
	t.Helper()
	b, e := os.ReadFile("testdata/evolved_occupied_mobile.json")
	if e != nil {
		t.Fatal(e)
	}
	var d occupiedRouteFixture
	if e = json.Unmarshal(b, &d); e != nil {
		t.Fatal(e)
	}
	if d.Format != "qb-evolved-occupied-mobile-v1" || len(d.Cases) != 24 || d.Comparisons != 144 || d.Witnesses != 1242 {
		t.Fatal("qualified inventory")
	}
	return d
}
func TestEvolvedOccupiedMobilePhasesAndEconomyHandoff(t *testing.T) {
	d := evolvedMobileLoad(t)
	economy := evolvedOccupiedLoad(t)
	events := 0
	routes, noTravel := 0, 0
	for _, c := range d.Cases {
		t.Run(c.Name, func(t *testing.T) {
			before := unpack(t, d.Worlds[c.BeforeSHA])
			if digest(before) != c.BeforeSHA {
				t.Fatal("before identity")
			}
			saved := bytes.Clone(before)
			in := continuationInputs(t, c.continuationCase)
			recipe, _ := json.Marshal(in)
			world, stats, e := ReplayEvolvedOccupiedHomeMobile(before, in)
			if e != nil {
				t.Fatal(e)
			}
			if digest(world) != c.SHA || stats.InitialState != c.State || stats.FinalState != c.Final || stats.Draws != c.Draws || stats.Groups != c.Groups || stats.WandererSector != c.Wanderer || stats.BaseSector != c.Base || stats.Allocations != c.Allocations || stats.Cache != c.Cache || stats.XannoronIncrement != c.Increment {
				t.Fatalf("complete phase/receipt mismatch: state %x/%x draws %d/%d", stats.FinalState, c.Final, stats.Draws, c.Draws)
			}
			if !reflect.DeepEqual(stats.WandererAttempts, c.Attempts) || stats.Births != nil {
				t.Fatal("existing homes only")
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
			routes += len(stats.Routes)
			for i, r := range stats.Routes {
				if r.Group == 20 && len(stats.Entered[i]) == 0 && r.Strength > 0 {
					noTravel++
					at := (51+r.Target-1)*137 + 129
					if !bytes.Equal(world[at:at+4], before[at:at+4]) {
						t.Fatal("non-travel group20 must skip mine increment")
					}
				}
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
				work, ps, e := ReplayEvolvedOccupiedPlanets(unpack(t, economy.Worlds[p.BeforeSHA]), planetInputs(t, p))
				if e != nil || digest(work) != c.BeforeSHA || ps.FinalState != c.State {
					t.Fatal("calculated economy handoff", e)
				}
				derived := in
				derived.State = ps.FinalState
				joined, js, e := ReplayEvolvedOccupiedHomeMobile(work, derived)
				if e != nil || digest(joined) != c.SHA || js.FinalState != c.Final {
					t.Fatal("actual Go phases", e)
				}
			}
			if !found {
				t.Fatal("missing economy case")
			}
			world[0] ^= 1
			if !bytes.Equal(before, saved) {
				t.Fatal("output alias")
			}
		})
	}
	if routes != 465 || noTravel != 9 {
		t.Fatal("route/non-travel inventory", routes, noTravel)
	}
	if events != 108 {
		t.Fatal("event inventory", events)
	}
}

func TestEvolvedOccupiedMobileAtomicRefusals(t *testing.T) {
	d := evolvedMobileLoad(t)
	c := d.Cases[0]
	for _, row := range d.Cases {
		if len(row.Events) > 0 {
			c = row
			break
		}
	}
	tests := map[string]func([]byte, *ContinuationInputs){
		"state":            func(w []byte, i *ContinuationInputs) { i.State = 1 << 24 },
		"clock exhaustion": func(w []byte, i *ContinuationInputs) { i.Helpers = i.Helpers[:len(i.Helpers)-1] },
		"surplus clock":    func(w []byte, i *ContinuationInputs) { i.Helpers = append(i.Helpers, i.Helpers[len(i.Helpers)-1]) },
		"caller":           func(w []byte, i *ContinuationInputs) { i.Helpers[len(i.Helpers)-1].Caller ^= 1 },
		"family":           func(w []byte, i *ContinuationInputs) { i.Helpers[0].Family = 2 },
		"clock":            func(w []byte, i *ContinuationInputs) { i.Helpers[0].Timer = encode(86400) },
		"day":              func(w []byte, i *ContinuationInputs) { planetPut(w, 1, 81, 305) },
		"geometry":         func(w []byte, i *ContinuationInputs) { planetPut(w, 1, 53, 52) },
		"human":            func(w []byte, i *ContinuationInputs) { planetPut(w, 2, 85, 1) },
		"hiring":           func(w []byte, i *ContinuationInputs) { planetPut(w, 3052, 89, 1) },
		"revenge":          func(w []byte, i *ContinuationInputs) { planetPut(w, 72, 105, 1) },
		"home name":        func(w []byte, i *ContinuationInputs) { w[4150*137] ^= 1 },
		"home owner":       func(w []byte, i *ContinuationInputs) { planetPut(w, 4150, 73, 0) },
		"home day":         func(w []byte, i *ContinuationInputs) { planetPut(w, 4150, 41, 306) },
		"new slot":         func(w []byte, i *ContinuationInputs) { planetPut(w, 4055, 85, 1) },
		"HQ":               func(w []byte, i *ContinuationInputs) { planetPut(w, 52, 105, 1) },
		"pointer":          func(w []byte, i *ContinuationInputs) { planetPut(w, 53, 105, 3001) },
		"orphan Xannor":    func(w []byte, i *ContinuationInputs) { planetPut(w, 52, 81, 10000); planetPut(w, 52, 85, -1) },
		"noninteger force": func(w []byte, i *ContinuationInputs) { planetPut(w, 905, 81, .5) },
		"unknown owner":    func(w []byte, i *ContinuationInputs) { planetPut(w, 905, 81, 1); planetPut(w, 905, 85, 2) },
		"neutral force":    func(w []byte, i *ContinuationInputs) { planetPut(w, 905, 81, 38); planetPut(w, 905, 85, 0) },
		"warp":             func(w []byte, i *ContinuationInputs) { planetPut(w, 52, 41, 3001) },
		"missing home": func(w []byte, i *ContinuationInputs) {
			for r := 52; r <= 3051; r++ {
				if portSingleValue([4]byte(w[(r-1)*137+93:(r-1)*137+97])) == 99 {
					planetPut(w, r, 93, 0)
				}
			}
		},
		"late mine":            func(w []byte, i *ContinuationInputs) { planetPut(w, 905, 129, 1) },
		"late foreign defense": func(w []byte, i *ContinuationInputs) { planetPut(w, 905, 81, 1); planetPut(w, 905, 85, -2) },
		"late exhausted ground": func(w []byte, i *ContinuationInputs) {
			planetPut(w, 4053, 77, float64(c.Events[0].InitialGround-c.Events[len(c.Events)-1].Ground))
		},
		"late zero ground":       func(w []byte, i *ContinuationInputs) { planetPut(w, 4053, 77, 0) },
		"late fractional ground": func(w []byte, i *ContinuationInputs) { planetPut(w, 4053, 77, .5) },
	}
	for name, change := range tests {
		t.Run(name, func(t *testing.T) {
			w := unpack(t, d.Worlds[c.BeforeSHA])
			i := continuationInputs(t, c.continuationCase)
			change(w, &i)
			saved := bytes.Clone(w)
			recipe, _ := json.Marshal(i)
			out, s, e := ReplayEvolvedOccupiedHomeMobile(w, i)
			after, _ := json.Marshal(i)
			if e == nil || out != nil || !reflect.DeepEqual(s, EvolvedOccupiedMobileStats{}) || !bytes.Equal(saved, w) || !bytes.Equal(recipe, after) {
				t.Fatal("non-atomic refusal", e)
			}
		})
	}
	w := unpack(t, d.Worlds[c.BeforeSHA])
	i := continuationInputs(t, c.continuationCase)
	if _, _, e := ReplayExistingHomeContinuation(w, i); e == nil {
		t.Fatal("old peaceful admission widened")
	}
	if _, _, e := ReplayNeutralGroundAssault(w, NeutralGroundInputs{Group: 2, Sector: 854, Force: 1, State: i.State}); e == nil {
		t.Fatal("old strong-ground admission widened")
	}
	if _, _, e := ReplayEvolvedOccupiedHomeMobile(w[:100], i); e == nil {
		t.Fatal("short world")
	}
}
