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

type evolvedTailCase struct {
	Name             string
	BeforeSHA        string `json:"before_sha256"`
	State            uint32 `json:"initial_state"`
	Final            uint32 `json:"final_state"`
	SHA              string `json:"expected_sha256"`
	Draws, Candidate int
	Lottery          string
	Helpers          []struct {
		Family int
		Caller uint16
		Timer  string
	}
	Seeds []struct {
		Family int
		Caller uint16
		Timer  string
		Old    uint32 `json:"old_state"`
		Seed   uint32 `json:"seeded_state"`
	}
	Mercenary struct {
		Force          int
		DesertionDraws int   `json:"desertion_draws"`
		MovementDraws  int   `json:"movement_gate_draws"`
		TargetDraws    int   `json:"target_draws"`
		Physical       []int `json:"desertion_sectors"`
		Final          []int `json:"final_sectors"`
		Activations    []struct {
			Origin, Force, Target int
			Gate                  string
			Held                  bool
			Candidates, Route     []int
		}
	}
}
type evolvedTailFixture struct {
	Format      string
	Worlds      map[string]string
	Cases       []evolvedTailCase
	Comparisons int `json:"native_six_file_comparisons"`
	Witnesses   int `json:"native_rng_witnesses"`
	Fields      int `json:"native_cache_fields"`
}

func evolvedTailLoad(t *testing.T) evolvedTailFixture {
	t.Helper()
	b, e := os.ReadFile("testdata/evolved_tail.json")
	if e != nil {
		t.Fatal(e)
	}
	var d evolvedTailFixture
	if e = json.Unmarshal(b, &d); e != nil {
		t.Fatal(e)
	}
	if d.Format != "qb-evolved-tail-v1" || len(d.Cases) != 15 || d.Comparisons != 90 || d.Fields != 1440 || d.Witnesses < 501 {
		t.Fatal("qualified inventory")
	}
	return d
}
func evolvedTailInputs(t *testing.T, c evolvedTailCase) EvolvedTailInputs {
	t.Helper()
	in := EvolvedTailInputs{State: c.State}
	for _, h := range c.Helpers {
		in.Helpers = append(in.Helpers, ContinuationClock{Family: h.Family, Caller: h.Caller, Timer: planetRaw(t, h.Timer)})
	}
	return in
}
func TestEvolvedTailQualifiedPhases(t *testing.T) {
	d := evolvedTailLoad(t)
	moving, reactivated := 0, 0
	for _, c := range d.Cases {
		t.Run(c.Name, func(t *testing.T) {
			before := unpack(t, d.Worlds[c.BeforeSHA])
			if digest(before) != c.BeforeSHA {
				t.Fatal("modeled input identity")
			}
			saved := bytes.Clone(before)
			in := evolvedTailInputs(t, c)
			helpers := append([]ContinuationClock(nil), in.Helpers...)
			out, s, e := ReplayEvolvedNPCTail(before, in)
			if e != nil {
				t.Fatal(e)
			}
			if digest(out) != c.SHA {
				t.Fatal("complete Python-qualified tail world mismatch")
			}
			if s.InitialState != c.State || s.FinalState != c.Final || s.Draws != c.Draws || s.Candidate != c.Candidate || s.Lottery != planetRaw(t, c.Lottery) || s.MercenaryForce != c.Mercenary.Force || s.MovementGateDraws != c.Mercenary.MovementDraws || s.TargetDraws != c.Mercenary.TargetDraws || !slices.Equal(s.DesertionSectors, c.Mercenary.Physical) || !slices.Equal(s.FinalMercenarySectors, c.Mercenary.Final) || len(s.DesertionSectors) != c.Mercenary.DesertionDraws {
				t.Fatalf("tail statistics: %+v", s)
			}
			if len(s.Seeds) != len(c.Seeds) || len(s.Activations) != len(c.Mercenary.Activations) {
				t.Fatal("source call/activation inventory")
			}
			for i, seed := range s.Seeds {
				w := c.Seeds[i]
				if seed.Clock.Family != w.Family || seed.Clock.Caller != w.Caller || seed.Clock.Timer != planetRaw(t, w.Timer) || seed.OldState != w.Old || seed.SeededState != w.Seed {
					t.Fatal("modeled helper reseed")
				}
			}
			for i, a := range s.Activations {
				w := c.Mercenary.Activations[i]
				if a.Origin != w.Origin || a.Target != w.Target || a.Force != w.Force || a.Gate != planetRaw(t, w.Gate) || a.Held != w.Held || !slices.Equal(a.Candidates, w.Candidates) || !slices.Equal(a.Route, w.Route) {
					t.Fatal("descending mutable scan / route")
				}
				if !a.Held {
					moving++
					for _, o := range []int{81, 85} {
						pos := (50+a.Origin)*RecordSize + o
						if [4]byte(out[pos:pos+4]) != ([4]byte{0, 0, 0x28, 0}) {
							t.Fatal("departure FAC residue")
						}
					}
				}
			}
			if len(s.Activations) > 1 {
				reactivated++
			}
			owned := map[int]bool{}
			for _, a := range s.Activations {
				for _, sector := range []int{a.Origin, a.Target} {
					if sector == 0 {
						continue
					}
					for _, o := range []int{81, 85} {
						for j := 0; j < 4; j++ {
							owned[(50+sector)*RecordSize+o+j] = true
						}
					}
				}
			}
			for i, b := range out {
				if !owned[i] && b != saved[i] {
					t.Fatal("unwritten byte changed")
				}
			}
			if !bytes.Equal(before, saved) || !slices.Equal(helpers, in.Helpers) || in.State != c.State {
				t.Fatal("mutated input")
			}
			out[0] ^= 255
			if !bytes.Equal(before, saved) {
				t.Fatal("output alias")
			}
		})
	}
	if moving == 0 || reactivated == 0 {
		t.Fatal("native Mercenary movement/reactivation coverage")
	}
}
func TestGoEvolvedEconomyContinuationAndTail(t *testing.T) {
	d := evolvedTailLoad(t)
	p := planetLoad(t)
	c := continuationLoad(t)
	count := 0
	for _, tail := range d.Cases {
		for _, continuation := range c.Cases {
			if tail.Name != "convergence/"+continuation.Name {
				continue
			}
			for _, phase := range p.Cases {
				if phase.Name != continuation.Name {
					continue
				}
				economy, ps, e := ReplayEvolvedPlanets(unpack(t, p.Worlds[phase.BeforeSHA]), planetInputs(t, phase))
				if e != nil {
					t.Fatal(e)
				}
				ci := continuationInputs(t, continuation)
				ci.State = ps.FinalState
				mobile, ms, e := ReplayExistingHomeContinuation(economy, ci)
				if e != nil {
					t.Fatal(e)
				}
				if digest(mobile) != tail.BeforeSHA || ms.FinalState != tail.State {
					t.Fatal("Go-only tail handoff identity")
				}
				ti := evolvedTailInputs(t, tail)
				ti.State = ms.FinalState
				out, ts, e := ReplayEvolvedNPCTail(mobile, ti)
				if e != nil || digest(out) != tail.SHA || ts.FinalState != tail.Final {
					t.Fatal("three-phase Go composition", e)
				}
				count++
			}
		}
	}
	if count != 6 {
		t.Fatal("composition coverage")
	}
}
func TestEvolvedTailAtomicRefusals(t *testing.T) {
	d := evolvedTailLoad(t)
	var c evolvedTailCase
	for _, v := range d.Cases {
		if strings.HasPrefix(v.Name, "route-mercenary-100000/") {
			c = v
			break
		}
	}
	cases := map[string]func([]byte, *EvolvedTailInputs){
		"state":            func(w []byte, i *EvolvedTailInputs) { i.State = 1 << 24 },
		"human":            func(w []byte, i *EvolvedTailInputs) { planetPut(w, 2, 85, 1) },
		"tax":              func(w []byte, i *EvolvedTailInputs) { planetPut(w, 3052, 89, 1) },
		"Base":             func(w []byte, i *EvolvedTailInputs) { planetPut(w, 4150, 85, 0) },
		"revenge":          func(w []byte, i *EvolvedTailInputs) { planetPut(w, 72, 105, 1) },
		"fractional force": func(w []byte, i *EvolvedTailInputs) { planetPut(w, 52, 81, .5) },
		"human owner":      func(w []byte, i *EvolvedTailInputs) { s := c.Mercenary.Physical[0]; planetPut(w, 51+s, 85, 2) },
		"clock exhaustion": func(w []byte, i *EvolvedTailInputs) { i.Helpers = nil },
		"wrong caller":     func(w []byte, i *EvolvedTailInputs) { i.Helpers[0].Caller = 0x437a },
		"wrong family":     func(w []byte, i *EvolvedTailInputs) { i.Helpers[0].Family = 2 },
		"timer":            func(w []byte, i *EvolvedTailInputs) { i.Helpers[0].Timer = encode(86400) },
		"unconsumed clock": func(w []byte, i *EvolvedTailInputs) {
			i.Helpers = append(i.Helpers, ContinuationClock{Family: 1, Caller: 0x53b4})
		},
		"entered mine": func(w []byte, i *EvolvedTailInputs) {
			s := c.Mercenary.Activations[0].Route[1]
			planetPut(w, 51+s, 129, 1)
		},
		"entered planet": func(w []byte, i *EvolvedTailInputs) {
			s := c.Mercenary.Activations[0].Route[1]
			planetPut(w, 51+s, 93, 2)
		},
		"entered defense": func(w []byte, i *EvolvedTailInputs) {
			// Relocate an existing defense so eager draw count and target stay fixed.
			target := c.Mercenary.Activations[0].Route[1]
			for _, sector := range c.Mercenary.Physical {
				a := (50 + sector) * RecordSize
				if portSingleValue([4]byte(w[a+85:a+89])) != -1 {
					continue
				}
				force := portSingleValue([4]byte(w[a+81 : a+85]))
				planetPut(w, 51+sector, 81, 0)
				planetPut(w, 51+sector, 85, 0)
				planetPut(w, 51+target, 81, force)
				planetPut(w, 51+target, 85, -1)
				return
			}
			t.Fatal("no physical Xannor defense")
		},
	}
	for name, change := range cases {
		t.Run(name, func(t *testing.T) {
			w := unpack(t, d.Worlds[c.BeforeSHA])
			in := evolvedTailInputs(t, c)
			change(w, &in)
			saved := bytes.Clone(w)
			helpers := append([]ContinuationClock(nil), in.Helpers...)
			out, s, e := ReplayEvolvedNPCTail(w, in)
			if e == nil || out != nil || !reflect.DeepEqual(s, EvolvedTailStats{}) {
				t.Fatal("non-atomic refusal")
			}
			if name == "entered defense" && !strings.Contains(e.Error(), "merge/defense combat") {
				t.Fatal("wrong rejection boundary", e)
			}
			if !bytes.Equal(w, saved) || !slices.Equal(in.Helpers, helpers) {
				t.Fatal("mutated input on refusal")
			}
		})
	}
	if out, _, e := ReplayEvolvedNPCTail(nil, EvolvedTailInputs{}); e == nil || out != nil {
		t.Fatal("world extent")
	}
}
func TestEvolvedTailHeldAndLotteryGate(t *testing.T) {
	// Synthetic before-only boundary, not an additional native execution.
	d := evolvedTailLoad(t)
	w := unpack(t, d.Worlds[d.Cases[0].BeforeSHA])
	for s := 1; s <= 3000; s++ {
		planetPut(w, 51+s, 81, 0)
		planetPut(w, 51+s, 85, 0)
	}
	planetPut(w, 3051, 81, 37)
	planetPut(w, 3051, 85, -2)
	planetPut(w, 3051, 93, 99)
	state := uint32(0)
	for ; state < 10000; state++ {
		g := qbrng.New(state)
		g.Float32()
		gate := g.Float32()
		lottery := g.Float32()
		if gate < .66 && lottery < .5 {
			break
		}
	}
	if state == 10000 {
		t.Fatal("synthetic seed")
	}
	out, s, e := ReplayEvolvedNPCTail(w, EvolvedTailInputs{State: state})
	if e != nil {
		t.Fatal(e)
	}
	if !bytes.Equal(w, out) || len(s.Activations) != 1 || !s.Activations[0].Held || s.Candidate != 0 || s.Draws != 3 || len(s.Seeds) != 0 {
		t.Fatal("held gate or absent lottery clock")
	}
	_, _, e = ReplayEvolvedNPCTail(w, EvolvedTailInputs{State: state, Helpers: []ContinuationClock{{Family: 1, Caller: 0x53b4}}})
	if e == nil {
		t.Fatal("unused lottery clock admitted")
	}
}

func TestEvolvedTailCountsPhysicalForcesNotGroupPointers(t *testing.T) {
	d := evolvedTailLoad(t)
	c := d.Cases[0]
	w := unpack(t, d.Worlds[c.BeforeSHA])
	for g := 0; g < 20; g++ {
		planetPut(w, 52+g, 105, float64(c.Mercenary.Physical[0]))
	}
	out, s, e := ReplayEvolvedNPCTail(w, evolvedTailInputs(t, c))
	if e != nil {
		t.Fatal(e)
	}
	if s.Draws != c.Draws || s.FinalState != c.Final || len(s.DesertionSectors) != 3 || !bytes.Equal(w, out) {
		t.Fatal("duplicate pointer inflated desertion draws")
	}
	timer := planetRaw(t, c.Helpers[0].Timer)
	if _, e := ReplayInitialNPCTail(w, TailInputs{State: c.State, CandidateTimer: &timer}); e == nil {
		t.Fatal("historical initial profile admitted duplicate layout")
	}
}

func TestEvolvedTailSameOriginReseedsWithoutAnotherGate(t *testing.T) {
	// Construct source inputs using qualified RND, not a captured endpoint oracle.
	d := evolvedTailLoad(t)
	w := unpack(t, d.Worlds[d.Cases[0].BeforeSHA])
	for s := 1; s <= 3000; s++ {
		planetPut(w, 51+s, 81, 0)
		planetPut(w, 51+s, 85, 0)
	}
	g := qbrng.New(0)
	g.Float32()
	g.Float32()
	g.RandomizeMBF([4]byte{})
	origin := int(float32(g.Float32()*3000)) + 1
	old := g.State()
	target := 0
	var timer [4]byte
	for seconds := 1; seconds < 86400; seconds++ {
		h := qbrng.New(old)
		timer = encode(seconds)
		h.RandomizeMBF(timer)
		n := int(float32(h.Float32()*3000)) + 1
		if n > origin {
			target = n
			g = h
			break
		}
	}
	if target == 0 {
		t.Fatal("synthetic ascending target")
	}
	planetPut(w, 51+origin, 81, 37)
	planetPut(w, 51+origin, 85, -2)
	planetPut(w, 51+origin, 93, 0)
	planetPut(w, 51+target, 93, 0)
	planetPut(w, 51+target, 129, 0)
	for j := 0; j < 6; j++ {
		planetPut(w, 51+origin, 41+4*j, 0)
	}
	planetPut(w, 51+origin, 41, float64(target))
	in := EvolvedTailInputs{State: 0, Helpers: []ContinuationClock{{Family: 1, Caller: 0x48cf}, {Family: 1, Caller: 0x48cf, Timer: timer}}}
	if g.Float32() >= .5 {
		in.Helpers = append(in.Helpers, ContinuationClock{Family: 1, Caller: 0x53b4})
	}
	_, s, e := ReplayEvolvedNPCTail(w, in)
	if e != nil {
		t.Fatal(e)
	}
	if s.MovementGateDraws != 1 || s.TargetDraws != 2 || len(s.Activations) != 1 || !slices.Equal(s.Activations[0].Candidates, []int{origin, target}) {
		t.Fatal("same-origin retry chronology")
	}
}
